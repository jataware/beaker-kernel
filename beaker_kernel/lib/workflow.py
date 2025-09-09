from dataclasses import dataclass, field
from typing import Literal, Optional, Any, TypedDict

WORKFLOW_PREAMBLE_PROMPT="""

## Workflows
- You will be given a few preselected workflows and processes to work through.
- A workflow is a commonly grouped set of tasks to solve an end-to-end problem.
- ONE workflow will be ACTIVE and currently ready for use.
  - You may replace the ACTIVE workflow if the user requests a different workflow, through the `attach_workflow` tool.
- Workflows are divided into STAGES that contain STEPS.

- CRITICAL: at the end of each STAGE, you must use the "mark_workflow_stage" tool and you must show the results of each STAGE to the user and then ask them to confirm to continue.
- CRITICAL: after the user confirms to start the next STAGE, use the "mark_workflow_stage" tool to communicate that the stage is in progress.
- CRITICAL: do not ever use assumed or example data if data is not available; stop and inform the user and ask how to proceed.

- IMPORTANT: When using `ask_user` in a workflow, use the `workflow_confirmation` format.

- When a user asks for something that aligns with a given workflow, you will communicate that it is within your skillset
  - When starting a workflow, use the `display_workflow_panel` tool
  - Next, use the `ask_user` tool to ask them if this workflow looks correct and if they would like to start it.
    - The response to `ask_user` will be "continue", "cancel", or something else -- such as a similar investigation or retrying a step.
      - Proceed if they choose to continue.
      - Stop the workflow if they choose to cancel. It may be resumed later.
      - Doing what else the user request takes precedence over the workflow if they request something else.
  - As you finish each major STAGE, present your findings to the user and ask them if it is correct and if they would like to continue.
  - At any point, you may ask for clarification from the user.

The workflows you have to offer are as follows:

```
{workflow_synopsis}
```

- - -

The current ACTIVE workflow is

```
{attached_workflow}
```
"""

@dataclass(kw_only=True)
class WorkflowStep:
    prompt: str
    metadata: Optional[dict[str, Any]] = field(default_factory=lambda: {})

    @staticmethod
    def from_yaml(source: str | dict[str, Any]) -> "WorkflowStep":
        match source:
            case str():
                return WorkflowStep(prompt=source, metadata={})
            case dict():
                return WorkflowStep(prompt=source["prompt"], metadata=source.get("metadata", {}))


@dataclass(kw_only=True)
class WorkflowStage:
    name: str
    steps: list[WorkflowStep]
    metadata: Optional[dict[str, Any]] = field(default_factory=lambda: {})
    # human readable string describing the stage
    description: Optional[list[str]]

    @staticmethod
    def from_yaml(source: dict[str, Any]) -> "WorkflowStage":
        return WorkflowStage(
            name=source["name"],
            description=source.get("description", None),
            steps=[WorkflowStep.from_yaml(step) for step in source["steps"]],
            metadata=source.get("metadata", {})
        )


@dataclass(kw_only=True)
class Workflow:
    title: str
    agent_description: str
    human_description: str
    example_prompt: str
    stages: list[WorkflowStage]

    hidden: Optional[bool] = field(default=False)
    is_context_default: Optional[bool] = field(default=False)
    category: Optional[str] = field(default=None)
    metadata: Optional[dict[str, Any]] = field(default_factory=lambda: {})
    output_prompt: Optional[str] = field(default=None)

    @staticmethod
    def from_yaml(source: dict[str, Any]) -> "Workflow":
        import logging
        logger = logging.getLogger(__name__)
        
        stages = [WorkflowStage.from_yaml(stage) for stage in source.get("stages", [])]
        title = source["title"]
        output_prompt = source.get("output_prompt", None)
        
        logger.info(f"WORKFLOW LOAD: Loading workflow '{title}'")
        logger.info(f"WORKFLOW LOAD: output_prompt exists={output_prompt is not None}")
        if output_prompt:
            truncated_prompt = output_prompt[:150] + "..." if len(output_prompt) > 150 else output_prompt
            logger.info(f"WORKFLOW LOAD: output_prompt preview: {repr(truncated_prompt)}")
        else:
            logger.warning(f"WORKFLOW LOAD: output_prompt is None/empty for workflow '{title}'")
        
        return Workflow(
            title=title,
            agent_description=source["agent_description"],
            human_description=source["human_description"],
            example_prompt=source["example_prompt"],
            stages=stages,

            hidden=source.get("hidden", None),
            category=source.get("category", None),
            is_context_default=source.get("is_context_default", False),
            metadata=source.get("metadata", {}),
            output_prompt=output_prompt
        )

    # text representation of the prompt itself, fed directly into the agent.
    def to_prompt(self) -> str:
        return "\n\n".join(
            [
                (f"{stage.name}:\n" + ('\n'.join([step.prompt for step in stage.steps])))
                for stage in self.stages
            ]
        )


class WorkflowStageProgress(TypedDict):
    state: Literal['in_progress', 'finished']
    code_cell_id: str
    results_markdown: str


class WorkflowState(TypedDict):
    workflow_id: str
    progress: dict[str, WorkflowStageProgress | None]
    final_response: str

    @classmethod
    def from_workflow(cls, workflow_id: str, workflow: Workflow) -> "WorkflowState": # type: ignore
        return cls(
            workflow_id=workflow_id,
            progress={
                stage.name: None
                for stage in workflow.stages
            },
            final_response=""
        )


def create_available_workflows_prompt(
    workflows: list[Workflow],
    attached_workflow: Optional[Workflow] = None
) -> str:
    """
    Create a fully rendered prompt for the context based on a list of workflows and which,
    if any, of them is active.
    """
    workflow_synopsis = "\n\n".join([
        f"{workflow.title}: {workflow.agent_description}"
        for workflow in workflows
    ])

    return WORKFLOW_PREAMBLE_PROMPT.format(
        workflow_synopsis=workflow_synopsis,
        attached_workflow=(
            attached_workflow.to_prompt()
            if attached_workflow
            else "No active workflow selected."
        )
    )
