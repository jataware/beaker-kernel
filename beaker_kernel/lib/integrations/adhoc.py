import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from string import Template
from typing import Optional, cast, Literal, TYPE_CHECKING
from typing_extensions import Self
from uuid import uuid4

import yaml
from archytas.tool_utils import AgentRef, LoopControllerRef, ReactContextRef, tool

from beaker_kernel.lib.integrations.base import MutableBaseIntegrationProvider
from beaker_kernel.lib.types import ExampleResource, FileResource, Integration, Resource

if TYPE_CHECKING:
    from adhoc_api.curation import Example
    from adhoc_api.tool import APISpec


logger = logging.getLogger(__file__)

# this keeps the yaml output much more human readable for code examples and long prompts.
def string_formatter(dumper, data):
    max_line_length = 120
    if len(data.splitlines()) == 1 and len(data) < max_line_length:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
yaml.representer.SafeRepresenter.add_representer(str, string_formatter)


@dataclass
class AdhocSpecificationIntegration(Integration):
    location: Optional[os.PathLike] = None

    @classmethod
    def from_dict(cls, location: os.PathLike, provider: str, content: dict) -> Self:
        """
        Creates a AdhocSpecificationIntegration from a dict.

        location: folder name (does not necessarily match slug/name)
        source: deserialized yaml of the integration
        """
        try:
            name = content["name"]
            description = content["description"]
            source = content["source"]
        except KeyError as e:
            msg = "Missing required field on API"
            raise KeyError(msg) from e
        # slug = content.get("slug", cls.slugify(name))
        slug = cls.slugify(name)
        uuid = content.get("uuid", str(uuid4()))

        # convert yaml dict resources to dataclass objects, parsing them
        resources: dict[str, Resource] = {}
        for resource_id, resource_value in content.get("resources", {}).items():
            if (resource_type := resource_value.get("resource_type")) == "file" or resource_value.get("filepath") is not None:
                resource = FileResource(**(resource_value | {"integration": uuid}))
                if resource.filepath is None:
                    logger.warning("Resource filepath is None - ensure that it has a filepath. Using a default based on name")
                    resource.filepath = resource.name.lower().replace(" ", "_")
                # load file contents into integration so that we can write them when changes get populated
                # by frontend.
                resource.content = (Path(location) / "attachments" / resource.filepath).read_text()
            elif resource_type == "example" or resource_value.get("code") is not None:
                resource = ExampleResource(**(resource_value | {"integration": uuid}))
            else:
                msg = "Resources must be either of type file or example for adhoc."
            resources[resource_id] = resource

        datatype = content.get("datatype", "api")
        integration = cls(
            provider=f"adhoc:{provider}",
            name=name,
            slug=slug,
            uuid=uuid,
            description=description,
            source=source,
            location=location,
            datatype=datatype,
        )
        integration.add_resources(resource_list=list(resources.values()))
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

    def get_adhoc_api_examples(self) -> "list[Example]":
        return [
            {
                "code": example.code,
                "query": example.query,
                "notes": example.notes or ""
            }
            for example in self.get_examples()
        ]

    def render(self, overrides: Optional[dict[str, str]] = None) -> "APISpec | None":
        """
        Renders a template with included files given a relative root to start from.
        Raises on nonexistent files and a failure to load.

        Overrides are template substitutions that will take precedence over existing
        fields, such as dataset_root.

        Attachments are loaded from `relative_root/attachments` as a starting path.
        """

        from adhoc_api.curation import Example
        from adhoc_api.tool import APISpec

        if self.location is None or self.slug is None or self.source is None:
            msg = "invalid specification: missing one of: location, slug, source."
            raise ValueError(msg)
        substitutions = {
            attachment.name: (Path(self.location) / "attachments" / attachment.filepath)
                .resolve()
                .read_text()
            for attachment in self.get_files()
            if attachment.filepath is not None
        }
        substitutions |= (overrides or {})
        try:
            documentation = Template(self.source).substitute(substitutions)
            # add dataset path to examples
            examples = [
                Example(
                    code=Template(example["code"]).substitute(substitutions),
                    query=example["query"],
                    notes=example.get("notes", "")
                )
                for example in self.get_adhoc_api_examples()
            ]
            return APISpec(
                name=self.name,
                slug=self.slug,
                cache_key=f"beaker_{self.slug}",
                description=self.description,
                examples=examples,
                documentation=documentation
            )
        except KeyError as e:
            logger.error(f"Failed to render: `${{{e}}}` referenced in {self.name} but does not exist. Continuing, but disabling.")
            return None


    def to_yaml(self) -> str:
        integration = asdict(self)
        # don't save relative path into file - this is computed at load time
        integration.pop("location")
        # we write files separately outside to disk instead of inline in yaml
        # pop the loaded field that's populated at load time
        for resource in integration.get("resources", {}).values():
            if resource.get("resource_type") == "file":
                resource.pop("content")
        return yaml.safe_dump(integration)



