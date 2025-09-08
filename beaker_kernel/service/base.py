import getpass
import importlib
import logging
import os
import pwd
import shutil
import signal
import urllib.parse
# from importlib.metadata import entry_points
from typing import Optional, Any, cast

import traitlets
from traitlets import Unicode, Integer, Float, Bool, Dict

from jupyter_client.ioloop.manager import AsyncIOLoopKernelManager
from jupyter_client import kernelspec
from jupyter_server.auth import Authorizer, IdentityProvider
from jupyter_server.services.contents.largefilemanager import AsyncLargeFileManager
from jupyter_server.services.kernels.kernelmanager import AsyncMappingKernelManager
from jupyter_server.services.sessions.sessionmanager import SessionManager
from jupyter_server.serverapp import ServerApp
from jupyterlab_server import LabServerApp

from beaker_kernel.lib.app import BeakerApp
from beaker_kernel.lib.extension import BeakerExtension
from beaker_kernel.lib.autodiscovery import autodiscover
from beaker_kernel.lib.config import config
from beaker_kernel.lib.utils import import_dotted_class
from beaker_kernel.service.auth import current_user, BeakerUser, BeakerAuthorizer, BeakerIdentityProvider
from beaker_kernel.service.auth.notebook import AllowAllAuthorizer, NotebookIdentityProvider
# from beaker_kernel.service.provisioning import DockerProvisioner
from beaker_kernel.service.handlers import register_handlers, request_log_handler


logger = logging.getLogger("beaker_server")
HERE = os.path.dirname(__file__)

version = "1.0.0"


class BeakerContentsManager(AsyncLargeFileManager):
    def _get_os_path(self, path):
        """Override path resolution to use user-specific home directory.

        Parameters
        ----------
        path : str
            Relative path to resolve

        Returns
        -------
        str
            Absolute path within user's home directory
        """
        user: BeakerUser = current_user.get()
        if user:
            path = os.path.join(user.home_dir, path)
        return super()._get_os_path(path)


class BeakerSessionManager(SessionManager):

    def get_kernel_env(self, path, name = None):
        """Get environment variables for Beaker kernel sessions.

        Sets up environment variables including session name, Beaker session,
        and user information for kernel execution.

        Parameters
        ----------
        path : str
            Session path
        name : str, optional
            Session name

        Returns
        -------
        dict
            Environment variables for kernel
        """
        # This only sets env variables for the Beaker Kernel, not subkernels.
        try:
            beaker_user = path.split(os.path.sep)[0]
        except:
            pass
        env = {
            **os.environ,
            "JPY_SESSION_NAME": path,
            "BEAKER_SESSION": str(name),
        }
        if beaker_user:
            env.update({
                "BEAKER_USER": beaker_user,
                "LANGSMITH_BEAKER_USER": beaker_user,
            })

        return env

    async def start_kernel_for_session(self, session_id, path, name, type, kernel_name):
        """Start a kernel for a session with user-specific path and permissions.

        For Beaker kernels, sets up user-specific home directories and proper
        file permissions for the subkernel user.

        Parameters
        ----------
        session_id : str
            Unique identifier for the session
        path : str
            Path for the session
        name : str
            Session name
        type : str
            Session type
        kernel_name : str
            Name of the kernel to start

        Returns
        -------
        dict
            Session information from parent class
        """
        if kernel_name == "beaker_kernel":
            user: BeakerUser = current_user.get()
            if user:
                path = os.path.join(user.home_dir, path)
                virtual_home_root = self.kernel_manager.root_dir
                virtual_home_dir = os.path.join(virtual_home_root, user.home_dir)

                subkernel_user = self.parent.subkernel_user
                if not os.path.isdir(virtual_home_dir):
                    os.makedirs(virtual_home_dir, exist_ok=True)
                    shutil.chown(virtual_home_dir, user=subkernel_user, group=subkernel_user)
                path = os.path.join(os.path.relpath(virtual_home_dir, self.kernel_manager.root_dir), name)
        return await super().start_kernel_for_session(session_id, path, name, type, kernel_name)


