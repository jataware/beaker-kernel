import json
import logging
import re

import requests
from archytas.react import Undefined
from archytas.tool_utils import AgentRef, LoopControllerRef, tool, toolset

from beaker_kernel.lib.agent import BaseAgent
from beaker_kernel.lib.context import BaseContext
from beaker_kernel.lib.jupyter_kernel_proxy import JupyterMessage

logging.disable(logging.WARNING)  # Disable warnings
logger = logging.Logger(__name__)

@toolset()
class MiraModelToolset:
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

        prompt = f"""
You are a programmer writing code to help with scientific data analysis and manipulation in Python.

Please write code that satisfies the user's request below.

You have access to a variable name `model` that is a Petrinet model with the following structure:
{await agent.context.model_structure()}


If you are asked to modify or update the model, modify the model in place, keeping the updated variable to still be named `model`.
You have access to the MIRA libraries.

If you are asked to stratify the model, use the available function named `stratify` that is defined by the following python code:
````````````````````
def stratify(
    template_model: mira.metamodel.template_model.TemplateModel,
    *,
    key: str,
    strata: Collection[str],
    strata_curie_to_name: Optional[Mapping[str, str]] = None,
    strata_name_lookup: bool = False,
    structure: Optional[Iterable[Tuple[str, str]]] = None,
    directed: bool = False,
    conversion_cls: Type[mira.metamodel.templates.Template] = mira.metamodel.templates.NaturalConversion,
    cartesian_control: bool = False,
    modify_names: bool = True,
    params_to_stratify: Optional[Collection[str]] = None,
    params_to_preserve: Optional[Collection[str]] = None,
    concepts_to_stratify: Optional[Collection[str]] = None,
    concepts_to_preserve: Optional[Collection[str]] = None,
) -> mira.metamodel.template_model.TemplateModel

    Multiplies a model into several strata.

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
        or ``[geonames:4930956, geonames:5128581]``.
    strata_curie_to_name :
        If provided, should map from a key used in ``strata`` to a name.
        For example, ``{{"geonames:4930956": "boston",
        "geonames:5128581": "nyc"}}``.
    strata_name_lookup :
        If true, will try to look up the entity names of the strata values
        under the assumption that they are curies. This flag has no impact
        if ``strata_curie_to_name`` is given.
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


class MiraModelAgent(BaseAgent):

    def __init__(self, context: BaseContext = None, tools: list = None, **kwargs):
        tools = [MiraModelToolset]
        super().__init__(context, tools, **kwargs)
