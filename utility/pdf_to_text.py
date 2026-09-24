from PyPDF2 import PdfReader
import logging

logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    level=logging.DEBUG,
    handlers=[logging.FileHandler("app.log")],
    force=True
)

def pdf_to_text_extract(pdf_path):

    reader = PdfReader(pdf_path)
    number_of_pages = len(reader.pages)
    page = reader.pages[0]
    text = page.extract_text()
    if text:
        logging.log(level=20, msg="Pdf text extracted.")
        return text