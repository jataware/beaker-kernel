import datetime
import json
import logging
import os
from typing import Dict

from jupyter_server.base.handlers import JupyterHandler
from jupyter_server.extension.handler import (
    ExtensionHandlerMixin,
)
from jupyter_server.utils import url_path_join as ujoin
from jupyterlab_server import LabServerApp
from tornado.web import StaticFileHandler, RedirectHandler

from beaker_kernel.lib.autodiscovery import autodiscover
from beaker_kernel.lib.context import BaseContext
from beaker_kernel.lib.subkernels.base import BaseSubkernel

logger = logging.getLogger(__file__)

HERE = os.path.dirname(__file__)

version = "0.0.1"


def _jupyter_server_extension_points():
    return [{"module": "beaker_kernel.server.main", "app": BeakerJupyterApp}]


class NotebookHandler(ExtensionHandlerMixin, JupyterHandler):

    def get(self):
        return self.write(json.dumps(notebook_content))

    def post(self):
        global notebook_content
        notebook_content = self.get_json_body()
        notebook_content["lastSaved"] = datetime.datetime.utcnow().isoformat()
        return self.write(json.dumps(notebook_content))



class ConfigHandler(ExtensionHandlerMixin, JupyterHandler):
    """
    Provide config via an endpoint
    """

    def get(self):
        """
        """
        base_url = f"{self.request.protocol}://{self.request.host}"
        if self.request.protocol.endswith("s"):
            ws_proto = "wss"
        else:
            ws_proto = "ws"
        ws_url = f"{ws_proto}://{self.request.host}"

        config_data = {
            "appUrl": os.environ.get("APP_URL", base_url),
            "baseUrl": os.environ.get("JUPYTER_BASE_URL", base_url),
            "wsUrl": os.environ.get("JUPYTER_WS_URL", ws_url),
            "token": os.environ.get("JUPYTER_TOKEN", "89f73481102c46c0bc13b2998f9a4fce"),
        }
        return self.write(config_data)


class ContextHandler(ExtensionHandlerMixin, JupyterHandler):
    """
    Provide information about llm contexts via an endpoint
    """

    def get(self):
        """Get the main page for the application's interface."""
        ksm = self.kernel_spec_manager
        contexts: Dict[str, BaseContext] = autodiscover("contexts")
        possible_subkernels: Dict[str, BaseSubkernel] = autodiscover("subkernels")
        subkernel_by_kernel_index = {subkernel.KERNEL_NAME: subkernel for subkernel in possible_subkernels.values()}
        installed_kernels = [
            subkernel_by_kernel_index[kernel_name] for kernel_name in ksm.find_kernel_specs().keys()
            if kernel_name in subkernel_by_kernel_index
        ]
        contexts = sorted(contexts.items(), key=lambda item: (item[1].WEIGHT, item[0]))

        # Extract data from auto-discovered contexts and subkernels to provide options
        context_data = {
            context_slug: {
                "languages": [
                    {
                        "slug": subkernel_slug,
                        "subkernel": getattr(possible_subkernels.get(subkernel_slug), "KERNEL_NAME")
                    }
                    for subkernel_slug in context.available_subkernels()
                    if subkernel_slug in set(subkernel.SLUG for subkernel in installed_kernels)
                ],
                "defaultPayload": context.default_payload()
            }
            for context_slug, context in contexts
        }
        return self.write(context_data)


class BeakerJupyterApp(LabServerApp):
    name = "beaker_kernel"
    load_other_extensions = True
    app_name = "Beaker Jupyter App"
    app_version = version
    allow_origin = "*"
    open_browser = False
    extension_url = "/"

    def initialize_handlers(self):
        """Bypass initializing the default handler since we don't need to use the webserver, just the websockets."""
        self.handlers.append(("/contexts", ContextHandler))
        self.handlers.append(("/config", ConfigHandler))
        self.handlers.append(("/notebook", NotebookHandler))
        self.handlers.append((r"(/?)", StaticFileHandler, {"path": os.path.join(HERE, "ui"), "default_filename": "index.html"}))
        self.handlers.append((r"/index.html", StaticFileHandler, {"path": os.path.join(HERE, "ui"), "default_filename": "index.html"}))
        self.handlers.append((r"/favicon.ico", StaticFileHandler, {"path": os.path.join(HERE, "ui")}))
        self.handlers.append((r"/static/(.*)", StaticFileHandler, {"path": os.path.join(HERE, "ui", "static")}))
        self.handlers.append((r"/themes/(.*)", StaticFileHandler, {"path": os.path.join(HERE, "ui", "themes")}))
        self.handlers.append((r"/dev_ui/?(.*)", RedirectHandler, {"url": r"/{0}"}))

    def initialize_settings(self):
        # Override to allow cross domain websockets
        self.settings["allow_origin"] = "*"
        self.settings["disable_check_xsrf"] = True


if __name__ == "__main__":
    BeakerJupyterApp.launch_instance()
