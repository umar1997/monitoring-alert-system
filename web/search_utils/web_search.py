import json
import httpx
import asyncio

import pandas as pd

from web.search_utils.scrape_data import ScrapeWebText, CreateChunks

from utilities.timer import Timer
from utilities.async_utils import async_get_api
timer = Timer()


class BingSearchClient:
    def __init__(self, 
            subscription_key, 
            custom_config_id, 
            bing_url,
        ):
        self.subscription_key = subscription_key
        self.custom_config_id = custom_config_id
        self.bing_url = bing_url

    def postprocess_response(self, response):
        empty_df = pd.DataFrame([], columns=['name', 'url', 'published_date', 'snippet', "text"])
        try:
            if response.status_code == 200:
                response = json.loads(response.text)
                response = response["webPages"]["value"]
                website_response = [{
                        "name": resp["name"] if "name" in resp else "",
                        "url": resp["url"] if "url" in resp else "",
                        "published_date": resp["datePublishedDisplayText"] if "datePublishedDisplayText" in resp else "",
                        "snippet": resp["snippet"] if "snippet" in resp else "",
                        "text": ""
                    } for resp in response]
                df = pd.DataFrame(website_response, columns=['name', 'url', 'published_date', 'snippet', "text"])
                return df
            else:
                print(f"Custom Error: func(postprocess_response) - Request failed with status code: {response.status_code}")
                return empty_df
        except Exception as e:
            print(f"Custom Exception func(postprocess_response): {e}")
            return empty_df

    async def web_search(self, query_text, sites):
        if isinstance(sites, str):
            query = f"{query_text} site:{sites}"
        else:
            query = "(" + " OR ".join([f"site:{site}" for site in sites]) + ")" + f" {query_text}"
        params = {
            "q": query,
            "customconfig": self.custom_config_id,
            "mkt": "en-US"
        }
        headers = {
            "Ocp-Apim-Subscription-Key": self.subscription_key
        }
        response = await async_get_api(request_url=self.bing_url, headers=headers, params=params)
        response = self.postprocess_response(response)
        return response
    
    async def execute_retrieve(self, query_text, site_name, top_k=5):  
        try:
            with timer("RetrieveWebSearch"):
                response = await self.web_search(query_text, site_name)
            
            response = response[:top_k]
            result = []
            if not response.empty:
                df_list = []
                tasks = []
                with timer("ScrapeWebSearch"):
                    for _, site_response in response.iterrows():
                        scrape_task = asyncio.create_task(ScrapeWebText().execute_scrape(site_response['url']))
                        tasks.append(scrape_task)
                    scraped_texts = await asyncio.gather(*tasks)
                
                with timer("SimilarContext"):
                    for (_, site_response), scraped_text in zip(response.iterrows(), scraped_texts):
                        chunked_text = CreateChunks().similar_context_from_snippet(scraped_text, site_response["snippet"])
                        site_resp = {
                            'name': site_response['name'], 
                            'url': site_response['url'], 
                            'published_date': site_response['published_date'],
                            'snippet': site_response['snippet'], 
                            'chunk': chunked_text
                        }
                        result.append(site_resp)
                    result = result[:top_k]
########################################## Chunking + Cosine 
                # with timer("ChunkingWebText"):
                #     for (_, site_response), scraped_text in zip(response.iterrows(), scraped_texts):
                #         chunks = CreateChunks().chunk_web_text(scraped_text)
                #         site_chunks = [{
                #             'name': site_response['name'], 
                #             'url': site_response['url'], 
                #             'published_date': site_response['published_date'],
                #             'snippet': site_response['snippet'], 
                #             'chunk': chunk
                #         } for chunk in chunks]
                #         df_list += site_chunks

                # with timer("RetreiveSimilarTexts"):
                #     df = pd.DataFrame(pd.concat([pd.DataFrame(df_list)]))
                #     chunked_text = df['chunk'].tolist()
                #     similar_texts = TextSimilarity(self.embedding_api_endpoint, self.embedding_model_name)
                #     top_k_indices, top_k_similarities = await similar_texts.execute_text_similarity(query_text, chunked_text, top_k)
                
                # with timer("ResponseFormat"):
                #     df_top_k = df.loc[top_k_indices]
                #     if len(df_top_k) == len(top_k_similarities):
                #         df_top_k['score'] = top_k_similarities
                #     result = df_top_k.to_dict(orient='records')
########################################## End
            else:
                result = []
            with timer("RetrieveReturn"):
                return result
        except Exception as e:
            print(f"Custom Exception (execute_retrieve): {e}")
            return []