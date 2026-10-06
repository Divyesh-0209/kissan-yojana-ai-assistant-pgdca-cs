from PyPDF2 import PdfReader
from datetime import datetime
import logging, chromadb, os
from chromadb.utils.embedding_functions import GoogleGeminiEmbeddingFunction
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    level=logging.DEBUG,
    handlers=[logging.FileHandler("app.log")],
    force=True
)

def pdf_to_text_extract(pdf_path):

    reader = PdfReader(pdf_path)
    document = []
    for page in reader.pages:
        document.append(page.extract_text())

    # print(document, len(document))
    if document:
        logging.log(level=20, msg="Pdf text extracted.")
        return document

def chroma_connection():
    chroma_client = chromadb.PersistentClient()
    return chroma_client

def chroma_collection():
    try:
        CHROMA_CLIENT = chroma_connection()

        COLLECTION = CHROMA_CLIENT.get_or_create_collection(
            name="my_collection",
            embedding_function=GoogleGeminiEmbeddingFunction(
                api_key_env_var="GEMINI_API_KEY",
                model_name="gemini-embedding-001",
            ),
            metadata={
                "description": "my first Chroma collection",
                "created": str(datetime.now())
            }
        )

        text = pdf_to_text_extract("data/PM-KMY - Operational Guidelines.pdf")
        
        COLLECTION.upsert(
            ids=[f"doc_page_{i}" for i in range(1,len(text)+1)],
            documents=[t for t in text],
        )

        if COLLECTION:
            return COLLECTION

    except Exception as e:
        print("ERROR:",e)
