from pathlib import Path
from hatchling.plugin import hookimpl
from hatch.template.plugin.interface import TemplateInterface
from hatch.template import File
from hatch.template.files_default import PyProject

from . import TemplateFile, PathTemplate
from .paths import package_name, context_subdir


class AgentFile(TemplateFile):

    PATH_PARTS = [
        'agent.py'
    ]

    TEMPLATE = """\
from typing import TYPE_CHECKING

from beaker_kernel.lib.tools import tool
from beaker_kernel.lib.utils import get_beaker_kernel
from beaker_kernel.lib.agent import BeakerAgent

if TYPE_CHECKING:
    from beaker_kernel.kernel import BeakerKernel


@tool
async def magic_eight_ball(question: str) -> str:
    \"\"\"
    This is an example tool that is provided to help users understand how tools work in Beaker. It should only be
    used when a user explicitly asks for it.

    This simulates a Magic 8 ball toy where a person asks questions and gets answers indicating yes/no/maybe.

    Args:
        question (str): The question the user would like to have answered. The question must be answerable as
                        yes/no/maybe. If the question is not a yes/no/maybe question then inform the user to
                        reword the question so that it is a proper question before proceeding.
    Returns:
        str: A string that is either the response the magic eight ball returned.
    \"\"\"
    import random
    choices = [
        "Signs point to yes!",
        "Doesn't look good...",
        "My sources say no.",
        "I asked Siri and she said it's a secret.",
        f"How on earth can you think that '{{question.strip()}}' is an appropriate question to ask me!?!?",
        "Yes, duh!",
        "No way, Jose!",
    ]
    if question.startswith("sudo"):
        return "Your wish is granted!"
    return random.choice(choices)


class {agent_class}(BeakerAgent):
    \"\"\"
    You are a helpful agent that will answer questions and help with what is asked of you.
    \"\"\"
    
    def __init__(self, context=None, tools=None, **kwargs):
        # Add our custom tools
        default_tools = [magic_eight_ball]
        all_tools = default_tools + (tools or [])
        
        # Initialize the parent agent
        super().__init__(context=context, tools=all_tools, **kwargs)

"""
