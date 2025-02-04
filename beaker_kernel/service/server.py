import logging
import os
import shutil
import urllib.parse

from jupyter_client.ioloop.manager import AsyncIOLoopKernelManager
from jupyter_server.services.kernels.kernelmanager import AsyncMappingKernelManager
from jupyter_server.serverapp import ServerApp
from jupyterlab_server import LabServerApp
from tornado.web import StaticFileHandler

from beaker_kernel.lib.config import config
from beaker_kernel.service.handlers import (
    PageHandler, StatsHandler, ConfigHandler, ContextHandler, SummaryHandler, ExportAsHandler, DownloadHandler,
    ConfigController, request_log_handler, sanitize_env
)

logger = logging.getLogger(__file__)

HERE = os.path.dirname(__file__)

version = "0.0.1"


def _jupyter_server_extension_points():
    return [{"module": "beaker_kernel.service.server", "app": BeakerJupyterApp}]


class BeakerKernelManager(AsyncIOLoopKernelManager):
    agent_user: str
    subkernel_user: str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent_user = os.environ.get("BEAKER_AGENT_USER", "jupyter")
        self.subkernel_user = os.environ.get("BEAKER_SUBKERNEL_USER", "user")

    def write_connection_file(self, **kwargs: object) -> None:
        super().write_connection_file(
            server=self.parent.parent.public_url,
            **kwargs
        )
        # Set file to be owned by and modifiable by the beaker user so the beaker user can modify the file.
        os.chmod(self.connection_file, 0o0775)
        shutil.chown(self.connection_file, user=self.agent_user)

    async def _async_pre_start_kernel(self, **kw):
        # Fetch values from super()
        cmd, kw = await super()._async_pre_start_kernel(**kw)

        env = kw.pop("env", {})

        # Update user, env variables, and home directory based on type of kernel being started.
        if self.kernel_name == "beaker_kernel":
            user = self.agent_user
        else:
            user = self.subkernel_user
            env = sanitize_env(env)
        home_dir = os.path.expanduser(f"~{user}")
        env["USER"] = user
        env["HOME"] = home_dir

        # Update keyword args that are passed to Popen()
        kw["user"] = user
        kw["cwd"] = home_dir
        kw["env"] = env

        return cmd, kw
    pre_start_kernel = _async_pre_start_kernel


class BeakerKernelMappingManager(AsyncMappingKernelManager):
    kernel_manager_class = "beaker_kernel.service.server.BeakerKernelManager"
    connection_dir = os.path.join(config.beaker_run_path, "kernelfiles")

    def __init__(self, **kwargs):
        # Ensure connection dir exists and is readable
        if not os.path.isdir(self.connection_dir):
            os.makedirs(self.connection_dir, mode=0o0755)
        else:
            os.chmod(self.connection_dir, 0o0755)
        super().__init__(**kwargs)



class BeakerServerApp(ServerApp):
    """
    Customizable ServerApp for use with Beaker
    """

    kernel_manager_class = BeakerKernelMappingManager
    subkernel_user = "user"
    root_dir = os.path.expanduser(f'~{os.environ.get("BEAKER_SUBKERNEL_USER", subkernel_user)}')
    allow_root = True
    ip = "0.0.0.0"

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


class BeakerJupyterApp(LabServerApp):
    name = "beaker_kernel"
    serverapp_class = BeakerServerApp
    load_other_extensions = True
    app_name = "Beaker Jupyter App"
    app_version = version
    allow_origin = "*"
    open_browser = False
    extension_url = "/"
    connection_dir = ""

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
        # Log requests to console
        app.web_app.settings["log_function"] = request_log_handler
        return app

    def initialize_handlers(self):
        """Bypass initializing the default handler since we don't need to use the webserver, just the websockets."""
        # Build up static and page definitions for handler pages and static files
        pages = []
        statics = []
        for file in os.listdir(self.ui_path):
            if file.startswith(('_', '.')):
                continue
            if file.endswith(".html"):
                pages.append(os.path.splitext(file)[0])
            else:
                if os.path.isdir(os.path.join(self.ui_path, file)):
                    statics.append(f"{file}/")
                else:
                    statics.append(f"{file}$")

        self.handlers.append(("/contexts", ContextHandler))
        self.handlers.append(("/config/control", ConfigController))
        self.handlers.append(("/config", ConfigHandler))
        self.handlers.append(("/stats", StatsHandler))
        self.handlers.append((r"/admin/?()", StaticFileHandler, {"path": self.ui_path, "default_filename": "admin.html"}))
        self.handlers.append((r"/summary", SummaryHandler))
        self.handlers.append((r"/export/(?P<format>\w+)", ExportAsHandler)),
        self.handlers.append((f"/()", PageHandler, {"path": self.ui_path, "default_filename": "index.html"}))
        if statics:
            static_handler = ("/((" + "|".join(statics) + ").*)", StaticFileHandler, {"path": self.ui_path})
            self.handlers.append(static_handler)
        if pages:
            page_handler = ("/((" + "|".join(pages) + "))", PageHandler, {"path": self.ui_path, "default_filename": "index.html"})
            self.handlers.append(page_handler)
        super().initialize_handlers()

    def initialize_settings(self):
        # Override to allow cross domain websockets
        self.settings["allow_origin"] = "*"
        self.settings["disable_check_xsrf"] = True


if __name__ == "__main__":
    BeakerJupyterApp.launch_instance()