class BeakerKernelSpecManager(kernelspec.KernelSpecManager):
    NAME_SEP = r"%%"
    parent: "traitlets.Instance[BeakerServerApp]"

    @property
    def kernel_spec_managers(self) -> dict[str, kernelspec.KernelSpecManager]:
        """Get kernel specification managers from parent server app.

        Returns
        -------
        dict[str, kernelspec.KernelSpecManager]
            Mapping of extension names to kernel spec managers
        """
        return self.parent.kernel_spec_managers

    def get_default_kernel_name(self) -> str:
        """Get the default kernel name.

        Returns
        -------
        str
            The default kernel name (beaker_kernel)
        """
        return f"beaker_kernel"

    def _update_spec(self, name: str, spec: dict[str, dict]) -> dict[str, dict]:
        """Update kernel spec with name if not present.

        Parameters
        ----------
        name : str
            Kernel name to add to spec
        spec : dict[str, dict]
            Kernel specification dictionary

        Returns
        -------
        dict[str, dict]
            Updated kernel specification
        """
        if "name" not in spec:
            spec["name"] = name
        return spec

    def get_all_specs(self) -> dict[str, dict]:
        """Get all available kernel specifications from all managers.

        Aggregates kernel specifications from local manager and all extension
        managers, applying proper namespacing for extension specs.

        Returns
        -------
        dict[str, dict]
            Dictionary mapping kernel names to their specifications
        """
        res = {}
        for spec_slug, spec_manager in self.kernel_spec_managers.items():

            if not self.parent.kernel_spec_include_local and spec_slug is None:
                # Even we are not including local specs, we need to include beaker_kernel
                res["beaker_kernel"] = self._update_spec(spec_manager.get_all_specs()["beaker_kernel"])

            specs = spec_manager.get_all_specs().items()
            for kernel_name, spec in specs:
                if spec_slug is None:
                    key = kernel_name
                else:
                    key = f"{spec_slug}{self.NAME_SEP}{kernel_name}"
                res[key] = self._update_spec(kernel_name, spec)
        return res

    def get_kernel_spec(self, kernel_name) -> kernelspec.KernelSpec:
        """Get a specific kernel specification by name.

        Handles both local kernel specs and extension-namespaced specs.
        Extension specs use the format: extension_name%%kernel_name

        Parameters
        ----------
        kernel_name : str
            Name of the kernel spec to retrieve, optionally namespaced

        Returns
        -------
        kernelspec.KernelSpec
            The requested kernel specification

        Raises
        ------
        kernelspec.NoSuchKernel
            If the specified kernel is not found
        """
        if self.NAME_SEP in kernel_name:
            spec_slug, name = kernel_name.split(self.NAME_SEP, maxsplit=1)
        else:
            spec_slug = None
            name = kernel_name

        spec_manager = self.kernel_spec_managers.get(spec_slug, None)
        if spec_manager is None:
            raise kernelspec.NoSuchKernel(kernel_name)

        spec = spec_manager.get_kernel_spec(name)

        if spec is None:
            raise kernelspec.NoSuchKernel(kernel_name)

        # spec = super().get_kernel_spec(kernel_name)
        # if kernel_name == "beaker_kernel":
        #     return spec
        # elif self.parent.provisioner_class:
        #     provisioner_obj = {
        #         "provisioner_name": "beaker-docker-provisioner",
        #         "config": {
        #             "image": "beaker-kernel-python",
        #             "max_cpus": 4,
        #         },
        #     }
        #     spec.metadata["kernel_provisioner"] = provisioner_obj
        return spec



