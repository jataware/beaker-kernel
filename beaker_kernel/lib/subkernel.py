import abc
import asyncio
import json
from typing import Any, Callable, TYPE_CHECKING
import hashlib
import shutil
from tempfile import mkdtemp
import os
import os.path
import requests

from archytas.tool_utils import AgentRef, tool, LoopControllerRef, ReactContextRef

from .autodiscovery import autodiscover
from .utils import env_enabled, action, ExecutionTask
from .jupyter_kernel_proxy import ProxyKernelClient
from .config import config
from .context import BeakerContext
# from archytas.summarizers import llm_message_summarizer

if TYPE_CHECKING:
    from langchain_core.messages import ToolMessage, AIMessage, BaseMessage, ToolCall
    from archytas.models.base import BaseArchytasModel
    from archytas.agent import Agent
    from archytas.chat_history import ChatHistory

Checkpoint = dict[str, str]


class JsonStateEncoder(json.JSONEncoder):
    pass


import logging
logger = logging.getLogger(__name__)


async def run_code_summarizer(message: "ToolMessage", chat_history: "ChatHistory", agent: "Agent", model: "BaseArchytasModel"):
    from langchain_core.messages import AIMessage
    size_threshold = 800
    excision_text_template = "...skipping {} characters..."
    split_percentage = 0.7
    text = message.text()
    message_len = len(text)
    calling_record, tool_call = chat_history.get_tool_caller(message.tool_call_id)
    calling_message: AIMessage = calling_record.message
    code = tool_call.get("args", {}).get("code", "")
    code_len = len(code)

    if message_len > size_threshold:
        message_excision_label_len = len(excision_text_template) - 2 + len(str(message_len - size_threshold))
        message_excision_text = excision_text_template.format(message_len - size_threshold + message_excision_label_len)
        message_excision_start = int(size_threshold * split_percentage)
        message_excision_end = message_len - (size_threshold - message_excision_start - len(message_excision_text))

        message.additional_kwargs["orig_content"] = message.content
        message.content = "".join([
            text[:message_excision_start],
            message_excision_text,
            text[message_excision_end:],
        ])
    if code_len > size_threshold:
        code_excision_label_len = len(excision_text_template) - 2 + len(str(code_len - size_threshold))
        code_excision_text = excision_text_template.format(code_len - size_threshold + code_excision_label_len)
        code_excision_start = int(size_threshold * split_percentage)
        code_excision_end = code_len - (size_threshold - code_excision_start - len(code_excision_text))

        message.additional_kwargs["orig_code"] = code
        tool_call["_orig_code"] = code
        shortened_code = "".join([
            code[:code_excision_start],
            code_excision_text,
            code[code_excision_end:],
        ])

        tool_call["args"]["code"] = shortened_code

        if isinstance(calling_message.content, list):
            for content in calling_message.content:
                if (
                    isinstance(content, dict)
                    and content.get("type", None) == "tool_use"
                    and content.get("id", None) == message.tool_call_id
                ):
                    code_input = content.get("input", None)
                    if isinstance(code_input, dict) and "code" in code_input:
                        content["input"]["code"] = shortened_code
    message.artifact["summarized"] = True


