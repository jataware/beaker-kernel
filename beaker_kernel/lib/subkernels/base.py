import abc
import json
from typing import Any, Callable
import hashlib
import shutil
from tempfile import mkdtemp
from os import makedirs, environ
import requests

from archytas.tool_utils import AgentRef, tool, LoopControllerRef, ReactContextRef

from ..utils import env_enabled, action, ExecutionTask
from ..jupyter_kernel_proxy import ProxyKernelClient
from ..config import config
from ..context import BeakerContext

Checkpoint = dict[str, str]


class JsonStateEncoder(json.JSONEncoder):
    pass


import logging
logger = logging.getLogger(__name__)


class BeakerSubkernel(abc.ABC):
    DISPLAY_NAME: str
    SLUG: str
    KERNEL_NAME: str

    WEIGHT: int = 50  # Used for auto-sorting in drop-downs, etc. Lower weights are listed earlier.

    TOOLS: list[tuple[Callable, bool]]  = []

    FETCH_STATE_CODE: str = ""

    @classmethod
    @abc.abstractmethod
    def parse_subkernel_return(cls, execution_result) -> Any:
        ...

    @property
    def tools(self):
        return [tool for tool, condition in self.TOOLS if condition]

    def __init__(self, jupyter_id: str, subkernel_configuration: dict, context: BeakerContext):
        self.jupyter_id = jupyter_id
        self.connected_kernel = ProxyKernelClient(subkernel_configuration, session_id=context.beaker_kernel.session_id)
        self.context = context

    def cleanup(self):
        if self.jupyter_id is not None:
            try:
                print(f"Shutting down connected subkernel {self.jupyter_id}")
                res = requests.delete(
                    f"{config.JUPYTER_SERVER}/api/kernels/{self.jupyter_id}",
                    headers={"Authorization": f"token {config.JUPYTER_TOKEN}"},
                )
                if res.status_code == 204:
                    self.jupyter_id = None
            except requests.exceptions.HTTPError as err:
                print(err)


@tool()
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
        checkpoint_index, execution_task = await agent.context.subkernel.checkpoint_and_execute(
            code, not autoexecute, parent_header=message.header, identities=identities
        )
        execute_request_msg = {
            name: getattr(execution_task.execute_request_msg, name)
            for name in execution_task.execute_request_msg.json_field_names
        }
        agent.context.send_response(
            "iopub",
            "add_child_codecell",
            {
                "action": "code_cell",
                "language": agent.context.subkernel.SLUG,
                "code": code.strip(),
                "autoexecute": autoexecute,
                "execute_request_msg": execute_request_msg,
                "checkpoint_index": checkpoint_index,
            },
            parent_header=message.header,
            parent_identities=getattr(message, "identities", None),
        )

        execution_context = await execution_task
    except Exception as err:
        logger.error(err, exc_info=err)
        raise

    return format_execution_context(execution_context)

# Provided for backwards compatibility
BaseSubkernel = BeakerSubkernel

class CheckpointableBeakerSubkernel(BeakerSubkernel):
    SERIALIZATION_EXTENSION: str = "storage"

    TOOLS = [
        (run_code, env_enabled("ENABLE_CHECKPOINTS"))
    ]

    def __init__(self, jupyter_id: str, subkernel_configuration: dict, context):
        super().__init__(jupyter_id, subkernel_configuration, context)
        self.checkpoints_enabled = env_enabled("ENABLE_CHECKPOINTS")
        if self.checkpoints_enabled:
            self.checkpoints : list[Checkpoint] = []
            self.storage_prefix = mkdtemp()
            makedirs(self.storage_prefix, exist_ok=True)

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

    @action(action_name="rollback", enabled=env_enabled("ENABLE_CHECKPOINTS"))
    async def rollback_action(self, message):
        checkpoint_index = message.content.get("checkpoint_index", None)
        await self.rollback(checkpoint_index)
    rollback_action._default_payload = "{\n\t\"checkpoint_index\": 0\n}"

    @action(action_name="add_checkpoint", enabled=env_enabled("ENABLE_CHECKPOINTS"))
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
