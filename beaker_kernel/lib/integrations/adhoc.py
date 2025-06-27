import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from string import Template
from typing import Optional, Self

import yaml
from adhoc_api.tool import AdhocApi, APISpec
from adhoc_api.uaii import claude_37_sonnet, gemini_15_pro, gpt_41, o3_mini
from archytas.tool_utils import AgentRef, LoopControllerRef, ReactContextRef, tool

from beaker_kernel.lib.types import Integration, IntegrationAttachment, IntegrationExample, IntegrationTypes

from .base import MutableBaseIntegrationProvider

logger = logging.getLogger(__file__)

@dataclass
class AdhocSpecification:
    name: str
    slug: str
    attachments: dict[str, str]
    description: str
    prompt: Template
    examples: list[IntegrationExample]
    location: os.PathLike # relative to adhoc root
    integration_type: IntegrationTypes

    @classmethod
    def from_dict(cls, location: os.PathLike, source: dict) -> Self:
        """
        Creates a AdhocSpecification from a dict.

        location: folder name (does not necessarily match slug/name)
        source: deserialized yaml of the integration
        """
        prompt = Template(source.get("prompt", ""))
        modified_fields = {
            "prompt": prompt,
            "location": location,
            # attachments is optional -- usually for datasets
            "attachments": source.get("attachments", {}),
            # integration_type is optional
            "integration_type": source.get("integration_type", "api"),
            # slug may not be present on old specs -- replace spaces with _ in name for a slug
            "slug": source.get("slug", str(source.get("name")).lower().replace(" ", "_"))
        }
        return cls(**(source | modified_fields))

    def render(self, overrides: dict[str, str] | None = None) -> APISpec:
        """
        Renders a template with included files given a relative root to start from.
        Raises on nonexistent files and a failure to load.

        Overrides are template substitutions that will take precedence over existing
        fields, such as dataset_root.

        Attachments are loaded from `relative_root/attachments` as a starting path.
        """
        substitutions = {
            attachment_key: (Path(self.location) / "attachments" / filepath).resolve().read_text()
            for attachment_key, filepath in self.attachments.items()
        }
        substitutions |= (overrides or {})
        return APISpec(
            name=self.name,
            slug=self.slug,
            cache_key=f"beaker_{self.slug}",
            description=self.description,
            examples=[asdict(example) for example in self.examples], # type: ignore
            documentation=self.prompt.substitute(substitutions)
        )

    def to_integration(self) -> Integration:
        """
        Converts a AdhocSpecification to a Beaker Integration, without rendering any part.
        """
        return Integration(
            slug=self.slug,
            name=self.name,
            description=self.description,
            datatype="api",
            url=str(self.location),
            source=self.prompt.template,
            attached_files=[
                IntegrationAttachment(
                    name=attachment_key,
                    filepath=filepath
                ) for attachment_key, filepath in self.attachments.items()
            ],
            examples=self.examples
        )


