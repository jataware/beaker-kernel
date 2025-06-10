import logging
import os
import urllib.parse

from jupyter_client.ioloop.manager import AsyncIOLoopKernelManager
from jupyter_server.services.kernels.kernelmanager import AsyncMappingKernelManager
from jupyter_server.serverapp import ServerApp
from jupyterlab_server import LabServerApp

from beaker_kernel.lib.app import BeakerApp
from beaker_kernel.lib.config import config
from beaker_kernel.lib.utils import import_dotted_class
from beaker_kernel.service.handlers import register_handlers, sanitize_env


logger = logging.getLogger(__file__)

HERE = os.path.dirname(__file__)

version = "0.0.1"


def _jupyter_server_extension_points():
    return [{"module": "beaker_kernel.service.notebook", "app": BeakerNotebookApp}]


class BeakerKernelManager(AsyncIOLoopKernelManager):

    @property
    def beaker_config(self):
        return getattr(self.parent, 'beaker_config')

    def write_connection_file(self, **kwargs: object) -> None:
        beaker_app: BeakerApp = self.beaker_config.get("app", None)
        default_context = beaker_app and beaker_app._default_context
        if default_context:
            app_context_dict = default_context.asdict()
            kwargs['context'] = {
                "default_context": app_context_dict.pop("slug"),
                "default_context_payload": app_context_dict.pop("payload"),
            }
            if app_context_dict:
                kwargs["context"].update(**app_context_dict)
        return super().write_connection_file(
            server=self.parent.parent.public_url,
            **kwargs
        )

    async def _async_pre_start_kernel(self, **kw):
        # Fetch values from super()
        cmd, kw = await super()._async_pre_start_kernel(**kw)
        # Sanitize env variables for subkernels to prevent accidental spillage of credentials.
        if self.kernel_name != "beaker_kernel":
            kw["env"] = sanitize_env(kw.get("env", {}))
        return cmd, kw


class BeakerKernelMappingManager(AsyncMappingKernelManager):
    kernel_manager_class = "beaker_kernel.service.notebook.BeakerKernelManager"

    @property
    def beaker_config(self):
        return getattr(self.parent, 'beaker_config', None)


class BeakerNotebookServer(ServerApp):
    """
    Customizable ServerApp for use with Beaker Notebooks to return proper urls, etc.
    """

    kernel_manager_class = BeakerKernelMappingManager
    reraise_server_extension_failures = True

    @property
    def beaker_config(self):
        return getattr(self.starter_app, 'extension_config', None)

    @property
    def public_url(self):
        return f"http://{self.ip}:{self.port}/"

    @property
    def local_url(self):
        return self.public_url

    @property
    def display_url(self):
        return f"    {self.public_url}"

    def _get_urlparts(self, path: str | None = None, include_token: bool = False) -> urllib.parse.ParseResult:
        # Always return urls without tokens
        return super()._get_urlparts(path, False)


class BeakerNotebookApp(LabServerApp):
    name = "beaker_kernel"
    serverapp_class = BeakerNotebookServer
    load_other_extensions = True
    app_name = "Beaker Jupyter App"
    app_version = version
    allow_origin = "*"
    open_browser = False
    extension_url = "/"
    reraise_server_extension_failures = True

    subcommands = {}

    ui_path = os.path.join(HERE, "ui")

    @classmethod
    def get_extension_package(cls):
        return cls.__module__

    @classmethod
    def initialize_server(cls, argv=None, load_other_extensions=True, **kwargs):
        # Set Jupyter token from config
        os.environ.setdefault("JUPYTER_TOKEN", config.jupyter_token)
        app = super().initialize_server(argv=argv, load_other_extensions=load_other_extensions, **kwargs)
        return app

    def initialize_handlers(self):
        """Bypass initializing the default handler since we don't need to use the webserver, just the websockets."""
        register_handlers(self)
        super().initialize_handlers()

    def initialize_settings(self):
        # Override to allow cross domain websockets
        self.settings["allow_origin"] = "*"
        self.settings["disable_check_xsrf"] = True

        beaker_app_slug = os.environ.get("BEAKER_APP", None)
        if beaker_app_slug:
            cls: type[BeakerApp] = import_dotted_class(beaker_app_slug)
            beaker_app: BeakerApp = cls()
            self.extension_config["app_cls"] = cls
            self.extension_config["app"] = beaker_app
        else:
            self.extension_config["app_cls"] = None
            self.extension_config["app"] = None


if __name__ == "__main__":
    BeakerNotebookApp.launch_instance()
