import json
import logging
import re

from archytas.react import Undefined
from archytas.tool_utils import AgentRef, LoopControllerRef, tool, toolset

from beaker_kernel.lib.agent import BaseAgent
from beaker_kernel.lib.context import BaseContext
from beaker_kernel.lib.jupyter_kernel_proxy import JupyterMessage

logging.disable(logging.WARNING)  # Disable warnings
logger = logging.Logger(__name__)

@toolset()
class DatasetToolset:

    @tool()
    async def generate_code(
        self, query: str, agent: AgentRef, loop: LoopControllerRef
    ) -> None:
        """
        Generated  code to be run in an interactive Jupyter notebook for the purpose of exploring, modifying and visualizing a Dataframe.

        Input is a full grammatically correct question about or request for an action to be performed on the loaded dataframe.

        Args:
            query (str): A fully grammatically correct question about the current dataset.

        """
        # set up the agent
        # str: Valid and correct python code that fulfills the user's request.
        var_sections = []
        for var_name, dataset_obj in agent.context.dataset_map.items():
            df_info = await agent.context.describe_dataset(var_name)
            var_sections.append(f"""
You have access to a variable name `{var_name}` that is a {agent.context.metadata.get("df_lib_name", "Pandas")} Dataframe with the following structure:
{df_info}
--- End description of variable `{var_name}`
""")
        prompt = f"""
You are a programmer writing code to help with scientific data analysis and manipulation in {agent.context.metadata.get("name", "a Jupyter notebook")}.

Please write code that satisfies the user's request below.

{"".join(var_sections)}

If you are asked to modify or update the dataframe, modify the dataframe in place, keeping the updated variable the same unless specifically specified otherwise.

You also have access to the libraries {agent.context.metadata.get("libraries", "that are common for these tasks")}.

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
                "language": agent.context.lang,
                "content": code.strip(),
            }
        )
        return result


class DatasetAgent(BaseAgent):

    def __init__(self, context: BaseContext = None, tools: list = None, **kwargs):
        tools = [DatasetToolset]
        super().__init__(context, tools, **kwargs)
