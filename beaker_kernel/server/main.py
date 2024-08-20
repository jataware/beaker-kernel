import asyncio
import datetime
import json
import logging
import os
import uuid
import urllib.parse
from typing import Dict

from jupyter_core.utils import ensure_async
from jupyter_server.auth.decorator import authorized
from jupyter_server.base.handlers import JupyterHandler
from jupyter_server.extension.handler import ExtensionHandlerMixin
from jupyter_server.serverapp import ServerApp
from jupyter_server.services.kernels.handlers import MainKernelHandler, json_default
from jupyter_server.utils import url_escape, url_path_join
from jupyterlab_server import LabServerApp
from tornado import web, httputil
from tornado.web import StaticFileHandler, RedirectHandler, RequestHandler, HTTPError

from beaker_kernel.lib.autodiscovery import autodiscover
from beaker_kernel.lib.context import BeakerContext
from beaker_kernel.lib.subkernels.base import BeakerSubkernel
from beaker_kernel.lib.agent_tasks import summarize
from beaker_kernel.lib.config import config, JUPYTER_SERVER_DEFAULT
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
        # If no session is provided on a root request, generate a session uuid and redirect to it
        if path == "":
            session_id = self.get_query_argument("session", None)
            if not session_id:
                session_id = str(uuid.uuid4())
                to_url = httputil.url_concat(
                    path,
                    {"session": session_id},
                )
                return self.redirect(to_url, permanent=False)

        # Otherwise, serve files as normal

        # Ensure a proper xsrf cookie value is set.
        cookie_name = self.settings.get("xsrf_cookie_name", "_xsrf")
        xsrf_token=self.xsrf_token.decode("utf8")
        xsrf_cookie = self.request.cookies.get(cookie_name, None)
        if not xsrf_cookie or xsrf_cookie.value != xsrf_token:
            kwargs = self.settings.get("xsrf_cookie_kwargs", {})
            self.set_cookie(cookie_name, xsrf_token, **kwargs)

        return await super().get(path, include_body=include_body)


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
            "token": config.JUPYTER_TOKEN,
        }
        return self.write(config_data)


class ContextHandler(ExtensionHandlerMixin, JupyterHandler):
    """
    Provide information about llm contexts via an endpoint
    """

    def get(self):
        """Get the main page for the application's interface."""
        ksm = self.kernel_spec_manager
        contexts: Dict[str, BeakerContext] = autodiscover("contexts")
        possible_subkernels: Dict[str, BeakerSubkernel] = autodiscover("subkernels")
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


class UploadHandler(RequestHandler):
    def post(self):
        filenames = []
        for file in self.request.files["uploadfiles"]:
            # Files are actually an array within an array?
            filename = file["filename"]
            if os.path.exists(filename):
                self.write(f"'{filename}' already exists.")
                raise HTTPError(401)
            with open(filename, 'wb') as output_file:
                output_file.write(file["body"])
            filenames.append(filename)
        self.finish(f"Saved files {', '.join(filenames)} uploaded.")


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
            "token": os.environ.get("JUPYTER_TOKEN", "89f73481102c46c0bc13b2998f9a4fce"),
        }
        return self.write(json.dumps(output))


class BeakerServerApp(ServerApp):
    """
    Customizable ServerApp for use with Beaker
    """

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

    @classmethod
    def get_extension_package(cls):
        return cls.__module__

    @classmethod
    def initialize_server(cls, argv=None, load_other_extensions=True, **kwargs):
        # TODO: catch and handle any custom command line arguments here
        app = super().initialize_server(argv=argv, load_other_extensions=load_other_extensions, **kwargs)
        return app

    def initialize_handlers(self):
        """Bypass initializing the default handler since we don't need to use the webserver, just the websockets."""
        self.handlers.append((r"/api/kernels", SafeKernelHandler))
        self.handlers.append(("/contexts", ContextHandler))
        self.handlers.append(("/config", ConfigHandler))
        self.handlers.append(("/stats", StatsHandler))
        self.handlers.append((r"/admin/?()", StaticFileHandler, {"path": os.path.join(HERE, "ui"), "default_filename": "admin.html"}))
        self.handlers.append(("/notebook", NotebookHandler))
        self.handlers.append((r"/upload", UploadHandler))
        self.handlers.append((r"/download/(.*)", DownloadHandler))
        self.handlers.append((r"/summary", SummaryHandler))
        self.handlers.append((r"(/?)", MainHandler, {"path": os.path.join(HERE, "ui"), "default_filename": "index.html"}))
        self.handlers.append((r"/index.html", StaticFileHandler, {"path": os.path.join(HERE, "ui"), "default_filename": "index.html"}))
        self.handlers.append((r"/(favicon.ico)", StaticFileHandler, {"path": os.path.join(HERE, "ui")}))
        self.handlers.append((r"/static/(.*)", StaticFileHandler, {"path": os.path.join(HERE, "ui", "static")}))
        self.handlers.append((r"/themes/(.*)", StaticFileHandler, {"path": os.path.join(HERE, "ui", "themes")}))
        self.handlers.append((r"/dev_ui/?(.*)", RedirectHandler, {"url": r"/{0}"}))
        super().initialize_handlers()

    def initialize_settings(self):
        # Override to allow cross domain websockets
        self.settings["allow_origin"] = "*"
        self.settings["disable_check_xsrf"] = True


if __name__ == "__main__":
    BeakerJupyterApp.launch_instance()
