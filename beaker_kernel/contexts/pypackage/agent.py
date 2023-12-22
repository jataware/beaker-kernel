import json
import logging
import re

from archytas.tool_utils import AgentRef, LoopControllerRef, tool

from beaker_kernel.lib.agent import BaseAgent
from beaker_kernel.lib.context import BaseContext


logger = logging.getLogger(__name__)


class PyPackageAgent(BaseAgent):
    """
    You are an programming assistant to aid a developer working in a Jupyter notebook by answering their questions and helping write code for them based on their
    prompt.

    You have the ability to look up information regarding the environment via the tools that are provided. You should use these tools whenever are not able to
    satisfy the request to a high level of reliability. You should avoid guessing at how to do something in favor of using the provided tools to look up more
    information. Do not make assumptions, always check the documentation instead of assuming.

    If you are requested to work with a package for which you have low information, you should first use the `get_package_structure` tool to learn about the package
    and better plan how to retrieve the needed information.
    Please feel free to step through several iterations of using tools to fetch more information until you are able to fully satisfy the request or feel like you
    are getting stuck.
    """
    def __init__(self, context: BaseContext = None, tools: list = None, **kwargs):
        libraries = {
        }
        super().__init__(context, tools, **kwargs)

    @tool(autosummarize=True)
    async def get_package_structure(self, target: str, agent:AgentRef, loop: LoopControllerRef) -> str:
        """
        This tool enumerates all of the sub-packages, modules, and importable objects within a python package.

        If a member of the package is provided, it will include the entire list of items for the package that contains the member.
        Modules that have already been imported will be marked with an asterisk after the package name.
        You can use this to help decide which documentation to retrieve or how to find a particular member of a package.

        Args:
            target (str): A python package or a member of a python package for which an enumeration of importable members.
        Returns:
            str: A new-line delimeted list of members of a particular package, including the package itself, with already imported members followed by an asterisk.
        """

        code = agent.context.get_code("get_package_structure", {"target": target})
        structure = await agent.context.evaluate(code)
        return structure["return"]

    @tool(autosummarize=True)
    async def get_documentation(self, target: str, agent: AgentRef, loop: LoopControllerRef) -> str:
        """
        This tool retrieves documentation about a Python package/module/class/etc. If you don't know where to locate the item, use the get_package_structure tool
        to determine the correct dot-seperated path to look up.

        You should use this to fetch documentation about a module and/or a class to determine how to use it. This can be used to answer questions about the code
        posed by the user, but also can be used to learn how to write the code if you are asked to generate code using any of these tools.

        Args:
            target (str): Python package, module or function for which documentation is requested
        Returns:
            str: Human readable documentation for the provided item.
        """
        module = target.split('.', 1)[0]
        code = agent.context.get_code("get_documentation", {"module": module, "target": target})
        response = await agent.context.evaluate(code)
        return response["return"]

    @tool(autosummarize=True)
    async def get_variables_in_scope(self, agent: AgentRef) -> str:
        """
        This tool returns a list of all variables that exist in the current scope, along with any type/class information of what the variable represents.

        Returns:
            str: Human readable list of variables, followed by any type/class information.
        """
        code = agent.context.get_code("get_variables", {})
        response = await agent.context.evaluate(code)
        return response["return"]

    @tool()
    async def get_info_on_variable(self, variable_name: str, agent: AgentRef) -> str:
        """
        This tool allows you to fetch information about a variable and what it represents.

        Thi

        Args:
            variable_name (str): A strings which is the name of a variable in the current scope that you want more information about.
        Returns:
            str: Human readable information about the variable.
        """
        code = agent.context.get_code("get_variable_info", {"variable_name": variable_name})
        response = await agent.context.evaluate(code)
        return response["return"]


    @tool()
    async def generate_code(self, code_request: str, agent: AgentRef, loop: LoopControllerRef):
        """
        Generated Python code to be run in an interactive Jupyter notebook.

        Input is a full grammatically correct question about or request for an action to be performed in the current environment.
        If you need more information on how to accomplish the request, you should use the other tools prior to using this one.


        Args:
            code_request (str): A fully grammatically correct question about the current model.
        """

        code_generation_prompt = f"""
DO NOT USE A TOOL to generate the code. The code should be generated by the LLM and not by a tool.
However, you SHOULD USE the others tools for information/documentation retrieval if you do not have enough information to complete the request
without making assumptions.

Please generate Python code to satisfy the user's request below.

Request:
```
{code_request}
```

Please generate the code as if you were programming inside a Jupyter Notebook and the code is to be executed inside a cell.
You MUST wrap the code with a line containing three backticks (```) before and after the generated code.
No addtional text is needed in the response, just the code block.
""".strip()

        response = await agent.query(code_generation_prompt)
        preamble, code, coda = re.split("```\w*", response)
        loop.set_state(loop.STOP_SUCCESS)

        result = {
            "action": "code_cell",
            "language": "python3",
            "content": code.strip(),
        }

        return json.dumps(result)