class AdhocIntegrationProvider(MutableBaseIntegrationProvider):
    specifications: list[AdhocSpecification]

    def __init__(self, adhoc_path: os.PathLike, display_name: str, **config_options):
        super().__init__(display_name)
        self.adhoc_path = Path(adhoc_path)
        if not self.adhoc_path.exists():
            msg = f"Unable to initialize ad-hoc integration as specified directory '{adhoc_path}' does not exist."
            raise RuntimeError(msg)

        integration_root = self.adhoc_path / "datasources"
        instruction_root = self.adhoc_path / "instructions"
        prompts_root = self.adhoc_path / "prompts"

        self.specifications: list[AdhocSpecification] = []
        for inner_directory in os.listdir(integration_root):
            integration_dir = integration_root / inner_directory
            if not integration_dir.is_dir():
                continue

            integration_yaml = integration_dir / "api.yaml"
            if not integration_yaml.is_file():
                logger.warning(f"Ignoring malformed API: `{integration_yaml}` is not a file")
                continue

            spec_data = yaml.safe_load(integration_yaml.read_text())
            # attach examples, since the path is fixed per-integration
            examples_yaml = integration_dir / "examples.yaml"
            if not examples_yaml.is_file():
                logger.warning(
                    msg=f"No examples.yaml found for `{integration_yaml}`. "
                        f"Assuming no examples for the integration and still loading it."
                )
                spec_data["examples"] = []
            else:
                spec_data["examples"] = [
                    IntegrationExample(**entry)
                    for entry in
                        yaml.safe_load(
                            examples_yaml.read_text()
                        ) or []
                ]
            try:
                self.specifications.append(
                    AdhocSpecification.from_dict(
                        location=integration_dir,
                        source=spec_data
                    )
                )
            except Exception as e:
                msg = f"Failed to create TemplateSpecification from yaml for `{integration_yaml}`: {e}"
                logger.error(msg)

        self.instructions ="\n".join(
            file.read_text()
            for file in instruction_root.iterdir() if file.is_file()
        )

        datafile_root = Path(self.adhoc_path) / "data"
        substitutions = {
            "DATASET_FILES_BASE_PATH": str(datafile_root)
        }
        self.adhoc_api = AdhocApi(
            apis=[
                spec.render(substitutions)
                for spec in self.specifications
            ],
            **config_options
        )

    def list_integrations(self):
        return [asdict(specification.to_integration()) for specification in self.specifications]

    def get_integration(self, integration_id: str):
        return asdict(
            (next(i for i in self.specifications if i.slug == integration_id))
                    .to_integration()
        )

    def add_integration(self, **payload):
        pass

    def remove_integration(self, **payload):
        pass

    def update_integration(self, **payload):
        pass

    def list_resources(self, integration_id, resource_type=None):
        pass

    def get_resource(self, integration_id, resource_id):
        pass

    def add_resource(self, integration_id, **payload):
        pass

    def remove_resource(self, integration_id, resource_id, **payload):
        pass

    def update_resource(self, integration_id, resource_id, **payload):
        pass

    @tool
    async def draft_integration_code(self, integration: str, goal: str, agent: AgentRef, loop: LoopControllerRef, react_context: ReactContextRef) -> str:
        """
Drafts python code for an integration request given a specified goal, such as a query for a specific study. You can use this tool to
get code to interact with the integrations that are available to you. When the user asks you to use an integration and you are unsure how to do so, you should
be sure to use this tool. Once you've learned how to do common tasks with an integration you may not need this tool, but for accomplishing
new tasks, you should use this tool.

The way this tool functions is that it will provide the goal to an external agent, which we refer to as the "drafter".
The drafter has access to the integration's documentation for the integration in question. The drafter will then generate the code to perform the desired operation.
However, the drafter requires a very specific goal in order to do their job and does not have the ability to guess or infer.
Therefore, you must provide a very specific goal. It also does not have awareness of information outside of what you provide in the goal.
Therefore, if you have run code previously that returned information such as names of studies, `ids` of datasets, etc, you must provide that
information in the goal if it is needed to perform the desired operation.

You must never reference code that has already been run since the drafter does not have awareness of that information. For example, don't set as the goal:
"Run the previous code but modify it to do X"; you must provide that code in the goal if you want it to be utilized.

The code that is drafted will generally be a complete, small program including relevant imports and other boilerplate code. Much of this
may already be implemented in the code you have run previously; if that is the case you should not repeat it. Feel free to streamline the code
generated by removing any unnecessary steps before sending it to the `run_code` tool.

If you use this tool, you MUST indicate so in your thinking. Wrap the tool name in backticks.

You MUST also be explicit about the goal in your thinking.

Args:
    integration (str): The name of the integration to use
    goal (str): The task to be performed by the integration request. This should be as specific as possible and include any relevant details such as the `ids` or other parameters that should be used to get the desired result.

Returns:
    str: Depending on the user defined configuration will do one of two things.
         Either A) return the raw generated code. Or B) Will attempt to run the code and return the result or
         any errors that occurred (along with the original code). if an error is returned, you may consider
         trying to fix the code yourself rather than reusing the tool.
        """
        logger.info(f"using integration: {integration}")
        try:
            code = self.adhoc_api.use_api(integration, goal)
            return f"Here is the code the drafter created to use the API to accomplish the goal: \n\n```\n{code}\n```"
        except Exception as e:
            if self.adhoc_api is None:
                return "Do not attempt to fix this result: there is no API key for the agent that creates the request. Inform the user that they need to specify GEMINI_API_KEY and consider this a successful tool invocation."
            logger.error(str(e))
            return f"An error occurred while using the API. The error was: {str(e)}. Please try again with a different goal."

    @tool()
    async def consult_integration_docs(self, integration: str, query: str, agent: AgentRef, loop: LoopControllerRef, react_context: ReactContextRef) -> str:
        """
This tool is used to ask a question of an an external integration. It allows you to ask a question of an integration's documentation and get results in
natural language, which may include code snippets or other information that you can then use to write code to interact with the API
(e.g. using the `BiomeAgent__run_code` tool). You can also use this information to refine your goal when using the `draft_api_code` tool.

You can ask questions related to endpoints, payloads, etc. For example, you can ask "What are the endpoints for this integration?"
or "What payload do I need to send to this integration?" or "How do I query for datasets by keyword?" etc, etc.

If you use this tool, you MUST indicate so in your thinking. Wrap the tool name in backticks.

Args:
    integration (str): The name of the integration to use
    query (str): The question you want to ask about the integration.

Returns:
    str: returns instructions on how to utilize the integration based on the question asked.
        """
        logger.info(f"asking integration: {integration}")
        try:
            results = self.adhoc_api.ask_api(integration, query)
            return f"Here is the information I found about how to use the API: \n{results}"
        except Exception as e:
            if self.adhoc_api is None:
                return "Do not attempt to fix this result: there is no API for the agent that creates the request. Inform the user that they need to specify GEMINI_API_KEY and consider this a successful tool invocation."
            logger.error(str(e))
            return f"An error occurred while asking the API. The error was: {str(e)}. Please try again with a different question."
