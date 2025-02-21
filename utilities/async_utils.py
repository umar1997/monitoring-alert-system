import httpx 

async def async_post_api(request_url, headers, data=None):
    timeout = httpx.Timeout(3 * 3600)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response_ = await client.post(
                url=request_url,
                headers=headers,
                json=data 
            )
            await client.aclose()
            response_.raise_for_status()
            return response_
    except httpx.HTTPStatusError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as e:
        print(f"Custom Exception func(fetch_embeddings_async): {e}")
        return []
    
async def async_post_api_data(request_url, headers, data=None):
    timeout = httpx.Timeout(3 * 3600)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response_ = await client.request(
                method='post',
                url=request_url,
                headers=headers,
                data=data 
            )
            await client.aclose()
            return response_
    except Exception as e:
        print(f"Custom Exception func(async_post_api): {e}")
        return []
    
async def async_post_api_files(request_url, headers, files):
    timeout = httpx.Timeout(3 * 3600)
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            response_ = await client.post(
                url=request_url,
                headers=headers,
                files=files 
            )
            return response_
    except Exception as e:
        print(f"Custom Exception func(async_post_api): {e}")
        return []
    
async def async_get_api(request_url, headers, params=None):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response_ = await client.request(
                method='get',
                url=request_url,
                headers=headers,
                params=params 
            )
            await client.aclose()
            return response_
    except Exception as e:
        print(f"Custom Exception func(async_get_api): {e}")
        return []