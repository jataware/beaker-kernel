import json
import logging
import re

from archytas.tool_utils import AgentRef, LoopControllerRef, tool

from beaker_kernel.lib.agent import BaseAgent
from beaker_kernel.lib.context import BaseContext

logging.disable(logging.WARNING)  # Disable warnings
logger = logging.Logger(__name__)



class OceananigansAgent(BaseAgent):
    """
    LLM Agent useful for working with the Julia language and the Oceananigans modeling Julia package.
    """

    def __init__(self, context: BaseContext = None, tools: list = None, **kwargs):
        super().__init__(context, tools, **kwargs)

    @tool()
    async def generate_code(
        self, query: str, agent: AgentRef, loop: LoopControllerRef
    ) -> None:
        """
        Generated Julia code to be run in an interactive Jupyter notebook for the purpose of creating models, visualizations, and simulations in Oceananigans.

        Input is a full grammatically correct question about or request for an action to be performed with the Julia language or Oceananigans.

        Args:
            query (str): A fully grammatically correct queistion about the current model.
        """
        prompt = f"""
You are a programmer writing code to help with writing simulations in Julia and Oceananigans.jl, a fast, friendly, flexible software package for finite volume simulations of the nonhydrostatic and hydrostatic Boussinesq equations on CPUs and GPUs.

As an Oceananigans example, you can run a two-dimensional, horizontally-periodic simulation of turbulence using 128² finite volume cells for 4 non-dimensional time units:
```
using Oceananigans
grid = RectilinearGrid(CPU(), size=(128, 128), x=(0, 2π), y=(0, 2π), topology=(Periodic, Periodic, Flat))
model = NonhydrostaticModel(; grid, advection=WENO())
ϵ(x, y) = 2rand() - 1
set!(model, u=ϵ, v=ϵ)
simulation = Simulation(model; Δt=0.01, stop_time=4)
run!(simulation)
```

If you have other knowledge of Oceananigans.jl, please use that as well.

When doing visualization tasks, please use `WGLMakie`.

Note that `using Oceananigans, WGLMakie` has already been run so do not include it in your output.

Here are the currently active Oceananigans-related variables in state, please don't redefine these since they are in state:
```
{await agent.context.get_available_vars()}
```

Please write code that satisfies the user's request below.

Please generate the code as if you were programming inside a Jupyter Notebook and the code is to be executed inside a cell.
You MUST wrap the code with a line containing three backticks (```) before and after the generated code.
No addtional text is needed in the response, just the code block.
"""

        llm_response = await agent.oneshot(prompt=prompt, query=query)
        loop.set_state(loop.STOP_SUCCESS)
        preamble, code, coda = re.split("```\w*", llm_response)
        result = json.dumps(
            {
                "action": "code_cell",
                "language": "julia-1.9",
                "content": code.strip(),
            }
        )
        return result
