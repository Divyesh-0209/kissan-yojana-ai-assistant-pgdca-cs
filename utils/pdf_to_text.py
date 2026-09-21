from PyPDF2 import PdfReader


def pdf_to_text_extract(pdf_path):

    reader = PdfReader(pdf_path)
    number_of_pages = len(reader.pages)
    page = reader.pages[0]
    text = page.extract_text()
    return text