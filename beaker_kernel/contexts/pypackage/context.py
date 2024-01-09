from typing import TYPE_CHECKING, Any, Dict, List

from beaker_kernel.lib.context import BaseContext
from beaker_kernel.lib.subkernels.python import PythonSubkernel

from .agent import PyPackageAgent

if TYPE_CHECKING:
    from beaker_kernel.kernel import LLMKernel
    from beaker_kernel.lib.agent import BaseAgent
    from beaker_kernel.lib.subkernels.base import BaseSubkernel

class PyPackageContext(BaseContext):

    agent_cls: "BaseAgent" = PyPackageAgent

    def __init__(self, beaker_kernel: "LLMKernel", subkernel: "BaseSubkernel", config: Dict[str, Any]) -> None:
        if not isinstance(subkernel, PythonSubkernel):
            raise ValueError("This context is only valid for Python.")
        super().__init__(beaker_kernel, subkernel, self.agent_cls, config)

    async def setup(self, config=None, parent_header=None):
        await self.execute(self.get_code("setup", {}))
        return await super().setup(config, parent_header)
