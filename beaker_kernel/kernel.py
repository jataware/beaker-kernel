import asyncio
import copy
import inspect
import json
import logging
import os
import sys
import traceback
import uuid
from functools import partial
from typing import TYPE_CHECKING, Optional

import requests
from tornado import ioloop

from .contexts.default.context import DefaultContext
from .lib.context import BaseContext, autodiscover_contexts
from .lib.jupyter_kernel_proxy import (KERNEL_SOCKETS, KERNEL_SOCKETS_NAMES,
                                       InterceptionFilter, JupyterMessage,
                                       KernelProxyManager)
from .lib.subkernels import autodiscover_subkernels
from .lib.utils import message_handler, LogMessageEncoder, magic, handle_message

if TYPE_CHECKING:
    from .lib.agent import BaseAgent
    from .lib.subkernels.base import BaseSubkernel

USER_RESPONSE_WAIT_TIME = 100

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

AVAILABLE_CONTEXTS = autodiscover_contexts()
AVAILABLE_SUBKERNELS = autodiscover_subkernels()

def get_socket(stream_name: str):
    socket = KERNEL_SOCKETS[KERNEL_SOCKETS_NAMES.index(stream_name)]
    return socket


class LLMKernel(KernelProxyManager):
    implementation = "beaker-kernel"
    implementation_version = "0.1"
    banner = "Beaker Kernel"

    language_info = {
        "mimetype": "text/plain",
        "name": "text",
        "file_extension": ".txt",
    }

    kernel_id: Optional[str]
    connection_file: Optional[str]
    context: Optional[BaseContext]
    internal_executions: set[str]
    subkernel: "BaseSubkernel"
    subkernel_execution_tracking: dict[str, str]
    user_responses: dict[str, str]
    debug_enabled: bool
    magic_commands: dict[str, callable]

    def __init__(self, session_config, kernel_id=None, connection_file=None):
        self.kernel_id = kernel_id
        self.connection_file = connection_file
        self.debug_enabled = False
        self.verbose = False
        self.magic_commands = {}
        self.internal_executions = set()
        self.subkernel_execution_tracking = {}
        self.subkernel_id = None
        super().__init__(session_config)
        self.register_magic_commands()
        self.add_base_intercepts()
        self.subkernel = None
        self.context = None
        self.user_responses = dict()
        # Initialize context (Using the event loop to simulate `await`ing the async func in non-async setup)
        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(self.set_context("default", {}))

    def add_base_intercepts(self):
        """
        Adds intercepts used by the Beaker kernel
        """
        self.server.intercept_message(
            "shell", "kernel_info_reply", self.kernel_info_reply
        )
        self.server.intercept_message(
            "shell", "context_info_request", self.context_info_request
        )
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
        self.server.intercept_message("stdin", "input_reply", self.input_reply)

    def register_magic_commands(self):
        for _, method in inspect.getmembers(self, lambda member: inspect.ismethod(member) and hasattr(member, "_magic_prefix")):
            prefix = getattr(method, "_magic_prefix")
            self.magic_commands[prefix] = method

        self.server.intercept_message(
            "shell", "execute_request", self.handle_magic_word
        )

    async def handle_magic_word(self, server, target_stream, data):
        message = JupyterMessage.parse(data)
        cell_content: str = message.content.get("code", "").strip()
        if not cell_content.startswith("%"):
            return data
        parts = cell_content.split(maxsplit=1)
        if len(parts) == 1:
            head, tail = parts[0], None
        else:
            head, tail = parts
        for prefix, fn in self.magic_commands.items():
            if head == prefix:
                self.debug(event_type="magic_word", content={"magic_word": head, "fn": fn.__name__})
                async with handle_message(self, server, target_stream, data) as ctx:
                    result = await fn(tail, magic_word=head, parent_header=message.header)
                    ctx.return_val = result
                return None
        return data

    @magic("set_context")
    async def set_context_magic(self, cell_content: str, magic_word=None, parent_header=None):
        context_name, language, context_config = cell_content.split(maxsplit=2)
        context_info = json.loads(context_config)
        self.stdout(f"Switching from context {self.context.slug} to {context_name}...", parent_header=parent_header)
        await self.set_context(context_name=context_name, language=language, context_info=context_info, parent_header=parent_header)

        # Send message to trigger updating the context info
        self.send_response(
            stream="iopub",
            msg_or_type="context_info_update",
            content={},
            parent_header=parent_header,
        )
        self.stdout(f"Context switch complete.", parent_header=parent_header)
        return None

    @magic("run_action")
    async def run_action_magic(self, cell_content: str, magic_word=None, parent_header=None):
        action_name, payload = cell_content.split(maxsplit=1)
        request_name = f"{action_name}_request"
        content = json.loads(payload)
        self.stdout(f"Running action `{action_name}`...", parent_header=parent_header)

        for intercept in self.server.filters:
            if intercept.stream_type.name == "shell" and intercept.msg_type == request_name:
                action_func = intercept.callback
                data = self.connected_kernel.make_multipart_message(msg_type=request_name, content=content, parent_header=parent_header)
                response = await action_func(self.server, self.connected_kernel.streams.shell, data)
                self.stdout(f"Action `{action_name}` execution complete.", parent_header=parent_header)
                result_data = {}
                try:
                    result_data["text/plain"] = json.dumps(response, cls=LogMessageEncoder, indent=2)
                    result_data["application/json"] = response
                except TypeError:
                    result_data["text/plain"] = str(response)

                self.send_response(
                    stream="iopub",
                    msg_or_type=parent_header.get('msg_type').replace("_request", "") + "_result",
                    content={"execution_count": -1, "data": result_data, "metadata": {}},
                    parent_header=parent_header,
                )
                break
        else:
            self.stderr(f"Unable to find an action with name `{action_name}`.")
        return result_data

    def new_kernel(self, language: str):
        self.debug("new_kernel", f"Setting new kernel of `{language}`")
        kernel_opts = {
            subkernel.KERNEL_NAME: subkernel
            for subkernel in AVAILABLE_SUBKERNELS.values()
        }

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
        self.connect_to(self.subkernel_id)
        self.subkernel = kernel_opts[language](self)

    def shutdown_subkernel(self):
        self.subkernel.cleanup()
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
        self, thought: str, tool_name: str, tool_input: str, parent_header: dict = {}
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

    def remove_intercept(self, msg_type, func, stream=None):
        if stream is None:
            stream = MESSAGE_STREAMS.get(msg_type, None)
        if stream is None:
            logger.error(
                "No stream found for msg_type=%s.\nNot able to remove intercept.",
                msg_type,
            )
            return
        socket = get_socket(stream)
        self.server.filters.remove(InterceptionFilter(socket, msg_type, func))

    async def send_preview(self, parent_header=None):
        generate_preview = getattr(self.context, "generate_preview", None)
        if generate_preview and (callable(generate_preview) or inspect.iscoroutinefunction(generate_preview)):
            preview_payload = await generate_preview()
            if preview_payload:
                self.send_response("iopub", "preview", preview_payload, parent_header=parent_header)

    async def execute(self, command, response_handler=None, parent_header={}):
        self.debug("execution_start", {"command": command}, parent_header=parent_header)
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
            filter_list.remove(
                InterceptionFilter(iopub_socket, "execute_result", collect_result)
            )

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
        # Wait for any straggling messages
        await asyncio.sleep(0.2)
        self.internal_executions.remove(message_id)
        self.debug("execution_end", message_context, parent_header=parent_header)
        return message_context

    async def evaluate(self, expression, parent_header={}):
        result = await self.execute(expression, parent_header=parent_header)
        try:
            parsed_result = self.subkernel.parse_subkernel_return(result)
            result["return"] = parsed_result
        except Exception:
            logger.error("Unable to parse result.")
            logger.debug("Subkernel: %s\nResult:\n%s", self.subkernel, result)
        return result

    async def update_connection_file(self, **kwargs):
        try:
            with open(self.connection_file, "r") as connection_file:
                run_info: dict = json.load(connection_file)
        except IOError:
            run_info = {}
        run_info.update(kwargs)
        with open(self.connection_file, "w") as connection_file:
                json.dump(run_info, connection_file, indent=2)

    async def set_context(self, context_name, context_info, language="python3", parent_header={}):

        context_cls = AVAILABLE_CONTEXTS.get(context_name, None)
        if not context_cls:
            # TODO: Should we return an error if the requested context isn't available?
            return False

        if (not self.subkernel) or self.subkernel.KERNEL_NAME != language:
            logger.info("Subkernel changed: %s != %s", getattr(self.subkernel, "KERNEL_NAME", "unknown"), language)

        # Always create a new subkernel so changing context results in a clean runtime
        self.subkernel.cleanup()
        self.new_kernel(language=language)

        # Cleanup the old context, then create and setup the new context
        if self.context:
            await self.context.cleanup()
        self.context = context_cls(beaker_kernel=self, config=context_info)
        await self.context.setup(config=context_info, parent_header=parent_header)
        await self.send_preview(parent_header=parent_header)
        await self.update_connection_file(context={"name": context_name, "config": context_info})

    async def post_execute(self, queue, message_id, data):
        message = JupyterMessage.parse(data)

        # Only run if there is an active context
        if self.context is None:
            return data

        # Don't run for internal executions
        if message.parent_header.get("msg_id") in self.internal_executions:
            return data

        # Fetch event loop and ensure it's valid
        loop = asyncio.get_event_loop()
        post_execute = getattr(self.context, "post_execute", None)
        async def task():
            """
            Task that runs post_execute and then preview in the background as a async task.
            This allows the normal execution flow to respond quickly in case these tasks are slow
            or resource intensive.
            """
            if post_execute and (callable(post_execute) or inspect.iscoroutinefunction(post_execute)):
                # If we have a callback function, then add it as a task to the execution loop so it runs
                await post_execute(message)
            # Always only generate and send preview after post_execute completes in case state changes or setup is
            # performed in the post_execute function
            await self.send_preview(parent_header=message.parent_header)

        if loop:
            loop.create_task(task())
        return data

    def send_response(
        self, stream, msg_or_type, content=None, channel=None, parent_header={}, parent_identities=None, msg_id=None,
    ):
        # Parse response as needed
        stream = getattr(self.server.streams, stream)
        message = self.server.make_multipart_message(
            msg_type=msg_or_type, content=content, parent_header=parent_header, msg_id=msg_id
        )
        if parent_identities:
            stream.send_multipart(parent_identities + message)
        else:
            stream.send_multipart(message)
        # Flush to ensure messages are sent immediately
        # TODO: Make flushing behind a flag?
        stream.flush()
        return message

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

    async def prompt_user(self, query, parent_message=None):
        msg_id = str(uuid.uuid4())
        self.send_response(
            "stdin",
            "input_request",
            {"prompt": query},
            parent_header=parent_message.header,
            parent_identities=getattr(parent_message, "identities", None),
            msg_id=msg_id,
        )
        for _ in range(USER_RESPONSE_WAIT_TIME):
            if msg_id in self.user_responses:
                result = self.user_responses[msg_id]
                del self.user_responses[msg_id]
                return result
            await asyncio.sleep(1)

        raise Exception("Query timed out. User took too long to respond.")

    def log(self, event_type: str, content, parent_header=None):
        # Re-encode data to fix issues with un-json-encodable elements in the debug output
        content = json.loads(json.dumps(content, cls=LogMessageEncoder))
        message_content = {
            "seq": 0,
            "type": "event",
            "event": event_type,
            "body": content,
        }
        message = self.server.make_multipart_message(
            msg_type="debug_event",
            content=message_content,
            parent_header=parent_header,
        )
        stream = self.server.streams.iopub
        stream.send_multipart(message)
        stream.flush()

    def debug(self, event_type: str, content, parent_header=None):
        if not self.debug_enabled:
            return
        self.log(event_type=event_type, content=content, parent_header=parent_header)

    def send_stream_message(self, stream_type, text, parent_header=None):
        if isinstance(text, bytes):
            text = text.decode()
        message = self.server.make_multipart_message(
            msg_type="stream",
            content={
                'name': stream_type,
                'text': text,
            },
            parent_header=parent_header,
        )
        stream = self.server.streams.iopub
        stream.send_multipart(message)
        stream.flush()

    def stdout(self, text, parent_header=None):
        self.send_stream_message(stream_type="stdout", text=text, parent_header=parent_header)

    def stderr(self, text, parent_header=None):
        self.send_stream_message(stream_type="stderr", text=text, parent_header=parent_header)

    @message_handler
    async def llm_request(self, message):
        # Send "code" to LLM Agent. The "code" is actually the LLM query
        content = message.content
        request = content.get("request", None)
        if not request:
            return
        if not self.context:
            raise Exception("Context has not been set")
        try:
            # Before starting ReAct loop, replace thought handler with partial func with parent_header so we can track thoughts
            self.context.agent.thought_handler = partial(self.handle_thoughts, parent_header=message.header)
            self.debug("llm_query", request, parent_header=message.header)
            result = await self.context.agent.react_async(request, react_context={"message": message})
        except Exception as err:
            error_text = f"""LLM Error:
{err}

{traceback.format_exc()}
"""
            stream_content = {"name": "stderr", "text": error_text}
            self.send_response(
                "iopub", "stream", stream_content, parent_header=message.header
            )
            raise
        try:
            # Normalize result
            if isinstance(result, (str, bytes, bytearray)):
                data = json.loads(result)
            else:
                data = result

            if isinstance(data, dict) and data.get("action") == "code_cell":
                stream_content = {
                    "language": data.get("language"),
                    "code": data.get("content"),
                }
                self.send_response(
                    "iopub", "code_cell", stream_content, parent_header=message.header
                )
            else:
                stream_content = {"name": "response_text", "text": f"{data}"}
                self.send_response(
                    "iopub", "llm_response", stream_content, parent_header=message.header
                )
        except (
            json.JSONDecodeError
        ):  # If response is not a json, it's just text so treat it like text
            stream_content = {"name": "response_text", "text": f"{result}"}
            self.send_response(
                "iopub", "llm_response", stream_content, parent_header=message.header
            )
        finally:
            # When done, put thought handler back to default to not potentially cause confused thoughts.
            self.context.agent.thought_handler = self.handle_thoughts

    async def kernel_info_reply(self, server, target_stream, data):
        await self.send_preview(parent_header={})
        return data

    @message_handler
    async def context_info_request(self, message):
        context_slugs_by_class = dict((cls, slug) for slug, cls in AVAILABLE_CONTEXTS.items())
        context_class = self.context.__class__
        context_slug = context_slugs_by_class.get(context_class, "Not Found")
        full_context_class = f"{context_class.__module__}.{context_class.__name__}"
        context_config = getattr(self.context, "config", None)
        context_info = self.context.get_info()
        self.send_response(
            stream="iopub",
            msg_or_type="context_info_response",
            content={
                "slug": context_slug,
                "class": full_context_class,
                "config": context_config,
                "language": {
                    "slug": self.context.subkernel.SLUG,
                    "subkernel": self.context.subkernel.KERNEL_NAME,
                },
                "info": context_info,
            },
            parent_header=message.header,
        )
        return False

    @message_handler
    async def context_setup_request(self, message):
        content = message.content
        context_name = content.get("context")
        context_info = content.get("context_info", {})
        language = content.get("language", "python3")
        enable_debug = content.get("debug", None)
        verbose = content.get("verbose", None)

        # Only update enable_debug and verbose if they are set and valid types.
        if verbose in (True, False):
            self.verbose = verbose
        if enable_debug in (True, False):
            self.debug_enabled = enable_debug
        if enable_debug in (True, False) or verbose in (True, False):
            self.debug("debug_update", {"debug_enabled": self.debug_enabled, "verbose": self.verbose}, parent_header=message.header)

        parent_header = copy.deepcopy(message.header)
        if content:
            await self.set_context(context_name, context_info, language=language, parent_header=parent_header)

        # Send context_response
        context_response_content = self.context.get_info()
        self.send_response(
            stream="iopub",
            msg_or_type="context_setup_response",
            content=context_response_content,
            parent_header=parent_header,
        )

    @message_handler
    async def input_reply(self, message):
        content = message.content
        parent_id = message.parent_header["msg_id"]
        self.user_responses[parent_id] = content["value"]


def cleanup(kernel: LLMKernel):
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

    _, kernel_file = os.path.split(connection_file)
    kernel_id = os.path.basename(kernel_file)[7:-5]  # Remove 'kernel-' and '.json' from the beginning and end of the filename.
    kernel = LLMKernel(notebook_config, kernel_id=kernel_id, connection_file=connection_file)

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
    main()
