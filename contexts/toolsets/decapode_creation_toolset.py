
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
class DecapodesCreationToolset(BaseToolset):
    """ """

    toolset_name = "decapodes_creation"
    codeset_name = "decapodes"

    decapodes_expression_dsl: Optional[str] = None
    var_name: Optional[str] = "_expr"

    def __init__(self, context, *args, **kwargs):
        super().__init__(context=context, *args, **kwargs)
        self.intercepts = {
            "save_amr_request": (self.save_amr_request, "shell"),
            "construct_amr_request": (self.construct_amr, "shell"),
            "compile_expr_request": (self.compile_expr, "shell"),
        }
        self.reset()

    async def setup(self, config, parent_header):
        command = "\n".join(
            [
                self.get_code("setup"),
                f"{self.var_name} = parse_decapode(quote end)",
            ]
        )
        print(f"Running command:\n-------\n{command}\n---------")
        await self.context.execute(command)
        print("Decapodes creation environment set up")


    async def post_execute(self, message):
        await self.send_decapodes_preview_message(parent_header=message.parent_header)

    def reset(self):
        pass

    async def auto_context(self):
        return """You are an scientific modeler whose goal is to construct a DecaExpr for Decapodes.jl modeling library.

Explanation of Decapodes.jl from the docs
> Discrete Exterior Calculus Applied to Partial and Ordinary Differential Equations (Decapodes) is a diagrammatic language
> used to express systems of ordinary and partial differential equations. The Decapode provides a visual framework for
> understanding the coupling between variables within a PDE or ODE system, and a combinatorial data structure for working
> with them. Below, we provide a high-level overview of how Decapodes can be generated and interpreted.

However, we will just be instantiating a model with SyntacticModels.jl
Explanation of SyntacticModels from the docs.
> SyntacticModels.jl is a Julia library for representing models as syntactic expressions.
> The driving example for this library is the need to interoperate models between programming languages in the DARPA
> ASKEM Program. The AlgebraicJulia ecosystem includes some great tools for specifying modeling languages, but they are
> deeply connected to the Julia language. This package aims to provide simple tools for specifying domain specific
> programming languages that can be used to exchange the specification of scientific models between host languages.
> We heavily use the MLStyle.jl package for defining Algebraic Data Types so you should familiarize yourself with those
> concepts before reading on in this documentation.
>
> The easiest way to write down a DecaExpr is in our DSL and calling the parser.
```
_expr = Decapodes.parse_decapode(quote
  X::Form0{Point}
  V::Form0{Point}

  k::Constant{Point}

  ∂ₜ(X) == V
  ∂ₜ(V) == -1*k*(X)
end
)
```


The definition of the current model is:
--- START ---
{self.decapodes_expression_dsl}
--- END ---

Currently, the model has the following structure:
--- START ---
""" + await self.model_structure() + """
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
                f"_expr |> string"
            )
        )["return"]
        return json.dumps(amr, indent=2)


    @tool()
    async def generate_response(
        self, query: str, agent: AgentRef, loop: LoopControllerRef
    ) -> None:
        """
        DO NOT USE THIS TOOL. IT IS USELESS.


        Args:
            query (str): A fully grammatically correct queistion about the current model.
        """
        return


    @tool()
    async def generate_code(
        self, query: str, agent: AgentRef, loop: LoopControllerRef
    ) -> None:
        """
        Generated Julia code to be run in an interactive Jupyter notebook for the purpose of exploring and modifying systems the DecaExpr.

        Input is a full grammatically correct question about or request for an action to be performed on the loaded model.

        Assume that the expression is already loaded and has the variable named `_expr`.
        Information about the dataframe can be loaded with the `model_structure` tool.

        Args:
            query (str): A fully grammatically correct queistion about the current model.
        """
        # set up the agent
        # str: Valid and correct julia code that fulfills the user's request.
        prompt = f"""
You are a programmer writing code to help with scientific data analysis and manipulation in Julia.

Please write code that satisfies the user's request below.

You have access to a variable name `_expr` that is a Decapodes SyntacticModel model with the following structure:
{await self.model_structure()}

Your generated will be in the form `_expr = parse_decapode(quote ...modified object.. end)`

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
        self, server=None, target_stream=None, data=None, parent_header=None
    ):
        if parent_header is None:
            parent_header = {}
        result = await self.context.evaluate(self.get_code("expr_to_info"))
        content = result["return"]
        if content is None:
            raise RuntimeError("Info not returned for preview")

        self.context.kernel.send_response(
            "iopub", "decapodes_preview", content, parent_header=parent_header
        )

    async def compile_expr(self, server, target_stream, data):
        message = JupyterMessage.parse(data)
        content = message.content

        declaration = content.get("declaration")
        self.decapodes_expression_dsl = declaration

        command = "\n".join(
            [
                self.get_code("construct_expr", {"declaration": declaration, "var_name": self.var_name}),
                "nothing"
            ]
        )
        await self.context.execute(command)

        self.context.kernel.send_response(
            "iopub", "compile_expr_response", {"successs": True}, parent_header=message.header
        )
        await self.send_decapodes_preview_message(parent_header=message.header)

        
    async def construct_amr(self, server, target_stream, data):
        message = JupyterMessage.parse(data)
        content = message.content

        header =  {
            "description": content.get("description", None),
            "name": content.get("name", None),
            "_type": "Header",
            "model_version": "v1.0",
            "schema": "https://raw.githubusercontent.com/DARPA-ASKEM/Model-Representations/decapodes-intertypes/decapodes/decapodes_schema.json",
            "schema_name": "decapode"
        }        
        id_value = content.get("id", None)
        if id_value:
            header['id'] = id_value

        preview = await self.context.evaluate(self.get_code("expr_to_info", {"var_name": self.var_name}))
        model = preview["return"]["application/json"]

        amr = {
            "header": header,
            "model": model,
            "_type": "ASKEMDecaExpr",
            "annotations": [],
        }

        self.context.kernel.send_response(
            "iopub", "save_model_response", amr, parent_header=message.header
        )

    async def save_amr_request(self, server, target_stream, data):
        message = JupyterMessage.parse(data)
        content = message.content

        header = content["header"]
        header["_type"] = "Header"

        preview = await self.context.evaluate(self.get_code("expr_to_info", {"var_name": self.var_name}))
        model = preview["return"]["application/json"]

        amr = {
            "header": header,
            "model": model,
            "_type": "ASKEMDecaExpr",
            "annotations": [],
        }

        create_req = requests.post(
            f"{os.environ['DATA_SERVICE_URL']}/models", json=amr
        )
        new_model_id = create_req.json()["id"]

        self.context.kernel.send_response(
            "iopub", "save_model_response", content, parent_header=message.header
        )
