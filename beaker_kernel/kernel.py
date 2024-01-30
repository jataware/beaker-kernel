import asyncio
import copy
import inspect
import json
import logging
import os
import sys
import traceback
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
from .lib.utils import message_handler, LogMessageEncoder

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

    context: Optional[BaseContext]
    internal_executions: set[str]
    subkernel: "BaseSubkernel"
    subkernel_execution_tracking: dict[str, str]
    user_responses: dict[str, str]
    debug_enabled: bool

    def __init__(self, server):
        self.debug_enabled = False
        self.verbose = False
        self.internal_executions = set()
        self.subkernel_execution_tracking = {}
        self.subkernel_id = None
        super().__init__(server)
        self.new_kernel(language="python3")
        self.context = DefaultContext(beaker_kernel=self, subkernel=self.subkernel, config={})
        self.user_responses = dict()
        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(self.context.setup())
        self.add_base_intercepts()

    def add_base_intercepts(self):
        """
        Adds intercepts used by the Beaker kernel
        """
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
        self.subkernel = kernel_opts[language]()

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

    async def set_context(self, context_name, context_info, language="python3", parent_header={}):

        context_cls = AVAILABLE_CONTEXTS.get(context_name, None)
        if not context_cls:
            # TODO: Should we return an error if the requested context isn't available?
            return False

        if (not self.subkernel) or self.subkernel.KERNEL_NAME != language:
            logger.info("Subkernel changed: %s != %s", getattr(self.subkernel, "KERNEL_NAME", "unknown"), language)

        # Always create a new subkernel so changing context results in a clean runtime
        self.new_kernel(language=language)

        # Cleanup the old context, then create and setup the new context
        await self.context.cleanup()
        self.context = context_cls(beaker_kernel=self, subkernel=self.subkernel, config=context_info)
        await self.context.setup(config=context_info, parent_header=parent_header)

    async def post_execute(self, queue, message_id, data):
        message = JupyterMessage.parse(data)

        # Only run if there is an active context
        if self.context is None:
            return

        # Don't run for internal executions
        if message.parent_header.get("msg_id") in self.internal_executions:
            return data

        # Fetch event loop and ensure it's valid
        loop = asyncio.get_event_loop()
        callback = getattr(self.context, "post_execute", None)
        if loop and callback and (callable(callback) or inspect.iscoroutinefunction(callback)):
            # If we have a callback function, then add it as a task to the execution loop so it runs
            loop.create_task(callback(message))
            self.debug("post_execute", {}, parent_header=message.header)
        return data

    def send_response(
        self, stream, msg_or_type, content=None, channel=None, parent_header={}, parent_identities=None
    ):
        # Parse response as needed
        stream = getattr(self.server.streams, stream)
        message = self.server.make_multipart_message(
            msg_type=msg_or_type, content=content, parent_header=parent_header
        )
        if parent_identities:
            stream.send_multipart(parent_identities + message)
        else:
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

    async def prompt_user(self, query):
        if query in self.user_responses:
                del self.user_responses[query]
        self.send_response(
            "iopub", "input_request", {"prompt": query}
        )
        for _ in range(USER_RESPONSE_WAIT_TIME):
            if query in self.user_responses:
                return self.user_responses[query]
            await asyncio.sleep(1)

        raise Exception("Query timed out. User took too long to respond.")

    def debug(self, event_type: str, content, parent_header=None):
        if not self.debug_enabled:
            return
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
            result = await self.context.agent.react_async(request)
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

    @message_handler
    async def context_info_request(self, message):
        context_slugs_by_class = dict((cls, slug) for slug, cls in AVAILABLE_CONTEXTS.items())
        context_class = self.context.__class__
        context_slug = context_slugs_by_class.get(context_class, "Not Found")
        full_context_class = f"{context_class.__module__}.{context_class.__name__}"
        context_config = getattr(self.context, "config", None)
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
                }
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
        self.user_responses[content["prompt"]] = content["reply"]


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
    main()
