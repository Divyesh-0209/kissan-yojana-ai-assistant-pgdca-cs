from flask import Flask,render_template,jsonify,request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    user_data = request.get_json()
    user_message = user_data.get('message', '')


    if "hello" in user_message.lower():
        bot_reply = "Hi there! Glad you reached out."
    elif "help" in user_message.lower():
        bot_reply = "Sure, I can assist you. What seems to be the issue?"
    else:
        bot_reply = f"I received your message: '{user_message}'. However, my AI brain is still evolving!"

    return jsonify({'reply': bot_reply})

if __name__=='__main__':
    app.run()