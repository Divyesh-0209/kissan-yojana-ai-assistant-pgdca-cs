from flask import Flask,render_template,jsonify,request
from ai_services.gemini_api import generate_answer
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    user_data = request.get_json()
    user_message = user_data.get('message', '')
    answer=generate_answer(user_message)
    return jsonify({'reply': answer})

if __name__=='__main__':
    app.run()