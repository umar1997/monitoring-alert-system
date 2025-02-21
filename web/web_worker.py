import os
import json
import time
import logging

import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import (
    FastAPI, 
    APIRouter, 
    Request, 
    BackgroundTasks,
    UploadFile, 
    File, 
    Body, 
    Form
)
from fastapi.responses import StreamingResponse, JSONResponse

from utilities.timer import Timer
from utilities.utils import (
    load_configurations,
    calculate_time
)

from web.application_utils.configurations import (
    update_config_from_env
)
from web.application_utils.schema_models import WebSearchModel
from web.search_utils.web_search import BingSearchClient

timer = Timer()
logging.getLogger("httpx").setLevel(logging.WARNING)

class WebWorker:
    def __init__(
        self,
        cwd: str
    ):

        self.lock = asyncio.Lock()
        self.non_async_running = 0
        self.executor = ThreadPoolExecutor()

        self.cwd = cwd
        self.configurations = load_configurations(cwd)
        self.init_worker()

        self.config = self.configurations["web_configurations"]
        self.search_client = BingSearchClient(
                subscription_key= self.config["subscription_key"], 
                custom_config_id= self.config["custom_config_id"], 
                bing_url= self.config["bing_url"]
        )

    def init_worker(self):
        self.configurations = update_config_from_env(self.configurations)
        if not self.configurations:
            print("ERROR: Configurations not properly configured!.")
        else:
            print("SUCCESS: Configurations Added")

    async def execute_web_retrieve(self, request: WebSearchModel):
        
        ## For multiple sites together
        result = await self.search_client.execute_retrieve(query_text=request.query_text, site_name=request.sites, top_k=request.top_k)
        ## For multiple sites
        # tasks = [search_client.execute_retrieve(query_text=request.query_text, site_name=site_name, top_k=request.top_k) for site_name in request.sites]
        # result = await asyncio.gather(*tasks)
        ## For single sites
        # site_name = request.sites[0]
        # result = await search_client.execute_retrieve(query_text=request.query_text, site_name=site_name, top_k=request.top_k)
        response = {"query": request.query_text, "site": request.sites, "response": result}
        return response

    def chunks_and_urls(self, data):
        urls_string = "\nReference Links:\n" + "\n".join(item["url"] for item in data["response"])
        query_and_chunks = "Question: " + data["query"] + "?\nSnippets:" + " ".join(item["chunk"] for item in data["response"])
        return query_and_chunks, urls_string

# "pubmed" : "pubmed.ncbi.nlm.nih.gov",
# "nhs": "www.nhs.uk",
# "webmd": "www.webmd.com",
# "fda": "www.fda.gov",
# "clinicaltrials": "clinicaltrials.gov",
# "cdc": "www.cdc.gov"