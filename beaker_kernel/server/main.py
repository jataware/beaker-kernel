import asyncio
import datetime
import json
import logging
import os
import uuid
import urllib.parse
from dataclasses import is_dataclass, asdict
from collections.abc import Mapping, Collection
from typing import get_origin, get_args, GenericAlias, Union, Generic
from types import UnionType

from jupyter_client.ioloop.manager import AsyncIOLoopKernelManager
from jupyter_core.utils import ensure_async
from jupyter_server.services.kernels.kernelmanager import AsyncMappingKernelManager
from jupyter_server.auth.decorator import authorized
from jupyter_server.base.handlers import JupyterHandler
from jupyter_server.extension.handler import ExtensionHandlerMixin
from jupyter_server.serverapp import ServerApp
from jupyter_server.services.kernels.handlers import MainKernelHandler, json_default
from jupyter_server.services.contents.handlers import ContentsHandler
from jupyter_server.utils import url_escape, url_path_join
from jupyterlab_server import LabServerApp
from tornado import web, httputil
from tornado.web import StaticFileHandler, RedirectHandler, RequestHandler, HTTPError

from beaker_kernel.lib.autodiscovery import autodiscover
from beaker_kernel.lib.context import BeakerContext
from beaker_kernel.lib.subkernels.base import BeakerSubkernel
from beaker_kernel.lib.agent_tasks import summarize
from beaker_kernel.lib.config import config, locate_config, Config, Table, Choice, ConfigClass, recursiveOptionalUpdate, reset_config
from beaker_kernel.server import admin_utils

logger = logging.getLogger(__file__)

HERE = os.path.dirname(__file__)

version = "0.0.1"


def _jupyter_server_extension_points():
    return [{"module": "beaker_kernel.server.main", "app": BeakerJupyterApp}]


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


class SafeKernelHandler(MainKernelHandler):

    @web.authenticated
    @authorized
    async def post(self):
        km = self.kernel_manager
        model = self.get_json_body()
        if model is None:
            model = {"name": km.default_kernel_name}
        else:
            model.setdefault("name", km.default_kernel_name)

        env = self.session_manager.get_kernel_env(path=model.get("path"), name=model["name"])
        env = secure_env(env)

        kernel_id = await ensure_async(
            km.start_kernel(  # type:ignore[has-type]
                kernel_name=model["name"], path=model.get("path"), env=env
            )
        )
        model = await ensure_async(km.kernel_model(kernel_id))
        location = url_path_join(self.base_url, "api", "kernels", url_escape(kernel_id))
        self.set_header("Location", location)
        self.set_status(201)
        self.finish(json.dumps(model, default=json_default))


class NotebookHandler(ExtensionHandlerMixin, JupyterHandler):

    def get(self):
        return self.write(json.dumps(notebook_content))

    def post(self):
        global notebook_content
        notebook_content = self.get_json_body()
        notebook_content["lastSaved"] = datetime.datetime.utcnow().isoformat()
        return self.write(json.dumps(notebook_content))


class MainHandler(StaticFileHandler):
    """
    Handle the main interface to properly set a session
    """
    async def get(self, path: str, include_body: bool = True) -> None:

        url_path = self.parse_url_path(path)
        absolute_path = self.get_absolute_path(self.root, url_path)
        try:
            validated_path = self.validate_absolute_path(self.root, absolute_path)
        except HTTPError as e:
            # If path cannot be found, check again with a .html extension
            if e.status_code == 404:
                html_path = f"{absolute_path}.html"
                validated_path = self.validate_absolute_path(self.root, html_path)
            else:
                raise

        # If no session is provided on a root request, generate a session uuid and redirect to it
        if validated_path.endswith('.html'):
            session_id = self.get_query_argument("session", None)
            if not session_id:
                session_id = str(uuid.uuid4())
                to_url = httputil.url_concat(
                    f"{'/' if path.startswith('/') else '' }{path}",
                    {"session": session_id},
                )
                return self.redirect(to_url, permanent=False)
            path = os.path.relpath(validated_path, self.root)
        # Otherwise, serve files as normal

        # Ensure a proper xsrf cookie value is set.
        cookie_name = self.settings.get("xsrf_cookie_name", "_xsrf")
        xsrf_token = self.xsrf_token.decode("utf8")
        xsrf_cookie = self.request.cookies.get(cookie_name, None)
        if not xsrf_cookie or xsrf_cookie.value != xsrf_token:
            kwargs = self.settings.get("xsrf_cookie_kwargs", {})
            self.set_cookie(cookie_name, xsrf_token, **kwargs)

        return await super().get(path, include_body=include_body)


