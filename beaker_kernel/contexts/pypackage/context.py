from typing import TYPE_CHECKING, Any, Dict, List

from beaker_kernel.lib.context import BaseContext
from beaker_kernel.lib.subkernels.python import PythonSubkernel

from .agent import PyPackageAgent

if TYPE_CHECKING:
    from beaker_kernel.kernel import LLMKernel
    from beaker_kernel.lib.agent import BaseAgent

class PyPackageContext(BaseContext):

    agent_cls: "BaseAgent" = PyPackageAgent

    def __init__(self, beaker_kernel: "LLMKernel", config: Dict[str, Any]):
        super().__init__(beaker_kernel, self.agent_cls, config)
        if not isinstance(self.subkernel, PythonSubkernel):
            raise ValueError("This context is only valid for Python.")

    async def setup(self, context_info=None, parent_header=None):
        await self.execute(self.get_code("setup", {}))
        return await super().setup(context_info, parent_header)
