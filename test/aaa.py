# import google.generativeai as genai
# from dotenv import load_dotenv
# import os

# # Load environment and configure
# load_dotenv()
# try:
#     genai.configure(api_key=os.environ["GEMINI_API_KEY"])
#     print("✅ API key loaded successfully")
# except KeyError:
#     print("❌ Error: GEMINI_API_KEY environment variable not set.")
#     exit()

# # Initialize the model (same as in utils.py)
# # model = genai.GenerativeModel('models/gemini-2.5-flash-lite-preview-06-17')
# model = genai.GenerativeModel('gemini-2.5-flash')


# def test_basic_ping():
#     """Simple ping test"""
#     print("🚀 Testing basic model response...")
    
#     prompt = "Hello! Please respond with 'Model is working correctly' followed by a simple Prolog fact."
    
#     try:
#         response = model.generate_content(prompt)
#         print(f"✅ Response received:")
#         print(f"Text: {response.text}")
#         print("-" * 50)
#         return True
#     except Exception as e:
#         print(f"❌ Error: {e}")
#         return False

# def test_prolog_generation():
#     """Test Prolog code generation"""
#     print("🔧 Testing Prolog generation...")
    
#     prompt = """
#     Generate a simple Prolog rule that defines eligibility for a service.
#     The rule should check if a person is over 18 years old.
#     Return only the Prolog code without explanation.
#     """
    
#     try:
#         response = model.generate_content(prompt)
#         print(f"✅ Prolog Response:")
#         print(response.text)
#         print("-" * 50)
#         return True
#     except Exception as e:
#         print(f"❌ Error: {e}")
#         return False

# def test_model_info():
#     """Test model information"""
#     print("ℹ️  Model Information:")
#     print(f"Model name: {model.model_name}")
#     print("-" * 50)

# if __name__ == "__main__":
#     print("🚀 Direct LLM Model Testing...")
#     print("=" * 60)
    
#     test_model_info()
    
#     success1 = test_basic_ping()
#     success2 = test_prolog_generation()
    
#     if success1 and success2:
#         print("✅ All tests passed! Your LLM setup is working correctly.")
#     else:
#         print("❌ Some tests failed. Check your configuration.")


# from google import genai
# from google.genai import types

# # The client gets the API key from the environment variable `GEMINI_API_KEY`.
# client = genai.Client()

# response = client.models.generate_content(
#     model="gemini-2.5-flash-lite", contents="Explain how AI works in a few words",
#     config=types.GenerateContentConfig(
#         thinking_config=types.ThinkingConfig(thinking_budget=512) # Disables thinking
#     ),
# )
# print(response.text)