from dataclasses import dataclass
from datetime import datetime
from typing import Any
from enum import Enum
import asyncio

from archytas.agent import Agent

OUTPUT_CHAR_LIMIT = 1000

class SummarizationLevel(int, Enum):
    SENTENCE = 1
    PARAGRAPH = 2
    LONG = 3 

    @classmethod
    def get_prompt(cls, level: "SummarizationLevel") -> str:
        if level == cls.SENTENCE:
            return "The summary should be a single sentence"
        if level == cls.SENTENCE:
            return "The summary should be a single paragraph"
        else:
            return "If needed, the summary may be multiple paragraphs long"


@dataclass
class IBeakerHistoryEvent:
    kernel_id: str | None
    kernel_slug: str | None
    context_slug: str | None
    creation_time: datetime | None

@dataclass
class IBeakerHistoryExecutionEvent(IBeakerHistoryEvent):
    cell_id: str
    execution_id: int
    source: str | list[str]
    result: Any
    stdin: str | list[str]
    stderr: str
    success: bool = True
    execution_time: datetime | None = None
    execution_duration: float | None = None
    silent: bool = False

@dataclass
class IBeakerHistoryQueryEvent(IBeakerHistoryEvent):
    cell_id: str
    prompt: str
    source: str | list[str]
    thoughts: list[str]
    result: str
    execution_time: datetime | None = None
    execution_duration: int | None = None

BeakerHistoryEvent = IBeakerHistoryExecutionEvent | IBeakerHistoryQueryEvent;

class IBeakerHistory:
    session_id: str = ""
    events: list[BeakerHistoryEvent] = []
    original_notebook: dict | None = None # TODO: Remove

    async def summarize(self, level: SummarizationLevel = SummarizationLevel.SENTENCE, use_notebook: bool = False) -> str:
        agent = Agent()
        prompt = "Here is the history of a user's interaction with an LLM-powered notebook: \n\n"
        mark_na = lambda x: x if x is not None else "N/A"
        if not use_notebook:
            for event in self.events:
                if isinstance(event, IBeakerHistoryExecutionEvent):
                    prompt += f"Code Execution Event: \n"
                    prompt += f"\tSource Code: {event.source} \n"
                    prompt += f"\tResult: {str(event.result)[:OUTPUT_CHAR_LIMIT]} \n"
                    prompt += f"\tExecution Time: {mark_na(event.execution_time)} \n"
                    prompt += f"\tExecution Duration: {mark_na(event.execution_duration)} \n"
                elif isinstance(event, IBeakerHistoryQueryEvent):
                    prompt += f"Query Event: {event.cell_id} \n"
                    prompt += f"\tPrompt: {event.prompt} \n"
                    prompt += f"\tThoughts: {event.thoughts} \n"
                    prompt += f"\tResult: {event.result} \n"
                    prompt += f"\tExecution Time: {mark_na(event.execution_time)} \n"
                    prompt += f"\tExecution Duration: {mark_na(event.execution_duration)} \n"
                else: # TODO: Add support for `raw` and `markdown` cells once they exist
                    continue
        else:
            prompt += f"The histroy is this notebook: {self.original_notebook} \n"
        query = ( "Please summarize the events in this history. "
                  "The summary doesn't need to include detail that this was done in an LLM-powered notebook. " 
                  f"{SummarizationLevel.get_prompt(level)}")
        response = await agent.oneshot(prompt, query)
        return response
    
    @classmethod
    def from_notebook(cls, notebook: dict) -> "IBeakerHistory":
        # Trim notebook. This may be removed in the future since we will likely stop saving the notebook to the history
        for cell in notebook["cells"]:
            if "outputs" in cell and len(cell["outputs"]) > 0:
                for output in cell["outputs"]:
                    if "data" in output:
                        for data_type in output["data"]:
                            output["data"][data_type] = output["data"][data_type][:OUTPUT_CHAR_LIMIT]
        
        history = cls()
        history.original_notebook = notebook
        for cell in notebook["cells"]:
            general_args = {
                "kernel_id" : None,
                "kernel_slug" : None,
                "context_slug" : None,
                "creation_time" : None
            }
            cell_type = cell["metadata"].get("beaker_cell_type", cell["cell_type"])
            if cell_type == "code":
                event = IBeakerHistoryExecutionEvent(
                    **general_args,
                    cell_id = cell["id"],
                    # NOTE: `execution_count` isn't used. The frontend wil manage cell order in the future anyway
                    execution_id = cell["execution_count"],
                    source = cell["source"],
                    result = cell.get("outputs", []),
                    stdin = cell.get("stdin", ""),
                    stderr = cell.get("stderr", "")
                )
            elif cell_type == "query":
                if len(cell["metadata"]["events"]) == 0:
                    result = None
                else:
                    final_event = cell["metadata"]["events"][-1]
                    result = final_event["content"] if final_event["type"] == "response" else None
                event = IBeakerHistoryQueryEvent(
                    **general_args,
                    cell_id = cell["id"],
                    prompt = cell["metadata"]["prompt"],
                    source = cell["source"],
                    thoughts = cell["metadata"]["events"],
                    result = result,
                )
            else: # NOTE: `markdown` and `raw` cells don't exist in history type
                continue
            history.events.append(event)
        return history
