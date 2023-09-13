import asyncio
import functools
import logging
from typing import Dict, Any, Type, TYPE_CHECKING

from archytas.react import ReActAgent

from .subkernels.base import BaseSubkernel
from .toolsets.base import BaseToolset
from .codesets import get_metadata, get_template

if TYPE_CHECKING:
    from llmkernel.kernel import LLMKernel

logger = logging.getLogger(__name__)

class Context:
    subkernel: BaseSubkernel
    toolset: BaseToolset
    config: Dict[str, Any]
    agent: ReActAgent
    kernel: "LLMKernel"

    def __init__(self, kernel: "LLMKernel", subkernel: BaseSubkernel, toolset_cls: Type[BaseToolset], config: Dict[str, Any]) -> None:
        self.kernel = kernel
        self.subkernel = subkernel
        self.toolset = toolset_cls(context=self)
        self.agent = ReActAgent(
            tools=[self.toolset],
            allow_ask_user=False,
            verbose=True,
            spinner=None,
            rich_print=False,
            thought_handler=self.kernel.handle_thoughts,
        )
        self.config = config

        # Add intercepts
        for message, (handler, stream) in self.toolset.intercepts.items():
            self.kernel.add_intercept(message, handler, stream=stream)

        # Set auto-context from toolset
        if getattr(self.toolset, "auto_context", None) is not None:
            self.agent.set_auto_context("Default context", self.toolset.auto_context)

    async def setup(self, parent_header=None):
        await self.toolset.setup(self.config, parent_header=parent_header)

    @property
    def lang(self):
        return self.subkernel.KERNEL_NAME

    def metadata(self):
        return get_metadata(self.toolset.toolset_name, self.lang)

    def get_code(self, name, render_dict: Dict[str, Any]={}) -> str:
        return get_template(self.toolset.toolset_name, self.lang, name, render_dict)

    async def execute(self, command, response_handler=None, parent_header={}):
        return await self.kernel.execute(command, response_handler, parent_header)

    async def evaluate(self, expression, parent_header={}):
        return await self.kernel.evaluate(expression, parent_header)