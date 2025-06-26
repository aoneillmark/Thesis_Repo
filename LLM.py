import os
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ["MISTRAL_API_KEY"]

client = Mistral(api_key=api_key)

model = "ministral-3b-latest"

def generate_response_with_LLM(text: str):
    message = [
        {
            "role": "user", 
            "content": f"{text}"
        }
    ]

    chat_response = client.chat.complete(
        model=model,
        messages=message
    )
    
    return (chat_response.choices[0].message.content)