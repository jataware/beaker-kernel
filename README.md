# Jupyter package

This package provides a custom Jupyter kernel that allows extra communication
beyond the usual Jupyter message types to allow for the kernel to interact with
an LLM (GPT-4) and answer questions and generate code that is runnable in
native notebook code cells.


This package contains 4 different products:

* A Python module named `beaker_kernel` (`pyproject.toml`)
* A Jupyter kernel (`beaker`)
* A Jupyter service (`main.py`)
* A standalone development interface (`dev_ui`)

## Install / setup

### beaker_kernel Python module

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

More information can be found in the official docs (link coming soon).
