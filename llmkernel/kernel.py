import time
import json
import traceback

from ipykernel.kernelbase import Kernel
from ipykernel.ipkernel import IPythonKernel
from toolsets.dataset_toolset import DatasetToolset
from archytas.react import ReActAgent

class PythonLLMKernel(IPythonKernel):
    implementation = "askem-chatty-py"
    implementation_version = "0.1"
    banner = "Chatty ASKEM"

    language_info = {
        "mimetype": "text/plain",
        "name": "text",
        "file_extension": ".txt",
    }


    def setup_instance(self, *args, **kwargs):
        # Init LLM agent
        self.toolset = DatasetToolset()
        self.agent = ReActAgent(tools=[self.toolset], allow_ask_user=False, verbose=True, spinner=None)
        self.toolset.agent = self.agent
        if getattr(self, 'context', None) is not None:
            self.agent.clear_all_context()
        self.context = None
        self.msg_types.append("context_setup_request")
        self.msg_types.append("llm_request")
        return super().setup_instance(*args, **kwargs)


    def set_context(self, context, context_info):
        match context:
            case "dataset":
                dataset_id = context_info["id"]
                print(f"Processing dataset w/id {dataset_id}")
                self.toolset.set_dataset(dataset_id)
                self.context = self.agent.add_context(self.toolset.context())
                # self.shell.ex("""import pandas as pd; import numpy as np;""")
                self.shell.ex("""import pandas as pd; import numpy as np; import scipy;""")
                self.shell.push({
                    "df": self.toolset.df
                })
                self.send_df_preview_message()


    def send_df_preview_message(self):
        import pandas as pd
        df = self.shell.ev("df")
        if isinstance(df, pd.DataFrame):
            split_df = json.loads(df.head(10).to_json(orient="split"))
            payload = {
                "name": "Temp dataset (not saved)",
                "headers": split_df["columns"],
                "csv": [split_df["columns"]] + split_df["data"],
            }
            self.send_response(self.iopub_socket, "dataset", payload)


    # def send_response(self, stream, msg_or_type, content=None, ident=None, buffers=None, track=False, header=None, metadata=None, channel="shell"):
    #     # Parse response as needed
    #     return super().send_response(stream, msg_or_type, content, ident, buffers, track, header, metadata, channel)


    async def llm_request(self, queue, message_id, message, **kwargs):
        # Send "code" to LLM Agent. The "code" is actually the LLM query
        request = message.get("content", {}).get("request", None)
        if not request:
            return
        try:
            result = self.agent.react(request)
        except Exception as err:
            error_text = f"""LLM Error:
{err}

{traceback.format_exc()}
"""
            stream_content = {"name": "stderr", "text": error_text}
            self.send_response(self.iopub_socket, "stream", stream_content)
            return {
                "status": "error",
                "execution_count": self.execution_count,
                "payload": [],
                'user_expressions': {},
            }

        try:
            data = json.loads(result)
            if data.get("action") == "code_cell":
                stream_content = {"language": data.get("language"), "code": data.get("content")}
                self.send_response(self.iopub_socket, "code_cell", stream_content)
        except json.JSONDecodeError:  # If response is not a json, it's just text so treat it like text
            stream_content = {"name": "response_text", "text": f"{result}"}
            self.send_response(self.iopub_socket, "chatty_response", stream_content)

        return {
            "status": "ok",
            "execution_count": self.execution_count,
            "payload": [],
            'user_expressions': {},
        }


    async def context_setup_request(self, queue, message_id, message, **kwargs):
        # TODO: Set up environment for kernel
        # Basically, run any code/import any files needed for context

        content = message.get('content', {})
        context = content.get('context')
        context_info = content.get('context_info', {})

        if content:
            self.set_context(context, context_info)

        self.send_response(
            stream=self.iopub_socket,
            msg_or_type="status",
            content={
                "execution_state": "idle",
            },
            channel="iopub"

        )

    async def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False, *, cell_id=None):
        result = await super().do_execute(code, silent, store_history, user_expressions, allow_stdin, cell_id=cell_id)
        self.send_df_preview_message()
        return result

if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=PythonLLMKernel)
