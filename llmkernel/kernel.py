import ast
import asyncio
import copy
import datetime
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

from tornado import ioloop
from jupyter_kernel_proxy import KernelProxyManager, JupyterMessage, InterceptionFilter, KERNEL_SOCKETS, KERNEL_SOCKETS_NAMES
from jupyter_core.paths import jupyter_runtime_dir, jupyter_data_dir

from toolsets.dataset_toolset import DatasetToolset
from toolsets.mira_model_toolset import MiraModelToolset
from archytas.react import ReActAgent

logger = logging.getLogger(__name__)

PROXIED_KERNEL_ID = None
server_url = os.environ.get("JUPYTER_SERVER", None)
server_token = os.environ.get("JUPYTER_TOKEN", None)

class PythonLLMKernel(KernelProxyManager):
    implementation = "askem-chatty-py"
    implementation_version = "0.1"
    banner = "Chatty ASKEM"

    language_info = {
        "mimetype": "text/plain",
        "name": "text",
        "file_extension": ".txt",
    }

    def __init__(self, server):
        super().__init__(server)
        self.new_kernel()
        self.setup_instance()

    def setup_instance(self):
        # Init LLM agent
        print("Initializing LLM")
        self.toolset = DatasetToolset()
        self.agent = ReActAgent(tools=[self.toolset], allow_ask_user=False, verbose=True, spinner=None, rich_print=False)
        self.toolset.agent = self.agent
        if getattr(self, 'context', None) is not None:
            self.agent.clear_all_context()
        self.context = None
        self.server.intercept_message("shell", "context_setup_request", self.context_setup_request)
        self.server.intercept_message("shell", "llm_request", self.llm_request)

        # self.msg_types.append("download_dataset_request")
        # self.msg_types.append("save_dataset_request")
        # self.msg_types.append("save_amr_request")
        # self.msg_types.append("load_dataset")
        # self.msg_types.append("load_mira_model")

    def connect_to_last(self):
        # We don't want to automatically connect to the last kernel
        return
    
    def new_kernel(self):
        if PROXIED_KERNEL_ID is not None:
            # We should destroy any existing sub-kernel before creating a new one
            del_res = requests.delete(f"{server_url}/api/kernels/{PROXIED_KERNEL_ID}", headers={"Authorization": f"token {server_token}"})
            print(del_res.status_code)
            print(del_res.json())

        # TODO: Replace hard coded python3
        res = requests.post(f"{server_url}/api/kernels", json={"name": "python3", "path": ""}, headers={"Authorization": f"token {server_token}"})
        kernel_info = res.json()
        self.update_running_kernels()
        sub_kernel = kernel_info['id']
        PROXIED_KERNEL_ID = sub_kernel
        self.connect_to(sub_kernel)

    async def execute(self, command, response_handler=None, collect_output=True):
        # print(f"self.response_data: '{getattr(self, 'response_data', None)}'")
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
            parent_header={},
            metadata={
                "trusted": True,
            }
        )
        stream.send_multipart(execution_message)
        message_id = JupyterMessage.parse(execution_message).header.get("msg_id")


        message_context = {
            "id": message_id,
            "stdout_list": [],
            "stderr_list": [],
            "return": None,
            "error": None,
            "done": False,
            "result": None,
        }

        filter_list = self.server.filters

        shell_socket = KERNEL_SOCKETS[KERNEL_SOCKETS_NAMES.index("shell")]
        iopub_socket = KERNEL_SOCKETS[KERNEL_SOCKETS_NAMES.index("iopub")]


        # Generate a handler to catch and silence the output
        async def silence_message(server, target_stream, data):
            message = JupyterMessage.parse(data)

            filter_list.remove(InterceptionFilter(iopub_socket, "execute_input", silence_message))
            filter_list.remove(InterceptionFilter(iopub_socket, "execute_request", silence_message))

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

        async def cleanup(server, target_stream, data):
            message = JupyterMessage.parse(data)
            # Ensure we are only working on handlers for this message response
            if message.parent_header.get("msg_id", None) != message_id:
                return data
            if response_handler:
                filter_list.remove(InterceptionFilter(iopub_socket, "stream", response_handler))
            if collect_stream:
                filter_list.remove(InterceptionFilter(iopub_socket, "stream", collect_stream))
            filter_list.remove(InterceptionFilter(iopub_socket, "execute_result", collect_result))
            filter_list.remove(InterceptionFilter(shell_socket, "execute_reply", cleanup))
            message_context["result"] = message
            message_context["done"] = True


        filter_list.append(InterceptionFilter(iopub_socket, "execute_input", silence_message))
        filter_list.append(InterceptionFilter(iopub_socket, "execute_request", silence_message))
        filter_list.append(InterceptionFilter(iopub_socket, "execute_result", collect_result))
        filter_list.append(InterceptionFilter(shell_socket, "execute_reply", cleanup))
        if collect_stream:
            filter_list.append(InterceptionFilter(iopub_socket, "stream", collect_stream))

        if response_handler:
            filter_list.append(InterceptionFilter(iopub_socket, "stream", response_handler))
        
        await asyncio.sleep(0.1)
        while not message_context["done"]:
            await asyncio.sleep(1)
        return message_context


    async def evaluate(self, variable):
        result = await self.execute(variable, collect_output=True)
        return result
        

    async def set_context(self, context, context_info):
        print("set context")
        match context:
            case "dataset":
                self.toolset = DatasetToolset()
                self.agent = ReActAgent(tools=[self.toolset], allow_ask_user=False, verbose=True, spinner=None, rich_print=False)
                self.toolset.agent = self.agent
                if getattr(self, 'context', None) is not None:
                    self.agent.clear_all_context()
                dataset_id = context_info["id"]
                print(f"Processing dataset w/id {dataset_id}")
                self.toolset.set_dataset(dataset_id)
                self.context = self.agent.add_context(self.toolset.context())
                await self.execute('''import pandas as pd; import numpy as np; import scipy; import pickle; df = pickle.loads({}); print("done");'''.format(pickle.dumps(self.toolset.df)))
                await self.send_df_preview_message()
            # case "mira_model":
            #     self.toolset = MiraModelToolset()
            #     self.agent = ReActAgent(tools=[self.toolset], allow_ask_user=False, verbose=True, spinner=None, rich_print=False)
            #     self.toolset.agent = self.agent
            #     if getattr(self, 'context', None) is not None:
            #         self.agent.clear_all_context()
            #     item_id = context_info["id"]
            #     item_type = context_info.get("type", "model")
            #     print(f"Processing {item_type} AMR {item_id} as a MIRA model")
            #     self.toolset.kernel = self.shell
            #     self.toolset.set_model(item_id, item_type)
            #     self.context = self.agent.add_context(self.toolset.context())
            #     self.send_mira_preview_message()

    def send_mira_preview_message(self):
        try:
            self.shell.ex(
                '_mira_model = Model(model);\n'
                '_model_size = len(_mira_model.variables) + len(_mira_model.transitions);\n'
                'del _mira_model;\n'
            )
            model_size = self.shell.ev('_model_size')
            if model_size < 800:
                preview = self.shell.ev('GraphicalModel.for_jupyter(model)')
                formatter = InteractiveShell.instance().display_formatter.format
                format_dict, md_dict = formatter(preview) #, include=include, exclude=exclude)
                self.send_response(
                    stream=self.iopub_socket,
                    msg_or_type="model_preview",
                    content={
                        "data": format_dict
                    },
                )
            else:
                print(f"Note: Model is too large ({model_size} nodes) for auto-preview.", file=sys.stderr, flush=True)
        except Exception as e:
            raise

    async def send_df_preview_message(self):
        print("Sending preview")
        import pandas as pd
        result = await self.evaluate("pickle.dumps(df)")
        result_literal = ast.literal_eval(result["return"])
        # df = pd.read_json(result["return"])
        df = pickle.loads(result_literal)
        if isinstance(df, pd.DataFrame):
            split_df = json.loads(df.head(30).to_json(orient="split"))
            payload = {
                "name": "Temp dataset (not saved)",
                "headers": split_df["columns"],
                "csv": [split_df["columns"]] + split_df["data"],
            }
            self.send_response("iopub", "dataset", payload)


    def send_response(self, stream, msg_or_type, content=None, channel=None):
        # Parse response as needed
        stream = getattr(self.server.streams, stream)
        stream.send_multipart(self.server.make_multipart_message(msg_type=msg_or_type, content=content, parent_header={}))


    # async def llm_request(self, queue, message_id, message, **kwargs):
    async def llm_request(self, queue, message_id, message, **kwargs):
        # Send "code" to LLM Agent. The "code" is actually the LLM query
        message = JupyterMessage.parse(message)
        content = message.content
        request = content.get('request', None)
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
            self.send_response("iopub", "stream", stream_content)
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
                self.send_response("iopub", "code_cell", stream_content)
        except json.JSONDecodeError:  # If response is not a json, it's just text so treat it like text
            stream_content = {"name": "response_text", "text": f"{result}"}
            self.send_response("iopub", "llm_response", stream_content)
        # return 

    # async def context_setup_request(self, queue, message_id, message, **kwargs):
    async def context_setup_request(self, server, target_stream, data):
        # TODO: Set up environment for kernel
        # Basically, run any code/import any files needed for context

        print("set context")
        message = JupyterMessage.parse(data)
        content = message.content
        context = content.get('context')
        context_info = content.get('context_info', {})

        if content:
            await self.set_context(context, context_info)

        self.send_response(
            stream="iopub",
            msg_or_type="status",
            content={
                "execution_state": "idle",
            },
            channel="iopub",
        )
    
    async def load_dataset(self, queue, message_id, message, **kwargs):
        content = message.get('content', {})
        dataset_id = content.get('dataset_id', None)
        filename = content.get('filename', None)
        var_name = content.get('var_name', 'df')
        meta_url = f"{os.environ['DATA_SERVICE_URL']}/datasets/{dataset_id}"
        if not filename:
            dataset_meta = requests.get(meta_url).json()
            filename = dataset_meta.get('file_names', [])[0]
        data_url_req = requests.get(f'{meta_url}/download-url?filename={filename}')
        data_url = data_url_req.json().get('url', None)
        self.shell.ex(
            """import pandas as pd; import numpy as np; import scipy;\n"""
            """import sympy; import itertools; from mira.metamodel import *; from mira.modeling import Model;\n"""
            """from mira.modeling.askenet.petrinet import AskeNetPetriNetModel; from mira.modeling.viz import GraphicalModel;\n"""
            f"""{var_name} = pd.read_csv({data_url});"""
            f"""{var_name};"""
        )
        
    def _publish_execute_input(self, code, parent, execution_count):
        """Publish the code request on the iopub stream."""
        # Override the default action to pass along the parent metadata so we can track the container
        self.session.send(
            self.iopub_socket,
            "execute_input",
            {"code": code, "execution_count": execution_count},
            parent=parent,
            ident=self._topic("execute_input"),
            metadata=parent.get("metadata", None),
        )
    
    async def load_mira_model(self, queue, message_id, message, **kwargs):
        content = message.get('content', {})
        model_id = content.get('model_id', None)
        var_name = content.get('var_name', 'model')

        model_url = f"{os.environ['DATA_SERVICE_URL']}/models/{model_id}"

        self.shell.ex(
            """import requests; import pandas as pd; import numpy as np; import scipy;\n"""
            """import json; from mira.sources.askenet.petrinet import template_model_from_askenet_json;\n"""
            """import sympy; import itertools; from mira.metamodel import *; from mira.modeling import Model;\n"""
            """from mira.modeling.askenet.petrinet import AskeNetPetriNetModel; from mira.modeling.viz import GraphicalModel;\n"""
            f"""amr = requests.get({model_url}).json(); {var_name} = template_model_from_askenet_json(amr));"""
            f"""${var_name};"""
        )
    
    async def execute_request(self, stream, ident, parent):
        # Rewrite parent so that this is properly tied to requests in terarium
        # notebook_item = parent.get('metadata', {}).get('notebook_item', None)
        # if notebook_item:
        #     parent["msg_id"] = notebook_item
        #     parent["header"]["msg_id"] = notebook_item
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


    async def save_amr_request(self, queue, message_id, message, **kwargs):
        self.send_response(
            stream=self.iopub_socket,
            msg_or_type="status",
            content={
                "execution_state": "busy",
            },
            channel="iopub",
        )

        content = message.get('content', {})
        # parent_model_id = content.get("parent_model_id")
        new_name = content.get("name")
        var_name = 'model'

        new_model: dict = self.shell.ev(f"AskeNetPetriNetModel(Model({var_name})).to_json()")

        # parent_url = f"{os.environ['DATA_SERVICE_URL']}/models/{parent_model_id}"
        # parent_model = requests.get(parent_url).json()
        # if not parent_model:
        #     raise Exception(f"Unable to locate parent model '{parent_model_id}'")
        
        # new_model = copy.deepcopy(parent_model)
        original_name = new_model.get("name", "None")
        original_model_id = self.toolset.model_id
        new_model["name"] = new_name
        new_model["description"] += f"\nTransformed from model '{original_name}' ({original_model_id}) at {datetime.datetime.utcnow().strftime('%c %Z')}"
        if getattr(self.toolset, 'configuration', None) is not None:
            new_model["description"] += f"\nfrom base configuration '{self.toolset.configuration.get('name')}' ({self.toolset.configuration.get('id')})"
        

        create_req = requests.post(f"{os.environ['DATA_SERVICE_URL']}/models", json=new_model)
        new_model_id = create_req.json()["id"]

        self.send_response(
            stream=self.iopub_socket,
            msg_or_type="save_model_response",
            content={
                "model_id": new_model_id,
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
        self.send_mira_preview_message()
        return result


def cleanup():

    pass

def start(connection_file):
    loop = ioloop.IOLoop.current()

    with open(connection_file) as f:
        notebook_config = json.load(f)

    proxy_manager = PythonLLMKernel(notebook_config)

    try:
        loop.start()
    except KeyboardInterrupt:
        # Perform shutdown cleanup here
        cleanup()
        sys.exit(0)


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "start":
        start(sys.argv[2])
    else:
        print("Usage: {:s} start <connection_file>".format(sys.argv[0]))

if __name__ == "__main__":
    asyncio.run(main())


