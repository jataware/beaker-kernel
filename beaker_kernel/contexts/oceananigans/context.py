import json
import logging
import os
from typing import TYPE_CHECKING, Any, Dict

import requests

from beaker_kernel.lib.context import BaseContext
from beaker_kernel.lib.utils import intercept

from .agent import OceananigansAgent

if TYPE_CHECKING:
    from beaker_kernel.kernel import LLMKernel
    from beaker_kernel.lib.subkernels.base import BaseSubkernel


logger = logging.getLogger(__name__)


class OceananigansContext(BaseContext):

    slug = "oceananigans"
    agent_cls = OceananigansAgent

    def __init__(self, beaker_kernel: "LLMKernel", subkernel: "BaseSubkernel", config: Dict[str, Any]) -> None:
        self.target = "oceananigan"
        self.reset()
        super().__init__(beaker_kernel, subkernel, self.agent_cls, config)


    async def setup(self, config, parent_header):
        await self.execute(self.get_code("setup"))
        print("Oceananigans creation environment set up")


    async def post_execute(self, message):
        pass

    def reset(self):
        pass

    async def auto_context(self):
        return f"""You are a scientific modeler whose goal is to help the user with Julia and Oceananigans.jl

Here are the currently active Oceananigans-related variables in state:
```
{await self.get_available_vars()}
```
Please answer any user queries to the best of your ability, but do not guess if you are not sure of an answer.
If you are asked to write code, please use the generate_code tool. Please use existing variables if you can and try
not to redefine existing variables or redo a task the user has already done (unless it needs correcting).
"""

    async def get_available_vars(self, parent_header={}):
        code = self.get_code("var_info")
        var_info_response = await self.beaker_kernel.evaluate(
            code,
            parent_header=parent_header,
        )
        return  var_info_response.get('return')



    @intercept(msg_type="save_data_request") 
    async def save_data(self, message):
        content = message.content

        result = await self.evaluate(
            self.get_code("save_data", 
                {
                    "dataservice_url": os.environ["DATA_SERVICE_URL"], 
                    "name": content.get("name"),
                    "description": content.get("description", ""),
                    "filenames": content.get("filenames"),
                }
            ),
        )

        self.beaker_kernel.send_response(
            "iopub", "save_data_response", result["return"], parent_header=message.header
        )

