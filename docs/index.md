---
layout: default
title: Beaker Kernel
nav_order: 1
has_toc: true
---

# Beaker Kernel: Contextually-aware notebooks with built-in AI assistant

Beaker is a custom Jupyter kernel that allows you not just work in notebooks in the language of your choice, but to integrate notebooks into any web application. You can design your own notebook or not even display a notebook at all, allowing native elements in your web application to run code in any language in a persistent session. And by leveraging the power of LLMs, you can easily super-power your application and/or notebook with a powerful [ReAct](https://www.promptingguide.ai/techniques/react) agent powered by [Archytas](https://github.com/jataware/archytas).

The Beaker AI agent can generate code to populate an existing notebook, or run code in the notebook environment in the background, passing the updated state or task response to the front-end for display. This allows for tasks such as asking Beaker to create a certain document, and not only will Beaker generate the text of the document, but will take care of creating, filling, and saving the document, and then notify the front-end the id of the document so it can be displayed to the user once it's complete.


## Components of Beaker

This package contains the following components:

* The Beaker Jupyter kernel (`beaker`)
* A stand-alone Jupyter service (`service`)
  * Contains a both a production-ready custom server and a standalone development interface
* A library of contexts (`contexts`) that can be extended to add functionality to Beaker
* The Beaker AI/LLM agent (`agent`) that brings the power of LLMs to whatever you are doing, wherever you are doing it


## How Beaker works

The Beaker kernel acts as a custom Python kernel that sits between the user interface and the execution environment (subkernel) and proxies messages, as needed, to the subkernel. The Beaker kernel inspects the messages that pass through it and may take extra actions, as needed. This allows you to define custom message types that result in custom behavior, have extra behavior be triggered by normal actions, or modify the request and/or response messages on the fly.

When it is first initialized, the Beaker kernel will start a subkernel using its defaults (usually Python3). If you check the existing kernels in the Jupyter service, will see both kernels listed. At this point, you can use Beaker as a naive kernel and all regular messages will be sent to the subkernel as if you were connected directly to the subkernel itself. To really get started with Beaker, you need to set a context.




## Differences from vanilla Jupyter

This setup uses stock Jupyter services as provided in the Jupyter Python packages.

The entry point of the docker file runs the file main.py which starts a JupyterLab Server App. The only differences here are:
1. This service does not run any front-end and only provides
  API and websocket access as Terarium is meant to be the interface when deployed.
2. Some settings are changed to allow access through the
  Terarium interface and be accessed by the proxy kernel:
    1. allow_orgin rule
    2. disable_check_xsrf security issue to allow the proxy
    kernel to make API calls
