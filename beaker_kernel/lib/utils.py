import asyncio
import os
import json
import logging
import sys
import traceback
import warnings
from contextlib import AbstractAsyncContextManager
from functools import wraps, update_wrapper
from typing import Any, TYPE_CHECKING

from archytas.tool_utils import tool

from .jupyter_kernel_proxy import ( KERNEL_SOCKETS, KERNEL_SOCKETS_NAMES,
                                   JupyterMessage, JupyterMessageTuple)
from .config import config


logger = logging.getLogger(__name__)


def env_enabled(env_var: str):
    return os.environ.get(env_var, "false").lower() == "true"

def get_socket(stream_name: str):
    socket = KERNEL_SOCKETS[KERNEL_SOCKETS_NAMES.index(stream_name)]
    return socket


class ExecutionTask(asyncio.Task):
    execute_request_msg: JupyterMessage | None

    def __init__(
        self,
        *args,
        execute_request_msg: JupyterMessage | None = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.execute_request_msg = execute_request_msg


class handle_message(AbstractAsyncContextManager):
    def __init__(self, server, target_stream, msg_data: JupyterMessageTuple, send_status_updates=True) -> None:
        super().__init__()
        self.beaker_kernel = server.manager
        self.send_status_updates = send_status_updates
        message = JupyterMessage.parse(msg_data)
        self.server = server
        self.target_stream = target_stream
        self.msg_data = msg_data
        self.message = message
        self.message_type = message.header["msg_type"]
        self.reply_type = self.message_type.replace("_request", "") + "_reply"
        self.return_val = None
        if self.send_status_updates:
            self.beaker_kernel.send_response(
                "iopub", "status", {"execution_state": "busy"}, parent_header=message.header
            )

    async def __aenter__(self):
        """Return `self` upon entering the runtime context."""
        return self

    async def __aexit__(self, exc_type, exc_value, traceback_value):
        """Raise any exception triggered within the runtime context."""
        if exc_type:
            formatted_tb = traceback.format_exception(exc_type, exc_value, traceback_value)
            sys.stderr.write("\n".join(formatted_tb))
            sys.stderr.flush()
            reply_content = {
                "status": "error",
                "execution_count": None,
                "ename": exc_type.__name__,
                "evalue": str(exc_value),
                "traceback": formatted_tb,
            }

        else:
            reply_content = {
                "status": "ok",
                "execution_count": None,
                "return": self.return_val,
            }

        self.beaker_kernel.send_response(
            "shell", self.reply_type, reply_content, parent_header=self.message.header, parent_identities=self.message.identities
        )
        if self.send_status_updates:
            self.beaker_kernel.send_response(
                "iopub", "status", {"execution_state": "idle"}, parent_header=self.message.header, parent_identities=self.message.identities
            )
        return None


def message_handler(fn):
    """
    Method decorator that handles the parsing and responding to of messages.
    """
    @wraps(fn)
    async def wrapper(self, server, target_stream, data: JupyterMessageTuple):
        async with handle_message(server, target_stream, data) as ctx:
            result = await fn(self, ctx.message)
            ctx.return_val = result
            # If message data is returned, then the message should be proxied, but if None or any other type is
            # returned, the message should be dropped and not continue on to the proxied server.
            if isinstance(result, JupyterMessageTuple) or result is None:
                return result
    return wrapper


def intercept(msg_type=None, stream="shell", docs: str|None=None, default_payload=None):
    """
    Method decorator to identify message intercepts.
    """
    def register_intercept(fn):
        # Wrap function in message_handler decorator/wrapper for that functionality, which we always want.
        fn = message_handler(fn)
        message_type = msg_type or fn.__name__  # Default msg_type value to be the name of the function if undefined/falsey
        setattr(fn, "_intercept", (message_type, stream))

        fn_docs = getattr(fn, "_docs", getattr(fn, "__doc__", None))
        if docs is not None:
            setattr(fn, "_docs", docs.strip())
        else:
            if isinstance(fn_docs, str):
                setattr(fn, "_docs", fn_docs.strip())
            else:
                setattr(fn, "_docs", fn_docs)

        if default_payload is not None:
            setattr(fn, "_default_payload", default_payload)

        update_wrapper(register_intercept, fn)
        return fn

    return register_intercept


def action(action_name: str|None=None, docs: str|None=None, default_payload=None, enabled: bool=True):
    """
    Method decorator to identify and register context actions.
    """
    if not enabled:
        def disable(_fn):
            def disabled_message(*args, **kwargs):
                raise RuntimeError("This action is disabled.")
            return disabled_message
        return disable
    def register_method(fn):

        action_nm = action_name or fn.__name__  # Default msg_type value to be the name of the function if undefined/falsey
        if action_nm.lower().endswith("request"):
            logger.error("Beaker action names should not include the `_request` suffix.")
        msg_request_type = f"{action_nm}_request"

        setattr(fn, "_action", action_nm)

        if default_payload and hasattr(fn, '_default_payload') and default_payload != getattr(fn, '_default_payload'):
            raise ValueError(f"The default payload for action `{action_nm}` is defined twice. Please ensure only one definition.")

        intercept_fn = intercept(msg_type=msg_request_type, stream="shell", docs=docs, default_payload=default_payload)(fn)
        update_wrapper(register_method, intercept_fn)
        return intercept_fn
    return register_method


def magic(magic_word: str|None):
    """
    Method decorator to identify magic word action methods
    """
    def register_magic(fn):
        magic_prefix = "%" + (magic_word or fn.__name__)
        setattr(fn, "_magic_prefix", magic_prefix)
        update_wrapper(register_magic, fn)
        return fn
    return register_magic


class LogMessageEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        try:
            return super().default(o)
        except:
            return str(o)


class SubkernelStateEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        # if callable(o):
        #     # return f"Function named"
        #     return super().default(o)
        try:
            return super().default(o)
        except:
            return str(o)


def togglable_tool(env_var, *, name: str | None = None):
    warnings.warn("This decorator is deprecated and will be removed in version 1.6.0")
    def noop(fn):
        return fn
    return noop
