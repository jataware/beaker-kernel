import os
import json
import logging
import traceback
from functools import wraps, update_wrapper
from typing import Any

from archytas.tool_utils import tool

from .jupyter_kernel_proxy import JupyterMessage


logger = logging.getLogger(__name__)


def message_handler(fn):
    @wraps(fn)
    async def wrapper(self, server, target_stream, data):
        message = JupyterMessage.parse(data)
        message_type = message.header["msg_type"]
        reply_type = message_type.replace("_request", "") + "_reply"
        self.send_response(
            "iopub", "status", {"execution_state": "busy"}, parent_header=message.header
        )

        reply_content = {
            "status": "ok",
        }
        try:
            result = await fn(self, message)
            reply_content["return"] = result
        except Exception as e:
            logger.error(f"Error while handling message {message_type} in function {fn.__name__}", exc_info=True)
            # send an error message back!
            reply_content["status"] = "error"
            reply_content["ename"] = e.__class__.__name__
            reply_content["evalue"] = str(e)
            reply_content["traceback"] = traceback.format_tb(e.__traceback__)

        if reply_content["status"] == "ok":
            reply_content["return"] = result

        self.send_response(
            "shell", reply_type, reply_content, parent_header=message.header, parent_identities=message.identities
        )
        self.send_response(
            "iopub", "status", {"execution_state": "idle"}, parent_header=message.header, parent_identities=message.identities
        )
    return wrapper


def intercept(msg_type=None, stream="shell"):
    """
    Method wrapper to identify interce
    """
    def register_intercept(fn):
        # Wrap function in message_handler decorator/wrapper for that functionality, which we always want.
        fn = message_handler(fn)
        message_type = msg_type or fn.__name__  # Default msg_type value to be the name of the function if undefined/falsey
        setattr(fn, "_intercept", (message_type, stream))
        update_wrapper(register_intercept, fn)
        return fn

    return register_intercept

def togglable_tool(env_var, *, name: str | None = None):
    """
    Register tool if it is enabled in environment
    """
    ENABLE = os.environ.get(env_var, "false").lower() == "true"
    if not ENABLE:
        def disable(_fn):
            return
        return disable
    else:
        return tool(name=name)

class LogMessageEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        try:
            return super().default(o)
        except:
            return str(o)
