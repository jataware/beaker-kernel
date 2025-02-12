import logging
import os
import urllib.parse

from jupyter_client.ioloop.manager import AsyncIOLoopKernelManager
from jupyter_server.services.kernels.kernelmanager import AsyncMappingKernelManager
from jupyter_server.serverapp import ServerApp
from jupyterlab_server import LabServerApp
from tornado.web import StaticFileHandler

from beaker_kernel.lib.app import BeakerApp
from beaker_kernel.lib.config import config
from beaker_kernel.lib.utils import import_dotted_class
from beaker_kernel.service.handlers import (
    PageHandler, StatsHandler, ConfigHandler, ContextHandler, SummaryHandler, ExportAsHandler, DownloadHandler,
    ConfigController, AppConfigHandler, request_log_handler, sanitize_env
)


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
        # Build up static and page definitions for handler pages and static files
        pages = []
        statics = []
        default_page_filename = "index.html"

        beaker_app: BeakerApp = self.extension_config.get("app", None)
        if beaker_app and beaker_app.asset_dir:
            if os.path.isdir(beaker_app.asset_dir):
                self.handlers.append((f"/assets/{beaker_app.slug}/(.*)", StaticFileHandler, {"path": beaker_app.asset_dir}))

        try:
            ui_files = os.listdir(self.ui_path)
        except FileNotFoundError:
            ui_files = []
        for file in ui_files:
            if file.startswith(('_', '.')):
                continue
            if file.endswith(".html"):
                page = os.path.splitext(file)[0]
                if beaker_app:
                    if page in beaker_app.pages:
                        pages.append(page)
                        if getattr(beaker_app._pages[page], "default", False):
                            default_page_filename = file
                else:
                    pages.append(page)
            else:
                if os.path.isdir(os.path.join(self.ui_path, file)):
                    statics.append(f"{file}/")
                else:
                    statics.append(f"{file}$")


        self.handlers.append(("/contexts", ContextHandler))
        self.handlers.append(("/config/control", ConfigController))
        self.handlers.append(("/config", ConfigHandler))
        self.handlers.append(("/stats", StatsHandler))
        self.handlers.append(("/appconfig.js", AppConfigHandler))
        self.handlers.append((r"/admin/?()", StaticFileHandler, {"path": self.ui_path, "default_filename": "admin.html"}))
        self.handlers.append((r"/export/(?P<format>\w+)", ExportAsHandler)),
        self.handlers.append((f"/()", PageHandler, {"path": self.ui_path, "default_filename": default_page_filename}))
        if statics:
            static_handler = ("/((" + "|".join(statics) + ").*)", StaticFileHandler, {"path": self.ui_path})
            self.handlers.append(static_handler)
        if pages:
            page_handler = ("/(" + "|".join(pages) + ")", PageHandler, {"path": self.ui_path, "default_filename": default_page_filename})
            self.handlers.append(page_handler)
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
