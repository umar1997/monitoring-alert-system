import re

import os
import aiofiles
from jinja2 import Environment, FileSystemLoader, Template

from utilities.async_utils import async_post_api

async def create_prompt(config, extracted_text, check_type):
    # template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'prompts/{check_type}.txt')
    template_path = os.path.join(config["current_working_dir"], f'prompts/{check_type}.txt')
    async with aiofiles.open(template_path, mode='r') as file:
        template_content = await file.read()
    
    template = Template(template_content)
    context = {'input_text': extracted_text}
    prompt = template.render(context)
    return prompt


async def model_generate(prompt, api_endpoint, model_name, model_api, max_tokens=60, temperature=0, stop=None):
    url = f"{api_endpoint}/chat/completions" if model_api == "chat" else f"{api_endpoint}/completions"
    headers = {
        "Content-Type": "application/json"
    }
    if model_api == "chat":
        # system_prompt = "You are a helpful biomedical assistant tasked with evaluating parsed text."
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
    response = await async_post_api(request_url=url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json(), model_api
    else:
        print(f"Custom Error in func(model_generate) {response.status_code}")
        return None, model_api


def postprocess(response, chat_type):
    if chat_type == "chat":
        try:
            resp = response["choices"][0]["message"]["content"]
        except:
            resp = ""
    else:
        try:
            resp = response["choices"][0]["text"]
        except:
            resp = ""
    return resp

def count_tokens(text, word=True):
    if word:
        tokens = re.findall(r'\w+|\W', text)
        tokens = [token for token in tokens if not token.isspace()]
        return len(tokens)
    else:
        return int(len(text)/4)