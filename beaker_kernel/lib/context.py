import inspect
import json
import logging
import os.path
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Tuple

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

from .codeset import get_metadata, get_template

if TYPE_CHECKING:
    from archytas.react import ReActAgent

    from beaker_kernel.kernel import LLMKernel

    from .agent import BaseAgent
    from .subkernels.base import BaseSubkernel
    from .toolset import BaseToolset

logger = logging.getLogger(__name__)

class BaseContext:
    slug: str
    beaker_kernel: "LLMKernel"
    subkernel: "BaseSubkernel"
    toolset: "BaseToolset"
    config: Dict[str, Any]
    agent: "ReActAgent"

    intercepts: Dict[str, Tuple[Callable, str]] = {}
    jinja_env: Optional[Environment] = None
    templates: Dict[str, Template] = {}


    def __init__(self, beaker_kernel: "LLMKernel", subkernel: "BaseSubkernel", agent_cls: "BaseAgent", config: Dict[str, Any]) -> None:  # toolset_cls: Type["BaseToolset"],
        self.beaker_kernel = beaker_kernel
        self.subkernel = subkernel
        # self.toolset = toolset_cls(context=self)
        self.agent = agent_cls(
            context=self,
            tools=[],
        )
        self.config = config

        # Add intercepts
        for message, (handler, stream) in self.intercepts.items():
            self.beaker_kernel.add_intercept(message, handler, stream=stream)

        # Set auto-context from toolset
        if getattr(self, "auto_context", None) is not None:
            self.agent.set_auto_context("Default context", self.auto_context)

        class_dir = inspect.getfile(self.__class__)
        code_dir = os.path.join(os.path.dirname(class_dir), "code", self.subkernel.SLUG)
        if os.path.exists(code_dir):
            self.jinja_env = Environment(
                loader=FileSystemLoader(code_dir),
                autoescape=select_autoescape()
            )

            for template_file in self.jinja_env.list_templates():
                template_name, _ = os.path.splitext(template_file)
                template = self.jinja_env.get_template(template_file)
                self.templates[template_name] = template

    async def setup(self, parent_header=None):
        await self.toolset.setup(self.config, parent_header=parent_header)

    @property
    def lang(self):
        return self.subkernel.KERNEL_NAME

    @property
    def metadata(self):
        return json.loads(self.get_code('metadata'))

    def get_code(self, name, render_dict: Dict[str, Any]=None) -> str:
        if render_dict is None:
            render_dict = {}
        template = self.templates.get(name, None)
        if template is None:
            raise ValueError(
                f"'{name}' is not a defined codeset for context '{self.__class__.__name__}' and "
                f"subkernel '{self.subkernel.DISPLAY_NAME} ({self.subkernel.KERNEL_NAME})'"
            )
        return template.render(**render_dict)

    async def execute(self, command, response_handler=None, parent_header={}):
        return await self.beaker_kernel.execute(command, response_handler, parent_header)

    async def evaluate(self, expression, parent_header={}):
        return await self.beaker_kernel.evaluate(expression, parent_header)


def collect_contexts(path):
    return []