class BeakerKernelManager(AsyncIOLoopKernelManager):
    beaker_session = Unicode(allow_none=True, help="Beaker session identifier", config=True)

    # Longer wait_time for shutdown before killing processed due to potentially needing to shutdown both the subkernel
    # and the beaker kernel.
    shutdown_wait_time = Float(
        10.0,
        help="Time to wait for shutdown before killing processes",
        config=True
    )


    @property
    def beaker_config(self):
        """Get Beaker configuration from parent.

        Returns
        -------
        dict
            Beaker configuration dictionary
        """
        return getattr(self.parent, 'beaker_config')

    @property
    def app(self) -> "BeakerServerApp":
        """Get the BeakerServerApp instance.

        Returns
        -------
        BeakerServerApp
            The server application instance
        """
        return self.parent.parent

    def write_connection_file(self, **kwargs: object) -> None:
        """Write kernel connection file with Beaker-specific context.

        Extends the standard connection file with Beaker session information,
        server URL, and default context from the Beaker application.

        Parameters
        ----------
        **kwargs : object
            Additional connection file parameters
        """
        beaker_session: Optional[str] = self.beaker_session
        jupyter_session: Optional[str] = kwargs.get("jupyter_session", None)
        if beaker_session:
            kwargs["beaker_session"] = beaker_session
        if jupyter_session:
            kwargs["jupyter_session"] = jupyter_session
        beaker_app: BeakerApp = self.beaker_config.get("app", None)
        default_context = beaker_app and beaker_app._default_context
        if default_context:
            app_context_dict = default_context.asdict()
            kwargs['context'] = {
                "default_context": default_context.slug,
                "default_context_payload": default_context.payload,
            }
            if app_context_dict:
                kwargs["context"].update(**app_context_dict)

        super().write_connection_file(
            server=self.app.public_url,
            **kwargs
        )

        # Set file to be owned by and modifiable by the beaker user so the beaker user can modify the file.
        os.chmod(self.connection_file, 0o0775)
        shutil.chown(self.connection_file, user=self.app.agent_user)

    async def _async_pre_start_kernel(self, **kw):
        """Pre-start kernel setup including user switching and environment setup.

        Configures the kernel environment with appropriate user permissions,
        working directory, and environment variables before kernel launch.

        Parameters
        ----------
        **kw
            Keyword arguments for kernel startup

        Returns
        -------
        tuple
            Command and keyword arguments for kernel launch
        """
        # Stash beaker_session value so it can be written in the connection file.
        beaker_session = kw.get('env', {}).get('BEAKER_SESSION', None) or kw.get("session_path", None)
        if beaker_session and not self.beaker_session:
            self.beaker_session = beaker_session

        cmd, kw = await super()._async_pre_start_kernel(**kw)

        env = kw.pop("env", {})

        # Update user, env variables, and home directory based on type of kernel being started.
        if self.kernel_name == "beaker_kernel":
            kernel_user = self.app.agent_user
            home_dir = os.path.expanduser(f"~{kernel_user}")
            kw["cwd"] = self.app.working_dir
        else:
            kernel_user = self.app.subkernel_user
            home_dir = kw.get("cwd")

        user_info = pwd.getpwnam(kernel_user)
        home_dir = os.path.expanduser(f"~{kernel_user}")
        group_list = os.getgrouplist(kernel_user, user_info.pw_gid)
        if user_info.pw_uid != os.getuid():
            env["USER"] = kernel_user
            kw["user"] = kernel_user
            env["HOME"] = home_dir
        if os.getuid() == 0 or os.geteuid() == 0:
            kw["group"] = user_info.pw_gid
            kw["extra_groups"] = group_list[1:]
        kw["cwd"] = self.app.working_dir

        # Update keyword args that are passed to Popen()
        kw["env"] = env

        return cmd, kw
    pre_start_kernel = _async_pre_start_kernel

    async def _async_launch_kernel(self, kernel_cmd, **kw):
        kw.pop("session_path", None)
        return await super()._async_launch_kernel(kernel_cmd, **kw)

    async def _async_interrupt_kernel(self):
        if self.shutting_down and self.kernel_name == "beaker_kernel":
            # During shutdown, interrupt Beaker kernel instances without interrupting the subkernel which is being
            # interrupted/shutdown in parallel by the server.
            # Sending an INTERRUPT signal notifies beaker to interrupt without affecting the subkernel.
            # Normal interrupts are done via a interrupt message, which will also interrupt the subkernel.
            return await self._async_signal_kernel(signal.SIGINT)
        return await super()._async_interrupt_kernel()


