import inspect
import json
import logging
import os.path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

from beaker_kernel.lib.autodiscovery import autodiscover
from beaker_kernel.lib.utils import intercept

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

    def __init__(self, beaker_kernel: "LLMKernel", subkernel: "BaseSubkernel", agent_cls: "BaseAgent", config: Dict[str, Any]) -> None:
        self.intercepts = []
        self.jinja_env = None
        self.templates = {}
        self.beaker_kernel = beaker_kernel
        self.subkernel = subkernel
        self.agent = agent_cls(
            context=self,
            tools=[],
        )
        self.config = config

        # Add intercepts, by inspecting the instance and extracting matching methods
        for _, method in inspect.getmembers(self, lambda member: inspect.ismethod(member) and hasattr(member, "_intercept")):
            msg_type, stream = getattr(method, "_intercept")
            self.intercepts.append((msg_type, method, stream))
            self.beaker_kernel.add_intercept(msg_type=msg_type, func=method, stream=stream)

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

    async def cleanup(self):
        for msg_type, intercept_func, stream in self.intercepts:
            self.beaker_kernel.remove_intercept(msg_type=msg_type, func=intercept_func, stream=stream)
        del self.agent

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
        intercept_details = {
            message_type: {
                "func": f"{intercept_func.__module__}.{intercept_func.__class__.__name__}.{intercept_func.__name__}"
                # TODO: Add more info here
            }
            for message_type, intercept_func, stream in self.intercepts
        }
        if self.agent:
            agent_details = self.agent.get_info()
        else:
            agent_details = None
        payload = {
            "language": self.subkernel.DISPLAY_NAME,
            "subkernel": self.subkernel.KERNEL_NAME,
            "intercepts": intercept_details,
            "procedures": list(self.templates.keys()),
            "agent": agent_details,
        }
        return payload

    @intercept(msg_type="debug_message_history_request")
    async def debug_messages(self, message):
        agent_messages = await self.agent.all_messages()
        self.send_response(
            stream="iopub",
            msg_or_type="debug_message_history_reply",
            content= agent_messages,
            parent_header=message.header,
        )

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
        return await self.beaker_kernel.execute(command, response_handler, parent_header)

    async def evaluate(self, expression, parent_header={}):
        return await self.beaker_kernel.evaluate(expression, parent_header)

def autodiscover_contexts():
    return autodiscover("contexts")