class AdhocIntegrationProvider(MutableBaseIntegrationProvider):
    specifications: list[AdhocSpecificationIntegration]
    provider_type = "adhoc"

    def write_all_specifications(self):
        for spec in self.specifications:
            if spec.location is None:
                msg = "invalid specification: location must not be none"
                raise ValueError(msg)
            location = Path(spec.location)
            (location / "attachments").mkdir(parents=True, exist_ok=True)
            (location / "api.yaml").write_text(spec.to_yaml())
            # write file contents to their respective filepaths
            for resource in spec.resources.values():
                if resource.resource_type == "file":
                    resource = cast(FileResource, resource)
                    resource_path = Path(spec.location) / "attachments" / (resource.filepath or resource.name)
                    resource_path.write_text(resource.content or "")

    def build_adhoc(self):
        from adhoc_api.tool import AdhocApi
        datafile_root = Path(self.adhoc_path) / "data"
        substitutions = {
            "DATASET_FILES_BASE_PATH": str(datafile_root)
        }
        # handling None cases in failed renders keeps them editable but not usable by the agent
        rendered_apis = [spec.render(substitutions) for spec in self.specifications]
        self.adhoc_api = AdhocApi(
            apis=[api for api in rendered_apis if api is not None],
            **self.adhoc_config_options
        )

    def refresh_adhoc_specs(self):
        # TODO: future way to not fully reinitialize to make it less slow.
        self.build_adhoc()

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

        self.specifications: list[AdhocSpecificationIntegration] = []
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
                    AdhocSpecificationIntegration.from_dict(
                        location=integration_dir,
                        provider=self.slug,
                        content=spec_data
                    )
                )
            except Exception as e:
                msg = f"Failed to create TemplateSpecification from yaml for `{integration_yaml}`: {e}"
                logger.error(msg)

        prompts ="\n".join(
            file.read_text()
            for file in prompts_root.iterdir() if file.is_file()
        )

        self.prompt_instructions = f"{prompts}"
        self.write_all_specifications()
        self.build_adhoc()

    @property
    def prompt(self):
        agent_details = {spec.slug: spec.description for spec in self.specifications}
        delimiter = "```"
        parts = [
            f"{self.display_name}:",
            "You have access to the following integrations to use with the `draft_integration_code` and `consult_integration_docs` tools,",
            "as well as their descriptions for when and why you should use the given integration, delimited in three backticks.",
            "Only use these integrations with the `draft_integration_code` and `consult_integration_docs` tools.",
            "",
            delimiter
        ]
        parts.extend([f"Integration: {slug}\nDescription: {desc}\n\n" for slug, desc in agent_details.items()])
        parts.append(delimiter)
        return "\n".join(parts)

    def _get_specification(self, specification_id: str) -> AdhocSpecificationIntegration:
        """
        Look up a specification by slug and return it.
        """
        try:
            return next(
                spec for spec in self.specifications
                if spec.uuid == specification_id
            )
        except StopIteration:
            raise KeyError(f"Integration id {specification_id} not found in {[spec.uuid for spec in self.specifications]}")

    def list_integrations(self) -> list[Integration]:
        return self.specifications # type: ignore

    def get_integration(self, integration_id: str) -> Integration:
        return self._get_specification(integration_id)

    def add_integration(self, **payload) -> Integration:
        for field in ["resources", "uuid", "slug", "url"]:
            payload.pop(field, None)
        integration_root = self.adhoc_path / "datasources"
        new_specification = AdhocSpecificationIntegration.from_dict(
            provider=self.slug,
            location=integration_root / payload["name"].lower().replace(" ", "_"),
            content=payload
        )
        self.specifications.append(new_specification)
        self.write_all_specifications()
        self.refresh_adhoc_specs()
        return new_specification

    def remove_integration(self, integration_id: str, **payload) -> None:
        self.specifications = [spec for spec in self.specifications if spec.uuid != integration_id]
        self.write_all_specifications()
        self.refresh_adhoc_specs()

    def update_integration(self, integration_id: str, **payload) -> Integration:
        specification = self._get_specification(integration_id)
        self.specifications = [spec for spec in self.specifications if spec.uuid != integration_id]

        # we handle resources separately through other routes, so ignore it here.
        # resources come in as untyped dicts from JS
        payload.pop("resources", None)

        updated_spec_dict = (
            asdict(specification)
            | {k: v for k, v in payload.items() if k in asdict(specification)}
        )

        # calling asdict will also call asdict on nested dataclasses like resources
        # so we need to rebuild as if a fresh parse
        if specification.location is None:
            msg = "invalid specification: location must not be none"
            raise ValueError(msg)
        updated_integration = AdhocSpecificationIntegration.from_dict(
            location=specification.location,
            provider=self.slug,
            content=updated_spec_dict
        )
        self.specifications.append(updated_integration)
        self.write_all_specifications()
        self.refresh_adhoc_specs()
        return updated_integration

    def list_resources(self, integration_id: str, resource_type: Optional[str] = None) -> list[Resource]:
        specification = self._get_specification(integration_id)
        return (
            specification.get_resources_by_type(resource_type)
            if resource_type is not None
            else list(specification.resources.values())
        )

    def get_resource(self, integration_id: str, resource_id: str) -> Resource:
        return self._get_specification(integration_id).resources[resource_id]

    def add_resource(self, integration_id, **payload) -> Resource:
        specification = self._get_specification(integration_id)
        resource_type = payload["resource_type"]
        if resource_type == "file":
            resource = FileResource(**(payload | {"integration": integration_id}))
        elif resource_type == "example":
            resource = ExampleResource(**(payload | {"integration": integration_id}))
        else:
            msg = "Only examples and files are valid on an adhoc integration."
            raise ValueError(msg)
        if resource.resource_id is None:
            raise ValueError("Resource must have resource ID to attach to integration.")
        specification.resources[resource.resource_id] = resource
        self.write_all_specifications()
        self.refresh_adhoc_specs()
        return resource

    def remove_resource(self, integration_id: str, resource_id: str) -> None:
        specification = self._get_specification(integration_id)
        del specification.resources[resource_id]
        self.write_all_specifications()
        self.refresh_adhoc_specs()

    def update_resource(self, integration_id: str, resource_id: str, **payload) -> Resource:
        # should this only allow updating an id to a different resource type?
        specification = self._get_specification(integration_id)
        if resource_id not in specification.resources:
            raise KeyError(f"Resource {resource_id} not found in resources for {integration_id}: {specification.resources.keys()}")
        resource = specification.resources.pop(resource_id)
        updated_resource_dict = (
            asdict(resource)
            | {k: v for k, v in payload.items() if k in asdict(resource)}
            | {"integration": integration_id}
        )
        if resource.resource_type == "file":
            resource = FileResource(**updated_resource_dict)
        elif resource.resource_type == "example":
            resource = ExampleResource(**updated_resource_dict)
        else:
            msg = "Only examples and files are valid on an adhoc integration."
            raise ValueError(msg)
        specification.resources[resource_id] = resource # type: ignore
        self.write_all_specifications()
        self.refresh_adhoc_specs()
        return resource

    @tool
    async def add_example(self, integration: str, query: str, code: str, notes: str) -> str:
        """
        Adds an example based on the prior conversation. If the user wants to add a successful operation as an example,
        you must determine the last used integration (if it is unclear, ask the user to clarify which integration) and
        fill in the example details to save the working operation.

        Args:
            integration (str): The name of the integration to save the example to.
            query (str): The task to performed by the user
            code (str): The code ran by the specialist agent to fulfill that task
            notes (str): Additional relevant details about what was happening and what the purpose of the task is and how it was solved

        Returns:
            str: Whether adding the example succeeded or failed
        """
        try:
            integration_id = next(
                specification.uuid for specification in self.specifications
                if specification.slug == integration
            )
        except StopIteration:
            logger.warning(f"add example: integration slug not found: {integration}")
            return "Failed to look up integration by name."

        try:
            self.add_resource(
                integration_id,
                resource_type="example",
                query=query,
                code=code,
                notes=notes
            )
        except Exception as e:
            logger.warning(f"add example: failed to add resource: {e}")
            return "Add resource tool failed."
        return f"Example has been added to {integration}."

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

    @tool
    async def consult_integration_docs(self, integration: str, query: str, agent: AgentRef, loop: LoopControllerRef, react_context: ReactContextRef) -> str:
        """
This tool is used to ask a question of an an external integration. It allows you to ask a question of an integration's documentation and get results in
natural language, which may include code snippets or other information that you can then use to write code to interact with the API
(e.g. using the `run_code` tool). You can also use this information to refine your goal when using the `draft_api_code` tool.

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
