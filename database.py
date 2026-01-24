import sqlite3
import hashlib
import os
import datetime

# --- 1. SECURITY HELPERS ---
def hash_password(password):
    """Converts a plain text password into a secure hash."""
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_password(password, hashed_pw):
    """Checks if a plain text password matches the stored hash."""
    if not password: return False
    return hash_password(password) == hashed_pw

# --- 2. DATABASE INITIALIZATION ---
def init_db():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    c = conn.cursor()
    
    # Create Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            name TEXT,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    
    # Create Messages Table (for chat history)
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create Sessions Table (for chat titles)
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_email TEXT,
            title TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # --- SECURE ADMIN CREATION (FROM SECRETS) ---
    # This reads from .env (Local) or Streamlit Secrets (Cloud)
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_pass = os.getenv("ADMIN_PASSWORD")
    
    if admin_email and admin_pass:
        # Check if this admin already exists
        c.execute('SELECT * FROM users WHERE email = ?', (admin_email,))
        if not c.fetchone():
            hashed_pw = hash_password(admin_pass)
            try:
                c.execute('INSERT INTO users (email, password, name, is_admin) VALUES (?, ?, ?, ?)', 
                          (admin_email, hashed_pw, "System Admin", 1))
                print(f"✅ Admin account ({admin_email}) created securely from environment variables.")
            except Exception as e:
                print(f"⚠️ Could not create admin: {e}")
    
    conn.commit()
    conn.close()

# --- 3. USER FUNCTIONS ---

def login_user(email, password):
    conn = sqlite3.connect('users.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('SELECT name, is_admin, password FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    
    if user and check_password(password, user[2]):
        return user[0], user[1] # Returns (Name, Is_Admin)
    return None

def register_user(email, password, name, is_admin=False):
    conn = sqlite3.connect('users.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    if c.fetchone():
        conn.close()
        return False # User exists
    
    hashed_pw = hash_password(password)
    c.execute('INSERT INTO users (email, password, name, is_admin) VALUES (?, ?, ?, ?)', 
              (email, hashed_pw, name, 1 if is_admin else 0))
    conn.commit()
    conn.close()
    return True

def get_all_users():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('SELECT email, name, is_admin FROM users')
    data = c.fetchall()
    conn.close()
    return data

def delete_user(email):
    conn = sqlite3.connect('users.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE email = ?', (email,))
    conn.commit()
    conn.close()
    return True

# --- 4. CHAT HISTORY FUNCTIONS ---

def save_message(user_email, session_id, role, content):
    conn = sqlite3.connect('users.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('INSERT INTO messages (user_email, session_id, role, content) VALUES (?, ?, ?, ?)',
              (user_email, session_id, role, content))
    conn.commit()
    conn.close()

def get_session_history(session_id):
    conn = sqlite3.connect('users.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('SELECT role, content FROM messages WHERE session_id = ? ORDER BY timestamp ASC', (session_id,))
    data = c.fetchall()
    conn.close()
    return [{"role": role, "content": content} for role, content in data]

def save_session_title(user_email, session_id, title):
    conn = sqlite3.connect('users.db', check_same_thread=False)
    c = conn.cursor()
    # Only insert if not exists
    c.execute('INSERT OR IGNORE INTO sessions (session_id, user_email, title) VALUES (?, ?, ?)',
              (session_id, user_email, title))
    conn.commit()
    conn.close()

def get_user_sessions(user_email):
    conn = sqlite3.connect('users.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('SELECT session_id, title FROM sessions WHERE user_email = ? ORDER BY created_at ASC', (user_email,))
    data = c.fetchall()
    conn.close()
    return data