import json
import logging
import re
import typing

from archytas.react import ReActAgent, Undefined
from archytas.tool_utils import AgentRef, LoopControllerRef, tool

if typing.TYPE_CHECKING:
    from .context import BaseContext


logger = logging.getLogger(__name__)

class BaseAgent(ReActAgent):

    context: "BaseContext"

    def __init__(
        self,
        context: "BaseContext" = None,
        tools: list = None,
        **kwargs,
    ):
        self.context = context

        super().__init__(
            # model="gpt-4",  # Use default
            # api_key=api_key,  # TODO: get this from configuration
            tools=tools,
            verbose=True,
            spinner=None,
            rich_print=False,
            allow_ask_user=False,
            thought_handler=context.beaker_kernel.handle_thoughts,
            **kwargs
        )

    @tool()
    async def generate_code(
        self, query: str, agent: AgentRef, loop: LoopControllerRef
    ) -> None:
        """
        Generated code to be run in an interactive Jupyter notebook.

        Args:
            query (str): A fully grammatically correct question or request.
        """


        prompt = f"""
    You are a programmer writing code to help with working in a Python notebook.

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
                "language": "python3",
                "content": code.strip(),
            }
        )
        return result
