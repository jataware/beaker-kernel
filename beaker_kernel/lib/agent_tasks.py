import asyncio
import json

from archytas.agent import Agent

OUTPUT_CHAR_LIMIT = 1000

async def summarize(notebook: dict,
    summary_types: tuple[str, ...] = (
        "a single sentence BLUF that must be in past tense",
        "a three sentence summary in active voice",
        "a third-person paragraph summary where the first sentence describes overall what was accomplished",
    )
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
Generate a list where each element summarizes a cell in the notebook provided above. Each summary must be in imperative
mood and past tense, e.g. "Loaded dataset of Indonesian population from 2003 to 2006".
    """
    history_response = await agent.oneshot(history_prompt, history_query)
    history = json.loads(history_response)

    summaries = {
        "history": history
    }
    for summary_type in summary_types:
        prompt = "You are going to write about this list of actions taken in order:\n"
        for event in history:
            prompt += f"\t- {event}\n"
        prompt += "\n"
        query = f"Produce a {summary_type}." 
        response = await agent.oneshot(prompt, query)
        summaries[summary_type] = response
    return summaries
