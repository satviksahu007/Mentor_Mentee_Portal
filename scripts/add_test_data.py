import sqlite3
from datetime import datetime

conn = sqlite3.connect("mentor.db")
cursor = conn.cursor()

# Add test users
cursor.execute("INSERT OR IGNORE INTO users (name, role, email, password, specialization, created_at) VALUES (?, ?, ?, ?, ?, ?)",
              ("John Doe", "mentee", "john@example.com", "123", "Student", "2026-03-11"))
cursor.execute("INSERT OR IGNORE INTO users (name, role, email, password, specialization, created_at) VALUES (?, ?, ?, ?, ?, ?)",
              ("Dr. Smith", "mentor", "smith@example.com", "123", "Python", "2026-03-11"))

# Add test progress data
test_data = [
    ("John Doe", "Dr. Smith", "Python Basics", 85, "2026-03-01"),
    ("John Doe", "Dr. Smith", "Data Structures", 92, "2026-03-05"),
    ("John Doe", "Dr. Smith", "Web Development", 78, "2026-03-10"),
]

cursor.executemany("INSERT OR IGNORE INTO progress (student, mentor, task, score, date) VALUES (?, ?, ?, ?, ?)", test_data)
conn.commit()
conn.close()

print("✅ Test data added! Login as 'John Doe' to see stats.")
    