class ConfigController(ExtensionHandlerMixin, JupyterHandler):
    """
    """
    @staticmethod
    def map_type(type_obj: type):
        type_def = {}
        try:
            try:
                type_origin = get_origin(type_obj)
                type_args = get_args(type_obj)
            except:
                type_origin = None
                type_args = None
            if type_args:
                if isinstance(type_obj, UnionType):
                    type_def["type_str"] = repr(type_obj)
                elif issubclass(type_origin, Choice):
                    source = get_args(type_args[0])[0]
                    type_def["type_str"] = f"{type_origin.__name__}['{source}']"
                    type_def["choice_source"] = source
                else:
                    type_def["type_str"] = f"{type_origin.__name__}[{', '.join(arg.__name__ for arg in type_args)}]"
                if type_origin:
                    type_def["type_origin"] = ConfigController.map_type(type_origin)
                if type_args:
                    type_def["type_args"] = [ConfigController.map_type(type_arg) for type_arg in type_args]

            elif is_dataclass(type_obj):
                type_def.update(ConfigController.jsonify_dataclass_schema(type_obj))
            else:
                if isinstance(type_obj, type):
                    type_def["type_str"] = type_obj.__name__
                else:
                    type_def["type_str"] = repr(type_obj)

            if hasattr(type_obj, "default_value"):
                default_value = type_obj.default_value()
                type_def["default_value"] = default_value
            else:
                try:
                    default_value = type_obj()
                    type_def["default_value"] = default_value
                except TypeError:
                    pass
        except:
            type_def["type_str"] = repr(type_obj)
        return type_def


    @staticmethod
    def jsonify_dataclass_schema(obj):
        result = {
            "type_str": f"Dataclass[{obj.__name__}]",
            "fields": {},
        }
        for field_name, field in obj.__dataclass_fields__.items():
            type_def = ConfigController.map_type(field.type)
            metadata = dict(field.metadata)
            description = metadata.pop("description", None)
            option_func = metadata.pop("options", None)
            if option_func and callable(option_func):
                metadata["options"] = option_func()
            field_result = {
                "name": field.name,
                "description": description,
                "metadata": metadata,
                **type_def,
            }
            result["fields"][field_name] = field_result

        return result


    @staticmethod
    def jsonify_dataclass_object(obj):
        result = {}
        for field_name, field in obj.__dataclass_fields__.items():
            current_value = getattr(obj, field_name, None)
            if get_origin(field.type) and issubclass(get_origin(field.type), Table):
                record_type = get_args(field.type)[0]
                if is_dataclass(record_type):
                    current_value = {
                        key: ConfigController.jsonify_dataclass_object(record_type(**value))
                        for key, value in current_value.items()
                    }
            # TODO: Verify value is in choice list?
            # elif get_origin(field.type) and issubclass(get_origin(field.type), Choice):
            #     current_value = ""
            elif is_dataclass(current_value):
                current_value = ConfigController.jsonify_dataclass_object(current_value)
                if not current_value:
                    current_value = {}

            if field.metadata.get("sensitive", True):
                # Track if a value is defined or not.
                current_value = None if current_value else ""
                # current_value = ""
            result[field_name] = current_value
        return result


    def get(self):
        if "schema" in self.request.query:
            return self.get_config_schema()
        else:
            return self.get_config()

    async def post(self):
        config_changes = self.get_json_body()
        updated_config: dict = recursiveOptionalUpdate(config, config_changes)
        config.update(updates=updated_config)
        reset_config()
        return await self.get_config()

    async def get_config_schema(self):
        config_cls = Config
        schema = self.jsonify_dataclass_schema(config_cls)
        return self.write(schema)


    async def get_config(self):
        config_file = locate_config()
        payload = self.jsonify_dataclass_object(config)

        return self.write(
            {
                "config": payload,
                "config_type": config.config_type,
                "config_id": str(config_file),
            }
        )

