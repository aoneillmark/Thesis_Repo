# from typing import List, Dict, Tuple
# from openai import OpenAI
# from tenacity import retry, wait_random_exponential, stop_after_attempt
# from .models import ModelBase


# @retry(wait=wait_random_exponential(min=1, max=10), stop=stop_after_attempt(5))
# def gpt_chat(
#         client: OpenAI,
#         model: str,
#         messages: List[Dict],
#         tools: List[Dict] = [],
#         max_tokens: int = 1024,
#         stop_strs: List[str] = [],
#         temperature: float = 0.8
# ) -> Dict:
#     args = dict(
#         model=model,
#         messages=messages,
#         max_tokens=max_tokens,
#         temperature=temperature,
#         top_p=0.95,
#         stop=stop_strs
#     )
#     if len(tools) > 0:
#         args['tools'] = tools

#     response = client.chat.completions.create(**args)

#     prompt_tokens = response.usage.prompt_tokens
#     completion_tokens = response.usage.completion_tokens

#     return {
#         'output': response.choices[0].message.content,
#         'message': response.choices[0].message.model_dump(),
#         'tokens_count': {
#             'prompt_tokens': prompt_tokens,
#             'completion_tokens': completion_tokens
#         }
#     }



# @retry(wait=wait_random_exponential(min=10, max=20), stop=stop_after_attempt(10))
# def gpt_embed(
#         client: OpenAI,
#         model: str,
#         input: str
# ) -> Dict:
#     response = client.embeddings.create(
#         input=input,
#         model=model
#     )
#     prompt_tokens = response.usage.prompt_tokens
#     total_tokens = response.usage.total_tokens

#     return {
#         'output': response.data[0].embedding,
#         'tokens_count': {
#             'prompt_tokens': prompt_tokens,
#             'completion_tokens': total_tokens
#         }
#     }


# class APIModels(ModelBase):
#     def __init__(self, name: str, model_path: str = 'gpt-3.5-turbo', **args):
#         self.name = name
#         self.model_path = model_path
#         self.client = OpenAI(**args)

#     def generate_chat(
#             self,
#             messages: List[Dict],
#             tools: List[Dict] = [],
#             max_tokens: int = 1024,
#             stop_strs: List[str] = [],
#             temperature: float = 0.8
#     ) -> Dict:
#         return gpt_chat(
#             client=self.client,
#             model=self.model_path,
#             messages=messages,
#             tools=tools,
#             max_tokens=max_tokens,
#             stop_strs=stop_strs,
#             temperature=temperature
#         )

#     def generate_embed(
#             self,
#             input: str,

#     ) -> Dict:
#         return gpt_embed(
#             client=self.client,
#             model=self.model_path,
#             input=input
#         )


# import os
# from typing import List, Dict
# from mistralai import Mistral
# from tenacity import retry, wait_random_exponential, stop_after_attempt
# from .models import ModelBase
# from dotenv import load_dotenv

# load_dotenv()


# @retry(wait=wait_random_exponential(min=1, max=10), stop=stop_after_attempt(5))
# def mistral_chat(
#     client: Mistral,
#     model: str,
#     messages: List[Dict],
#     max_tokens: int = 1024,
#     temperature: float = 0.8
# ) -> Dict:
#     response = client.chat.complete(
#         model=model,
#         messages=messages,
#         max_tokens=max_tokens,
#         temperature=temperature
#     )

#     return {
#         'output': response.choices[0].message.content,
#         'message': response.choices[0].message.model_dump(),
#         'tokens_count': {
#             'prompt_tokens': response.usage.prompt_tokens,
#             'completion_tokens': response.usage.completion_tokens
#         }
#     }


# @retry(wait=wait_random_exponential(min=10, max=20), stop=stop_after_attempt(10))
# def mistral_embed(
#     client: Mistral,
#     model: str,
#     input: str
# ) -> Dict:
#     response = client.embeddings.create(
#         input=input,
#         model=model
#     )

#     return {
#         'output': response.data[0].embedding,
#         'tokens_count': {
#             'prompt_tokens': response.usage.prompt_tokens,
#             'completion_tokens': response.usage.total_tokens
#         }
#     }


# class APIModels(ModelBase):
#     def __init__(self, name: str, model_path: str = 'ministral-3b-latest', **args):
#         self.name = name
#         self.model_path = model_path

#         # Pop api_key and base_url from args if present
#         api_key = args.pop("api_key", None)
#         # base_url = args.pop("base_url", None)

#         self.client = Mistral(api_key=api_key, ) # not including base_url or **args

#     def generate_chat(
#         self,
#         messages: List[Dict],
#         max_tokens: int = 1024,
#         temperature: float = 0.8
#     ) -> Dict:
#         return mistral_chat(
#             client=self.client,
#             model=self.model_path,
#             messages=messages,
#             max_tokens=max_tokens,
#             temperature=temperature
#         )

#     def generate_embed(
#         self,
#         input: str
#     ) -> Dict:
#         return mistral_embed(
#             client=self.client,
#             model=self.model_path,
#             input=input
#         )

import os
from typing import List, Dict
from tenacity import retry, wait_random_exponential, stop_after_attempt
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from .models import ModelBase


@retry(wait=wait_random_exponential(min=1, max=10), stop=stop_after_attempt(5))
def local_chat(
    model,
    tokenizer,
    messages: List[Dict],
    max_tokens: int = 1024,
    temperature: float = 0.8
) -> Dict:
    # Format messages with Qwen-specific chat template and thinking mode
    input_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False
    )
    inputs = tokenizer([input_text], return_tensors="pt").to(model.device)

    # Generate response
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=temperature > 0.0,
            top_p=0.95,
            top_k=50,
            repetition_penalty=1.1,
            pad_token_id=tokenizer.eos_token_id,
        )

    generated_ids = outputs[0][inputs["input_ids"].shape[1]:].tolist()

    # Attempt to split thinking and actual answer
    try:
        end_think_token = tokenizer.convert_tokens_to_ids("</think>")
        split_index = len(generated_ids) - generated_ids[::-1].index(end_think_token)
    except ValueError:
        split_index = 0

    thinking_content = tokenizer.decode(generated_ids[:split_index], skip_special_tokens=True).strip()
    response_text = tokenizer.decode(generated_ids[split_index:], skip_special_tokens=True).strip()

    return {
        'output': response_text,
        'message': {"role": "assistant", "content": response_text},
        'tokens_count': {
            'prompt_tokens': inputs["input_ids"].shape[1],
            'completion_tokens': len(generated_ids)
        },
        'thinking': thinking_content  # Optional: can be used or ignored by your pipeline
    }


class APIModels(ModelBase):
    def __init__(self, name: str, model_path: str = '/vol/bitbucket/mo1024/models/qwen3-1.7b', **args):
        self.name = name
        self.model_path = model_path

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map="auto",
            torch_dtype="auto",
            trust_remote_code=True
        )

    def generate_chat(
        self,
        messages: List[Dict],
        max_tokens: int = 1024,
        temperature: float = 0.8
    ) -> Dict:
        return local_chat(
            model=self.model,
            tokenizer=self.tokenizer,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

    def generate_embed(self, input: str) -> Dict:
        raise NotImplementedError("Embedding is not supported with this local model.")
