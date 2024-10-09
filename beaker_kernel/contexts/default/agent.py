import json
import logging
import re

from archytas.tool_utils import AgentRef, LoopControllerRef, tool

from beaker_kernel.lib.agent import BeakerAgent
from beaker_kernel.lib.context import BeakerContext


logger = logging.getLogger(__name__)


class DefaultAgent(BeakerAgent):
    """
    You are an programming assistant to aid a developer working in a Jupyter notebook by answering their questions and helping write code for them based on their
    prompt.
    """

    @tool()
    async def tell_a_joke(self, topic: str, agent: AgentRef, loop: LoopControllerRef) -> str:
        """
        Generates a joke for the user.


        Args:
            topic (str): A topic that the joke should be about
        Returns:
            str: The joke
        """
        joke = """Have you ever seen an elephant hiding in a tree? Me neither. They must be VERY good at it!
"""
        return joke
