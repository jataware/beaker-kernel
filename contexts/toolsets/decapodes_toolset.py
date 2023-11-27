import copy
import datetime
import json
import logging
import os
import re
import requests
import sys
from typing import Optional, Any

from archytas.tool_utils import tool, toolset, AgentRef, LoopControllerRef

from .base import BaseToolset
from lib.utils import message_handler
from lib.jupyter_kernel_proxy import JupyterMessage

logging.disable(logging.WARNING)  # Disable warnings
logger = logging.Logger(__name__)


@toolset()
class DecapodesToolset(BaseToolset):
    """ """

    toolset_name = "decapodes"

    model_id: Optional[str]
    model_json: Optional[str]
    model_dict: Optional[dict[str, Any]]
    var_name: Optional[str] = "model"

    def __init__(self, context, *args, **kwargs):
        super().__init__(context=context, *args, **kwargs)
        self.intercepts = {
            "save_amr_request": (self.save_amr_request, "shell"),
        }
        self.reset()

    async def setup(self, config, parent_header):
        item_id = config["id"]
        item_type = config.get("type", "model")
        print(f"Processing {item_type} AMR {item_id} as a Decapode model")
        await self.set_model(
            item_id, item_type, parent_header=parent_header
        )


    async def post_execute(self, message):
        await self.send_decapodes_preview_message(parent_header=message.parent_header)

    async def set_model(self, item_id, item_type="model", agent=None, parent_header={}):
        if item_type == "model":
            self.model_id = item_id
            self.config_id = "default"
            meta_url = f"{os.environ['DATA_SERVICE_URL']}/models/{self.model_id}"
            self.amr = requests.get(meta_url).json()
        elif item_type == "model_config":
            self.config_id = item_id
            meta_url = f"{os.environ['DATA_SERVICE_URL']}/model_configurations/{self.config_id}"
            self.configuration = requests.get(meta_url).json()
            self.model_id = self.configuration.get("model_id")
            self.amr = self.configuration.get("configuration")
        self.original_amr = copy.deepcopy(self.amr)
        if self.amr:
            await self.load_decapode()
        else:
            raise Exception(f"Model '{item_id}' not found.")
        await self.send_decapodes_preview_message(parent_header=parent_header)

    async def load_decapode(self):
        model_url = f"{os.environ['DATA_SERVICE_URL']}/models/{self.model_id}"
        command = "\n".join(
            [
                self.get_code("setup"),
                self.get_code("load_model", {
                    "var_name": self.var_name,
                    "model_url": model_url,
                }),
            ]
        )
        print(f"Running command:\n-------\n{command}\n---------")
        await self.context.execute(command)

    def reset(self):
        self.model_id = None

    async def auto_context(self):
        return f"""You are an scientific modeler whose goal is to use the Decapodes modeling library to manipulate Decapodes models in Julia.

You are working on a Multiphysics model named: {self.amr.get('name')}

The description of the model is:
{self.amr.get('description')}

The model has the following structure:
--- START ---
{await self.model_structure()}
--- END ---

Please answer any user queries to the best of your ability, but do not guess if you are not sure of an answer.
If you are asked to manipulate, stratify, or visualize the model, use the generate_code tool.
"""

    async def model_structure(self) -> str:
        """
        Inspect the model and return information and metadata about it.

        This should be used to answer questions about the model.


        Returns:
            str: a JSON representation of the model
        """
        # Update the local dataframe to match what's in the shell.
        # This will be factored out when we switch around to allow using multiple runtimes.
        amr = (
            await self.context.evaluate(
                # f"{self.var_name} |> json ∘ generate_json_acset"
                "nothing"
            )
        )["return"]
        return json.dumps(amr, indent=2)

    @tool()
    async def generate_code(
        self, query: str, agent: AgentRef, loop: LoopControllerRef
    ) -> None:
        """
        Generated Julia code to be run in an interactive Jupyter notebook for the purpose of exploring and modifying systems of partial differential equations.

        Input is a full grammatically correct question about or request for an action to be performed on the loaded model.

        Assume that the model is already loaded and has the variable named `model`.
        Information about the dataframe can be loaded with the `model_structure` tool.

        Args:
            query (str): A fully grammatically correct queistion about the current model.
        """
        # set up the agent
        # str: Valid and correct julia code that fulfills the user's request.
        prompt = f"""
You are a programmer writing code to help with scientific data analysis and manipulation in Julia.

Please write code that satisfies the user's request below.

You have access to a variable name `model` that is a Petrinet model with the following structure:
{await self.model_structure()}

If you are asked to modify or update the model, modify the model in place, keeping the updated variable to still be named `model`.
You have access to the AlgebraicJulia libraries: Decapodes, Catlab, ACSets, CombinatorialSpaces.

You also have access to the library HTTP.jl.

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
                "language": "julia-1.9",
                "content": code.strip(),
            }
        )
        return result

    async def send_decapodes_preview_message(
        self, server=None, target_stream=None, data=None, parent_header={}
    ):
        preview = await self.context.evaluate(self.get_code("output_model")) # TODO: Spit out something prettier than the JSON
        json_str = preview["return"]["json"]
        image = preview["return"]["image"]
        content = {
            "data": {
                "application/json": json_str,
                "image/svg": image,
            }
        }
        self.context.kernel.send_response(
            "iopub", "decapodes_preview", content, parent_header=parent_header
        )
    @message_handler
    async def save_amr_request(self, message):
        content = message.content

        new_name = content.get("name")

        new_model = await self.context.evaluate(self.get_code("output_model"))["return"]

        original_name = new_model.get("name", "None")
        original_model_id = self.model_id

        new_model["header"]["name"] = new_name
        new_description = new_model.get("header", {}).get("description", "") + f"\nTransformed from model '{original_name}' ({original_model_id}) at {datetime.datetime.utcnow().strftime('%c %Z')}"
        new_model["header"]["description"] = new_description
        if getattr(self, "configuration", None) is not None:
            new_model["header"][
                "description"
            ] += f"\nfrom base configuration '{self.configuration.get('name')}' ({self.configuration.get('id')})"

        create_req = requests.post(
            f"{os.environ['DATA_SERVICE_URL']}/models", json=new_model
        )
        new_model_id = create_req.json()["id"]

        content = {"model_id": new_model_id}
        self.context.kernel.send_response(
            "iopub", "save_model_response", content, parent_header=message.header
        )
