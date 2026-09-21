from flask import Flask,render_template,jsonify,request
from ai_services.gemini_api import generate_answer
from utils.pdf_to_text import pdf_to_text_extract
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    user_data = request.get_json()
    user_message = user_data.get('message', '')

    text=pdf_to_text_extract("data/Python.pdf")
    print(text)
    answer=generate_answer(user_message,text)
    return jsonify({'reply': answer})

if __name__=='__main__':
    app.run()