
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()
def generate_answer(user_message,text):

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    prompt=f"""

    You have to generate answer from the given text {text} only.
    user question: {user_message}

    """

    response = client.interactions.create(
        model="gemini-3.7-flash",
        input=prompt,
    )
    return response.output_text