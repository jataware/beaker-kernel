import logging
import os
import urllib.parse
from typing import Optional

from jupyter_client.ioloop.manager import AsyncIOLoopKernelManager
from jupyter_core.utils import ensure_async
from jupyter_server.services.kernels.kernelmanager import AsyncMappingKernelManager
from jupyter_server.serverapp import ServerApp
from jupyter_server.services.sessions.sessionmanager import SessionManager, KernelName, ModelName
from jupyterlab_server import LabServerApp
from tornado.web import StaticFileHandler

from beaker_kernel.lib.config import config
from beaker_kernel.service.handlers import (
    PageHandler, StatsHandler, ConfigHandler, ContextHandler, SummaryHandler, ExportAsHandler, DownloadHandler,
    ConfigController
)

logger = logging.getLogger(__file__)

HERE = os.path.dirname(__file__)

version = "0.0.1"


def _jupyter_server_extension_points():
    return [{"module": "beaker_kernel.service.server", "app": BeakerJupyterApp}]


def secure_env(env: dict) -> dict:
        UNSAFE_WORDS = ["KEY", "SECRET", "TOKEN", "PASSWORD"]
        safe_env = {}
        for env_name, env_value in env.items():
            for unsafe_word in UNSAFE_WORDS:
                if unsafe_word in env_name.upper():
                    break
            else:
                safe_env[env_name] = env_value
        return safe_env



class BeakerKernelManager(AsyncIOLoopKernelManager):
    def write_connection_file(self, **kwargs: object) -> None:
        super().write_connection_file(
            server=self.parent.parent.public_url,
            **kwargs
        )
        os.chmod(self.connection_file, 0o0777)


    async def _async_pre_start_kernel(self, **kw):
        if self.kernel_name == "beaker_kernel":
            user = os.environ.get("BEAKER_AGENT_USER", "jupyter")
        else:
            user = os.environ.get("BEAKER_SUBKERNEL_USER", "user")
        kw["user"] = user
        kw["cwd"] = f"~{user}"
        return await super()._async_pre_start_kernel(**kw)
    pre_start_kernel = _async_pre_start_kernel

    async def _async_launch_kernel(self, kernel_cmd, **kw):
        try:
            print('FOO', kernel_cmd, kw, self)
            return await super()._async_launch_kernel(kernel_cmd, **kw)
        except Exception as err:
            print("FOOFOOFOO", err)
    _launch_kernel = _async_launch_kernel


class BeakerKernelMappingManager(AsyncMappingKernelManager):
    kernel_manager_class = "beaker_kernel.service.server.BeakerKernelManager"
    connection_dir = os.environ.get("BEAKER_CONNECTION_DIR", None)

    def cwd_for_path(self, path, **kwargs):
        print(path, kwargs)
        return super().cwd_for_path(path, **kwargs)

    def _async_start_kernel(self, *, kernel_id = None, path = None, **kwargs):
        # kwargs["_kernel_name"] = kwargs["kernel_name"]
        return super()._async_start_kernel(kernel_id=kernel_id, path=path, **kwargs)

    start_kernel = _async_start_kernel

class BeakerSessionManager(SessionManager):

    def get_kernel_env(self, path, name=None, kernel_name=None):
        env = super().get_kernel_env(path, name)
        if kernel_name != "beaker_kernel":
            env = secure_env(env)
        return env

    async def start_kernel_for_session(
        self,
        session_id: str,
        path: Optional[str],
        name: Optional[ModelName],
        type: Optional[str],
        kernel_name: Optional[KernelName],
    ) -> str:
        print(kernel_name, type, path, session_id)
        # allow contents manager to specify kernels cwd
        kernel_path = await ensure_async(self.contents_manager.get_kernel_path(path=path))

        kernel_env = self.get_kernel_env(path, name, kernel_name)

        kernel_id = await self.kernel_manager.start_kernel(
            path=kernel_path,
            kernel_name=kernel_name,
            env=kernel_env,
        )
        return kernel_id



class BeakerServerApp(ServerApp):
    """
    Customizable ServerApp for use with Beaker
    """

    kernel_manager_class = BeakerKernelMappingManager
    session_manager_class = BeakerSessionManager

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
    def request_log_handler(cls, request):
        """Allow for debugging/extra logging of requests"""
        logging.debug(f"URI: {request.request.uri}")

    @classmethod
    def initialize_server(cls, argv=None, load_other_extensions=True, **kwargs):
        # Set Jupyter token from config
        os.environ.setdefault("JUPYTER_TOKEN", config.jupyter_token)
        # TODO: catch and handle any custom command line arguments here
        app = super().initialize_server(argv=argv, load_other_extensions=load_other_extensions, **kwargs)
        if cls.request_log_handler:
            app.web_app.log_request = cls.request_log_handler
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

        # self.handlers.append((r"/api/kernels", SafeKernelHandler))
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
