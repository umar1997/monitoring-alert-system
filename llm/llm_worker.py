import os
import re
import json
import httpx
import requests
import aiofiles
from jinja2 import Template

from utilities.utils import (
    load_configurations,
    calculate_time
)

from llm.application_utils.configurations import (
    update_config_from_env
)

class LLMGenerator:
    def __init__(self,
            cwd
        ):
        self.cwd = cwd
        self.configurations = load_configurations(cwd)
        self.config = self.configurations["llm_configurations"]
        self.init_worker()

        headers = {
            "Content-Type": "application/json"
        }
        headers["Authorization"] = f'Bearer {self.config["api_key"]}' if self.config["api_key"] else None
        self.headers = headers

        self.api_config = {
            "api_endpoint": self.config["model_endpoint"],
            "model_name": self.config["model_name"],
            "model_api": "chat",
            "max_tokens": 2000,
            "temperature": 0,
            "stop": None
        }

    def init_worker(self):
        self.configurations = update_config_from_env(self.configurations)
        if not self.configurations:
            print("ERROR: Configurations not properly configured!.")
        else:
            print("SUCCESS: Configurations Added")

    async def execute_llm(self, extracted_text, check_type):
        formatted_prompt = await self.create_prompt(extracted_text, check_type)
        api_config = self.api_config
        response, chat_type = self.model_generate(formatted_prompt, **api_config)
        resp = self.postprocess(response, chat_type)
        return resp

    async def create_prompt(self, extracted_text, check_type):
        template_path = os.path.join(self.cwd, f'prompts/{check_type}.txt')
        async with aiofiles.open(template_path, mode='r') as file:
            template_content = await file.read()
        
        template = Template(template_content)
        context = {'input_text': extracted_text}
        prompt = template.render(context)
        return prompt
    
    def model_generate(self, prompt, api_endpoint, model_name, model_api, max_tokens=60, temperature=0, stop=None):
        url = f"{api_endpoint}/chat/completions" if model_api == "chat" else f"{api_endpoint}/completions"
        
        if model_api == "chat":
            content = prompt
            messages = [{"role": "user", "content": content}]
            data = {
                "model": model_name,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stop": stop
            }
        else:
            data = {
                "model": model_name,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stop": stop
            }
        
        response = requests.post(url, headers=self.headers, data=json.dumps(data))
        return response.json(), model_api
    
    async def post_embedding_api(request_url, headers, data):
        async with httpx.AsyncClient(timeout=10.0) as client:
            embedding_response = await client.request(
                method='post',
                url=request_url,
                headers=headers,
                json=data 
            )
            await client.aclose()
            return embedding_response

    def postprocess(self, response, chat_type):
        if chat_type == "chat":
            try:
                return response["choices"][0]["message"]["content"]
            except:
                return ""
        else:
            try:
                return response["choices"][0]["text"]
            except:
                return ""

    @staticmethod
    def count_tokens(text, word=True):
        if word:
            tokens = re.findall(r'\w+|\W', text)
            tokens = [token for token in tokens if not token.isspace()]
            return len(tokens)
        else:
            return int(len(text) / 4)


