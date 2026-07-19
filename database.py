import sqlite3
from datetime import datetime
import random
import string

DB_NAME = "stock.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Stock table
    c.execute('''CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_code TEXT UNIQUE NOT NULL,
        stock_type TEXT NOT NULL,
        added_by INTEGER,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'active'
    )''')
    
    # Keys table
    c.execute('''CREATE TABLE IF NOT EXISTS keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_code TEXT UNIQUE NOT NULL,
        stock_type TEXT NOT NULL,
        generated_by INTEGER,
        generated_for INTEGER,
        status TEXT DEFAULT 'active',
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        claimed_at TIMESTAMP
    )''')
    
    # Logs table
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        key_code TEXT,
        stock_type TEXT,
        performed_by INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()

def generate_unique_key():
    prefix = "THUNDER"
    random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
    return f"{prefix}-{random_part}"

def add_stock(key_code, stock_type, user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO stock (key_code, stock_type, added_by) VALUES (?, ?, ?)",
              (key_code, stock_type, user_id))
    conn.commit()
    conn.close()
    log_action("ADD", key_code, stock_type, user_id)

def get_all_key_codes():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT key_code, stock_type FROM stock WHERE status='active'")
    data = c.fetchall()
    conn.close()
    return data

def get_stock_by_type(stock_type):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM stock WHERE stock_type=? AND status='active'", (stock_type,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def get_all_stock():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT key_code, stock_type FROM stock WHERE status='active' ORDER BY stock_type")
    data = c.fetchall()
    conn.close()
    return data

def generate_key(stock_type, generated_by, generated_for):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute("SELECT key_code FROM stock WHERE stock_type=? AND status='active' LIMIT 1", (stock_type,))
    result = c.fetchone()
    
    if not result:
        conn.close()
        return None, f"❌ {stock_type} out of stock!"
    
    key_code = result[0]
    
    c.execute("UPDATE stock SET status='inactive' WHERE key_code=?", (key_code,))
    
    c.execute('''INSERT INTO keys (key_code, stock_type, generated_by, generated_for) 
                 VALUES (?, ?, ?, ?)''', 
              (key_code, stock_type, generated_by, generated_for))
    
    conn.commit()
    conn.close()
    
    log_action("KEY_GENERATED", key_code, stock_type, generated_by)
    return key_code, f"✅ Key generated: {key_code}"

def get_keys_by_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT key_code, stock_type, status, generated_at FROM keys WHERE generated_for=? ORDER BY generated_at DESC", 
              (user_id,))
    data = c.fetchall()
    conn.close()
    return data

def get_all_keys():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT key_code, stock_type, generated_for, status, generated_at FROM keys ORDER BY generated_at DESC")
    data = c.fetchall()
    conn.close()
    return data

def log_action(action, key_code, stock_type, user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO logs (action, key_code, stock_type, performed_by) VALUES (?, ?, ?, ?)",
              (action, key_code, stock_type, user_id))
    conn.commit()
    conn.close()

def get_logs(limit=50):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM logs ORDER BY timestamp DESC LIMIT ?", (limit,))
    data = c.fetchall()
    conn.close()
    return data

def delete_all_stock(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE stock SET status='deleted' WHERE status='active'")
    conn.commit()
    conn.close()
    log_action("DELETE_ALL", "ALL", "ALL", user_id)