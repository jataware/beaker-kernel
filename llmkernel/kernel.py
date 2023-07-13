import copy
import datetime
import io
import json
import logging
import os
import requests
import tempfile
import time
import traceback
import pandas as pd

from ipykernel.kernelbase import Kernel
from ipykernel.ipkernel import IPythonKernel
from toolsets.dataset_toolset import DatasetToolset
from archytas.react import ReActAgent

logger = logging.getLogger(__name__)

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
        self.agent = ReActAgent(tools=[self.toolset], allow_ask_user=False, verbose=True, spinner=None, rich_print=False)
        self.toolset.agent = self.agent
        if getattr(self, 'context', None) is not None:
            self.agent.clear_all_context()
        self.context = None
        self.msg_types.append("context_setup_request")
        self.msg_types.append("llm_request")
        self.msg_types.append("download_dataset_request")
        self.msg_types.append("save_dataset_request")
        return super().setup_instance(*args, **kwargs)


    def set_context(self, context, context_info):
        match context:
            case "dataset":
                dataset_id = context_info["id"]
                print(f"Processing dataset w/id {dataset_id}")
                self.toolset.set_dataset(dataset_id)
                self.toolset.kernel = self.shell
                self.context = self.agent.add_context(self.toolset.context())
                self.shell.ex("""import pandas as pd; import numpy as np; import scipy;""")
                self.shell.push({
                    "df": self.toolset.df
                })
                self.send_df_preview_message()


    def send_df_preview_message(self):
        df = self.shell.ev("df")
        if isinstance(df, pd.DataFrame):
            split_df = json.loads(df.head(30).to_json(orient="split"))
            payload = {
                "name": "Temp dataset (not saved)",
                "headers": split_df["columns"],
                "csv": [split_df["columns"]] + split_df["data"],
            }
            self.send_response(
                stream=self.iopub_socket,
                msg_or_type="dataset",
                content=payload,
            )


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
            if isinstance(data, dict) and data.get("action") == "code_cell":
                stream_content = {"language": data.get("language"), "code": data.get("content")}
                self.send_response(self.iopub_socket, "code_cell", stream_content)
        except json.JSONDecodeError:  # If response is not a json, it's just text so treat it like text
            stream_content = {"name": "response_text", "text": f"{result}"}
            self.send_response(self.iopub_socket, "llm_response", stream_content)

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
            channel="iopub",
        )
    
    async def execute_request(self, stream, ident, parent):
        # Rewrite parent so that this is properly tied to requests in terarium
        notebook_item = parent.get('metadata', {}).get('notebook_item', None)
        if notebook_item:
            parent["msg_id"] = notebook_item
            parent["header"]["msg_id"] = notebook_item
        return await super().execute_request(stream, ident, parent)

    async def download_dataset_request(self, queue, message_id, message, **kwargs):
        content = message.get('content', {})
        # TODO: Collect any options that might be needed, if they ever are

        df = self.shell.ev("df")
        if isinstance(df, pd.DataFrame):
            output_buff = io.BytesIO()
            df.to_csv(output_buff, index=False, header=True)
            output_buff.seek(0)
            self.send_response(
                stream=self.iopub_socket,
                msg_or_type="download_response",
                content={"data": output_buff},
            )
        else:
            self.send_response(
                stream=self.iopub_socket,
                msg_or_type="stream",
                content={"name": "stderr", "text": "The dataframe is not able to be downloaded."},
            )


    async def save_dataset_request(self, queue, message_id, message, **kwargs):
        self.send_response(
            stream=self.iopub_socket,
            msg_or_type="status",
            content={
                "execution_state": "busy",
            },
            channel="iopub",
        )
        df = self.shell.ev('df')
        content = message.get('content', {})

        parent_dataset_id = content.get("parent_dataset_id")
        new_name = content.get("name")
        filename = content.get("filename", None)


        if filename is None:
            filename = "dataset.csv"
        parent_url = f"{os.environ['DATA_SERVICE_URL']}/datasets/{parent_dataset_id}"
        parent_dataset = requests.get(parent_url).json()
        if not parent_dataset:
            raise Exception(f"Unable to locate parent dataset '{parent_dataset_id}'")
        
        new_dataset = copy.deepcopy(parent_dataset)
        del new_dataset["id"]
        new_dataset["name"] = new_name
        new_dataset["description"] += f"\nTransformed from dataset '{parent_dataset['name']}' ({parent_dataset['id']}) at {datetime.datetime.utcnow().strftime('%c %Z')}"
        new_dataset["file_names"] = [filename]

        create_req = requests.post(f"{os.environ['DATA_SERVICE_URL']}/datasets", json=new_dataset)
        new_dataset_id = create_req.json()["id"]

        new_dataset["id"] = new_dataset_id
        new_dataset_url = f"{os.environ['DATA_SERVICE_URL']}/datasets/{new_dataset_id}"
        data_url_req = requests.get(f'{new_dataset_url}/upload-url?filename={filename}')
        data_url = data_url_req.json().get('url', None)

        # Saving as a temporary file instead of a buffer to save memory
        with tempfile.TemporaryFile() as temp_csv_file:
            df.to_csv(temp_csv_file, index=False, header=True)
            temp_csv_file.seek(0)
            upload_response = requests.put(data_url, data=temp_csv_file)
        if upload_response.status_code != 200:
            raise Exception(f"Error uploading dataframe: {upload_response.content}")

        self.send_response(
            stream=self.iopub_socket,
            msg_or_type="save_dataset_response",
            content={
                "dataset_id": new_dataset_id,
                "filename": filename,
                "parent_dataset_id": parent_dataset_id
            },
            channel="iopub",
        )
        self.send_response(
            stream=self.iopub_socket,
            msg_or_type="status",
            content={
                "execution_state": "idle",
            },
            channel="iopub",
        )
         
    async def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False, *, cell_id=None):
        result = await super().do_execute(code, silent, store_history, user_expressions, allow_stdin, cell_id=cell_id)
        self.send_df_preview_message()
        return result

if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=PythonLLMKernel)
