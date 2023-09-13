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
from lib.jupyter_kernel_proxy import JupyterMessage

logging.disable(logging.WARNING)  # Disable warnings
logger = logging.Logger(__name__)


@toolset()
class MiraModelToolset(BaseToolset):
    """ """

    toolset_name = "mira_model"

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
        print(f"Processing {item_type} AMR {item_id} as a MIRA model")
        await self.set_model(
            item_id, item_type, parent_header=parent_header
        )


    async def post_execute(self, message):
        await self.send_mira_preview_message(parent_header=message.parent_header)

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
            await self.load_mira()
        else:
            raise Exception(f"Model '{item_id}' not found.")
        await self.send_mira_preview_message(parent_header=parent_header)

    async def load_mira(self):
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
        return f"""You are an scientific modeler whose goal is to use the MIRA modeling library to manipulate and stratify Petrinet models in Python.

You are working on a Petrinet model named: {self.amr.get('name')}

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

        This should be used to answer questions about the model, including information about the states, populations, transistions, etc.


        Returns:
            str: a textual representation of the model
        """
        # Update the local dataframe to match what's in the shell.
        # This will be factored out when we switch around to allow using multiple runtimes.
        amr = (
            await self.context.evaluate(
                f"AskeNetPetriNetModel(Model({self.var_name})).to_json()"
            )
        )["return"]
        return json.dumps(amr, indent=2)

    @tool()
    async def generate_code(
        self, query: str, agent: AgentRef, loop: LoopControllerRef
    ) -> None:
        """
        Generated Python code to be run in an interactive Jupyter notebook for the purpose of exploring, modifying and visualizing a Pandas Dataframe.

        Input is a full grammatically correct question about or request for an action to be performed on the loaded model.

        Assume that the model is already loaded and has the variable named `model`.
        Information about the dataframe can be loaded with the `model_structure` tool.

        Args:
            query (str): A fully grammatically correct queistion about the current model.
        """
        # set up the agent
        # str: Valid and correct python code that fulfills the user's request.
        prompt = f"""
You are a programmer writing code to help with scientific data analysis and manipulation in Python.

Please write code that satisfies the user's request below.

You have access to a variable name `model` that is a Petrinet model with the following structure:
{await self.model_structure()}


If you are asked to modify or update the model, modify the model in place, keeping the updated variable to still be named `model`.
You have access to the MIRA libraries.

If you are asked to stratify the model, use the available function named `stratify` that is defined by the following python code:
````````````````````
def stratify(
    template_model: TemplateModel,
    *,
    key: str,
    strata: Collection[str],
    structure: Optional[Iterable[Tuple[str, str]]] = None,
    directed: bool = False,
    conversion_cls: Type[Template] = NaturalConversion,
    cartesian_control: bool = False,
    modify_names: bool = True,
    params_to_stratify: Optional[Collection[str]] = None,
    params_to_preserve: Optional[Collection[str]] = None,
    concepts_to_stratify: Optional[Collection[str]] = None,
    concepts_to_preserve: Optional[Collection[str]] = None,
) -> TemplateModel:
    \"\"\"Multiplies a model into several strata.

    E.g., can turn the SIR model into a two-city SIR model by splitting each concept into
    two derived concepts, each with the context for one of the two cities

    Parameters
    ----------
    template_model :
        A template model
    key :
        The (singular) name of the stratification, e.g., ``"city"``
    strata :
        A list of the values for stratification, e.g., ``["boston", "nyc"]``
    structure :
        An iterable of pairs corresponding to a directed network structure
        where each of the pairs has two strata. If none given, will assume a complete
        network structure. If no structure is necessary, pass an empty list.
    directed :
        Should the reverse direction conversions be added based on the given structure?
    conversion_cls :
        The template class to be used for conversions between strata
        defined by the network structure. Defaults to :class:`NaturalConversion`
    cartesian_control :
        If true, splits all control relationships based on the stratification.

        This should be true for an SIR epidemiology model, the susceptibility to
        infected transition is controlled by infected. If the model is stratified by
        vaccinated and unvaccinated, then the transition from vaccinated
        susceptible population to vaccinated infected populations should be
        controlled by both infected vaccinated and infected unvaccinated
        populations.

        This should be false for stratification of an SIR epidemiology model based
        on cities, since the infected population in one city won't (directly,
        through the perspective of the model) affect the infection of susceptible
        population in another city.
    modify_names :
        If true, will modify the names of the concepts to include the strata
        (e.g., ``"S"`` becomes ``"S_boston"``). If false, will keep the original
        names.
    params_to_stratify :
        A list of parameters to stratify. If none given, will stratify all
        parameters.
    params_to_preserve:
        A list of parameters to preserve. If none given, will stratify all
        parameters.
    concepts_to_stratify :
        A list of concepts to stratify. If none given, will stratify all
        concepts.
    concepts_to_preserve:
        A list of concepts to preserve. If none given, will stratify all
        concepts.

    Returns
    -------
    :
        A stratified template model
    \"\"\"
````````````````````

You also have access to the libraries pandas, numpy, scipy, matplotlib and the full mira python library.

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
                "language": "python3",
                "content": code.strip(),
            }
        )
        return result

    async def send_mira_preview_message(
        self, server=None, target_stream=None, data=None, parent_header={}
    ):
        try:
            await self.context.execute(
                "_mira_model = Model(model);\n"
                "_model_size = len(_mira_model.variables) + len(_mira_model.transitions);\n"
                "del _mira_model;\n"
            )
            model_size = (await self.context.evaluate("_model_size"))["return"]
            if model_size < 800:
                preview = await self.context.evaluate(self.get_code("model_preview"))
                format_dict, md_dict = preview["return"]
                content = {"data": format_dict}
                self.context.kernel.send_response(
                    "iopub", "model_preview", content, parent_header=parent_header
                )
            else:
                print(
                    f"Note: Model is too large ({model_size} nodes) for auto-preview.",
                    file=sys.stderr,
                    flush=True,
                )
        except Exception as e:
            raise

    async def save_amr_request(self, server, target_stream, data):
        message = JupyterMessage.parse(data)
        content = message.content

        new_name = content.get("name")

        new_model: dict = (
            await self.context.evaluate(
                f"AskeNetPetriNetModel(Model({self.var_name})).to_json()"
            )
        )["return"]

        original_name = new_model.get("name", "None")
        original_model_id = self.model_id

        # Deprecated: Handling both new and old model formats

        if "header" in new_model:
            new_model["header"]["name"] = new_name
            new_description = new_model.get("header", {}).get("description", "") + f"\nTransformed from model '{original_name}' ({original_model_id}) at {datetime.datetime.utcnow().strftime('%c %Z')}"
            new_model["header"]["description"] = new_description
            if getattr(self, "configuration", None) is not None:
                new_model["header"][
                    "description"
                ] += f"\nfrom base configuration '{self.configuration.get('name')}' ({self.configuration.get('id')})"
        else:
            new_model["name"] = new_name
            new_model[
                "description"
            ] += f"\nTransformed from model '{original_name}' ({original_model_id}) at {datetime.datetime.utcnow().strftime('%c %Z')}"
            if getattr(self, "configuration", None) is not None:
                new_model[
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
