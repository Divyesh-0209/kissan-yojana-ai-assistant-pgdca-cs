from flask import Flask,render_template,jsonify,request

app = Flask(__name__)

@app.route('/')
def home():
    # Renders the index.html page from the templates folder
    return render_template('index.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    # Extract the user's message from the incoming JSON body
    user_data = request.get_json()
    user_message = user_data.get('message', '')

    # --- CHATBOT CORE LOGIC GOES HERE ---
    # Replace this block with your actual NLP engine, rule-based dict, 
    # OpenAI API call, or Hugging Face library implementation.
    if "hello" in user_message.lower():
        bot_reply = "Hi there! Glad you reached out."
    elif "help" in user_message.lower():
        bot_reply = "Sure, I can assist you. What seems to be the issue?"
    else:
        bot_reply = f"I received your message: '{user_message}'. However, my AI brain is still evolving!"
    # -------------------------------------

    # Return the reply back to JavaScript as JSON
    return jsonify({'reply': bot_reply})

if __name__=='__main__':
    app.run()