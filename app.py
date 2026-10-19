from flask import Flask, render_template, jsonify, request
from ai_services.gemini_api import generate_answer, generate_answer_without_vectorsearch
import utility.pdf_to_text as pdf_reader
import logging, sqlite3, os

logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("app.log")],
    force=True
)

app = Flask(__name__)

DB_PATH = "chat_history.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT,
            sender TEXT,
            text TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

init_db()
try:
    CHROMA_COLLECTION = pdf_reader.chroma_collection()
    if CHROMA_COLLECTION == None or not  CHROMA_COLLECTION:
        raise Exception()
except Exception as e:
    print("[ERROR] Error in getting chroma_db collection (chroma_collection function):",e)
    logging.log(level=50, msg=f"Error in getting chroma_db collection (chroma_collection function): {e}")

@app.route('/')
def home():
    logging.log(level=20, msg="Chatbot Frontend Rendered")
    return render_template('index.html')

@app.route('/conversations', methods=['GET'])
def get_conversations():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title FROM conversations ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    conversations = [{'id': row[0], 'title': row[1]} for row in rows]
    return jsonify(conversations)

@app.route('/conversations', methods=['POST'])
def create_conversation():
    try:
        data = request.get_json() or {}
        conv_id = data.get('id')
        title = data.get('title', 'New Chat')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO conversations (id, title) VALUES (?, ?)', (conv_id, title))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'id': conv_id, 'title': title})
    except Exception as e:
        print("[ERROR] Error in creating conversation (creating_conversation function):",e)
        logging.log(level=50, msg=f"Error in creating conversation (creating_conversation function): {e}")

@app.route('/conversations/<conv_id>', methods=['GET'])
def get_conversation_messages(conv_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT sender, text, strftime("%H:%M", timestamp) FROM messages WHERE conversation_id = ? ORDER BY id ASC', (conv_id,))
    rows = cursor.fetchall()
    if len(rows)>0:
        last_msg=rows[len(rows)-1]
        if last_msg != 0 and last_msg[0] == "user":
            cursor.execute('DELETE FROM messages WHERE conversation_id = ? AND sender = "user" AND text = ?', (conv_id, last_msg[1],))
            conn.commit()
            try:
                response = get_response(message=last_msg[1], id=conv_id)
            except Exception as e:
                print("[ERROR] Error in response generation (get_response function):",e)
                logging.log(level=50, msg=f"Error in response generation (get_response function): {e}")

            if response and response != None:
                print("[INFO] Response received.")
            else:
                print("[ERROR] Response not received.")

            cursor.execute('SELECT sender, text, strftime("%H:%M", timestamp) FROM messages WHERE conversation_id = ? ORDER BY id ASC', (conv_id,))
            rows = cursor.fetchall()
    conn.close()
    messages = [{'sender': row[0], 'text': row[1], 'timestamp': row[2]} for row in rows]
    return jsonify(messages)

@app.route('/conversations/<conv_id>', methods=['DELETE'])
def delete_conversation(conv_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM messages WHERE conversation_id = ?', (conv_id,))
        cursor.execute('DELETE FROM conversations WHERE id = ?', (conv_id,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        print("[ERROR] Error in deleing conversation (delete_conversation function):",e)
        logging.log(level=50, msg=f"Error in deleing conversation (delete_conversation function): {e}")



@app.route('/get_response', methods=['POST'])
def get_response(message = None, id = None):
    
    if message != None and id != None:
        user_message = message
        conv_id = id

    else:
        user_data = request.get_json()
        user_message = user_data.get('message', '')
        conv_id = user_data.get('conversation_id', '')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Save user message
    cursor.execute('INSERT INTO messages (conversation_id, sender, text) VALUES (?, ?, ?)', (conv_id, 'user', user_message))
    conn.commit()

    # Update conversation title if it's the default or new
    cursor.execute('SELECT COUNT(*) FROM messages WHERE conversation_id = ? AND sender = "user"', (conv_id,))
    user_msg_count = cursor.fetchone()[0]
    if user_msg_count == 1:
        new_title = user_message[:25] + ('...' if len(user_message) > 25 else '')
        cursor.execute('UPDATE conversations SET title = ? WHERE id = ?', (new_title, conv_id))

    # Retrieve whole conversation history for context
    cursor.execute('SELECT sender, text FROM messages WHERE conversation_id = ? ORDER BY id ASC LIMIT 10', (conv_id,))
    history_rows = cursor.fetchall()
    conn.commit()
    conn.close()

    history_str = "\n".join([f"{sender.capitalize()}: {text}" for sender, text in history_rows])

    search_vector = generate_answer_without_vectorsearch(user_message)

    # Query ChromaDB
    if search_vector:
        try:
            print("[INFO] Searching vector database for context.")
            logging.log(level=20, msg=f"Searching vector database for context.")

            chroma_res = CHROMA_COLLECTION.query(
                query_texts=[user_message]
            )
        except Exception as e:
            print("[ERROR] Error in getting chromadb collection OR in querying it:",e)
            logging.log(level=50, msg=f"Error in getting chromadb collection OR in querying it: {e}")

        chroma_text = chroma_res["documents"][0] if chroma_res and "documents" in chroma_res else ""
    else:
        chroma_text=""

    try:
        print("[INFO] Send user prompt and context to LLM.")
        logging.log(level=20, msg=f"Send user prompt and context to LLM.")

        answer = generate_answer(user_message, chroma_text, history=history_str)
    except Exception as e:
        print("[ERROR] Error in answer generation (get_answer function):",e)
        logging.log(level=50, msg=f"Error in answer generation (get_answer function): {e}")

    if answer:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messages (conversation_id, sender, text) VALUES (?, ?, ?)', (conv_id, 'bot', answer))
        conn.commit()
        conn.close()
        print("[INFO] Answer received.")
        logging.log(level=20, msg="Answer received and passed.")
        return jsonify({'reply': answer})
    return None

if __name__=='__main__':
    app.run()
