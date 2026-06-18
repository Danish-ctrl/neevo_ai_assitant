import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join("data", "neevo.db")

def get_connection():
    """Establishes a connection to the SQLite database."""
    os.makedirs("data", exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    """Creates the necessary tables if they don't exist yet."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # TABLE 1: Chat Sessions (This populates your future left-sidebar)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            mode TEXT DEFAULT 'chat',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # TABLE 2: Chat Messages (This holds the actual back-and-forth text)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
    ''')

    # TABLE 3: Tasks & Reminders (This solves the Finished/Unfinished problem)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_text TEXT,
            trigger_time TIMESTAMP,
            status TEXT DEFAULT 'pending' 
        )
    ''')
    
    conn.commit()
    conn.close()

# --- HELPER FUNCTIONS FOR TASKS ---

def add_task_to_db(task_text, trigger_time_str):
    """Saves a new reminder to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tasks (task_text, trigger_time, status) VALUES (?, ?, ?)', 
                   (task_text, trigger_time_str, 'pending'))
    conn.commit()
    conn.close()

def mark_task_completed(task_id):
    """Changes a task from 'pending' to 'completed'."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status = 'completed' WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def get_pending_tasks():
    """Fetches all tasks that haven't been completed yet."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, task_text, trigger_time FROM tasks WHERE status = 'pending'")
    tasks = cursor.fetchall()
    conn.close()
    
    # Convert tuples to list of dictionaries for easy use
    return [{"id": t[0], "task": t[1], "time": t[2]} for t in tasks]

def delete_session_from_db(session_id):
    """Deletes a chat session and all its messages from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    # Delete the messages first (foreign key constraint)
    cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    # Then delete the session itself
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
    
def get_session_messages(session_id):
    """Retrieves all historical messages for a specific session ordered by time."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Selects the history matching your schema expectations
        cursor.execute("""
            SELECT role, content, timestamp 
            FROM messages 
            WHERE session_id = ? 
            ORDER BY timestamp ASC
        """, (session_id,))
        
        rows = cursor.fetchall()
        # Maps the rows into a list of dictionaries for main.py
        return [{"role": row[0], "content": row[1], "time": row[2]} for row in rows]
    except Exception as e:
        print(f"Database Error while fetching session history: {e}")
        return []
    finally:
        conn.close()
        
def delete_task(task_id):
    """Permanently deletes a reminder from the database and verifies completion."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # REPLACE 'YOUR_TABLE_NAME_HERE' with your actual table name (e.g., 'tasks')
        cursor.execute("DELETE FROM YOUR_TABLE_NAME_HERE WHERE id = ?", (task_id,))
        conn.commit()
        
        # This forces the terminal to tell us if the database actually deleted a row
        if cursor.rowcount == 0:
            print(f"⚠️ DB Warning: Command ran, but no task with ID {task_id} existed.")
        else:
            print(f"✅ DB Success: Task {task_id} permanently erased.")
            
    except Exception as e:
        # If it fails, it will now loudly print the exact reason to your console
        print(f"❌ CRITICAL DB ERROR deleting task: {e}")
    finally:
        conn.close()