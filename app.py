from flask import Flask, render_template, jsonify, request
from ai_services.gemini_api import generate_answer
import utility.pdf_to_text as pdf_reader
import logging, sqlite3, os

logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    level=logging.DEBUG,
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

CHROMA_COLLECTION = pdf_reader.chroma_collection()

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
    data = request.get_json() or {}
    conv_id = data.get('id')
    title = data.get('title', 'New Chat')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO conversations (id, title) VALUES (?, ?)', (conv_id, title))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'id': conv_id, 'title': title})

@app.route('/conversations/<conv_id>', methods=['GET'])
def get_conversation_messages(conv_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT sender, text, strftime("%H:%M", timestamp) FROM messages WHERE conversation_id = ? ORDER BY id ASC', (conv_id,))
    rows = cursor.fetchall()
    conn.close()
    messages = [{'sender': row[0], 'text': row[1], 'timestamp': row[2]} for row in rows]
    return jsonify(messages)

@app.route('/conversations/<conv_id>', methods=['DELETE'])
def delete_conversation(conv_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM messages WHERE conversation_id = ?', (conv_id,))
    cursor.execute('DELETE FROM conversations WHERE id = ?', (conv_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/get_response', methods=['POST'])
def get_response():
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
    cursor.execute('SELECT sender, text FROM messages WHERE conversation_id = ? ORDER BY id ASC', (conv_id,))
    history_rows = cursor.fetchall()
    conn.commit()
    conn.close()

    history_str = "\n".join([f"{sender.capitalize()}: {text}" for sender, text in history_rows])

    # Query ChromaDB
    chroma_res = CHROMA_COLLECTION.query(
        query_texts=[user_message]
    )

    chroma_text = chroma_res["documents"][0] if chroma_res and "documents" in chroma_res else ""

    answer = generate_answer(user_message, chroma_text, history=history_str)

    if answer:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messages (conversation_id, sender, text) VALUES (?, ?, ?)', (conv_id, 'bot', answer))
        conn.commit()
        conn.close()
        logging.log(level=20, msg="Generated response passed.")
        return jsonify({'reply': answer})

if __name__=='__main__':
    app.run()