@tool(autosummarize=True, summarizer=run_code_summarizer)
async def run_code(code: str, agent: AgentRef, loop: LoopControllerRef, react_context: ReactContextRef) -> str:
    """
    Executes code in the user's notebook on behalf of the user, but collects the outputs of the run for use by the Agent
    in the ReAct loop, if needed.

    The code runs in a new codecell and the user can watch the execution and will see all of the normal output in the
    Jupyter interface.

    This tool can be used to probe the user's environment or collect information to answer questions, or can be used to
    run code completely on behalf of the user. If a user asks the agent to do something that reasonably should be done
    via code, you should probably default to using this tool.

    This tool can be run more than once in a react loop. All actions and variables created in earlier uses of the tool
    in a particular loop should be assumed to exist for future uses of the tool in the same loop.

    Args:
        code (str): Code to run directly in Jupyter. This should be a string exactly as it would appear in a notebook
                    codecell. No extra escaping of newlines or similar characters is required.
    Returns:
        str: A summary of the run, along with the collected stdout, stderr, returned result, display_data items, and any
             errors that may have occurred.
    """
    def format_execution_context(context) -> str:
        """
        Formats the execution context into a format that is easy for the agent to parse and understand.
        """
        stdout_list = context.get("stdout_list")
        stderr_list = context.get("stderr_list")
        display_data_list = context.get("display_data_list")
        error = context.get("error")
        return_value = context.get("return")

        output = [
             """Execution report:""",
            f"""Execution id: {context['id']}""",
            f"""Successful?: {context['done'] and not context['error']}""",
            f"""Code executed:
```
{context['command']}
```\n""",
        ]

        if error:
            output.extend([
                 "The following error was thrown when executing the code",
                 "  Error:",
                f"    {error['ename']} {error['evalue']}",
                 "  TraceBack:",
                 "\n".join(error['traceback']),
                 "",
            ])


        if stdout_list:
            output.extend([
                "The execution produced the following stdout output:",
                "\n".join(["```", *stdout_list, "```\n"]),
            ])
        if stderr_list:
            output.extend([
                "The execution produced the following stderr output:",
                "\n".join(["```", *stderr_list, "```\n"]),
            ])
        if display_data_list:
            output.append(
                "The execution produced the following `display_data` objects to display in the notebook:",
            )
            for idx, display_data in enumerate(display_data_list):
                output.append(
                    f"display_data item {idx}:"
                )
                for mimetype, value in display_data.items():
                    if len(value) > 800:
                        value = f"{value[:400]} ... truncated ... {value[-400:]}"
                    output.append(
                        f"{mimetype}:"
                    )
                    output.append(
                        f"```\n{value}\n```\n"
                    )
        if return_value:
            output.append(
                "The execution returned the following:",
            )
            if isinstance(return_value, str):
                output.extend([
                    '```', return_value, '```\n'
                ])
        output.append("Execution Report Complete")
        return "\n".join(output)

    # TODO: In future, this may become a parameter and we allow the agent to decide if code should be automatically run
    # or just be added.
    autoexecute = True
    message = react_context.get("message", None)
    identities = getattr(message, 'identities', [])

    try:
        execution_task: ExecutionTask
        if isinstance(agent.context.subkernel, CheckpointableBeakerSubkernel) and is_checkpointing_enabled():
            checkpoint_index, execution_task = await agent.context.subkernel.checkpoint_and_execute(
                code, not autoexecute, parent_header=message.header, identities=identities
            )
        else:
            execution_task = agent.context.execute(
                code, store_history=True, surpress_messages=(not autoexecute), parent_header=message.header, identities=identities
            )
            checkpoint_index = None
        execute_request_msg = {
            name: getattr(execution_task.execute_request_msg, name)
            for name in execution_task.execute_request_msg.json_field_names
        }
        payload = {
            "action": "code_cell",
            "language": agent.context.subkernel.SLUG,
            "code": code.strip(),
            "autoexecute": autoexecute,
            "execute_request_msg": execute_request_msg,
        }
        if checkpoint_index is not None:
            payload["checkpoint_index"] = checkpoint_index
        agent.context.send_response(
            "iopub",
            "add_child_codecell",
            payload,
            parent_header=message.header,
            parent_identities=getattr(message, "identities", None),
        )

        execution_context = await execution_task

        try:
            preview_payload = await agent.context.preview()
            agent.context.send_response(
                "iopub",
                "preview",
                preview_payload,
                parent_header=message.header,
            )
        except Exception as e:
            logger.error(f"Successfully ran code, but failed to fetch preview: {e}")

        try:
            kernel_state_payload = await agent.context.kernel_state()
            agent.context.send_response(
                "iopub",
                "kernel_state_info",
                kernel_state_payload,
                parent_header=message.header,
            )
        except Exception as e:
            logger.error(f"Successfully ran code, but failed to fetch kernel state: {e}")

    except asyncio.CancelledError as err:
        logger.error("Code execution was interrupted by the user.")
        raise
    except Exception as err:
        logger.error(err, exc_info=err)
        raise

    return format_execution_context(execution_context)

class BeakerSubkernel(abc.ABC):
    DISPLAY_NAME: str
    SLUG: str
    KERNEL_NAME: str

    WEIGHT: int = 50  # Used for auto-sorting in drop-downs, etc. Lower weights are listed earlier.

    TOOLS: list[tuple[Callable, Callable]]  = [(run_code, lambda: True)]

    FETCH_STATE_CODE: str = ""

    @classmethod
    @abc.abstractmethod
    def parse_subkernel_return(cls, execution_result) -> Any:
        ...

    @property
    def tools(self):
        return [tool for tool, condition in self.TOOLS if condition()]

    def __init__(self, jupyter_id: str, subkernel_configuration: dict, context: BeakerContext):
        self.jupyter_id = jupyter_id
        self.connected_kernel = ProxyKernelClient(subkernel_configuration, session_id=context.beaker_kernel.session_id)
        self.context = context

    def cleanup(self):
        if self.jupyter_id is not None:
            try:
                print(f"Shutting down connected subkernel {self.jupyter_id}")
                res = requests.delete(
                    f"{self.context.beaker_kernel.jupyter_server}/api/kernels/{self.jupyter_id}",
                    headers={"Authorization": f"token {config.jupyter_token}"},
                    timeout=0.5,
                )
                if res.status_code == 204:
                    self.jupyter_id = None
            except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as err:
                message = f"Error while shutting down subkernel: {err}\n  Subkernel or server may have already been shut down."
                logger.error(message, exc_info=err)

    def format_kernel_state(self, state: dict) -> dict:
        return state

