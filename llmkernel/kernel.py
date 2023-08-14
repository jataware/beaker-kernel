import ast
import asyncio
import copy
import datetime
import functools
import io
import json
import logging
import os
import pickle
import requests
import sys
import time
import traceback
import uuid

from IPython.core.interactiveshell import InteractiveShell
from tornado import ioloop
from jupyter_kernel_proxy import (
    KernelProxyManager,
    JupyterMessage,
    InterceptionFilter,
    KERNEL_SOCKETS,
    KERNEL_SOCKETS_NAMES,
)
from jupyter_core.paths import jupyter_runtime_dir, jupyter_data_dir

from toolsets import DatasetToolset, MiraModelToolset
from archytas.react import ReActAgent


logger = logging.getLogger(__name__)

server_url = os.environ.get("JUPYTER_SERVER", None)
server_token = os.environ.get("JUPYTER_TOKEN", None)


MESSAGE_STREAMS = {
    "execute_input": "iopub",
    "execute_request": "shell",
    "execute_result": "iopub",
    "execute_reply": "shell",
    "stream": "iopub",
}


AVAILABLE_TOOLSETS = {
    "dataset": DatasetToolset,
    "mira_model": MiraModelToolset,
}


def get_socket(stream_name: str):
    socket = KERNEL_SOCKETS[KERNEL_SOCKETS_NAMES.index(stream_name)]
    return socket