class ConfigHandler(ExtensionHandlerMixin, JupyterHandler):
    """
    Provide config via an endpoint
    """

    def get(self):
        # If BASE_URL is not provided in the environment, assume that the base url is the same location that
        # is handling this request, as reported by the request headers.
        # If APP_URL is not provided, assume it is the same as BASE_URL.

        base_url = os.environ.get("JUPYTER_BASE_URL", f"{self.request.protocol}://{self.request.host}")

        base_scheme = urllib.parse.urlparse(base_url).scheme
        if base_scheme.endswith("s"):
            ws_scheme = "wss"
        else:
            ws_scheme = "ws"
        ws_url = base_url.replace(base_scheme, ws_scheme)

        config_data = {
            "appUrl": os.environ.get("APP_URL", base_url),
            "baseUrl": base_url,
            "wsUrl": os.environ.get("JUPYTER_WS_URL", ws_url),
            "token": config.jupyter_token,
            "config_type": config.config_type,
        }

        # Ensure a proper xsrf cookie value is set.
        cookie_name = self.settings.get("xsrf_cookie_name", "_xsrf")
        xsrf_token = self.xsrf_token.decode("utf8")
        xsrf_cookie = self.request.cookies.get(cookie_name, None)
        if not xsrf_cookie or xsrf_cookie.value != xsrf_token:
            kwargs = self.settings.get("xsrf_cookie_kwargs", {})
            self.set_cookie(cookie_name, xsrf_token, **kwargs)

        return self.write(config_data)


class ContextHandler(ExtensionHandlerMixin, JupyterHandler):
    """
    Provide information about llm contexts via an endpoint
    """

    def get(self):
        """Get the main page for the application's interface."""
        ksm = self.kernel_spec_manager
        contexts: dict[str, BeakerContext] = autodiscover("contexts")
        possible_subkernels: dict[str, BeakerSubkernel] = autodiscover("subkernels")
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


class DownloadHandler(RequestHandler):
    def get(self, filepath: str):
        if filepath.startswith("."):
            raise HTTPError(404)
        if os.path.isfile(filepath):
            _, file_name = os.path.split(filepath)
            if file_name.startswith("."):
                raise HTTPError(404)

            self.set_header('Content-Type', 'application/force-download')
            self.set_header('Content-Disposition', f'attachment; filename=%s' % file_name)
            try:
                with open(filepath, "rb") as f:
                    while True:
                        _buffer = f.read(4096)
                        if _buffer:
                            self.write(_buffer)
                        else:
                            f.close()
                            self.finish()
                            return
            except:
                raise HTTPError(404)
        else:
            raise HTTPError(404)


class SummaryHandler(ExtensionHandlerMixin, JupyterHandler):
    async def post(self):
        payload = json.loads(self.request.body)
        summary = await summarize(**payload)
        return self.write(summary)


