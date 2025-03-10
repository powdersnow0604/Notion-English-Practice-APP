from google import genai
import json

def generate_gemini_response(prompt, API_KEY):
    client = genai.Client(api_key=API_KEY)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )

    return response.text