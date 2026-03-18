import os
import sqlite3

print("Current folder:", os.getcwd())
print("Files here:", os.listdir('.'))

# Check if mentor.db exists
if os.path.exists('mentor.db'):
    print("✅ mentor.db FOUND")
    conn = sqlite3.connect('mentor.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, role FROM users")
    users = cursor.fetchall()
    print("Users in DB:", users)
    conn.close()
else:
    print("❌ mentor.db NOT FOUND")
    print("Creating fresh database...")
    
    # Create database + test users
    conn = sqlite3.connect('mentor.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        specialization TEXT,
        created_at TEXT
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student TEXT NOT NULL,
        mentor TEXT NOT NULL,
        task TEXT NOT NULL,
        score INTEGER NOT NULL,
        date TEXT NOT NULL
    )''')
    
    # Add test users
    cursor.execute("INSERT OR REPLACE INTO users (name, role, email, password, specialization, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                  ('Dr Smith', 'mentor', 'smith@email.com', '123', 'Data Structures', '2026-03-13'))
    cursor.execute("INSERT OR REPLACE INTO users (name, role, email, password, specialization, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                  ('Alice', 'mentee', 'alice@email.com', '123', '', '2026-03-13'))
    
    cursor.execute("INSERT OR REPLACE INTO progress (student, mentor, task, score, date) VALUES (?, ?, ?, ?, ?)",
                  ('Alice', 'Dr Smith', 'Quicksort', 85, '2026-03-13'))
    cursor.execute("INSERT OR REPLACE INTO progress (student, mentor, task, score, date) VALUES (?, ?, ?, ?, ?)",
                  ('Alice', 'Dr Smith', 'MergeSort', 92, '2026-03-13'))
    
    conn.commit()
    conn.close()
    print("✅ Database created with test data!")
