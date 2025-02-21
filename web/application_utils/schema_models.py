from typing import Optional
from typing import List, Dict
from pydantic import BaseModel, Field

class WebSearchModel(BaseModel):
    query_text:  str = Field(default="What are the symptoms of diabetes?")
    # sites: List[str] = Field(default=["pubmed.ncbi.nlm.nih.gov", "webmd.com"])
    sites: Optional[List[str]] = Field(default=["pubmed.ncbi.nlm.nih.gov", "webmd.com", "drugs.com", "cdc.gov", "fda.gov"])
    context_window: Optional[int] = Field(default=2)
    top_k: Optional[int] = Field(default=3)

# curl -X GET "https://api.bing.microsoft.com/v7.0/custom/search" \
# -H "Ocp-Apim-Subscription-Key: 329eeed01867475da7391cdd759cfba6" \
# -G \
# --data-urlencode "q=What are the side effects of Insulin Glargine (Lantus)? site:drugs.com" \
# --data-urlencode "customconfig=a409a970-23ac-49c3-9f11-2b7dd3d7262c" \
# --data-urlencode "mkt=en-US"