class BeakerKernelMappingManager(AsyncMappingKernelManager):
    kernel_manager_class = "beaker_kernel.service.base.BeakerKernelManager"
    connection_dir = Unicode(
        os.path.join(config.beaker_run_path, "kernelfiles"),
        help="Directory for kernel connection files",
        config=True
    )
    cull_idle_timeout = Integer(
        3600,
        help="Timeout in seconds for culling idle kernels",
        config=True
    )

    def __init__(self, **kwargs):
        """Initialize BeakerKernelMappingManager.

        Sets up the connection directory and initializes the kernel manager
        with default kernel name if available.

        Parameters
        ----------
        **kwargs
            Additional arguments passed to parent class
        """
        # Ensure connection dir exists and is readable
        if not os.path.isdir(self.connection_dir):
            os.makedirs(self.connection_dir, mode=0o0755)
        else:
            os.chmod(self.connection_dir, 0o0755)
        super().__init__(**kwargs)
        if hasattr(self.kernel_spec_manager, "get_default_kernel_name"):
            self.default_kernel_name = self.kernel_spec_manager.get_default_kernel_name()

    @property
    def beaker_config(self):
        return getattr(self.parent, 'beaker_config', None)

    def cwd_for_path(self, path, **kwargs):
        user: BeakerUser = current_user.get()
        if user:
            user_home = self.get_home_for_user(user)
            return super().cwd_for_path(user_home, **kwargs)
        else:
            return super().cwd_for_path(path, **kwargs)

    def get_home_for_user(self, user: BeakerUser) -> os.PathLike:
        return user.home_dir

    async def _async_start_kernel(self, *, kernel_id = None, path = None, **kwargs):
        kwargs.setdefault('session_path', path)
        return await super()._async_start_kernel(kernel_id=kernel_id, path=path, **kwargs)
    start_kernel = _async_start_kernel

    def pre_start_kernel(self, kernel_name: str, kwargs: dict):
        km, kernel_name, kernel_id = super().pre_start_kernel(kernel_name, kwargs)
        km = cast(BeakerKernelManager, km)
        beaker_session = kwargs.get("session_path", None)
        if beaker_session and not km.beaker_session:
            km.beaker_session = beaker_session
        return km, kernel_name, kernel_id

    async def cull_kernel_if_idle(self, kernel_id):
        """Cull a kernel if it is idle."""
        kernel = self._kernels.get(kernel_id, None)
        if getattr(kernel, "kernel_name", None) != "beaker_kernel":
            return
        result = await super().cull_kernel_if_idle(kernel_id)
        return result

class BeakerServerApp(ServerApp):
    """
    Customizable ServerApp for use with Beaker
    """

    kernel_manager_class = BeakerKernelMappingManager
    session_manager_class = BeakerSessionManager
    reraise_server_extension_failures = True
    contents_manager_class = BeakerContentsManager
    kernel_spec_manager_class = BeakerKernelSpecManager

    kernel_spec_include_local = Bool(True, help="Include local kernel specs", config=True)
    kernel_spec_managers = Dict(help="Kernel specification managers indexed by extension name", config=True)

    beaker_extensions = Dict(help="Auto-discovered Beaker extensions providing additional contexts and subkernels")

    service_user = Unicode(help="Username under which the Beaker service is running", config=True)
    agent_user = Unicode(help="Username for the Beaker kernel agent process", config=True)
    subkernel_user = Unicode(help="Username under which subkernels (Python, R, etc.) are executed", config=True)
    working_dir = Unicode(help="Working directory for kernel execution and file operations", config=True)

    @traitlets.default("identity_provider_class")
    def _default_identity_provider_class(self):
        from beaker_kernel.service.auth.notebook import NotebookIdentityProvider
        return NotebookIdentityProvider

    @traitlets.default("authorizer_class")
    def _default_authorizer_class(self):
        from beaker_kernel.service.auth.notebook import NotebookAuthorizer
        return NotebookAuthorizer


    def __init__(self, **kwargs):
        """Initialize BeakerServerApp with extension discovery and user configuration.

        Sets up the server with auto-discovered Beaker extensions and configures
        user accounts based on the execution context (root vs non-root).

        Parameters
        ----------
        **kwargs
            Additional keyword arguments passed to parent ServerApp
        """
        super().__init__(**kwargs)

    @traitlets.default('beaker_extensions')
    def _default_beaker_extensions(self):
        return {k: v for k, v in autodiscover("extensions").items()}

    @traitlets.default('service_user')
    def _default_service_user(self):
        return getpass.getuser()

    @traitlets.default('agent_user')
    def _default_agent_user(self):
        if self.service_user == "root":
            agent_user = os.environ.get("BEAKER_AGENT_USER", None)
            if agent_user is None:
                raise RuntimeError("When running as root, BEAKER_AGENT_USER environment variable must be set.")
            return agent_user
        else:
            return os.environ.get("BEAKER_AGENT_USER", self.service_user)

    @traitlets.default('subkernel_user')
    def _default_subkernel_user(self):
        if self.service_user == "root":
            subkernel_user = os.environ.get("BEAKER_SUBKERNEL_USER", None)
            if subkernel_user is None:
                raise RuntimeError("When running as root, BEAKER_SUBKERNEL_USER environment variable must be set.")
            return subkernel_user
        else:
            return os.environ.get("BEAKER_SUBKERNEL_USER", self.service_user)

    @traitlets.default('working_dir')
    def _default_working_dir(self):
        if self.service_user == "root":
            return os.path.expanduser(f"~{self.subkernel_user}")
        else:
            return os.getcwd()

    @traitlets.default('kernel_spec_managers')
    def _default_kernel_spec_managers(self):
        result = {}
        # Add local kernel specs in enabled first
        if self.kernel_spec_include_local:
            local_kernel_spec_manager = kernelspec.KernelSpecManager(parent=self)
            result[None] = local_kernel_spec_manager

        # Add kernel specs from extensions
        for extension_slug, extension_cls in self.beaker_extensions.items():
            spec_manager = getattr(extension_cls, "kernel_spec_manager_class", None)
            if spec_manager:
                result[extension_slug] = spec_manager(parent=self)
        return result

    @property
    def _default_root_dir(self):
        return self.working_dir or super()._default_root_dir()

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


