import logging
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from string import Template
from typing import ClassVar, Optional, Self
from uuid import UUID, uuid4

import yaml
from adhoc_api.curation import Example
from adhoc_api.tool import AdhocApi, APISpec
from archytas.tool_utils import AgentRef, LoopControllerRef, ReactContextRef, tool

from beaker_kernel.lib.integrations.base import MutableBaseIntegrationProvider
from beaker_kernel.lib.types import ExampleResource, FileResource, Integration, IntegrationTypes, Resource

logger = logging.getLogger(__file__)

# this keeps the yaml output much more human readable for code examples and long prompts.
def string_formatter(dumper, data):
    max_line_length = 120
    if len(data.splitlines()) == 1 and len(data) < max_line_length:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
def uuid_formatter(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data))
yaml.representer.SafeRepresenter.add_representer(str, string_formatter)
yaml.representer.SafeRepresenter.add_representer(UUID, uuid_formatter)

@dataclass
class AdhocSpecification:
    name: str
    slug: str
    description: str
    prompt: str
    location: os.PathLike # relative to adhoc root
    integration_type: IntegrationTypes
    resources: dict[UUID, Resource]

    @classmethod
    def from_dict(cls, location: os.PathLike, source: dict) -> Self:
        """
        Creates a AdhocSpecification from a dict.

        location: folder name (does not necessarily match slug/name)
        source: deserialized yaml of the integration
        """
        try:
            name = source["name"]
            description = source["description"]
            prompt = source["prompt"]
        except KeyError as e:
            msg = "Missing required field on API"
            raise KeyError(msg) from e
        slug = source.get("slug", str(uuid4()))

        # convert yaml dict resources to dataclass objects, parsing them
        resources = {}
        for resource_id, resource_value in source.get("resources", {}).items():
            if (resource_type := resource_value.get("resource_type")) == "file" or resource_value.get("filepath") is not None:
                resource = FileResource(**(resource_value | {"integration": slug}))
            elif resource_type == "example" or resource_value.get("code") is not None:
                resource = ExampleResource(**(resource_value | {"integration": slug}))
            else:
                msg = "Resources must be file or example for adhoc"
                raise ValueError(msg)
            resources[UUID(resource_id)] = resource

        integration_type = source.get("integration_type", "api")
        integration = cls(
            name=name,
            slug=slug,
            description=description,
            prompt=prompt,
            location=location,
            integration_type=integration_type,
            resources=resources
        )
        return integration

    def get_resources_by_type(self, resource_type: str) -> list:
        return [
            resource for resource in self.resources.values()
            if resource.resource_type == resource_type
        ]

    def get_files(self) -> list[FileResource]:
        return self.get_resources_by_type("file")

    def get_examples(self) -> list[ExampleResource]:
        return self.get_resources_by_type("example")

    def get_adhoc_api_examples(self) -> list[Example]:
        return [
            {
                "code": example.code,
                "query": example.query,
                "notes": example.notes or ""
            }
            for example in self.get_examples()
        ]

    def render(self, overrides: Optional[dict[str, str]] = None) -> APISpec:
        """
        Renders a template with included files given a relative root to start from.
        Raises on nonexistent files and a failure to load.

        Overrides are template substitutions that will take precedence over existing
        fields, such as dataset_root.

        Attachments are loaded from `relative_root/attachments` as a starting path.
        """
        substitutions = {
            attachment.name: (Path(self.location) / "attachments" / attachment.filepath)
                .resolve()
                .read_text()
            for attachment in self.get_files()
            if attachment.filepath is not None
        }
        substitutions |= (overrides or {})

        return APISpec(
            name=self.name,
            slug=self.name.lower().replace(" ", "_"),
            cache_key=f"beaker_{self.slug}",
            description=self.description,
            examples=self.get_adhoc_api_examples(),
            documentation=Template(self.prompt).substitute(substitutions)
        )

    def to_integration(self, provider_type: str, provider: str) -> Integration:
        """
        Converts a AdhocSpecification to a Beaker Integration, without rendering any part.
        """
        return Integration(
            slug=self.slug,
            name=self.name,
            description=self.description,
            datatype="api",
            url=str(self.location),
            source=self.prompt,
            provider=f"{provider_type}:{provider}"
        )

    def to_yaml(self) -> str:
        integration = asdict(self)
        integration.pop("location")
        return yaml.safe_dump(integration)



