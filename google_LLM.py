import google.generativeai as genai
import os
from dotenv import load_dotenv

# --- Configuration ---
# Load environment variables from .env file
load_dotenv()

try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    print("Error: GEMINI_API_KEY environment variable not set.")
    print("Please ensure you have a .env file with GEMINI_API_KEY=your_api_key")
    exit()

# print("Available models:")
# for model in genai.list_models():
#     print(model.name)

# ...existing code...
# --- Model Initialization ---
# model = genai.GenerativeModel('gemini-1.5-flash')
model = genai.GenerativeModel('models/gemini-2.5-flash-lite-preview-06-17') # RPM: 15, TPM: 250,000, RPD: 1,000

# --- Text Content ---
# This is from file `insurance_contract.txt`
with open("insurance_contract.txt", "r", encoding='utf-8') as file:
    text_content = file.read()

# --- Unguided Prolog Generation ---
with open("unguided_prolog_generation.txt", "r", encoding='utf-8') as file:
    unguided_prolog_generation = file.read().strip()

# --- Prompt Definition ---
# Create a clear and concise prompt for the AI.
prompt = f"""
- Instructions:
{unguided_prolog_generation}

- Insurance contract: {text_content}
"""

try:
    # --- Generate Content ---
    # Send the prompt to the model to generate the content.
    response = model.generate_content(prompt)

    # --- Output and Save ---
    # Extract the generated code from the response.
    prolog_code = response.text.strip()
    
    # Clean up the response to get just the code block
    if "```prolog" in prolog_code:
        prolog_code = prolog_code.split("```prolog\n")[1].split("\n```")[0]

    # Print the generated script to the console.
    print("--- Generated Prolog Script ---")
    print(prolog_code)
    print("-----------------------------\n")

    # Define the filename for the output script.
    filename = "hello_world.pl"

    # Save the generated code to a file.
    with open(filename, "w") as f:
        f.write(prolog_code)

    print(f"✅ Successfully saved the script to '{filename}'")
    print(f"To run it, use a Prolog interpreter like SWI-Prolog: swipl -s {filename}")

except Exception as e:
    print(f"An error occurred: {e}")