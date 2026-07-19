import sqlite3

DB_NAME = "stock.db"

def migrate():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Check if key_name column exists
    c.execute("PRAGMA table_info(stock)")
    columns = [col[1] for col in c.fetchall()]
    
    if 'key_name' not in columns:
        print("📦 Migrating database...")
        
        # Create new table with key_name
        c.execute('''CREATE TABLE stock_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            stock_type TEXT NOT NULL,
            added_by INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        )''')
        
        # Copy data from old table
        c.execute("SELECT id, item_name, quantity, stock_type, added_by, added_at, status FROM stock")
        rows = c.fetchall()
        
        for row in rows:
            c.execute('''INSERT INTO stock_new 
                         (id, key_name, quantity, stock_type, added_by, added_at, status) 
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (row[0], row[1], row[2], row[3], row[4], row[5], row[6]))
        
        # Drop old table and rename new one
        c.execute("DROP TABLE stock")
        c.execute("ALTER TABLE stock_new RENAME TO stock")
        
        # Update keys table
        c.execute("PRAGMA table_info(keys)")
        key_columns = [col[1] for col in c.fetchall()]
        
        if 'key_name' not in key_columns:
            c.execute('''CREATE TABLE keys_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_code TEXT UNIQUE NOT NULL,
                key_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                stock_type TEXT NOT NULL,
                generated_by INTEGER,
                generated_for INTEGER,
                status TEXT DEFAULT 'active',
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                claimed_at TIMESTAMP
            )''')
            
            c.execute("SELECT id, key_code, item_name, quantity, stock_type, generated_by, generated_for, status, generated_at, claimed_at FROM keys")
            rows = c.fetchall()
            
            for row in rows:
                c.execute('''INSERT INTO keys_new 
                             (id, key_code, key_name, quantity, stock_type, generated_by, generated_for, status, generated_at, claimed_at) 
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]))
            
            c.execute("DROP TABLE keys")
            c.execute("ALTER TABLE keys_new RENAME TO keys")
        
        # Update logs table
        c.execute("PRAGMA table_info(logs)")
        log_columns = [col[1] for col in c.fetchall()]
        
        if 'key_name' not in log_columns:
            c.execute('''CREATE TABLE logs_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                key_name TEXT,
                quantity INTEGER,
                stock_type TEXT,
                performed_by INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            c.execute("SELECT id, action, item_name, quantity, stock_type, performed_by, timestamp FROM logs")
            rows = c.fetchall()
            
            for row in rows:
                c.execute('''INSERT INTO logs_new 
                             (id, action, key_name, quantity, stock_type, performed_by, timestamp) 
                             VALUES (?, ?, ?, ?, ?, ?, ?)''',
                          (row[0], row[1], row[2], row[3], row[4], row[5], row[6]))
            
            c.execute("DROP TABLE logs")
            c.execute("ALTER TABLE logs_new RENAME TO logs")
        
        conn.commit()
        print("✅ Database migration completed!")
    else:
        print("✅ Database already up to date!")
    
    conn.close()

if __name__ == "__main__":
    migrate()