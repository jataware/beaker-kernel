from dataclasses import dataclass
from datetime import datetime
from typing import Any
from enum import Enum
import asyncio
import json

from archytas.agent import Agent

OUTPUT_CHAR_LIMIT = 1000

async def summarize(notebook: dict,
    summary_types=[
        "a single sentence BLUF in past tense imperative",
        "a three sentence summary",
        "a paragraph summary",
    ]
):
    for cell in notebook["cells"]:
        if "outputs" in cell and len(cell["outputs"]) > 0:
            for output in cell["outputs"]:
                if "text" in output:
                    output["text"] = output["text"][:OUTPUT_CHAR_LIMIT]
                if "traceback" in output:
                    del output["traceback"]
                if "data" in output:
                    for data_type in output["data"]:
                        output["data"][data_type] = output["data"][data_type][:OUTPUT_CHAR_LIMIT]
            
    agent = Agent()
    history_prompt = f"""
You will generate a JSON array containing summaries of the events from the LLM-powered notebook below.

Only respond with a JSON array. Do not include backticks '`' or extra text. 

{notebook}
"""

    history_query = """
Generate a list where each element is a summary of each event in an imperative mood, 
e.g. "Load dataset of Indonesian population from 2003 to 2006".
    """
    history_response = await agent.oneshot(history_prompt, history_query)
    history = json.loads(history_response)

    summaries = {
        "history": history
    }
    for summary_type in summary_types:
        prompt = "Here's a list of events that happened in a LLM-powered notebook:\n"
        for event in history:
            prompt += f"\t- {event}\n"
        prompt += "\n"
        query = f"Produce a {summary_type} of the list of events above." 
        response = await agent.oneshot(prompt, query)
        summaries[summary_type] = response
    return summaries
