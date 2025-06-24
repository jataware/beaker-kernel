from dataclasses import asdict
import json
import logging
import os
import yaml
from yaml import SafeDumper, SafeLoader
from pathlib import Path
from typing import Optional, cast

from archytas.tool_utils import tool, AgentRef, LoopControllerRef, ReactContextRef
from adhoc_api.tool import AdhocApi, ensure_name_slug_compatibility, APISpec
from adhoc_api.loader import load_yaml_api, interpolate_strings, YAMLFileLoader
from adhoc_api.uaii import gpt_41, o3_mini, claude_37_sonnet, gemini_15_pro

from beaker_kernel.lib.types import Integration, IntegrationAttachment

from .base import BaseIntegrationProvider

import re

logger = logging.getLogger(__file__)



# API specs can either be interpolated and evaluated or left unevaluated with references to other files.
# Prefer handling unevaluated files until at adhoc-api load time so that editing can work on tag directives
# rather than fully loaded content interpolated into the body.

# Beaker Integration             <-->   Raw, Uninterpolated Spec   <--> Interpolated API Spec
# (store this one on the class)         (intermediary format)           (what adhoc uses)



class RawYamlLoader(SafeLoader):
    pass
def ignore_tags(_loader, tag_suffix, node):
    return tag_suffix + " " + node.value
RawYamlLoader.add_multi_constructor("", ignore_tags)

class APISpecDumper(SafeDumper):
    pass

class LoadYamlTag(yaml.YAMLObject):
    yaml_tag = "!load_yaml"
    def __init__(self, payload):
        self.payload = payload
    def __repr__(self):
        return f"LoadYamlTag({self.payload})"
    @classmethod
    def from_yaml(cls, _loader, node):
        return LoadYamlTag(node.value)
    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.payload)
APISpecDumper.add_multi_representer(LoadYamlTag, LoadYamlTag.to_yaml)

class LoadTextTag(yaml.YAMLObject):
    yaml_tag = "!load_txt"
    def __init__(self, payload):
        self.payload = payload
    def __repr__(self):
        return f"LoadTextTag({self.payload})"
    @classmethod
    def from_yaml(cls, _loader, node):
        return LoadTextTag(node.value)
    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.payload)
APISpecDumper.add_multi_representer(LoadTextTag, LoadTextTag.to_yaml)

class FillTag(yaml.YAMLObject):
    yaml_tag = "!fill"
    def __init__(self, payload):
        self.payload = payload
    def __repr__(self):
        return f"FillTag({self.payload})"
    @classmethod
    def from_yaml(cls, _loader, node):
        return FillTag(node.value)
    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.payload, style="|")
APISpecDumper.add_multi_representer(FillTag, FillTag.to_yaml)

class AdhocYamlLoaderCustomPath(YAMLFileLoader):
    def __init__(self, stream):
        path = stream["path"]
        stream = stream["data"]
        super().__init__(stream)
        self._yaml_dir = path

def api_spec_from_integration(integration: Integration, data_root: os.PathLike) -> APISpec:
    """
    Converts a Beaker integration into a loaded adhoc_api spec.

    Preloading adhoc_api yaml specs would dump the file contents in the body of the loaded
    yaml versus keeping a reference for the purpose of frontend editing; this wraps evaluation
    of unevaluated (raw) specs until necessary.
    """
    slug = integration.slug or integration.name.lower().replace(" ", "_")
    integration_spec_represenation = {
        "name": integration.name,
        "slug": slug,
        "cache_key": f"integration_{slug}",
        "examples": LoadYamlTag("documentation/examples.yaml"),
        "description": integration.description,
        "documentation": FillTag(integration.source)
    }
    integration_root = integration.url or ""
    if integration_root == "":
        integration_root = integration.slug or integration.name.lower().replace(" ", "_")
    elif integration_root.endswith("api.yaml"):
        integration_root = integration_root[:-(len("api.yaml"))]
    for attachment in integration.attached_files or []:
        integration_spec_represenation |= {
            attachment.name: LoadTextTag(f"documentation/{attachment.filepath}")
        }
    # serialize into a compatible spec with laod directive tags so that filepaths get fully loaded
    adhoc_compatible_spec = yaml.dump(integration_spec_represenation, Dumper=APISpecDumper)
    return api_spec_from_raw_spec_str(adhoc_compatible_spec, integration_root, data_root) # type: ignore

def api_spec_from_raw_spec_str(raw_spec: str, api_yaml_root: Path, data_root: os.PathLike) -> dict:
    # use adhoc_api's loader
    raw_data = yaml.load(
        {"data": raw_spec, "path": api_yaml_root}, # type: ignore
        AdhocYamlLoaderCustomPath # noqa: S506 (inherits safeloader)
    )
    # handle the loader steps from string as source rather than filepath
    loaded_spec: dict = interpolate_strings(raw_data, raw_data) # type: ignore
    replace_dataset_paths(loaded_spec, data_root) # type: ignore
    ensure_name_slug_compatibility(loaded_spec) # type: ignore

    valid_keys = APISpec.__annotations__.keys()
    valid_spec = { key: loaded_spec[key] for key in valid_keys if key in loaded_spec }
    return valid_spec # type: ignore

