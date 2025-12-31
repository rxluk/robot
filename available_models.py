import google.generativeai as genai

GEMINI_API_KEY = ""
genai.configure(api_key=GEMINI_API_KEY)

# Liste os modelos disponíveis
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)