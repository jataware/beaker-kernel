from typing import TYPE_CHECKING, Any, Dict, List
import logging
logger = logging.getLogger(__name__)

from beaker_kernel.lib.context import BaseContext
from beaker_kernel.lib.autodiscovery import autodiscover
from beaker_kernel.lib.utils import action

from .agent import DefaultAgent

if TYPE_CHECKING:
    from beaker_kernel.kernel import LLMKernel
    from beaker_kernel.lib.agent import BaseAgent
    from beaker_kernel.lib.subkernels.base import BaseSubkernel

class DefaultContext(BaseContext):

    agent_cls: "BaseAgent" = DefaultAgent

    WEIGHT: 10

    def __init__(self, beaker_kernel: "LLMKernel", config: Dict[str, Any]):
        super().__init__(beaker_kernel, self.agent_cls, config)

    @classmethod
    def available_subkernels(cls) -> List["BaseSubkernel"]:
        subkernels: Dict[str, BaseSubkernel] = autodiscover("subkernels")
        subkernel_list = sorted(subkernels.values(), key=lambda subkernel: (subkernel.WEIGHT, subkernel.SLUG))
        subkernel_slugs = [subkernel.SLUG for subkernel in subkernel_list]
        return subkernel_slugs

    async def auto_context(self):
        return f"""
        If you need to generate code, you should write it in the '{self.subkernel.DISPLAY_NAME}' language for execution
        in a Jupyter notebook using the '{self.subkernel.KERNEL_NAME}' kernel.
        """.strip()

    async def generate_preview(self):
        """
        Preview what exists in the subkernel.
        """
        fetch_state_code = self.subkernel.FETCH_STATE_CODE
        result = await self.evaluate(fetch_state_code)
        state = result.get("return", None)
        if state:
            return {
                "x-application/beaker-subkernel-state": {
                    "state": {
                        "application/json": state
                    }
                },
            }
