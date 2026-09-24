
from google import genai
from dotenv import load_dotenv
import os, logging

load_dotenv()

logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    level=logging.DEBUG,
    handlers=[logging.FileHandler("app.log")],
    force=True
)

def generate_answer(user_message,text):

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    prompt=f"""

    You have to generate answer from the given text {text} only.
    user question: {user_message}

    """

    response = client.interactions.create(
        system_instruction="You are a multi-lingual indic chatbot for indian farmers to assist them with the Indian government schemes related to farmers. You will be provided with the context to generate answer from, the prompt itself. You have to strictly generate answer from the given context in the prompt and not outside from that. If you don't find the answer inn the given context say 'No related data found in the context.",
        model="gemini-3.5-flash-lite",
        input=prompt,
    )
    logging.log(level=20, msg="Response genrated.")
    return response.output_text