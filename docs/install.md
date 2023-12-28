---
layout: default
title: Install
nav_order: 2
has_toc: true
---

# Install / setup

## Structure

A Beaker install consists of the following:

* A Jupyter kernel (`beaker-kernel`)
* A Jupyter server (`beaker-server`) (optional but recommended)
* LLM integration (`archytas`) (optional)
* Custom contexts (`contexts`) (optional)


### Installing the kernel

Beaker-kernel can be installed as a normal Python package via pip, by using [Hatch](https://hatch.pypa.io/latest/), or as a docker image.


### python (local)

Normal installation:
```bash
$ pip install .
```

Dev installation:
```bash
$ pip install -e .
```

During pip install, the kernel is automatically installed in the proper location in your development environment.


## Dev setup

This package is bundled with a basic development UI for development and testing, wrapped in a docker image

To get started run this command:

```bash
$ make dev-install
```

This will ensure that all prerequisites are installed and ready for use, but you will need to update the .env file with your OpenAI/GPT API key to use the LLM.

To connect to the Terarium data service, you will need to update the .env file with the url of a running instance.

Once you have set up the environment and added your keys you can start the dev server by running:

```bash
$ make dev
```

This will start the Jupyter service and launch a specialized notebook interface in your browser similar to if you ran `$ jupyter notebook` normally.


## Adding python dependencies/updating requirements

The python requirements are maintained by Hatch and are defined in the pyproject.toml file.

Please see the [Hatch dependency documentation](https://hatch.pypa.io/latest/config/dependency/) for more details.
