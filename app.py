from flask import Flask,render_template,jsonify,request
from ai_services.gemini_api import generate_answer
from utility.pdf_to_text import pdf_to_text_extract
import logging

logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    level=logging.DEBUG,
    handlers=[logging.FileHandler("app.log")],
    force=True
)

app = Flask(__name__)

@app.route('/')
def home():
    logging.log(level=20, msg="Chatbot Frontend Rendered")
    return render_template('index.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    user_data = request.get_json()
    user_message = user_data.get('message', '')

    text=pdf_to_text_extract("data/PM-KMY - Operational Guidelines.pdf")
    print(text)
    logging.log(level=20, msg="Pdf text extracted.")
    answer=generate_answer(user_message,text)
    if answer:
        logging.log(level=20, msg="Generated responnse passed.")
        return jsonify({'reply': answer})

if __name__=='__main__':
    app.run(debug=True)