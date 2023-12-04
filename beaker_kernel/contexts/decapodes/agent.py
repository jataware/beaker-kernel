import json
import logging
import re

from archytas.tool_utils import AgentRef, LoopControllerRef, tool, toolset

from beaker_kernel.lib.agent import BaseAgent
from beaker_kernel.lib.context import BaseContext

logging.disable(logging.WARNING)  # Disable warnings
logger = logging.Logger(__name__)


@toolset()
class DecapodesToolset:
    """
    Toolset used for working with the Julia package Decacpodes, a framework for doing descrete exterior calculus based modeling.
    """

    @tool()
    async def generate_code(
        self, query: str, agent: AgentRef, loop: LoopControllerRef
    ) -> None:
        """
        Generated Julia code to be run in an interactive Jupyter notebook for the purpose of exploring and modifying systems the DecaExpr.

        Input is a full grammatically correct question about or request for an action to be performed on the loaded model.

        Assume that the expression is already loaded and has the variable named `_expr`.
        Information about the dataframe can be loaded with the `model_structure` tool.

        Args:
            query (str): A fully grammatically correct queistion about the current model.
        """
        prompt = f"""
You are a programmer writing code to help with scientific data analysis and manipulation in Julia.

Please write code that satisfies the user's request below.

You have access to a variable name `_expr` that is a Decapodes SyntacticModel model with the following structure:
{await agent.context.model_structure()}

Your generated will be in the form `_expr = parse_decapode(quote ...modified object.. end)`

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


class DecapodesAgent(BaseAgent):

    def __init__(self, context: BaseContext = None, tools: list = None, **kwargs):
        tools = [DecapodesToolset]
        super().__init__(context, tools, **kwargs)
