import json
import logging
import os
import re
import requests
from typing import Optional, Any

import pandas as pd

from archytas.tool_utils import tool, toolset, AgentRef, LoopControllerRef

logging.disable(logging.WARNING)  # Disable warnings
logger = logging.Logger(__name__)


@toolset()
class MiraModelToolset:
    """ """

    model_id: Optional[str]
    model_json: Optional[str]
    model_dict: Optional[dict[str, Any]]
    var_name: Optional[str] = 'model'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reset()

    def set_model(self, model_id, agent=None):
        self.model_id = model_id
        meta_url = f"{os.environ['DATA_SERVICE_URL']}/models/{self.model_id}"
        self.amr = requests.get(meta_url).json()
        if self.amr:
            self.load_mira()
        else:
            raise Exception(f"Model '{model_id}' not found.")

    def load_mira(self):
        command = (
                    """import requests; import pandas as pd; import numpy as np; import scipy;\n"""
                    """import json; import mira; from mira.modeling.askenet.petrinet import AskeNetPetriNetModel; from mira.sources.askenet.petrinet import template_model_from_askenet_json;\n"""
                    """import sympy; import itertools; from mira.metamodel import *; from mira.modeling import Model;\n"""
                    """from mira.modeling.askenet.petrinet import AskeNetPetriNetModel; from mira.modeling.viz import GraphicalModel;\n"""
                    f"""{self.var_name} = template_model_from_askenet_json({self.amr});\n"""
                )
        self.kernel.ex(command)

    def reset(self):
        self.model_id = None
        self.df = None

    def context(self):
        return f"""You are an scientific modeler whose goal is to use the MIRA modeling library to manipulate and stratify Petrinet models in Python.

You are working on a Petrinet model named: {self.amr.get('name')}

The description of the model is:
{self.amr.get('description')}

The model has the following structure:
--- START ---
{self.model_structure()}
--- END ---

Please answer any user queries to the best of your ability, but do not guess if you are not sure of an answer.
If you are asked to manipulate, stratify, or visualize the model, use the generate_python_code tool.
"""

    @tool()
    def model_structure(self) -> str:
        """
        Inspect the model and return information and metadata about it.

        This should be used to answer questions about the model, including information about the states, populations, transistions, etc.


        Returns:
            str: a textual representation of the model
        """
        # Update the local dataframe to match what's in the shell.
        # This will be factored out when we switch around to allow using multiple runtimes.
        if self.kernel:
            amr = self.kernel.ev(f"AskeNetPetriNetModel(Model({self.var_name})).to_json()")
            return json.dumps(amr, indent=2)
        return "UNDEFINED"


    @tool()
    def generate_python_code(
        self, query: str, agent: AgentRef, loop: LoopControllerRef
    ) -> str:
        """
        Generated Python code to be run in an interactive Jupyter notebook for the purpose of exploring, modifying and visualizing a Pandas Dataframe.

        Input is a full grammatically correct question about or request for an action to be performed on the loaded model.

        Assume that the model is already loaded and has the variable named `model`.
        Information about the dataframe can be loaded with the `model_structure` tool.

        Args:
            query (str): A fully grammatically correct queistion about the current model.

        Returns:
            str: A LLM prompt that should be passed evaluated.
        """
        # set up the agent
        # str: Valid and correct python code that fulfills the user's request.
        prompt = f"""
You are a programmer writing code to help with scientific data analysis and manipulation in Python.

Please write code that satisfies the user's request below.

You have access to a variable name `model` that is a Petrinet model with the following structure:
{self.model_structure()}


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
