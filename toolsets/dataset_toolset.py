import ast
import json
import logging
import os
import re
import requests
from typing import Optional

import pandas as pd

from archytas.tool_utils import tool, toolset, AgentRef, LoopControllerRef

logging.disable(logging.WARNING)  # Disable warnings
logger = logging.Logger(__name__)


@toolset()
class DatasetToolset:
    """ """

    dataset_id: Optional[int]
    df: Optional[pd.DataFrame]

    #TODO: Find a better way to organize and store these items. Maybe store as files and load into codeset dict at init?
    CODE = {
        "python": {
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
        }
    }

    def __init__(self, subkernel=None, language="python", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subkernel = subkernel
        # TODO: add checks and protections around loading codeset
        self.codeset = self.CODE[language]
        self.reset()

    async def set_dataset(self, dataset_id, agent=None):
        self.dataset_id = dataset_id
        meta_url = f"{os.environ['DATA_SERVICE_URL']}/datasets/{self.dataset_id}"
        self.dataset_info = requests.get(meta_url).json()
        if self.dataset_info:
            await self.load_dataframe()
        else:
            raise Exception(f"Dataset '{dataset_id}' not found.")

    async def load_dataframe(self, filename=None):
        if filename is None:
            filename = self.dataset_info.get('file_names', [])[0]
        meta_url = f"{os.environ['DATA_SERVICE_URL']}/datasets/{self.dataset_id}"
        data_url_req = requests.get(f'{meta_url}/download-url?filename={filename}')
        data_url = data_url_req.json().get('url', None)
        if data_url is not None:
            command = "\n".join([self.codeset['setup'], self.codeset['load_df'].format(data_url=data_url)])
            print(f"Running command:\n-------\n{command}\n---------")
            await self.subkernel.execute(command)
            # await self.subkernel.execute(f"""df = pd.read_csv('{data_url}')""")
        else:
            raise Exception('Unable to open dataset.')

    def reset(self):
        self.dataset_id = None
        # self.df = None

    def send_dataset(self):
        pass

    async def context(self):
        return f"""You are an analyst whose goal is to help with scientific data analysis and manipulation in Python.

You are working on a dataset named: {self.dataset_info.get('name')}

The description of the dataset is:
{self.dataset_info.get('description')}

The dataset has the following structure:
--- START ---
{await self.describe_dataset()}
--- END ---

Please answer any user queries to the best of your ability, but do not guess if you are not sure of an answer.
If you are asked to manipulate or visualize the dataset, use the generate_python_code tool.
"""


    async def df_preview(self, line_count=30):
        preview = await self.subkernel.evaluate(self.codeset["df_preview"])
        return preview["return"]


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

        df_info_result = await self.subkernel.evaluate(self.codeset["df_info"])
        df_info = df_info_result["return"]
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
    async def generate_python_code(
        self, query: str, agent: AgentRef, loop: LoopControllerRef
    ) -> str:
        """
        Generated Python code to be run in an interactive Jupyter notebook for the purpose of exploring, modifying and visualizing a Pandas Dataframe.

        Input is a full grammatically correct question about or request for an action to be performed on the loaded dataframe.

        Assume that the dataframe is already loaded and has the variable name `df`.

        Args:
            query (str): A fully grammatically correct queistion about the current dataset.

        Returns:
            str: A LLM prompt that should be passed evaluated.
        """
        # set up the agent
        # str: Valid and correct python code that fulfills the user's request.
        df_info = await self.describe_dataset()
        prompt = f"""
You are a programmer writing code to help with scientific data analysis and manipulation in Python.

Please write code that satisfies the user's request below.

You have access to a variable name `df` that is a Pandas Dataframe with the following structure:
{df_info}

If you are asked to modify or update the dataframe, modify the dataframe in place, keeping the updated variable to still be named `df`.

You also have access to the libraries pandas, numpy, scipy, matplotlib.

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
                "language": "python",
                "content": code.strip(),
            }
        )
        return result