class StatsHandler(ExtensionHandlerMixin, JupyterHandler):
    """
    """

    async def get(self):
        """
        """
        with open("/proc/sys/fs/file-nr") as filehandles:
            file_handle_details = filehandles.read().strip()
        fh_open, _, fh_total = map(int, file_handle_details.split())
        fh_usage = fh_open / fh_total * 100

        load_1, load_5, load_15 = [f"{avg:2f}" for avg in os.getloadavg()]
        mem_total, mem_used, mem_free = map(int, os.popen('free -t -m').readlines()[-1].split()[1:])
        disk_total, disk_used, disk_free, disk_usage, mount = list(os.popen('df -h .').readlines()[-1].split()[1:])


        # Fetch remote resources asynchronously
        (
            system_stats,
            sessions,
            kernels,
        ) = await asyncio.gather(
            admin_utils.fetch_system_stats(),
            self.session_manager.list_sessions(),
            admin_utils.fetch_kernel_info(self.kernel_manager),
        )
        ps_response, fh_response, lsof_response = system_stats

        proc_info = await admin_utils.build_proc_info(ps_response, fh_response)
        edges, kernel_by_pid_index = await admin_utils.build_edges_map(lsof_response, kernels)

        # Update each session with collected information
        for session in sessions:
            kernel_id = session.get("kernel", {}).get('id', None)
            kernel = kernels.get(kernel_id)
            session["kernel"].update(kernel)
            beaker_kernel_pid = kernels[kernel_id].get("pid", None)
            subkernel_pid = None
            if beaker_kernel_pid is not None:
                potential_subkernel_pids = [child for parent, child in edges if parent == beaker_kernel_pid]
                for psp in potential_subkernel_pids:
                    if psp in kernel_by_pid_index:
                        subkernel_pid = psp
                        session["subkernel"] = kernel_by_pid_index[psp]
                        break
            session["process_info"] = []
            pids_to_add = []
            if beaker_kernel_pid is not None:
                pids_to_add.append(beaker_kernel_pid)
            if subkernel_pid is not None:
                pids_to_add.append(subkernel_pid)
            while len(pids_to_add) > 0:
                pid = pids_to_add.pop()
                session["process_info"].append(proc_info[pid])
                for proc in proc_info.values():
                    if proc["ppid"] == pid:
                        pids_to_add.append(proc["pid"])

        output = {
            "file_handles": {
                "open": fh_open,
                "total": fh_total,
                "usage": f"{fh_usage:2f}"
            },
            "load": {
                "1_min": load_1,
                "5_min": load_5,
                "15_min": load_15,
            },
            "memory": {
                "total": mem_total,
                "used": mem_used,
                "free": mem_free,
                "usage": f"{int(mem_used/mem_total*100)}%",
            },
            "disk": {
                "total": disk_total,
                "used": disk_used,
                "free": disk_free,
                "usage": disk_usage,
                "mount": mount,
            },
            "sessions": sessions,
            "kernels": kernels,
            "token": config.jupyter_token,
        }
        return self.write(json.dumps(output))


class BeakerKernelManager(AsyncIOLoopKernelManager):
    def write_connection_file(self, **kwargs: object) -> None:
        return super().write_connection_file(
            server=self.parent.parent.public_url,
            **kwargs
        )


class BeakerKernelMappingManager(AsyncMappingKernelManager):
    kernel_manager_class = "beaker_kernel.server.main.BeakerKernelManager"


class BeakerServerApp(ServerApp):
    """
    Customizable ServerApp for use with Beaker
    """

    kernel_manager_class = BeakerKernelMappingManager

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

        self.handlers.append((r"/api/kernels", SafeKernelHandler))
        self.handlers.append(("/contexts", ContextHandler))
        self.handlers.append(("/config/control", ConfigController))
        self.handlers.append(("/config", ConfigHandler))
        self.handlers.append(("/stats", StatsHandler))
        self.handlers.append((r"/admin/?()", StaticFileHandler, {"path": self.ui_path, "default_filename": "admin.html"}))
        self.handlers.append((r"/summary", SummaryHandler))
        self.handlers.append((f"/()", MainHandler, {"path": self.ui_path, "default_filename": "index.html"}))
        if statics:
            static_handler = ("/((" + "|".join(statics) + ").*)", StaticFileHandler, {"path": self.ui_path})
            self.handlers.append(static_handler)
        if pages:
            page_handler = ("/((" + "|".join(pages) + "))", MainHandler, {"path": self.ui_path, "default_filename": "index.html"})
            self.handlers.append(page_handler)
        super().initialize_handlers()

    def initialize_settings(self):
        # Override to allow cross domain websockets
        self.settings["allow_origin"] = "*"
        self.settings["disable_check_xsrf"] = True


if __name__ == "__main__":
    BeakerJupyterApp.launch_instance()
