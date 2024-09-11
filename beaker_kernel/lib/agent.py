import json
import logging
import re
import typing

from archytas.agent import Message
from archytas.react import ReActAgent, Undefined
from archytas.tool_utils import AgentRef, LoopControllerRef, ReactContextRef, tool

from beaker_kernel.lib.config import config
from beaker_kernel.lib.utils import env_enabled

if typing.TYPE_CHECKING:
    from .context import BeakerContext

logger = logging.getLogger(__name__)


class AgentAuthenticationError(Exception):
    pass


class BeakerAgent(ReActAgent):

    context: "BeakerContext"
    MODEL: str = config.LLM_SERVICE_MODEL

    def __init__(
        self,
        context: "BeakerContext" = None,
        tools: list = None,
        **kwargs,
    ):
        self.context = context

        self.context.beaker_kernel.debug("init-agent", {
            "debug": self.context.beaker_kernel.debug_enabled,
            "verbose": self.context.beaker_kernel.verbose,
        })
        super().__init__(
            model=self.MODEL,
            api_key=config.LLM_SERVICE_TOKEN,
            tools=tools,
            verbose=self.context.beaker_kernel.verbose,
            spinner=None,
            rich_print=False,
            allow_ask_user=False,
            thought_handler=context.beaker_kernel.handle_thoughts,
            **kwargs
        )

    async def execute(self, additional_messages: list[Message] = None) -> str:
        import openai
        try:
            return await super().execute(additional_messages or [])
        except (openai.AuthenticationError) as e:
            raise AgentAuthenticationError(e)
        except (openai.OpenAIError) as e:
            if "The api_key client option must be set" in str(e):
                raise AgentAuthenticationError(e)
            else:
                raise

    async def oneshot(self, prompt: str, query: str) -> str:
        import openai
        try:
            return await super().oneshot(prompt, query)
        except (openai.AuthenticationError,) as e:
            raise AgentAuthenticationError(e)
        except (openai.OpenAIError) as e:
            if "The api_key client option must be set" in str(e):
                raise AgentAuthenticationError(e)
            else:
                raise

    def get_info(self):
        """
        Returns info about the agent for communication with the kernel.
        """
        info = {
            "name": self.__class__.__name__,
            "tools": {tool_name: tool_func.__doc__.strip() for tool_name, tool_func in self.tools.items()},
            "agent_prompt": self.__class__.__doc__.strip(),
        }
        return info

    def debug(self, event_type: str, content: typing.Any = None) -> None:
        self.context.beaker_kernel.debug(
            event_type=f"agent_{event_type}",
            content=content
        )
        return super().debug(event_type=event_type, content=content)

    def display_observation(self, observation):
        content = {
            "observation": observation
        }
        parent_header = {}
        self.context.send_response(
            stream="iopub",
            msg_or_type="llm_observation",
            content=content,
            parent_header=parent_header,
        )
        return super().display_observation(observation)

    @tool()
    async def ask_user(
        self, query: str, agent: AgentRef, loop: LoopControllerRef, react_context: ReactContextRef,
    ) -> str:
        """
        Sends a query to the user and returns their response

        Args:
            query (str): A fully grammatically correct question for the user.

        Returns:
            str: The user's response to the query.
        """
        return await self.context.beaker_kernel.prompt_user(query, parent_message=react_context.get("message", None))

# Provided for backwards compatibility
BaseAgent = BeakerAgent
