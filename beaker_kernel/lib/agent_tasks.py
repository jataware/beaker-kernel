import asyncio
import json

from archytas.react import ReActAgent

OUTPUT_CHAR_LIMIT = 1000

class Summarizer(ReActAgent):

    def __init__(
        self,
        notebook: dict = {},
        **kwargs,
    ):
        super().__init__(
            model="gpt-4-turbo-preview",
            # api_key=api_key,  # TODO: get this from configuration
            tools=[],
            verbose=False,
            spinner=None,
            rich_print=False,
            allow_ask_user=False,
            **kwargs
        )

        context = f"""
You are working to provide summaries of this provided LLM-Powered Beaker notebook:
```
{notebook}
```

Beaker notebooks are an extension of Jupyter Notebooks that supports a new subtype of
cell called a 'query' cell. This means that some markdown cells with the `beaker_cell_type`
of `query` contain the the user query, the agents thoughs and possibly the final response
of the agent. If a code cell has a parent_id, that means it was produced by the LLM Agent
in the parent query cell.
"""
        self.add_context(context)
        

async def summarize(notebook: dict,
    summary_types: tuple[str, ...] = (
        "a single sentence BLUF that must be in past tense",
        "a summary",
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
            
    agent = Summarizer(notebook)
    history_query = """
Generate a list of strings from the provided notebook where each string is a summary of an event. 
An event is either a single cell OR a parent query cell + a child code cell.
Each summary must be in imperative mood and past tense, e.g. "Loaded dataset of Indonesian population from 2003 to 2006".

Your final answer should be a JSON Array. Only respond with a JSON array. Do not include backticks '`' or extra text. 
"""
    history = await agent.react_async(history_query)

    summaries = {
        "history": history
    }
    for summary_type in summary_types:
        query = f"""
Produce a {summary_type} by following these steps:

Step 1: Generate a rough draft of {summary_type} by referencing the list of events previously generated.

Step 2: Rewrite the draft by reviewing details from the original notebook.

Step 4: Make the draft more concise by removing information the audience will already know. The information the audience
will already know is that this was a process done in a notebook and there was an interaction between a user and an agent.
Additionally, don't refer to a subject like "the team". The draft should strictly focus on the content of the notebook
and not infer an author.

Step 4: Rewrite the draft in needed to ensure that the grammatical mood, tense, etc is respected from the original
request.

Step 5: Return the final draft as the final answer.
""" 
        response = await agent.react_async(query)
        summaries[summary_type] = response
    return summaries
