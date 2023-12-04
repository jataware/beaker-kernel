import json
import logging
import os
from typing import TYPE_CHECKING, Any, Dict

import requests

from beaker_kernel.lib.context import BaseContext
from beaker_kernel.lib.jupyter_kernel_proxy import JupyterMessage

from .agent import DecapodesAgent

if TYPE_CHECKING:
    from beaker_kernel.kernel import LLMKernel
    from beaker_kernel.lib.subkernels.base import BaseSubkernel


logger = logging.getLogger(__name__)


class DecapodesContext(BaseContext):

    slug = "decapodes"
    agent_cls = DecapodesAgent

    def __init__(self, beaker_kernel: "LLMKernel", subkernel: "BaseSubkernel", config: Dict[str, Any]) -> None:
        self.target = "decapode"
        self.intercepts = {
            "save_amr_request": (self.save_amr_request, "shell"),
            "construct_amr_request": (self.construct_amr, "shell"),
            "compile_expr_request": (self.compile_expr, "shell"),
        }
        self.reset()
        super().__init__(beaker_kernel, subkernel, self.agent_cls, config)


    async def setup(self, config, parent_header):
        self.config = config
        var_names = list(config.keys())

        def fetch_model(model_id):
            meta_url = f"{os.environ['DATA_SERVICE_URL']}/models/{model_id}"
            response = requests.get(meta_url)
            if response.status_code >= 300:
                raise Exception(f"Failed to retrieve model {model_id} from server returning {response.status_code}")
            model = json.dumps(response.json()["model"])
            return model

        load_commands = [
            '%s = parse_json_acset(SummationDecapode{Symbol, Symbol, Symbol},"""%s""")' % (var_name, fetch_model(decapode_id))
            for var_name, decapode_id in config.items()
        ]

        command = "\n".join(
            [
                self.get_code("setup"),
                "decapode = @decapode begin end",
                *load_commands
            ]
        )
        print(f"Running command:\n-------\n{command}\n---------")
        await self.execute(command)
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
            await self.evaluate(
                f"_expr |> string"
            )
        )["return"]
        return json.dumps(amr, indent=2)

    async def send_decapodes_preview_message(
        self, server=None, target_stream=None, data=None, parent_header=None
    ):
        if parent_header is None:
            parent_header = {}
        preview = await self.evaluate(self.get_code("expr_to_info", {"target": self.target}))
        content = preview["return"]
        if content is None:
            raise RuntimeError("Info not returned for preview")

        self.beaker_kernel.send_response(
            "iopub", "decapodes_preview", content, parent_header=parent_header
        )

    async def compile_expr(self, server, target_stream, data):
        message = JupyterMessage.parse(data)
        content = message.content

        declaration = content.get("declaration")
        self.decapodes_expression_dsl = declaration

        command = "\n".join(
            [
                self.get_code("construct_expr", {"declaration": declaration, "target": self.target}),
                "nothing"
            ]
        )
        await self.execute(command)

        self.beaker_kernel.send_response(
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

        preview = await self.evaluate(self.get_code("expr_to_info", {"target": self.target}))
        model = preview["return"]["application/json"]

        amr = {
            "header": header,
            "model": model,
            "_type": "ASKEMDecaExpr",
            "annotations": [],
        }

        self.beaker_kernel.send_response(
            "iopub", "construct_amr_response", amr, parent_header=message.header
        )

    async def save_amr_request(self, server, target_stream, data):
        message = JupyterMessage.parse(data)
        content = message.content

        header = content["header"]
        header["_type"] = "Header"

        preview = await self.evaluate(self.get_code("expr_to_info", {"target": self.target}))
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

        self.beaker_kernel.send_response(
            "iopub", "save_model_response", content, parent_header=message.header
        )
