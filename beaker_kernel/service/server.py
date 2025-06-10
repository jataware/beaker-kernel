import logging
import os
import shutil
import signal
import urllib.parse

from jupyter_client.ioloop.manager import AsyncIOLoopKernelManager
from jupyter_server.services.kernels.kernelmanager import AsyncMappingKernelManager
from jupyter_server.serverapp import ServerApp
from jupyterlab_server import LabServerApp

from beaker_kernel.lib.app import BeakerApp
from beaker_kernel.lib.config import config
from beaker_kernel.lib.utils import import_dotted_class
from beaker_kernel.service.handlers import register_handlers, SummaryHandler, request_log_handler, sanitize_env

logger = logging.getLogger(__file__)

HERE = os.path.dirname(__file__)

version = "0.0.1"


def _jupyter_server_extension_points():
    return [{"module": "beaker_kernel.service.server", "app": BeakerJupyterApp}]


class BeakerKernelManager(AsyncIOLoopKernelManager):
    agent_user: str
    subkernel_user: str

    # Longer wait_time for shutdown before killing processed due to potentially needing to shutdown both the subkernel
    # and the beaker kernel.
    shutdown_wait_time = 10.0

    @property
    def beaker_config(self):
        return getattr(self.parent, 'beaker_config')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent_user = os.environ.get("BEAKER_AGENT_USER", "jupyter")
        self.subkernel_user = os.environ.get("BEAKER_SUBKERNEL_USER", "user")

    def write_connection_file(self, **kwargs: object) -> None:
        beaker_app: BeakerApp = self.beaker_config.get("app", None)
        default_context = beaker_app and beaker_app._default_context
        if default_context:
            kwargs['context'] = {
                "default_context": default_context.slug,
                "default_context_payload": default_context.payload,
            }
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

    async def _async_interrupt_kernel(self):
        if self.shutting_down and self.kernel_name == "beaker_kernel":
            # During shutdown, interrupt Beaker kernel instances without interrupting the subkernel which is being
            # interrupted/shutdown in parallel by the server.
            # Sending an INTERRUPT signal notifies beaker to interrupt without affecting the subkernel.
            # Normal interrupts are done via a interrupt message, which will also interrupt the subkernel.
            return await self._async_signal_kernel(signal.SIGINT)
        return await super()._async_interrupt_kernel()


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

    @property
    def beaker_config(self):
        return getattr(self.parent, 'beaker_config', None)


class BeakerServerApp(ServerApp):
    """
    Customizable ServerApp for use with Beaker
    """

    kernel_manager_class = BeakerKernelMappingManager
    subkernel_user = "user"
    root_dir = os.path.expanduser(f'~{os.environ.get("BEAKER_SUBKERNEL_USER", subkernel_user)}')
    allow_root = True
    ip = "0.0.0.0"
    reraise_server_extension_failures = True

    def stop(self, from_signal = False):
        print("Shutting down Beaker server...")
        return super().stop(from_signal)

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
        self.handlers.append((r"/summary", SummaryHandler))
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
    BeakerJupyterApp.launch_instance()
