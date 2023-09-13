import codecs
import copy
import datetime
import json
import logging
import os
import re
import requests
import tempfile
from functools import partial
from typing import Optional, Callable, List, Tuple, Any

from archytas.tool_utils import tool, toolset, AgentRef, LoopControllerRef

from .base import BaseToolset
from lib.jupyter_kernel_proxy import JupyterMessage


logging.disable(logging.WARNING)  # Disable warnings
logger = logging.Logger(__name__)


@toolset()
class DatasetToolset(BaseToolset):
    """ """

    dataset_map: Optional[dict[str, dict[str, Any]]]

    # {
    #   "df": {"id": 12345, "filename": "dataset.csv"},
    #   "df2": {"id": 54321}
    #   "df_map": {"id": 12345, "filename": "mappings.csv"},
    # }

    def __init__(self, context, *args, **kwargs):
        super().__init__(context=context, *args, **kwargs)
        self.dataset_map = {}
        self.intercepts = {
            "download_dataset_request": (self.download_dataset_request, "shell"),
            "save_dataset_request": (self.save_dataset_request, "shell"),
        }
        self.reset()

    async def setup(self, config, parent_header):
        # DEPRECATED: Backwards compatible handling of "old style" single id contexts
        if len(config) == 1 and "id" in config:
            dataset_id = config["id"]
            print(f"Processing dataset w/id {dataset_id}")
            await self.set_dataset(dataset_id, parent_header=parent_header)
        else:
            print(f"Processing datasets w/ids {', '.join(config.values())}")
            await self.set_datasets(config, parent_header=parent_header)

    async def post_execute(self, message):
        await self.update_dataset_map(parent_header=message.parent_header)
        await self.send_df_preview_message(parent_header=message.parent_header)

    async def set_datasets(self, dataset_map, parent_header={}):
        self.dataset_map = dataset_map
        for var_name, dataset_map_item in dataset_map.items():
            if isinstance(dataset_map_item, str):
                dataset_id = dataset_map_item
                self.dataset_map[var_name] = {"id": dataset_id}
            elif isinstance(dataset_map_item, dict):
                dataset_id = dataset_map_item["id"]
            else:
                raise ValueError("Unable to parse dataset mapping")
            meta_url = f"{os.environ['DATA_SERVICE_URL']}/datasets/{dataset_id}"
            dataset_info_req = requests.get(meta_url)
            if dataset_info_req.status_code == 404:
                raise Exception(f"Dataset '{dataset_id}' not found.")
            dataset_info = dataset_info_req.json()
            if dataset_info:
                self.dataset_map[var_name]["info"] = dataset_info
            else:
                raise Exception(f"Dataset '{dataset_id}' not able to be loaded.")
        await self.load_dataframes()
        await self.send_df_preview_message(parent_header=parent_header)

    async def set_dataset(self, dataset_id, parent_header={}):
        await self.set_datasets(
            {
                "df": {"id": dataset_id}
            },
            parent_header=parent_header
        )

    async def load_dataframes(self):
        var_map = {}
        for var_name, df_obj in self.dataset_map.items():
            filename = df_obj["info"].get("file_names", [])[0]
            meta_url = f"{os.environ['DATA_SERVICE_URL']}/datasets/{df_obj['id']}"
            data_url_req = requests.get(f"{meta_url}/download-url?filename={filename}")
            data_url = data_url_req.json().get("url", None)
            var_map[var_name] = data_url
        command = "\n".join(
            [
                self.get_code("setup"),
                self.get_code("load_df", {"var_map": var_map}),
            ]
        )
        await self.context.execute(command)
        await self.update_dataset_map()

    def reset(self):
        self.dataset_map = {}

    async def send_df_preview_message(
        self, server=None, target_stream=None, data=None, parent_header={}
    ):
        preview = {
            var_name: {
                "name": df.get("name"),
                "headers": df.get("columns"),
                "csv": df.get("head"),
            }
            for var_name, df in self.dataset_map.items()
        }
        self.context.kernel.send_response(
            "iopub", "dataset", preview, parent_header=parent_header
        )
        return data

    async def update_dataset_map(self, parent_header={}):
        code = self.get_code("df_info")
        df_info_response = await self.context.kernel.evaluate(
            code,
            parent_header=parent_header,
        )
        df_info = df_info_response.get('return')
        for var_name, info in df_info.items():
            if var_name in self.dataset_map:
                self.dataset_map[var_name].update(info)
            else:
                self.dataset_map[var_name] = {
                    "name": f"User created dataframe '{var_name}'",
                    "description": "",
                    **info,
                }

    async def auto_context(self):
        intro = f"""
You are an analyst whose goal is to help with scientific data analysis and manipulation in {self.metadata.get("name", "a Jupyter notebook")}.

You are working with the following dataset(s):
"""
        outro = f"""
Please answer any user queries to the best of your ability, but do not guess if you are not sure of an answer.
If you are asked to manipulate or visualize the dataset, use the generate_code tool.
"""
        dataset_blocks = []
        for var_name, dataset_obj in self.dataset_map.items():
            dataset_info = dataset_obj.get("info", {})
            dataset_description = await self.describe_dataset(var_name)
            dataset_blocks.append(f"""
Name: {dataset_info.get("name", "User defined dataset")}
Variable: {var_name}
Description: {dataset_info.get("description", "")}

The dataset has the following structure:
--- START ---
{dataset_description}
--- END ---
""")
        result = "\n".join([intro, *dataset_blocks, outro])
        return result

    async def describe_dataset(self, var_name) -> str:
        """
        Inspect the dataset and return information and metadata about it.

        This should be used to answer questions about the dataset, including information about the columns,
        and default parameter values and initial states.


        Returns:
            str: a textual representation of the dataset
        """
        # Update the local dataframe to match what's in the shell.
        # This will be factored out when we switch around to allow using multiple runtimes.

        df_info = self.dataset_map.get(var_name, None)
        if not df_info:
            return None
        output = f"""
Dataframe head:
{df_info["head"][:15]}


Columns:
{df_info["columns"]}


datatypes:
{df_info["datatypes"]}


Statistics:
{df_info["statistics"]}
"""
        return output

    @tool()
    async def generate_code(
        self, query: str, agent: AgentRef, loop: LoopControllerRef
    ) -> None:
        """
        Generated  code to be run in an interactive Jupyter notebook for the purpose of exploring, modifying and visualizing a Dataframe.

        Input is a full grammatically correct question about or request for an action to be performed on the loaded dataframe.

        Args:
            query (str): A fully grammatically correct question about the current dataset.

        """
        # set up the agent
        # str: Valid and correct python code that fulfills the user's request.
        var_sections = []
        for var_name, dataset_obj in self.dataset_map.items():
            df_info = await self.describe_dataset(var_name)
            var_sections.append(f"""
You have access to a variable name `{var_name}` that is a {self.metadata.get("df_lib_name", "Pandas")} Dataframe with the following structure:
{df_info}
--- End description of variable `{var_name}`
""")
        prompt = f"""
You are a programmer writing code to help with scientific data analysis and manipulation in {self.metadata.get("name", "a Jupyter notebook")}.

Please write code that satisfies the user's request below.

{"".join(var_sections)}

If you are asked to modify or update the dataframe, modify the dataframe in place, keeping the updated variable the same unless specifically specified otherwise.

You also have access to the libraries {self.metadata.get("libraries", "that are common for these tasks")}.

Please generate the code as if you were programming inside a Jupyter Notebook and the code is to be executed inside a cell.
You MUST wrap the code with a line containing three backticks (```) before and after the generated code.
No addtional text is needed in the response, just the code block.
"""

        llm_response = await agent.oneshot(prompt=prompt, query=query)
        loop.set_state(loop.STOP_SUCCESS)
        preamble, code, coda = re.split("```\w*", llm_response)
        result = json.dumps(
            {
                "action": "code_cell",
                "language": self.context.lang,
                "content": code.strip(),
            }
        )
        return result

    async def download_dataset_request(self, queue, message_id, data):
        message = JupyterMessage.parse(data)
        content = message.content
        var_name = content.get("var_name", "df")
        # TODO: Collect any options that might be needed, if they ever are

        # TODO: This doesn't work very well. Is very slow to encode, and transfer all of the required messages multiple times proxies through the proxy kernel.
        # We should find a better way to accomplish this if it's needed.
        code = self.get_code("df_download", {"var_name": var_name})
        df_response = await self.context.evaluate(code)
        df_contents = df_response.get("stdout_list")
        self.context.kernel.send_response(
            "iopub",
            "download_response",
            {
                "data": [
                    codecs.encode(line.encode(), "base64").decode()
                    for line in df_contents
                ]
            },
        )  # , parent_header=parent_header)

    async def save_dataset_request(self, queue, message_id, data):
        message = JupyterMessage.parse(data)
        content = message.content

        parent_dataset_id = content.get("parent_dataset_id")
        new_name = content.get("name")
        filename = content.get("filename", None)
        var_name = content.get("var_name", "df")
        dataservice_url = os.environ["DATA_SERVICE_URL"]

        if filename is None:
            filename = "dataset.csv"

        code = self.get_code(
            "df_save_as",
            {
                "parent_dataset_id": parent_dataset_id,
                "new_name": new_name,
                "filename": filename,
                "dataservice_url": dataservice_url,
                "var_name": var_name,
            }
        )

        df_response = await self.context.evaluate(code)

        if df_response:
            new_dataset_id = df_response.get("return", {}).get("dataset_id", None)
            if new_dataset_id:
                self.context.kernel.send_response(
                    "iopub",
                    "save_dataset_response",
                    {
                        "dataset_id": new_dataset_id,
                        "filename": filename,
                        "parent_dataset_id": parent_dataset_id,
                    },
                )
