# Beaker Kernel: Contextually-aware notebooks with built-in AI assistant
Beaker allows you not just work in notebooks, but to integrate notebooks into any web application, and by leveraging the power of LLMs, you can easily super-power your application and/or notebook with a powerful [ReAct](https://www.promptingguide.ai/techniques/react) agent powered by [Archytas](https://github.com/jataware/archytas).

The Beaker agent can generate code to populate an existing notebook, or run code in the notebook environment in the background, passing the updated state or task response to the front-end for display. This allows for tasks such as asking Beaker to create a certain document, and not only will Beaker generate the text of the document, but will take care of creating, filling, and saving the document, and then notify the front-end the id of the document so it can be displayed to the user once it's complete.


## Components of Beaker

This package contains the following components:

* The Beaker Jupyter kernel (`beaker`)
* A stand-alone Jupyter service (`service`)
  * Contains a both a production-ready custom server and a standalone development interface
* A library of contexts (`contexts`) that can be extended to add functionality to Beaker


## How Beaker works

The Beaker kernel acts custom Python kernel that sits between the user interface and the execution environment (subkernel) and proxies messages, as needed, to the subkernel. The Beaker kernel inspects the messages that pass through it and may take extra actions, as needed. This allows you to define custom message types that result in custom behavior, have extra behavior be triggered by normal actions, or modify the request and/or response messages on the fly.

When it is first initialized, the Beaker kernel will start a subkernel using its defaults (usually Python3). If you check the existing kernels in the Jupyter service, will see both kernels listed. At this point, you can use Beaker as a naive kernel and all regular messages will be sent to the subkernel as if you were connected directly to the subkernel itself. To really get started with Beaker, you need to set a context.

### Contexts

Beaker works best when used within a particular context. At a high level, a context has three parts: What language you're working in, what problem space are you working within, and any particular items/objects you are working on.

When connecting to Beaker, usually the first action following connecting is to set the context.

#### Setting a Beaker context will do the following:

* Change the subkernel language if needed (destroying the current subkernel and creating a new one)
* Set the LLM prompt for the context
* Run initialization code in the subkernel to pre-import libraries and load objects/instances  (optional)
* Register any context-specific custom message handlers (optional)
* Register any "post-execute" actions to run after a notebook cell is executed (optional)

** Currently, setting a context is the only way to change the language of the subkernel.

#### Setting the context

You set a context by sending a custom message to the beaker kernel. The message should have the following format:

`msg_type`: `context_setup_request`<br/>
`msg_payload`:<br/>
```json
{
  "language": "<subkernel name>",
  "context": "<context name>",
  "context_info": {"json payload of any settings/info required to start the context"}
}
```

The list of available languages and contexts depends on what has been installed. The `context_info` payload is dependent on the particular context chosen.

The Beaker service provides an end-point that will return a JSON payload listing the installed contexts and the languages available for each context to allow discovery.

This endpoint is found at: `http://{jupyter_url}/contexts`, usually, `http://localhost:8888/contexts`

### Components of contexts

#### Toolsets

Toolsets are, primarily, set of tools provided to the LLM that allows the LLM to interact with both the subkernel environment and the front-end using the [Archytas ReAct framework](https://github.com/jataware/archytas). Details for how toolsets work and should be defined can be found in the [Archytas documentation](https://github.com/jataware/archytas).


#### Codesets

Codesets define snippets of code that run in a subkernel. These can often be thought of as analogous to functions, although it can be important to keep in mind that these are executed directly within the subkernel environment exactly as if the codeset content were executed within a notebook code cell.

Codesets are separated by context and language, allowing for analogous behavior across different subkernel languages for each configured contexts.

Each codeset is defined using the [Jinja templating language](https://jinja.palletsprojects.com/en/3.1.x/), allowing for dynamic variation of the code based on the current state of the context/subkernel environment.

Code from a codeset can be rendered using the `get_code()` method on an context object.
Once the template is rendered in to properly formatted code, it can be executed in the subkernel using the `execute()` or `evaluate()` methods on the context.


#### Subkernels

The subkernel files within the context directory are required to define some common behaviours and provide a function for Beaker to behave consistently and properly parse the responses from subkernel executions.

#TODO: Move subkernels out of context?


## Install / setup

### Docker



### python (local)

Normal installation:
```bash
# Requires [hatch](https://github.com/pypa/hatch)
$ pip install hatch  # If needed
$ pip install .
```

Development installation
```bash
$ pip install -e .
```


### Jupyter kernel

The Beaker Kernel should be automatically installed if Beaker is installed
using the method above.

If the kernel is not installed, or you want to install the kernel manually
ensure that the `beaker_kernel` package is accessible in your environmnet
and then simply copy or symlink the `kernel.json` file to one of the 
directories defined in the following document inside a unique directory:

https://jupyter-client.readthedocs.io/en/stable/kernels.html#kernel-specs


For example:
```bash
$ cp -r beaker_kernel/kernel.json /usr/share/jupyter/kernels/beaker/kernel.json
```

Once the directory exists and the jupyter service is restarted the kernel
should be available for selection.


## Dev setup

This package is bundled with a basic development UI for development and testing.

You will need to update the .env file with your OpenAI/GPT API key to use the
LLM.

Once you have set up the environment and added your keys you can start the dev
server by running:

```bash
$ make dev
```

This will start the Jupyter service and launch a specialized notebook
interface in your browser similar to if you ran `$ jupyter notebook` normally.


## Differences from vanilla Jupyter

This setup uses mostly stock Jupyter services as provided in the Jupyter Python
packages, with minor differences.

The entry point of the docker file runs the file main.py which
starts a JupyterLab Server App. The key differences here
are:
1. This service does not run any front-end outside of dev mode and only provides
  API and websocket access as this service is expected to connect to a custom 
  interface.
2. Some security settings are loosened to allow access through the a custom 
  interface and allow Beaker to access the Jupyter service API to manage 
  subkernels:
    1. `allow_orgin` rule loosened as UI and Kernel likely do not share the same
      domain.
    2. `disable_check_xsrf` set so as the Jupyter API does not require xsrf 
      checks, allowing Beaker to make calls directly

These security settings will be reviewed in the future in an attempt to tighten
the modifications.

More information can be found in [the official docs](https://jataware.github.io/beaker-kernel/).