class LLMKernel(KernelProxyManager):
    implementation = "askem-chatty-py"
    implementation_version = "0.1"
    banner = "Chatty ASKEM"

    language_info = {
        "mimetype": "text/plain",
        "name": "text",
        "file_extension": ".txt",
    }

    internal_executions: set[str]
    subkernel_execution_tracking: dict[str, str]

    def __init__(self, server):
        self.internal_executions = set()
        self.subkernel_execution_tracking = {}
        self.subkernel_id = None
        self.subkernel_language = None
        self.context = None
        super().__init__(server)
        # We need to have a kernel when we start up, even though we can/will change the kernel/language when we set context
        self.new_kernel(language="python3")
        self.add_intercepts()

    def add_intercepts(self):
        self.server.intercept_message(
            "shell", "context_setup_request", self.context_setup_request
        )
        self.server.intercept_message("shell", "llm_request", self.llm_request)
        self.server.intercept_message(
            "shell", "execute_request", self.track_execute_request
        )
        self.server.intercept_message(
            "iopub", "execute_input", self.update_execute_input_response
        )
        self.server.intercept_message("shell", "execute_reply", self.post_execute)

    def connect_to_last(self):
        # We don't want to automatically connect to the last kernel
        return

    def new_kernel(self, language: str):
        # Shutdown any existing subkernel (if it exists) before spinnup up a new kernel
        self.shutdown_subkernel()

        res = requests.post(
            f"{server_url}/api/kernels",
            json={"name": language, "path": ""},
            headers={"Authorization": f"token {server_token}"},
        )
        kernel_info = res.json()
        self.update_running_kernels()
        self.subkernel_id = kernel_info["id"]
        self.subkernel_language = language
        self.connect_to(self.subkernel_id)

    def shutdown_subkernel(self):
        if self.subkernel_id is not None:
            try:
                print(f"Shutting down connected subkernel {self.subkernel_id}")
                res = requests.delete(
                    f"{server_url}/api/kernels/{self.subkernel_id}",
                    headers={"Authorization": f"token {server_token}"},
                )
                if res.status_code == 204:
                    self.subkernel_id = None
            except requests.exceptions.HTTPError as err:
                print(err)

    def handle_thoughts(
        self, thought: str, tool_name: str, tool_input: str, parent_header: dict
    ):
        content = {
            "thought": thought,
            "tool_name": tool_name,
            "tool_input": tool_input,
        }
        self.send_response(
            stream="iopub",
            msg_or_type="llm_thought",
            content=content,
            parent_header=parent_header,
        )

    def add_intercept(self, msg_type, func, stream=None):
        if stream is None:
            stream = MESSAGE_STREAMS.get(msg_type, None)
        if stream is None:
            logger.error(
                "No stream found for msg_type=%s.\nNot adding intercept.", msg_type
            )
            return
        self.server.intercept_message(stream, msg_type, func)

    def remove_intercept(self, msg_type, func):
        stream = MESSAGE_STREAMS.get(msg_type, None)
        if stream is None:
            logger.warning(
                "No stream found for msg_type=%s.\nNot able to remove intercept.",
                msg_type,
            )
            return
        socket = get_socket(stream)
        self.server.filters.remove(InterceptionFilter(socket, msg_type, func))

    async def execute(self, command, response_handler=None, parent_header={}):
        stream = self.connected_kernel.streams.shell
        execution_message = self.connected_kernel.make_multipart_message(
            msg_type="execute_request",
            content={
                "silent": False,
                "store_history": False,
                "user_expressions": {},
                "allow_stdin": True,
                "stop_on_error": False,
                "code": command,
            },
            parent_header=parent_header,
            metadata={
                "trusted": True,
            },
        )
        stream.send_multipart(execution_message)
        original_message = JupyterMessage.parse(execution_message)
        message_id = original_message.header.get("msg_id")
        self.internal_executions.add(message_id)

        message_context = {
            "id": message_id,
            "stdout_list": [],
            "stderr_list": [],
            "return": None,
            "error": None,
            "done": False,
            "result": None,
            "parent": original_message,
        }
        message_metadata = {}

        filter_list = self.server.filters

        shell_socket = get_socket("shell")
        iopub_socket = get_socket("iopub")

        # Generate a handler to catch and silence the output
        async def silence_message(server, target_stream, data):
            message = JupyterMessage.parse(data)

            if message.parent_header.get("msg_id", None) != message_id:
                return data
            return None

        async def collect_result(server, target_stream, data):
            message = JupyterMessage.parse(data)
            # Ensure we are only working on handlers for this message response
            if message.parent_header.get("msg_id", None) != message_id:
                return data

            data = message.content["data"].get("text/plain", None)
            message_context["return"] = data

        async def collect_stream(server, target_stream, data):
            message = JupyterMessage.parse(data)
            # Ensure we are only working on handlers for this message response
            if message.parent_header.get("msg_id", None) != message_id:
                return data
            stream = message.content["name"]
            message_context[f"{stream}_list"].append(message.content["text"])

        async def handle_error(server, target_stream, data):
            message = JupyterMessage.parse(data)
            content = message.content
            message_context["error"] = content
            logger.error(
                "Error: %s %s\nTraceback:\n%s",
                content["ename"],
                content["evalue"],
                "\n".join(content["traceback"]),
            )

        async def cleanup(server, target_stream, data):
            message = JupyterMessage.parse(data)
            # Ensure we are only working on handlers for this message response
            if message.parent_header.get("msg_id", None) != message_id:
                return data
            if response_handler:
                filter_list.remove(
                    InterceptionFilter(iopub_socket, "stream", response_handler)
                )
            filter_list.remove(
                InterceptionFilter(iopub_socket, "stream", collect_stream)
            )
            filter_list.remove(
                InterceptionFilter(iopub_socket, "execute_result", collect_result)
            )
            filter_list.remove(
                InterceptionFilter(iopub_socket, "execute_input", silence_message)
            )
            filter_list.remove(
                InterceptionFilter(iopub_socket, "execute_request", silence_message)
            )
            filter_list.remove(InterceptionFilter(iopub_socket, "error", handle_error))
            filter_list.remove(
                InterceptionFilter(shell_socket, "execute_reply", cleanup)
            )
            message_context["result"] = message
            message_context["done"] = True

        filter_list.append(
            InterceptionFilter(iopub_socket, "execute_input", silence_message)
        )
        filter_list.append(
            InterceptionFilter(iopub_socket, "execute_request", silence_message)
        )
        filter_list.append(
            InterceptionFilter(iopub_socket, "execute_result", collect_result)
        )
        filter_list.append(InterceptionFilter(shell_socket, "execute_reply", cleanup))
        filter_list.append(InterceptionFilter(iopub_socket, "stream", collect_stream))
        filter_list.append(InterceptionFilter(iopub_socket, "error", handle_error))

        if response_handler:
            filter_list.append(
                InterceptionFilter(iopub_socket, "stream", response_handler)
            )

        await asyncio.sleep(0.1)
        while not message_context["done"]:
            await asyncio.sleep(0.2)
        self.internal_executions.remove(message_id)
        return message_context

    async def evaluate(self, expression, parent_header={}):
        result = await self.execute(expression, parent_header=parent_header)
        return_str = result.get("return")
        if return_str:
            # TODO: This auto-conversion to json is probably not actually what we want. Better if it's
            # explicit rather than implicit.
            return_obj = ast.literal_eval(result["return"])
            if isinstance(return_obj, str):
                try:
                    return_obj = json.loads(return_obj)
                except json.JSONDecodeError:
                    pass
            result["return"] = return_obj
        return result

    async def set_context(self, context, context_info, language="python3", parent_header={}):
        # Spin up a new kernel if we are changing languages.
        if self.subkernel_language != language:
            self.new_kernel(language=language)

        toolset = AVAILABLE_TOOLSETS.get(context, None)
        if not toolset:
            return False
        self.toolset = toolset(kernel=self, language=self.subkernel_language)
        self.agent = ReActAgent(
            tools=[self.toolset],
            allow_ask_user=False,
            verbose=True,
            spinner=None,
            rich_print=False,
            thought_handler=functools.partial(
                self.handle_thoughts, parent_header=parent_header
            ),
        )
        self.toolset.agent = self.agent

        for message, (handler, stream) in self.toolset.intercepts.items():
            self.add_intercept(message, handler, stream=stream)

        match context:
            case "dataset":
                if getattr(self, "context", None) is not None:
                    self.agent.clear_all_context()
                dataset_id = context_info["id"]
                print(f"Processing dataset w/id {dataset_id}")
                await self.toolset.set_dataset(dataset_id, parent_header=parent_header)
                self.context = self.agent.add_context(await self.toolset.context())
            case "mira_model":
                if getattr(self, "context", None) is not None:
                    self.agent.clear_all_context()
                item_id = context_info["id"]
                item_type = context_info.get("type", "model")
                print(f"Processing {item_type} AMR {item_id} as a MIRA model")
                await self.toolset.set_model(
                    item_id, item_type, parent_header=parent_header
                )
                self.context = self.agent.add_context(await self.toolset.context())

    async def post_execute(self, queue, message_id, data):
        message = JupyterMessage.parse(data)

        # Don't run for internal executions
        if message.parent_header.get("msg_id") in self.internal_executions:
            return data

        # Fetch event loop and ensure it's valid
        loop = asyncio.get_event_loop()
        callback = getattr(self.toolset, "post_execute", None)
        if loop and callback and (callable(callback) or asyncio.iscoroutine(callback)):
            # If we have a callback function, then add it as a task to the execution loop so it runs
            loop.create_task(callback(message))
        return data

    def send_response(
        self, stream, msg_or_type, content=None, channel=None, parent_header={}
    ):
        # Parse response as needed
        stream = getattr(self.server.streams, stream)
        message = self.server.make_multipart_message(
            msg_type=msg_or_type, content=content, parent_header=parent_header
        )
        stream.send_multipart(message)
        # Flush to ensure messages are sent immediately
        # TODO: Make flushing behind a flag?
        stream.flush()

    async def track_execute_request(self, server, target_stream, data):
        message = JupyterMessage.parse(data)
        if "notebook_item" in message.metadata:
            message_id = message.header["msg_id"]
            notebook_item = message.metadata["notebook_item"]
            self.subkernel_execution_tracking[message_id] = notebook_item
        return data

    async def update_execute_input_response(self, server, target_stream, data):
        message = JupyterMessage.parse(data)
        parent_id = message.parent_header.get("msg_id")
        notebook_item = self.subkernel_execution_tracking.get(parent_id)
        if notebook_item:
            message.metadata["notebook_item"] = notebook_item
            data = message.parts
        return data

    async def llm_request(self, queue, message_id, data):
        # Send "code" to LLM Agent. The "code" is actually the LLM query
        message = JupyterMessage.parse(data)
        content = message.content
        request = content.get("request", None)
        if not request:
            return
        try:
            result = await self.agent.react_async(request)
        except Exception as err:
            error_text = f"""LLM Error:
{err}

{traceback.format_exc()}
"""
            stream_content = {"name": "stderr", "text": error_text}
            self.send_response(
                "iopub", "stream", stream_content, parent_header=message.header
            )
            return {
                "status": "error",
                "execution_count": 0,
                "payload": [],
                "user_expressions": {},
            }

        try:
            data = json.loads(result)
            if isinstance(data, dict) and data.get("action") == "code_cell":
                stream_content = {
                    "language": data.get("language"),
                    "code": data.get("content"),
                }
                self.send_response(
                    "iopub", "code_cell", stream_content, parent_header=message.header
                )
        except (
            json.JSONDecodeError
        ):  # If response is not a json, it's just text so treat it like text
            stream_content = {"name": "response_text", "text": f"{result}"}
            self.send_response(
                "iopub", "llm_response", stream_content, parent_header=message.header
            )

    async def context_setup_request(self, server, target_stream, data):
        # TODO: Set up environment for kernel
        # Basically, run any code/import any files needed for context

        print("set context")
        message = JupyterMessage.parse(data)
        content = message.content
        context = content.get("context")
        context_info = content.get("context_info", {})
        language = content.get("language", "python3")

        parent_header = copy.deepcopy(message.header)
        if content:
            await self.set_context(context, context_info, language=language, parent_header=parent_header)

        # TODO: Add parent header info to response
        # self.send_response(
        #     stream="iopub",
        #     msg_or_type="status",
        #     content={
        #         "execution_state": "idle",
        #     },
        #     channel="iopub",
        #     parent_header=parent_header,
        # )


def cleanup(kernel):
    try:
        kernel.shutdown_subkernel()
    except requests.exceptions.ConnectionError:
        print("Unable to connect to server. Possible server shutdown.")
    except Exception as err:
        print(f"Couldn't shutdown subkernel: {err}")


def start(connection_file):
    loop = ioloop.IOLoop.current()

    with open(connection_file) as f:
        notebook_config = json.load(f)

    kernel = LLMKernel(notebook_config)

    try:
        loop.start()
    except KeyboardInterrupt:
        # Perform shutdown cleanup here
        cleanup(kernel)
        sys.exit(0)


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "start":
        start(sys.argv[2])
    else:
        print("Usage: {:s} start <connection_file>".format(sys.argv[0]))


if __name__ == "__main__":
    asyncio.run(main())
