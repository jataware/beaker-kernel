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

This installs a CLI tool named `beaker` which allows you to work with and administer your local Beaker environment.

Now that you've got things installed and set up, to start a new Beaker notebook, just simply run:

```bash
beaker notebook
``` 

Your notebook server will start up and Beaker will be ready to use at [`localhost:8888`](http://localhost:8888).

## Configuration

When running as a local notebook, Beaker uses a configuration file to store your local settings, such as your preferred LLM provider.

You can locate, view, and update your Beaker configuration either via the Beaker UI or via the `beaker` cli command.

### Configuration file

The Beaker configuration can be stored either as user-wide configuration file, or as a per-directory configuration.
The user-wide configuration is usually located at `/home/{user}/.config/beaker.conf`, but you can confirm by running `beaker config find`.
Alternatively, a file named `.beaker.conf` can be placed in any directory. Running `beaker` commands (including starting a notebook)
in that directory (or any subdirectories in the tree), will use the local configuration file.

**Note:** `.beaker.conf` files may store your LLM provider API tokens. Take care to not accidentally expose this file, and exclude it from
git, etc.

### Viewing/Updating

In the UI, the configuration is accessible via the `Config` side-panel. When you make changes and save the config, the Beaker will update the active configuration file, or create a new user configuration file.

Next, you'll run `beaker config update` to set up your configuration. This will create a `beaker.conf` file in your home directory's `.config` folder. You can leave everything as the default except for the `LLM_SERVICE_TOKEN` which you'll need to set to your OpenAI API (or other LLM provider) key.

## Installing contexts

Contexts are designed to be shipped as Python packages. When installed, contexts register themselves with Beaker so that Beaker and can find and use the
context.

Contexts can be found in PyPi or installed directly via Python wheel files.

For example, to install a Beaker context designed for working with the PySB modeling library, you would run:

```bash
pip install beaker-pysb
```

The PySB context will then be available the next time you start up Beaker.

Contexts can also be installed in developer/local-edit mode. 

For example, after cloning a Beaker context from Github, you could install that context by navigating to the cloned directory which contains the
`pyproject.py` file and run:

```bash
$ pip install -e .
```

This will install the context so that it can be automatically loaded the next time you start Beaker. Any changes you make to the context will be reflected the next time you set the context on a session.

For debugging your custom context, you can try navigating to [`localhost:8888/dev`](http://localhost:8888/dev) which will launch the development UI. This gives you access to enhanced logging, the ability to inspect messages, and the ability to launch custom actions from the UI.

## Developer setup

For developers interested in modifying Beaker or contributing to it, you can start by cloning the repo and running:

```bash
$ make dev
```

This will start Beaker in development mode which will automatically reload when you make changes to the code so you can quickly iterate on your changes to the core codebase.