class AdhocIntegrationProvider(MutableBaseIntegrationProvider):
    specifications: list[AdhocSpecification]
    provider_type = "adhoc"

    def write_all_specifications(self):
        for spec in self.specifications:
            (Path(spec.location) / "api.yaml").write_text(spec.to_yaml())

    def build_adhoc(self):
        datafile_root = Path(self.adhoc_path) / "data"
        substitutions = {
            "DATASET_FILES_BASE_PATH": str(datafile_root)
        }
        self.adhoc_api = AdhocApi(
            apis=[
                spec.render(substitutions)
                for spec in self.specifications
            ],
            **self.adhoc_config_options
        )

    def __init__(
        self,
        adhoc_path: os.PathLike,
        display_name: str,
        **config_options
    ):
        super().__init__(display_name)
        self.adhoc_path = Path(adhoc_path)

        if not self.adhoc_path.exists():
            msg = f"Unable to initialize ad-hoc integration as specified directory '{adhoc_path}' does not exist."
            raise RuntimeError(msg)
        self.adhoc_config_options = config_options

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
        # todo: instructions
        self.write_all_specifications()
        self.build_adhoc()

    def get_specification(self, specification_id: str) -> AdhocSpecification:
        """
        Look up a specification by slug and return it.
        """
        try:
            return next(
                spec for spec in self.specifications
                if spec.slug == specification_id
            )
        except StopIteration as e:
            msg = f"`{specification_id}` not found in specifications."
            raise KeyError(msg) from e

    def list_integrations(self):
        return [
            asdict(specification.to_integration(
                provider_type=self.provider_type, provider=self.slug
            ))
            for specification in self.specifications
        ]

    def get_integration(self, integration_id: str) -> dict:
        """
        Returns the serializable dict representation of the given specification.
        """
        return asdict(
            (next(i for i in self.specifications if i.slug == integration_id))
            .to_integration(provider_type=self.provider_type, provider=self.slug)
        )

    def add_integration(self, **payload):
        self.specifications.append(AdhocSpecification(
            **payload,
            location=self.adhoc_path / payload["slug"],
            resources={}
        ))
        self.write_all_specifications()

    def remove_integration(self, **payload):
        self.specifications = [spec for spec in self.specifications if spec.slug != payload["slug"]]
        self.write_all_specifications()

    def update_integration(self, **payload):
        specification = self.get_specification(payload["slug"])
        self.specifications = [spec for spec in self.specifications if spec.slug != payload["slug"]]
        self.specifications.append(AdhocSpecification(**asdict(specification) | payload))
        self.write_all_specifications()

    def list_resources(self, integration_id, resource_type: Optional[str] = None):
        specification = self.get_specification(integration_id)
        if resource_type is not None:
            resources = specification.get_resources_by_type(resource_type)
        else:
            resources = specification.resources.values()
        return {resource.resource_id: asdict(resource) for resource in resources}

    def get_resource(self, integration_id, resource_id):
        if resource := self.get_specification(integration_id).resources.get(resource_id):
            return asdict(resource)
        return None

    def add_resource(self, integration_id, **payload):
        specification = self.get_specification(integration_id)
        resource_type = payload["resource_type"]
        if resource_type == "file":
            resource = FileResource(**(payload | {"integration": integration_id}))
        elif resource_type == "example":
            resource = ExampleResource(**(payload | {"integration": integration_id}))
        else:
            msg = "Only examples and files are valid on an adhoc integration."
            raise ValueError(msg)
        if resource.resource_id is not None:
            specification.resources[resource.resource_id] = resource
        self.write_all_specifications()

    def remove_resource(self, integration_id, resource_id):
        specification = self.get_specification(integration_id)
        specification.resources.pop(resource_id)
        self.write_all_specifications()

    def update_resource(self, integration_id, resource_id, **payload):
        # should this only allow updating an id to a different resource type?
        specification = self.get_specification(integration_id)
        resource = specification.resources.pop(resource_id)
        if resource.resource_type == "file":
            resource = FileResource(**(asdict(resource) | payload | {"integration": integration_id}))
        elif resource.resource_type == "example":
            resource = ExampleResource(**(asdict(resource) | payload | {"integration": integration_id}))
        else:
            msg = "Only examples and files are valid on an adhoc integration."
            raise ValueError(msg)

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
