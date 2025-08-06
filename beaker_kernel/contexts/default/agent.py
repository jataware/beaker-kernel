"""
Default agent implementation for Beaker.

Provides a default agent with basic functionality including a joke tool.
"""

import logging
from beaker_kernel.lib.agent import BeakerAgent
from beaker_kernel.lib.context import BeakerContext
from beaker_kernel.lib.utils import ExecutionError, get_beaker_kernel
from beaker_kernel.lib.tools import tool

logger = logging.getLogger(__name__)


@tool
async def tell_a_joke(topic: str = "any") -> str:
    """
    Generates a joke for the user.

    Args:
        topic (str): A topic that the joke should be about. If no topic is provided, use the default value of "any".
    Returns:
        str: The text of the joke, possibly with or without formatting.
    """
    code = """
import requests
url = 'https://v2.jokeapi.dev/joke/Programming,Miscellaneous,Pun,Spooky?blacklistFlags=nsfw,religious,political,racist,sexist,explicit'
result = requests.get(url).json()
if result.get('type') == 'single':
    formatted_joke = result.get('joke')
elif result.get('type') == 'twopart':
    formatted_joke = f'''
{result.get('setup')}

{result.get('delivery')}
'''.strip()

formatted_joke
""".strip()

    try:
        # Get the kernel to access the context
        kernel = get_beaker_kernel()
        if kernel and hasattr(kernel, 'context'):
            context = await kernel.context.evaluate(code)
            joke = context["return"]
        else:
            raise Exception("No kernel context available")
    except Exception as e:
        logger.warning(f"Error fetching joke: {e}")
        joke = """Have you ever seen an elephant hiding in a tree? Me neither. They must be VERY good at it!"""

    return joke


class DefaultAgent(BeakerAgent):
    """
    Default agent for Beaker contexts.
    
    Provides basic functionality with a joke tool as an example.
    """

    def __init__(self, context: BeakerContext = None, tools=None, **kwargs):
        # Add our default tools
        default_tools = [tell_a_joke]
        all_tools = default_tools + (tools or [])
        
        # Initialize the parent agent
        super().__init__(context=context, tools=all_tools, **kwargs)