---
layout: default
title: Install
nav_order: 2
has_toc: true
---

# Install / setup

Installing Beaker is easy! All you need to do is run:

```bash
pip install beaker-kernel
```

Next, you'll run `beaker config update` to set up your configuration. This will create a `beaker.conf` file in your home directory's `.config` folder. You can leave everything as the default except for the `LLM_SERVICE_TOKEN` which you'll need to set to your OpenAI API (or other LLM provider) key.

Now that you've got things installed and set up, just simply run:

```bash
beaker notebook
``` 

Your notebook server will start up and Beaker will be ready to use at [`localhost:8888`](http://localhost:8888).

## Installing custom contexts

To install a custom context, you should navigate to the context's folder and run:

```bash
$ pip install -e .
```

This will install the context so that it can be automatically loaded the next time you start Beaker.

For debugging your custom context, you can try navigating to [`localhost:8888/dev`](http://localhost:8888/dev) which will launch the development UI. This gives you access to enhanced logging, the ability to inspect messages, and the ability to launch custom actions from the UI.

## Developer setup

For developers interested in modifying Beaker or contributing to it, you can start by cloning the repo and running:

```bash
$ make dev
```

This will start Beaker in development mode which will automatically reload when you make changes to the code so you can quickly iterate on your changes to the core codebase.