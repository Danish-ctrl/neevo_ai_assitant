from core.database import get_connection, init_db
import json

# Ensure tables exist the moment this engine boots up
init_db()

# We track the active chat window so the AI knows where to save the text
CURRENT_SESSION_ID = None

def start_new_session(title="New Chat", mode="chat"):
    """Creates a fresh chat in the database and sets it as active."""
    global CURRENT_SESSION_ID
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sessions (title, mode) VALUES (?, ?)", (title, mode))
    CURRENT_SESSION_ID = cursor.lastrowid
    conn.commit()
    conn.close()
    return CURRENT_SESSION_ID

def set_active_session(session_id):
    """Changes the active memory track when you click an old chat in the UI."""
    global CURRENT_SESSION_ID
    CURRENT_SESSION_ID = session_id

def save_message(role, content):
    """Saves a single message to the active chat session."""
    global CURRENT_SESSION_ID
    if not CURRENT_SESSION_ID:
        start_new_session()
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                   (CURRENT_SESSION_ID, role, content))
    conn.commit()
    conn.close()

def get_memory_context():
    """Feeds the last 10 messages of the current chat to the LLM Brain."""
    global CURRENT_SESSION_ID
    if not CURRENT_SESSION_ID:
        return "No previous context."
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM messages WHERE session_id = ? ORDER BY timestamp ASC", (CURRENT_SESSION_ID,))
    rows = cursor.fetchall()
    conn.close()
    
    # Format for the system prompt
    context_str = "Previous conversation history:\n"
    for role, content in rows[-10:]:
        context_str += f"{role.upper()}: {content}\n"
        
    return context_str

# --- UI HELPER FUNCTIONS ---

def get_all_sessions():
    """Used by the Sidebar to list historical chats."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, mode, created_at FROM sessions ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "mode": r[2], "date": r[3]} for r in rows]

def get_session_messages(session_id):
    """Used to repopulate the screen when you click an old chat."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1], "time": r[2]} for r in rows]