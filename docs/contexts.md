---
layout: default
title: Contexts
nav_order: 4
has_toc: true
has_children: true
---

# Contexts

Beaker works best when used within a particular context. At a high level, a context consist of the following:
* A subkernel which acts as your notebook environment.
  * Selecting a subkernel also sets the language you will work in and what libraries you have
  access to.
* Knowledge regarding the items/objects that you are working on in, either in the subkernel or
  via the context tool or LLM Agent.
  * The context can automatically pre-load items at startup that you are planning to work on.
  * The context keeps a persitent state, allowing you work on items in more than one way.
* A set of tools that interacts with the subkernel and the front-end.
  * A set of subkernal procedures that manipulate the subkernel environment.
  * Message handlers that accept arbitrary requests from the front-end
  * The optional post-execute action runs any time code is executed in the subkernel, allowing
  you to keep your state up-to-date or send custom preview messages of the state to the
  front-end.
* An LLM Agent that accepts human languge requests and acts on your behalf.
  * Uses all of the tools available to it, and the knowledge contained in the context to make
  decisions on how to best satisfy your request.
  * Has its own set of ReAct tools to allow it to query the subkernel, the internet, or custom
  defined services to fetch the information it needs to complete the request.
  * Is able to answer questions, generate code to accomplish a request in a new code cell, or
  just execute code in the subkernel to update the state, and more.


When connecting to Beaker, usually the first action following connecting is to set the context.

## Setting a Beaker context will do the following:

* Change the subkernel, recreating if needed (destroying the current subkernel and creating a new one)
* Set the LLM prompt so that it is appropriate for the context
* Run initialization procedure(s) in the subkernel to pre-import libraries and load objects/instances  (optional)
* Register any context-specific custom message handlers (optional)
* Register any "post-execute" actions to run after a notebook cell is executed (optional)

** Currently, setting a context is the only way to change the language of the subkernel.

### Setting the context

You set a context by sending a custom message to the beaker kernel. The message should have the following format:

`msg_type`: `context_setup_request`<br/>
`msg_payload`:<br/>
```json
{
  "language": "<subkernel name>",
  "context": "<context name>",
  "context_info": {"<json payload of any settings/info required to start the context>"}
}
```

The list of available languages and contexts depends on what has been installed. The expected contents of`context_info` payload is customizable when defining a context.

The Beaker service provides an end-point that will return a JSON payload listing the installed contexts and the languages available for each context to allow discovery.

This endpoint is found at: `http://{jupyter_url}/contexts`, usually, `http://localhost:8888/contexts`

## Components of contexts

### [Context object](contexts_context.html)

A context object contains the state for a context, provides handlers for any custom messages, initializes the LLM agent, and defines the available subkernels their relevent procedures it can use.

State for the context should be defined in the context object class's `__init__()` method. The initial values for the state are often passed in via the `config` parameter which is usually set using the values of the `context_setup_request` message's `context_info` value in the message payload.


### Message Handlers

COMING SOON


### [Agents](contexts_agent.html)

The context's agent is a persistent LLM powered chat-bot with access to shared and custom tools.

The agent is initialized as part of the context's `__int__()` method by defining the `agent_cls` class variable to be an uninitialized subclass of `beaker_kernel.lib.agent.BaseAgent`.

The agent should also be provided a set of tools, usually in the form of a toolset that it can use when reasoning how to complete a user's request. These tools can run code in the Beaker kernel's python environment, in the subkernel environment, or access sources using HTTP requests.

More information on Agents, including how to create one can be found in [the agent documentation](contexts_agent.html).


### [Subkernels](subkernels.html)

A context can work with one or more subkernel types, but only one at a time. By default, a context can work with any installed subkernel, however many contexts require deeper integration with a subkernel, and therefore require custom subkernel procedures to be defined for each compatible subkernel.

If any subkernel procedures are installed, the context is limited to the subkernels for which procedures exist. If a procedure exists for any specified subkernel, it must be specified for all configured subkernels.


### [Subkernel Procedures](contexts_procedures.html)

Subkernel procedures define snippets of code that run in a subkernel. These can often be thought of as analogous to functions, although it can be important to keep in mind that these are executed directly within the subkernel environment exactly as if the procedure's content were executed within a notebook code cell.

Procedures are separated by context and language, allowing for analogous behavior across different subkernel languages for each configured contexts.

Procedures are defined using the [Jinja templating language](https://jinja.palletsprojects.com/en/3.1.x/), allowing for dynamic variation of the code based on the current state of the context/subkernel environment.

A subkernel procedure can be rendered using the `get_code()` method on an context object.
Once the template is rendered in to properly formatted code, it can be executed in the subkernel using the `execute()` or `evaluate()` methods on the context object.
