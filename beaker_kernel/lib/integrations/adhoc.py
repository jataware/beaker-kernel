import logging
import os
import yaml
from pathlib import Path
from typing import Optional

from archytas.tool_utils import tool, AgentRef, LoopControllerRef, ReactContextRef
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

If you are asked to query for something specific, e.g. a study, you MUST provide the relevant `id` as part of the goal if you have access to it.
Most APIs allow you to easily query by `id` so this is often possible to utilize.
For example, if you are asked to find a dataset and you have the `id` of the dataset, you should provide that in the goal.
Be as SPECIFIC as possible as this will help you get a more accurate and timely result. Do not be vague, provide
VERBOSE goals so that the drafter of the code has all the information needed to do their job.

You must never reference code that has already been run since the drafter does not have awareness of that information. For example, don't set as the goal:
"Run the previous code but modify it to do X"; you must provide that code in the goal if you want it to be utilized.

The code that is drafted will generally be a complete, small program including relevant imports and other boilerplate code. Much of this
may already be implemented in the code you have run previously; if that is the case you should not repeat it. Feel free to streamline the code
generated by removing any unnecessary steps before sending it to the `BiomeAgent__run_code` tool.

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
