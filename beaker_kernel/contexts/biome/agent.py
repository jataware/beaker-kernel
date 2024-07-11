import json
import logging
import re
import requests

from archytas.tool_utils import AgentRef, LoopControllerRef, tool

from beaker_kernel.lib.agent import BaseAgent
from beaker_kernel.lib.context import BaseContext


logger = logging.getLogger(__name__)

BIOME_URL = "http://biome_api.biome-beaker:8082"


class BiomeAgent(BaseAgent):
    """
    You are a chat assistant that helps the analyst user with their questions. You are running inside of the Analyst UI which is a chat application
    sitting on top of a Jupyter notebook. This means the user will not be looking at code and will expect you to run code under the hood. Of course,
    power users may end up inspecting the code you you end up running and editing it.

    You have the ability to look up information regarding the environment via the tools that are provided. You should use these tools whenever are not able to
    satisfy the request to a high level of reliability. You should avoid guessing at how to do something in favor of using the provided tools to look up more
    information. Do not make assumptions, always check the documentation instead of assuming.

    You are currently working in the Biome app. The Biome app is a collection of data sources where a data source is a profiled website targeted specifically
    at cancer research. The user can add new data sources or may ask you to browser the data sources and return relevant datasets or other info. An example
    of a flow could be looking through all the data sources, picking one, finding a dataset using the URL, and then finally loading that dataset into a pandas
    dataframe.
    """
    def __init__(self, context: BaseContext = None, tools: list = None, **kwargs):
        libraries = {
        }
        super().__init__(context, tools, **kwargs)


    @tool(autosummarize=True)
    async def search(self, query: str) -> list:
        """
        Search for data sources in the Biome app. Results will be matched semantically
        and string distance. Use this to find a data source. You don't need live
        web searches.

        Args:
            query (str): The query used to find the datasource.
        Returns:
            list: The data sources found ordered from most relevant to least relevant.
        """

        endpoint = f"{BIOME_URL}/sources"
        response = requests.get(endpoint, params={"query": query})
        raw_sources = response.json()['sources']
        sources = [
            # Include only necessary fields to ensure LLM context length is not exceeded.
            {
                "id": source["id"],
                "name": source["content"]["Web Page Descriptions"]["name"],
                "initials": source["content"]["Web Page Descriptions"]["initials"],
                "purpose": source["content"]["Web Page Descriptions"]["purpose"],
                "links": source["content"]["Information on Links on Web Page"],
                "base_url": source.get("base_url", None),
            } for source in raw_sources
        ]
        return str(sources)

    # TODO(DESIGN): Deal with long running jobs in tools
    #
    # Option 1: We can return the job id and the agent can poll for the result.
    # This will require a job status tool. Once the status is done, we can either
    # check the result if it's a query or check the data source if it's a scan.
    # This feels a bit messy though that the job creation has a similar return
    # output on queue but getting the result is very different for each job.
    #
    # Option 2: We can wait for the job and return it to the agent when it's done
    #
    # Option 3: We can maybe leverage new widgets in the Analyst UI??
    #

    # CHOOSING OPTION 2 FOR THE TIME BEING

    @tool()
    async def query_page(self, query: str, base_url: str) -> str:
        """
        Run a query over a *specific* source in the Biome app and return the results.
        Find the url from a data source by using `search` tool first and
        picking the most relevant one.

        Args:
            query (str): Query to run over the source.
            base_url (str): URL to run query over.
        Returns:
            str: The answer to the query running over the given url
        """
        response = requests.post( f"{BIOME_URL}/tasks/query", json={"user_task": query, "url": base_url})
        job_id = response.json()["job_id"]
        status = "queued"
        result = None
        while status == "queued" or status == "started":
            response = requests.get(f"{BIOME_URL}/tasks/{job_id}").json()
            status = response["status"]
            result = response["result"]["job_result"]
        if status != "finished":
            return f"Query failed to complete. Job {status}"
        return result["answer"]



    # @tool(autosummarize=True)
    # async def scan(self, base_url: str, agent:AgentRef, loop: LoopControllerRef) -> dict:
    #     """
    #     Profiles the given web page and adds it to the data sources in the Biome app.
    #     Note that this starts the scan job but does not wait for it to finish.

    #     Args:
    #         base_url (str): The url to scan and add to a data source.
    #     Returns:
    #         dict: The information about the scan job
    #     """

    #     url = f"{BIOME_URL}/tasks/scan"
    #     result = requests.post(url, json={"uris": [base_url]})
    #     return result.json()

    # @tool(autosummarize=True)
    # async def query(self, query: str, source_id: str, agent:AgentRef, loop: LoopControllerRef) -> str:
    #     """
    #     Run a query over a source in the Biome app and return the results.
    #     Note that this starts the query job but does not wait for it to finish.


    #     Args:
    #         query (str): Query to run over the source.
    #         source_id (str): Source to run query over.
    #     Returns:
    #         dict: The information about the query job
    #     """

    #     url = f"{BIOME_URL}/tasks/query"
    #     base_url = "TODO(IMPLEMENT): Use the source_id to get the base url"
    #     result = requests.post(url, json={"user_task": query, "url": base_url})
    #     return result.json()
