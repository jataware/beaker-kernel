from dataclasses import dataclass, field
from typing import Optional, Any, Self

WORKFLOW_PREAMBLE_PROMPT="""
You are given a few preselected workflows and processes to work through.

A workflow is a commonly grouped set of tasks to solve an end-to-end problem.

Workflows are divided into STAGES that contain STEPS.

CRITICAL: at the end of each STAGE, you must use the "mark_workflow_stage" tool and you must show the results of each STAGE to the user and then ask them to confirm to continue.

CRITICAL: after the user confirms to start the next STAGE, use the "mark_workflow_stage" tool to communicate that the stage is in progress.

CRITICAL: do not ever use assumed or example data if data is not available; stop and inform the user and ask how to proceed.

When a user asks for something that aligns with a given workflow, you will communicate that it is within your skillset and show them the to-do list that you will work through, letting the user inspect it and okay it before performing the steps in sequence. As you finish each major STAGE, allow the user to confirm with proceeding until it is done.

You will present the workflow as a markdown-formatted list, with empty checkboxes for the things you have not done, and checked boxes for the things you have. You will refer back to the to-do list as you work through the workflow and handle each STAGE and STEP within the STAGES.

ONE workflow will be ACTIVE and currently ready for use. The others may replace the ACTIVE workflow if the user requests, through the `attach_workflow` tool.

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

    @staticmethod
    def from_yaml(source: dict[str, Any]) -> "WorkflowStage":
        return WorkflowStage(
            name=source["name"],
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

    @staticmethod
    def from_yaml(source: dict[str, Any]) -> "Workflow":
        stages = [WorkflowStage.from_yaml(stage) for stage in source.get("stages", [])]
        return Workflow(
            title=source["title"],
            agent_description=source["agent_description"],
            human_description=source["human_description"],
            example_prompt=source["example_prompt"],
            stages=stages,

            hidden=source.get("hidden", None),
            category=source.get("category", None),
            is_context_default=source.get("is_context_default", False),
            metadata=source.get("metadata", {}),
        )

    # text representation of the prompt itself, fed directly into the agent.
    def to_prompt(self) -> str:
        return "\n\n".join(
            [
                (f"{stage.name}:\n" + ('\n'.join([step.prompt for step in stage.steps])))
                for stage in self.stages
            ]
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
