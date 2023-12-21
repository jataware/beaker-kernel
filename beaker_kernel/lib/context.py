import inspect
import json
import logging
import os.path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

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

    # intercepts: Dict[str, Tuple[Callable, str]] = {}
    jinja_env: Optional[Environment] = None
    templates: Dict[str, Template] = {}

    def __init__(self, beaker_kernel: "LLMKernel", subkernel: "BaseSubkernel", agent_cls: "BaseAgent", config: Dict[str, Any]) -> None:
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
                template_name, _ = os.path.splitext(template_file)
                template = self.jinja_env.get_template(template_file)
                self.templates[template_name] = template

    async def setup(self, config=None, parent_header=None):
        if config:
            self.config = config
        if callable(getattr(self.agent, 'setup', None)):
            await self.agent.setup(self.config, parent_header=parent_header)

    @classmethod
    def available_subkernels(cls) -> List["BaseSubkernel"]:
        class_dir = inspect.getfile(cls)
        proc_dir = os.path.join(os.path.dirname(class_dir), "procedures")
        if os.path.exists(proc_dir):
            subkernel_slugs = list(os.listdir(proc_dir))
            return subkernel_slugs
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

    def send_response(self, *args, **kwargs):
        return self.beaker_kernel.send_response(*args, **kwargs)

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
