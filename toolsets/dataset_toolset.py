import codecs
import copy
import datetime
import json
import logging
import os
import re
import requests
import tempfile
from typing import Optional, Callable, List, Tuple

from jupyter_kernel_proxy import JupyterMessage
from archytas.tool_utils import tool, toolset, AgentRef, LoopControllerRef

from .base import BaseToolset

logging.disable(logging.WARNING)  # Disable warnings
logger = logging.Logger(__name__)


@toolset()
class DatasetToolset(BaseToolset):
    """ """

    dataset_id: Optional[int]

    # TODO: Find a better way to organize and store these items. Maybe store as files and load into codeset dict at init?
    CODE = {
        "python3": {
            "name": "Python",
            # TODO: Maybe generate libraries and setup imports from a single source of truth?
            "libraries": """pandas as pd, numpy as np, scipy, pickle""",
            "setup": """import pandas as pd; import numpy as np; import scipy; import pickle;""",
            "load_df": """df = pd.read_csv('{data_url}');""",
            "df_info": """
{
    "head": str(df.head(15)),
    "columns": str(df.columns),
    "dtypes": str(df.dtypes),
    "statistics": str(df.describe()),
}
""".strip(),
            "df_preview": """
import json
split_df = json.loads(df.head(30).to_json(orient="split"))

{
    "name": "Temp dataset (not saved)",
    "headers": split_df["columns"],
    "csv": [split_df["columns"]] + split_df["data"],
}
""".strip(),
            "df_download": """
import pandas as pd; import io
import time
output_buff = io.BytesIO()
df.to_csv(output_buff, index=False, header=True)
output_buff.seek(0)

for line in output_buff.getvalue().splitlines():
    print(line.decode())
""".strip(),
            "df_save_as": """
import copy
import datetime
import requests
import tempfile

parent_url = f"{dataservice_url}/datasets/{parent_dataset_id}"
parent_dataset = requests.get(parent_url).json()
if not parent_dataset:
    raise Exception(f"Unable to locate parent dataset '{parent_dataset_id}'")

new_dataset = copy.deepcopy(parent_dataset)
del new_dataset["id"]
new_dataset["name"] = "{new_name}"
new_dataset["description"] += f"\\nTransformed from dataset '{{parent_dataset['name']}}' ({{parent_dataset['id']}}) at {{datetime.datetime.utcnow().strftime('%c %Z')}}"
new_dataset["file_names"] = ["{filename}"]

create_req = requests.post(f"{dataservice_url}/datasets", json=new_dataset)
new_dataset_id = create_req.json()["id"]

new_dataset["id"] = new_dataset_id
new_dataset_url = f"{dataservice_url}/datasets/{{new_dataset_id}}"
data_url_req = requests.get(f'{{new_dataset_url}}/upload-url?filename={filename}')
data_url = data_url_req.json().get('url', None)

# Saving as a temporary file instead of a buffer to save memory
with tempfile.TemporaryFile() as temp_csv_file:
    df.to_csv(temp_csv_file, index=False, header=True)
    temp_csv_file.seek(0)
    upload_response = requests.put(data_url, data=temp_csv_file)
if upload_response.status_code != 200:
    raise Exception(f"Error uploading dataframe: {{upload_response.content}}")

{{
    "dataset_id": new_dataset_id,
}}
""".strip(),
        }
    }

    def __init__(self, kernel=None, language="python3", *args, **kwargs):
        super().__init__(kernel=kernel, language=language, *args, **kwargs)
        # TODO: add checks and protections around loading codeset
        self.codeset = self.CODE[language]
        self.intercepts = {
            "download_dataset_request": (self.download_dataset_request, "shell"),
            "save_dataset_request": (self.save_dataset_request, "shell"),
        }
        self.reset()

    async def post_execute(self, message):
        await self.send_df_preview_message(parent_header=message.parent_header)

    async def set_dataset(self, dataset_id, agent=None, parent_header={}):
        self.dataset_id = dataset_id
        meta_url = f"{os.environ['DATA_SERVICE_URL']}/datasets/{self.dataset_id}"
        self.dataset_info = requests.get(meta_url).json()
        if self.dataset_info:
            await self.load_dataframe()
        else:
            raise Exception(f"Dataset '{dataset_id}' not found.")
        await self.send_df_preview_message(parent_header=parent_header)

    async def load_dataframe(self, filename=None):
        if filename is None:
            filename = self.dataset_info.get("file_names", [])[0]
        meta_url = f"{os.environ['DATA_SERVICE_URL']}/datasets/{self.dataset_id}"
        data_url_req = requests.get(f"{meta_url}/download-url?filename={filename}")
        data_url = data_url_req.json().get("url", None)
        if data_url is not None:
            command = "\n".join(
                [
                    self.codeset["setup"],
                    self.codeset["load_df"].format(data_url=data_url),
                ]
            )
            print(f"Running command:\n-------\n{command}\n---------")
            await self.kernel.execute(command)
        else:
            raise Exception("Unable to open dataset.")

    def reset(self):
        self.dataset_id = None

    async def send_df_preview_message(
        self, server=None, target_stream=None, data=None, parent_header={}
    ):
        preview_result = await self.kernel.evaluate(
            self.codeset["df_preview"], parent_header=parent_header
        )
        if isinstance(preview_result, dict):
            preview = preview_result.get("return", None)
            if preview:
                parent = preview_result.get("parent", None)
                if parent and not parent_header:
                    parent_header = parent.header
                self.kernel.send_response(
                    "iopub", "dataset", preview, parent_header=parent_header
                )
        return data

    def send_dataset(self):
        pass

    async def context(self):
        return f"""You are an analyst whose goal is to help with scientific data analysis and manipulation in {self.codeset.get("name", "a Jupyter notebook")}.

You are working on a dataset named: {self.dataset_info.get('name')}

The description of the dataset is:
{self.dataset_info.get('description')}

The dataset has the following structure:
--- START ---
{await self.describe_dataset()}
--- END ---

Please answer any user queries to the best of your ability, but do not guess if you are not sure of an answer.
If you are asked to manipulate or visualize the dataset, use the generate_code tool.
"""

    async def describe_dataset(self) -> str:
        """
        Inspect the dataset and return information and metadata about it.

        This should be used to answer questions about the dataset, including information about the columns,
        and default parameter values and initial states.


        Returns:
            str: a textual representation of the dataset
        """
        # Update the local dataframe to match what's in the shell.
        # This will be factored out when we switch around to allow using multiple runtimes.

        df_info_result = await self.kernel.evaluate(self.codeset["df_info"])
        df_info = df_info_result["return"]
        if not df_info:
            return None
        output = f"""
Dataframe head:
{df_info["head"]}


Columns:
{df_info["columns"]}


dtypes:
{df_info["dtypes"]}


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
        df_info = await self.describe_dataset()
        prompt = f"""