class BaseBeakerServerApp(LabServerApp):
    name = "beaker_kernel"
    serverapp_class = BeakerServerApp
    load_other_extensions = True
    app_name = "Beaker Jupyter App"
    app_version = version
    allow_origin = "*"
    open_browser = False
    extension_url = "/"
    connection_dir = ""

    log_requests = Bool(False, help="Enable request logging", config=True)

    subcommands = {}

    ui_path = Unicode(
        os.path.join(HERE, "ui"),
        help="Path to UI files",
        config=True
    )

    @classmethod
    def get_extension_package(cls):
        return cls.__module__

    @classmethod
    def initialize_server(cls, argv=None, load_other_extensions=True, **kwargs):
        """Initialize the Jupyter server with Beaker-specific configuration.

        Sets up authentication providers, loads extensions, and applies
        application-specific traits and settings.

        Parameters
        ----------
        argv : list, optional
            Command line arguments
        load_other_extensions : bool, optional
            Whether to load other Jupyter extensions (default True)
        **kwargs
            Additional server configuration

        Returns
        -------
        ServerApp
            Initialized server application instance
        """
        # Initialize app_traits if needed
        # app_traits = getattr(cls, '_default_app_traits', {})
        # if hasattr(cls, 'app_traits') and cls.app_traits:
        #     app_traits.update(cls.app_traits)
        # Update webserver app traits from app definition
        # kwargs.update(app_traits)

        # authorizer_class: Authorizer | None = None
        # identity_provider_class: IdentityProvider | None = None
        try:
            # Fetch from module if defined
            auth_mod_str = os.environ.get("BEAKER_AUTH")
            if auth_mod_str:
                auth_mod = importlib.import_module(auth_mod_str)
                authorizer_class = getattr(auth_mod, "authorizer", None)
                identity_provider_class = getattr(auth_mod, "identity_provider", None)
        except Exception as err:
            pass

        # if "BEAKER_AUTH_AUTHORIZER" in os.environ:
        #     authorizer_class = os.environ.get("BEAKER_AUTH_AUTHORIZER")
        # if "BEAKER_AUTH_IDENTITY_PROVIDER" in os.environ:
        #     identity_provider_class = os.environ.get("BEAKER_AUTH_IDENTITY_PROVIDER")

        # if authorizer_class:
        #     kwargs["authorizer_class"] = authorizer_class
        # if identity_provider_class:
        #     kwargs["identity_provider_class"] = identity_provider_class

        app = super().initialize_server(argv=argv, load_other_extensions=load_other_extensions, **kwargs)

        # Log requests to console if configured
        if cls.log_requests:
            app.web_app.settings["log_function"] = request_log_handler
        return app

    def initialize_handlers(self):
        """Bypass initializing the default handler since we don't need to use the webserver, just the websockets."""
        if self.serverapp.identity_provider:
            self.handlers.extend(self.serverapp.identity_provider.get_handlers())
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
    BeakerServerApp.launch_instance()
