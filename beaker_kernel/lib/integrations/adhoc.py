import logging
import os
import yaml
from pathlib import Path
from typing import Optional

from archytas.tool_utils import tool
from adhoc_api.tool import AdhocApi, ensure_name_slug_compatibility
from adhoc_api.loader import load_yaml_api
from adhoc_api.uaii import gpt_41, o3_mini, claude_37_sonnet, gemini_15_pro

from .base import BaseIntegrationProvider

logger = logging.getLogger(__file__)


class AdhocIntegrationProvider(BaseIntegrationProvider):
    specs: list

    def __init__(self,
        apis: list,
        instructions: Optional[str]=None,
        **config_options,
    ):
        super().__init__()
        self.adhoc_api = AdhocApi(
            apis=apis,
            **config_options,
        )
        self.instructions = instructions
        self.specs = apis


    @classmethod
    def from_file_structure(cls, adhoc_path: os.PathLike, **config_options):
        adhoc_path = Path(adhoc_path)
        if not adhoc_path.exists():
            raise RuntimeError(f"Unable to initialize ad-hoc integration as specified directory '{adhoc_path}' does not exist.")

        integration_root = adhoc_path / "datasources"
        datafile_root = adhoc_path / "data"
        instruction_root = adhoc_path / "instructions"
        prompts_root = adhoc_path / "prompts"

        # Get API specs and directories in one pass
        integration_specs = []
        raw_specs = [] # no interpolation
        integration_directories = {}
        for integration_dir in os.listdir(integration_root):
            # integration_full_path = os.path.join(integration_root, integration_dir)
            integration_dir = integration_root / integration_dir
            if integration_dir.is_dir():
                integration_yaml = integration_dir / 'api.yaml'
                if not integration_yaml.is_file():
                    logger.warning(f"Ignoring malformed API: {integration_yaml}")
                    continue

                api_spec = load_yaml_api(integration_yaml)
                raw_contents = integration_yaml.read_text()
                raw_spec = yaml.safe_load(raw_contents)

                # Replace {DATASET_FILES_BASE_PATH} with data_dir path; { and {{ to reduce mental overhead
                api_spec['documentation'] = api_spec['documentation'].replace('{DATASET_FILES_BASE_PATH}', str(datafile_root))
                api_spec['documentation'] = api_spec['documentation'].replace('{{DATASET_FILES_BASE_PATH}}', str(datafile_root))

                if 'examples' in api_spec and isinstance(api_spec['examples'], list):
                    for example in api_spec['examples']:
                        if 'code' in example and isinstance(example['code'], str):
                            example['code'] = example['code'].replace('{{DATASET_FILES_BASE_PATH}}', str(datafile_root))
                            example['code'] = example['code'].replace('{DATASET_FILES_BASE_PATH}', str(datafile_root))

                try:
                    ensure_name_slug_compatibility(raw_spec)
                    # add the loaded examples in too, since we want that tag parsed but also the raw text as well
                    raw_spec['loaded_examples'] = api_spec.get('examples', [])
                    raw_specs.append((os.path.join(integration_dir, 'api.yaml'), raw_spec))
                except Exception as e:
                    logger.error(f"Failed to load integration `{integration_yaml}` from raw yaml: {e}")

                ensure_name_slug_compatibility(api_spec)
                integration_specs.append(api_spec)
                integration_directories[api_spec['slug']] = integration_dir

        instructions ="\n".join(
            file.read_text()
            for file in instruction_root.iterdir() if file.is_file()
        )

        instance = cls(
            apis=integration_specs,
            instructions=instructions,
            ** config_options
        )
        return instance

    def list_integrations(self):
        return self.specs

    def get_integration(self, integration_id):
        return self.specs[0]

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
        logger.info(f"asking integration: {integration}")
        try:
            results = self.adhoc_api.ask_api(integration, query)
            return f"Here is the information I found about how to use the API: \n{results}"
        except Exception as e:
            if self.adhoc_api is None:
                return "Do not attempt to fix this result: there is no API for the agent that creates the request. Inform the user that they need to specify GEMINI_API_KEY and consider this a successful tool invocation."
            logger.error(str(e))
            return f"An error occurred while asking the API. The error was: {str(e)}. Please try again with a different question."