You are a programmer writing code to help with scientific data analysis and manipulation in {self.codeset.get("name", "a Jupyter notebook")}.

Please write code that satisfies the user's request below.

You have access to a variable name `df` that is a Pandas Dataframe with the following structure:
{df_info}

If you are asked to modify or update the dataframe, modify the dataframe in place, keeping the updated variable to still be named `df`.

You also have access to the libraries {self.codeset.get("libraries", "that are common for these tasks")}.

Please generate the code as if you were programming inside a Jupyter Notebook and the code is to be executed inside a cell.
You MUST wrap the code with a line containing three backticks (```) before and after the generated code.
No addtional text is needed in the response, just the code block.
"""

        llm_response = agent.oneshot(prompt=prompt, query=query)
        loop.set_state(loop.STOP_SUCCESS)
        preamble, code, coda = re.split("```\w*", llm_response)
        result = json.dumps(
            {
                "action": "code_cell",
                "language": self.language,
                "content": code.strip(),
            }
        )
        return result

    async def download_dataset_request(self, queue, message_id, data):
        logger.error("download_dataset_request")
        message = JupyterMessage.parse(data)
        content = message.content
        # TODO: Collect any options that might be needed, if they ever are

        # TODO: This doesn't work very well. Is very slow to encode, and transfer all of the required messages multiple times proxies through the proxy kernel.
        # We should find a better way to accomplish this if it's needed.
        code = self.codeset["df_download"]
        df_response = await self.kernel.evaluate(code)
        df_contents = df_response.get("stdout_list")
        self.kernel.send_response(
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
        logger.error("save_dataset_request")
        message = JupyterMessage.parse(data)
        content = message.content

        code = self.codeset["df_save_as"]

        parent_dataset_id = content.get("parent_dataset_id")
        new_name = content.get("name")
        filename = content.get("filename", None)
        dataservice_url = os.environ["DATA_SERVICE_URL"]

        if filename is None:
            filename = "dataset.csv"

        code = code.format(
            parent_dataset_id=parent_dataset_id,
            new_name=new_name,
            filename=filename,
            dataservice_url=dataservice_url,
        )

        df_response = await self.kernel.evaluate(code)

        if df_response:
            new_dataset_id = df_response.get("return", {}).get("dataset_id", None)
            if new_dataset_id:
                self.kernel.send_response(
                    "iopub",
                    "save_dataset_response",
                    {
                        "dataset_id": new_dataset_id,
                        "filename": filename,
                        "parent_dataset_id": parent_dataset_id,
                    },
                )
