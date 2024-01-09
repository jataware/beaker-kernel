import os
from typing import Dict

from jupyter_server.base.handlers import JupyterHandler
from jupyter_server.extension.handler import (
    ExtensionHandlerJinjaMixin,
    ExtensionHandlerMixin,
)
from jupyter_server.utils import url_path_join as ujoin
from jupyterlab_server import LabServerApp
from tornado import httputil
from tornado.web import Application

from beaker_kernel.lib.autodiscovery import autodiscover
from beaker_kernel.lib.context import BaseContext
from beaker_kernel.lib.subkernels.base import BaseSubkernel


HERE = os.path.dirname(__file__)

version = "0.0.1"


def _jupyter_server_extension_points():
    return [{"module": __name__, "app": BeakerJupyterApp}]


class ContextHandler(ExtensionHandlerMixin, JupyterHandler):
    """
    Provide information about llm contexts via an endpoint
    """

    def get(self):
        """Get the main page for the application's interface."""

        contexts: Dict[str, BaseContext] = autodiscover("contexts")
        subkernels: Dict[str, BaseSubkernel] = autodiscover("subkernels")

        # Extract data from auto-discovered contexts and subkernels to provide options
        context_data = {
            context_slug: {
                "languages": [
                    {
                        "slug": subkernel_slug,
                        "subkernel": getattr(subkernels.get(subkernel_slug), "KERNEL_NAME")
                    }
                    for subkernel_slug in context.available_subkernels()
                    if subkernel_slug in subkernels
                ],
                "defaultPayload": context.default_payload()
            }
            for context_slug, context in contexts.items()
        }

        context_data["foo"] = {
            "languages": [
                {
                    "slug": "reddit",
                    "subkernel": "reddit-v1"
                }
            ],
            "defaultPayload": "{foo:bar}"
        }
        context_data["bar"] = {
            "languages": [
                {
                    "slug": "reddit",
                    "subkernel": "reddit-v1"
                },
                {
                    "slug": "python3",
                    "subkernel": "python3"
                }
            ],
            "defaultPayload": "{bar:foo}"
        }
        return self.write(context_data)


class BeakerJupyterApp(LabServerApp):
    name = __name__
    load_other_extensions = False
    app_name = "Beaker Jupyter App"
    app_version = version
    allow_origin = "*"
    open_browser = False

    def initialize_handlers(self):
        """Bypass initializing the default handler since we don't need to use the webserver, just the websockets."""
        self.handlers.append(("/contexts", ContextHandler))

    def initialize_settings(self):
        # Override to allow cross domain websockets
        self.settings["allow_origin"] = "*"
        self.settings["disable_check_xsrf"] = True


if __name__ == "__main__":
    BeakerJupyterApp.launch_instance()