def replace_dataset_paths(loaded_spec: APISpec, data_root: os.PathLike):
    """
    Operates in-place on a loaded APIspec. Replaces the uninterpolated dataset paths with the
    correct dataset path in a parsed and evaluated APIspec.
    """
    # Replace {DATASET_FILES_BASE_PATH} with data_dir path; { and {{ to reduce mental overhead
    loaded_spec['documentation'] = loaded_spec['documentation'].replace('{DATASET_FILES_BASE_PATH}', str(data_root))
    loaded_spec['documentation'] = loaded_spec['documentation'].replace('{{DATASET_FILES_BASE_PATH}}', str(data_root))
    if 'examples' in loaded_spec and isinstance(loaded_spec['examples'], list):
        for example in loaded_spec['examples']:
            if 'code' in example and isinstance(example['code'], str):
                example['code'] = example['code'].replace('{{DATASET_FILES_BASE_PATH}}', str(data_root))
                example['code'] = example['code'].replace('{DATASET_FILES_BASE_PATH}', str(data_root))

def create_integration_from_raw_spec(raw_spec_path: os.PathLike, raw_spec: dict) -> Integration:
    """
    Creates a Beaker integration from a raw, uninterpolated APIspec.
    Needs to preserve lazy loading to not replace references to files with their contents.
    """
    attachments = []
    # assume any key not one of the following is an attached file
    for attachment_key in [
        key for key in raw_spec.keys() if key not in [
            "name",
            "slug",
            "description",
            "cache_key",
            "documentation",
            "examples",
            "cache_body",
            "loaded_examples"
        ]
    ]:
        if not isinstance(raw_spec[attachment_key], str):
            logger.warning(
                msg=f"warning: key {attachment_key} on spec {raw_spec['name']} is of type "
                    f"{type(raw_spec[attachment_key])} and not str. ignoring and continuing"
            )
            continue
        filepath_raw = re.sub(
                r"!load_[a-zA-Z]+",
                "",
                raw_spec[attachment_key].strip()
            ).strip().replace("documentation/", "")
        attachments.append(IntegrationAttachment(
            name=attachment_key,
            filepath=filepath_raw,
            content=None,
            is_empty_file=False
        ))
    integration = Integration(
        slug=raw_spec["slug"],
        url=str(raw_spec_path),
        name=raw_spec["name"],
        description=raw_spec.get("description", ""),
        source=raw_spec.get("documentation", "").replace("!fill", ""),
        attached_files=attachments,
        examples=raw_spec.get("loaded_examples", [])
    )
    return integration



class AdhocIntegrationProvider(BaseIntegrationProvider):
    integrations: list[Integration]

    def __init__(self,
        display_name: str,
        datafile_root: os.PathLike,
        adhoc_path: os.PathLike,
        integrations: list[Integration],
        instructions: Optional[str]=None,
        **config_options,
    ):
        super().__init__(display_name)
        self.datafile_root = datafile_root
        self.adhoc_path = adhoc_path
        self.instructions = instructions
        self.integrations = integrations
        self.adhoc_api = self.create_adhoc(**config_options)

    def create_adhoc(self, **config_options) -> AdhocApi:
        """
        Create a new adhoc instance from the current integrations.
        """
        apis = [
            api_spec_from_integration(integration, self.datafile_root)
            for integration in self.integrations
        ]
        return AdhocApi(
            apis=apis,
            **config_options,
        )

    @classmethod
    def from_file_structure(cls, adhoc_path: os.PathLike, **config_options):
        adhoc_path = Path(adhoc_path)
        if not adhoc_path.exists():
            raise RuntimeError(f"Unable to initialize ad-hoc integration as specified directory '{adhoc_path}' does not exist.")

        integration_root = adhoc_path / "datasources"
        datafile_root = adhoc_path / "data"
        instruction_root = adhoc_path / "instructions"
        prompts_root = adhoc_path / "prompts"

        raw_specs: list[tuple[os.PathLike, dict]] = [] # no interpolation

        for inner_directory in os.listdir(integration_root):
            integration_dir = integration_root / inner_directory
            if integration_dir.is_dir():
                integration_yaml = integration_dir / 'api.yaml'
                if not integration_yaml.is_file():
                    logger.warning(f"Ignoring malformed API: {integration_yaml}")
                    continue
                raw_contents = integration_yaml.read_text()
                raw_spec = yaml.load(raw_contents, RawYamlLoader) # noqa: S506 - inherits safeloader
                try:
                    ensure_name_slug_compatibility(raw_spec)
                    # add the loaded examples in too, since we want that tag parsed in order to get the file contents
                    # but also the raw text (that points to the file we're loading here) as well
                    loaded = api_spec_from_raw_spec_str(raw_contents, integration_dir, datafile_root)
                    raw_spec['loaded_examples'] = loaded.get('examples', [])
                    raw_specs.append((integration_dir / 'api.yaml', raw_spec))
                except Exception as e:
                    logger.error(f"Failed to load integration `{integration_yaml}` from raw yaml: {e}")

        integrations = [
            create_integration_from_raw_spec(filepath, raw_spec)
            for (filepath, raw_spec) in raw_specs
        ]

        instructions ="\n".join(
            file.read_text()
            for file in instruction_root.iterdir() if file.is_file()
        )

        # uninterpolated specs
        instance = cls(
            datafile_root=datafile_root,
            adhoc_path=adhoc_path,
            integrations=integrations,
            instructions=instructions,
            ** config_options
        )
        return instance

    def list_integrations(self):
        return [asdict(integration) for integration in self.integrations]

    def get_integration(self, integration_id: str):
        return asdict(next(i for i in self.integrations if i.slug == integration_id))

    def add_integration(self, **payload):
        pass

    def list_resources(self, integration_id, resource_type=None):
        pass

    def get_resource(self, integration_id, resource_id):
        pass

    def add_resource(self, integration_id, **payload):
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