# Provided for backwards compatibility
BaseSubkernel = BeakerSubkernel


def is_checkpointing_enabled():
    return getattr(config, "enable_checkpoints", True)


class CheckpointableBeakerSubkernel(BeakerSubkernel):
    SERIALIZATION_EXTENSION: str = "storage"

    def __init__(self, jupyter_id: str, subkernel_configuration: dict, context):
        super().__init__(jupyter_id, subkernel_configuration, context)
        self.checkpoints_enabled = is_checkpointing_enabled()
        self.storage_prefix = os.path.join(config.checkpoint_storage_path, self.jupyter_id)
        self.checkpoints : list[Checkpoint] = []
        if self.checkpoints_enabled:
            os.makedirs(self.storage_prefix, exist_ok=True, mode=0o777)
            os.chmod(self.storage_prefix, 0o777)

    def store_serialization(self, filename: str) -> str:
        with open(filename, "rb") as file:
            chunksize = 4 * 1024 * 1024
            hash = hashlib.new("sha256")
            while chunk := file.read(chunksize):
                hash.update(chunk)
            identifier = hash.hexdigest()
            new_filename = f"{self.storage_prefix}/{identifier}.{self.SERIALIZATION_EXTENSION}"

        shutil.move(filename, new_filename)
        return new_filename

    @abc.abstractmethod
    async def generate_checkpoint_from_state(self) -> Checkpoint:
        ...

    @abc.abstractmethod
    async def load_checkpoint(self, checkpoint: Checkpoint):
        ...

    async def add_checkpoint(self) :
        if not self.checkpoints_enabled:
            raise RuntimeError("Checkpoints are not enabled")
        fetched_checkpoint = await self.generate_checkpoint_from_state()
        checkpoint = {
            varname: self.store_serialization(filename) for
            varname, filename in fetched_checkpoint.items()
        }
        self.checkpoints.append(checkpoint)
        return len(self.checkpoints) - 1


    async def rollback(self, checkpoint_index: int):
        if not self.checkpoints_enabled:
            raise RuntimeError("Checkpoints are not enabled")
        if checkpoint_index >= len(self.checkpoints):
            raise IndexError(f"Checkpoint at index {checkpoint_index} does not exist")
        checkpoint = self.checkpoints[checkpoint_index]
        await self.load_checkpoint(checkpoint)
        self.checkpoints = self.checkpoints[:checkpoint_index + 1]

    @action(action_name="rollback", enabled=is_checkpointing_enabled)
    async def rollback_action(self, message):
        checkpoint_index = message.content.get("checkpoint_index", None)
        await self.rollback(checkpoint_index)
    rollback_action._default_payload = "{\n\t\"checkpoint_index\": 0\n}"

    @action(action_name="add_checkpoint", enabled=is_checkpointing_enabled)
    async def add_checkpoint_action(self, message):
        return await self.add_checkpoint()
    add_checkpoint_action._default_payload = "{}"


    def cleanup(self):
        super().cleanup()
        if self.checkpoints_enabled:
            shutil.rmtree(self.storage_prefix, ignore_errors=True)
            self.checkpoints = []

    async def checkpoint_and_execute(self, code: str, surpress_messages: bool = False, parent_header = None, identities = None) -> tuple[int, ExecutionTask]:
        checkpoint_index = await self.add_checkpoint()
        task = self.context.execute(code, store_history=True, surpress_messages=surpress_messages, parent_header=parent_header, identities=identities)
        return checkpoint_index, task

    async def execute_and_rollback(self, code: str, surpress_messages: bool = False, parent_header = None, identities=None):
        checkpoint_index = await self.add_checkpoint()
        result = await self.context.execute(code, surpress_messages=surpress_messages, parent_header=parent_header, identities=identities)
        await self.rollback(checkpoint_index)
        return str(result["return"])

# Provided for backwards compatibility
BaseCheckpointableSubkernel = CheckpointableBeakerSubkernel


def autodiscover_subkernels():
    return autodiscover("subkernels")
