import asyncio
import inspect
import json
import logging
import os.path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple
import requests

from .jupyter_kernel_proxy import InterceptionFilter, JupyterMessage

from beaker_kernel.lib.autodiscovery import autodiscover
from beaker_kernel.lib.utils import action, get_socket, server_token, server_url

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

if TYPE_CHECKING:
    from archytas.react import ReActAgent

    from beaker_kernel.kernel import LLMKernel

    from .agent import BaseAgent
    from .subkernels.base import BaseSubkernel

logger = logging.getLogger(__name__)


class BaseContext:
    beaker_kernel: "LLMKernel"
    subkernel: "BaseSubkernel"
    config: Dict[str, Any]
    agent: "ReActAgent"

    intercepts: List[Tuple[str, Callable, str]]
    jinja_env: Optional[Environment]
    templates: Dict[str, Template]

    WEIGHT: int = 50  # Used for auto-sorting in drop-downs, etc. Lower weights are listed earlier.

    def __init__(self, beaker_kernel: "LLMKernel", agent_cls: "BaseAgent", config: Dict[str, Any]):
        self.intercepts = []
        self.jinja_env = None
        self.templates = {}
        self.beaker_kernel = beaker_kernel
        self.agent = agent_cls(
            context=self,
            tools=[],
        )
        self.config = config
        self.subkernel = self.get_subkernel()


        # Add intercepts, by inspecting the instance and extracting matching methods
        self._collect_and_register_intercepts(self)
        self._collect_and_register_intercepts(self.subkernel)

        # Set auto-context from agent
        if getattr(self, "auto_context", None) is not None:
            self.agent.set_auto_context("Default context", self.auto_context)

        class_dir = inspect.getfile(self.__class__)
        code_dir = os.path.join(os.path.dirname(class_dir), "procedures", self.subkernel.SLUG)
        if os.path.exists(code_dir):
            self.jinja_env = Environment(
                loader=FileSystemLoader(code_dir),
                autoescape=select_autoescape()
            )

            for template_file in self.jinja_env.list_templates():
                if template_file.startswith('__'):
                    continue
                try:
                    template_name, _ = os.path.splitext(template_file)
                    template = self.jinja_env.get_template(template_file)
                    self.templates[template_name] = template
                except UnicodeDecodeError:
                    # For templates, this indicates a binary file which can't be a template, so throw a warning and skip.
                    logger.warn(f"File '{template_name}' in context '{self.__class__.__name__}' is not a valid template file as it cannot be decoded to a unicode string.")

    async def setup(self, config=None, parent_header=None):
        if config:
            self.config = config

        if callable(getattr(self.agent, 'setup', None)):
            await self.agent.setup(self.config, parent_header=parent_header)

    def cleanup(self):
        self.subkernel.cleanup()
        for msg_type, intercept_func, stream in self.intercepts:
            self.beaker_kernel.remove_intercept(msg_type=msg_type, func=intercept_func, stream=stream)
        del self.agent

    def _collect_and_register_intercepts(self, target):
        for _, method in inspect.getmembers(target, lambda member: inspect.ismethod(member) and hasattr(member, "_intercept")):
            msg_type, stream = getattr(method, "_intercept")
            self.intercepts.append((msg_type, method, stream))
            self.beaker_kernel.add_intercept(msg_type=msg_type, func=method, stream=stream)

    def get_subkernel(self):
        language = self.config.get("language", "python3")
        self.beaker_kernel.debug("new_kernel", f"Setting new kernel of `{language}`")
        kernel_opts = {
            subkernel.KERNEL_NAME: subkernel
            for subkernel in autodiscover("subkernels").values()
        }
        res = requests.post(
            f"{server_url}/api/kernels",
            json={"name": language, "path": ""},
            headers={"Authorization": f"token {server_token}"},
        )
        kernel_info = res.json()
        self.beaker_kernel.update_running_kernels()
        kernels = self.beaker_kernel.kernels
        subkernel_id = kernel_info["id"]
        # NOTE: MODIFIED `connect_to`
        # TODO: Refactor this into `lib/kernel_proxy_manager.py`
        matching = next((n for n in kernels if subkernel_id in n), None)
        if matching is None:
            raise ValueError("Unknown kernel " + subkernel_id)
        if kernels[matching] == self.beaker_kernel.server.config:
            raise ValueError("Refusing loopback connection")
        subkernel = kernel_opts[language](subkernel_id, kernels[matching], self)
        self.beaker_kernel.server.set_proxy_target(subkernel.connected_kernel)
        return subkernel


    @classmethod
    def available_subkernels(cls) -> List["BaseSubkernel"]:
        subkernels: Dict[str, BaseSubkernel] = autodiscover("subkernels")

        class_dir = inspect.getfile(cls)
        proc_dir = os.path.join(os.path.dirname(class_dir), "procedures")
        if os.path.exists(proc_dir):
            proc_slugs = list(os.listdir(proc_dir))
        else:
            proc_slugs = None
        subkernel_list = sorted(subkernels.values(), key=lambda subkernel: (subkernel.WEIGHT, subkernel.SLUG))

        if proc_slugs and subkernel_list:
            result = [subkernel.SLUG for subkernel in subkernel_list if subkernel.SLUG in proc_slugs]
            return result
        else:
            return []

    @classmethod
    def default_payload(cls) -> str:
        class_dir = inspect.getfile(cls)
        payload_file_path = os.path.join(os.path.dirname(class_dir), "default_payload.json")
        if os.path.exists(payload_file_path):
            with open(payload_file_path) as payload_file:
                return payload_file.read().strip()
        else:
            return "{}"

    def get_info(self) -> dict:
        """

        """
        custom_messages = {
            message_type: {
                "func": f"{intercept_func.__module__}.{intercept_func.__class__.__name__}.{intercept_func.__name__}",
                "docs": getattr(intercept_func, "_docs", None),
                "default_payload": getattr(intercept_func, "_default_payload", None),
            }
            for message_type, intercept_func, _ in self.intercepts
            if getattr(intercept_func, "_action", None) is None
        }
        action_details = {
            intercept_func._action: {
                "intercept": message_type,
                "func": f"{intercept_func.__module__}.{intercept_func.__class__.__name__}.{intercept_func.__name__}",
                "docs": getattr(intercept_func, "_docs", None),
                "default_payload": getattr(intercept_func, "_default_payload", None),
            }
            for message_type, intercept_func, _ in self.intercepts
            if getattr(intercept_func, "_action", None) is not None
        }
        if self.agent:
            agent_details = self.agent.get_info()
        else:
            agent_details = None
        payload = {
            "language": self.subkernel.DISPLAY_NAME,
            "subkernel": self.subkernel.KERNEL_NAME,
            "actions": action_details,
            "custom_messages": custom_messages,
            "procedures": list(self.templates.keys()),
            "agent": agent_details,
            "debug": self.beaker_kernel.debug_enabled,
            "verbose": self.beaker_kernel.verbose,
        }
        return payload


    @action()
    async def get_subkernel_state(self, message):
        """
        Fetches the state of the subkernel, including all defined variables, imports, and functions.
        """
        fetch_state_code = self.subkernel.FETCH_STATE_CODE
        state = await self.beaker_kernel.evaluate(fetch_state_code)
        result = state["return"]
        self.send_response(
            stream="iopub",
            msg_or_type="get_subkernel_state_response",
            content=result,
            parent_header=message.header,
        )
        return result
    get_subkernel_state._default_payload = "{}"


    @action()
    async def get_agent_history(self, message):
        """
        Returns all of the history for the LLM agent.
        """
        agent_messages = await self.agent.all_messages()
        self.send_response(
            stream="iopub",
            msg_or_type="get_agent_history_response",
            content= agent_messages,
            parent_header=message.header,
        )
        return agent_messages
    get_agent_history._default_payload = '{}'


    def send_response(self, stream, msg_or_type, content=None, channel=None, parent_header={}, parent_identities=None):
        return self.beaker_kernel.send_response(stream, msg_or_type, content, channel, parent_header, parent_identities)

    @property
    def slug(self) -> Optional[str]:
        """
        The slug should always be the same as the package that contains the class.
        I.e. For "beaker_kernel.contexts.pypackage" the slug should be "pypackage"
        """
        package_str = inspect.getmodule(self).__package__
        if package_str:
            return package_str.split(".")[-1]
        else:
            return None

    @property
    def lang(self):
        return self.subkernel.KERNEL_NAME

    @property
    def metadata(self):
        try:
            return json.loads(self.get_code('metadata'))
        except ValueError:
            return {}

    def get_code(self, name, render_dict: Dict[str, Any]=None) -> str:
        if render_dict is None:
            render_dict = {}
        template = self.templates.get(name, None)
        if template is None:
            raise ValueError(
                f"'{name}' is not a defined procedure for context '{self.__class__.__name__}' and "
                f"subkernel '{self.subkernel.DISPLAY_NAME} ({self.subkernel.KERNEL_NAME})'"
            )
        return template.render(**render_dict)


    async def execute(self, command, response_handler=None, parent_header={}):
        self.beaker_kernel.debug("execution_start", {"command": command}, parent_header=parent_header)
        stream = self.subkernel.connected_kernel.streams.shell
        execution_message = self.subkernel.connected_kernel.make_multipart_message(
            msg_type="execute_request",
            content={
                "silent": False,
                "store_history": False,
                "user_expressions": {},
                "allow_stdin": True,
                "stop_on_error": False,
                "code": command,
            },
            parent_header=parent_header,
            metadata={
                "trusted": True,
            },
        )
        stream.send_multipart(execution_message)
        original_message = JupyterMessage.parse(execution_message)
        message_id = original_message.header.get("msg_id")
        self.beaker_kernel.internal_executions.add(message_id)

        message_context = {
            "id": message_id,
            "stdout_list": [],
            "stderr_list": [],
            "return": None,
            "error": None,
            "done": False,
            "result": None,
            "parent": original_message,
        }
        message_metadata = {}

        filter_list = self.beaker_kernel.server.filters

        shell_socket = get_socket("shell")
        iopub_socket = get_socket("iopub")

        # Generate a handler to catch and silence the output
        async def silence_message(server, target_stream, data):
            message = JupyterMessage.parse(data)

            if message.parent_header.get("msg_id", None) != message_id:
                return data
            return None

        async def collect_result(server, target_stream, data):
            message = JupyterMessage.parse(data)
            # Ensure we are only working on handlers for this message response
            if message.parent_header.get("msg_id", None) != message_id:
                return data

            data = message.content["data"].get("text/plain", None)
            message_context["return"] = data
            filter_list.remove(
                InterceptionFilter(iopub_socket, "execute_result", collect_result)
            )

        async def collect_stream(server, target_stream, data):
            message = JupyterMessage.parse(data)
            # Ensure we are only working on handlers for this message response
            if message.parent_header.get("msg_id", None) != message_id:
                return data
            stream = message.content["name"]
            message_context[f"{stream}_list"].append(message.content["text"])

        async def handle_error(server, target_stream, data):
            message = JupyterMessage.parse(data)
            content = message.content
            message_context["error"] = content
            logger.error(
                "Error: %s %s\nTraceback:\n%s",
                content["ename"],
                content["evalue"],
                "\n".join(content["traceback"]),
            )

        async def cleanup(server, target_stream, data):
            message = JupyterMessage.parse(data)
            # Ensure we are only working on handlers for this message response
            if message.parent_header.get("msg_id", None) != message_id:
                return data
            if response_handler:
                filter_list.remove(
                    InterceptionFilter(iopub_socket, "stream", response_handler)
                )
            filter_list.remove(
                InterceptionFilter(iopub_socket, "stream", collect_stream)
            )
            filter_list.remove(
                InterceptionFilter(iopub_socket, "execute_input", silence_message)
            )
            filter_list.remove(
                InterceptionFilter(iopub_socket, "execute_request", silence_message)
            )
            filter_list.remove(InterceptionFilter(iopub_socket, "error", handle_error))
            filter_list.remove(
                InterceptionFilter(shell_socket, "execute_reply", cleanup)
            )
            message_context["result"] = message
            message_context["done"] = True

        filter_list.append(
            InterceptionFilter(iopub_socket, "execute_input", silence_message)
        )
        filter_list.append(
            InterceptionFilter(iopub_socket, "execute_request", silence_message)
        )
        filter_list.append(
            InterceptionFilter(iopub_socket, "execute_result", collect_result)
        )
        filter_list.append(InterceptionFilter(shell_socket, "execute_reply", cleanup))
        filter_list.append(InterceptionFilter(iopub_socket, "stream", collect_stream))
        filter_list.append(InterceptionFilter(iopub_socket, "error", handle_error))

        if response_handler:
            filter_list.append(
                InterceptionFilter(iopub_socket, "stream", response_handler)
            )

        await asyncio.sleep(0.1)
        while not message_context["done"]:
            await asyncio.sleep(0.2)
        # Wait for any straggling messages
        await asyncio.sleep(0.2)
        self.beaker_kernel.internal_executions.remove(message_id)
        self.beaker_kernel.debug("execution_end", message_context, parent_header=parent_header)
        return message_context

    async def evaluate(self, expression, parent_header={}):
        result = await self.execute(expression, parent_header=parent_header)
        try:
            parsed_result = self.subkernel.parse_subkernel_return(result)
            result["return"] = parsed_result
        except Exception:
            logger.error("Unable to parse result.")
            logger.debug("Subkernel: %s\nResult:\n%s", self.subkernel.connected_kernel, result)
        return result

def autodiscover_contexts():
    return autodiscover("contexts")
