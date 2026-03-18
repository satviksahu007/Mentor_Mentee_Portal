import sqlite3

# Replace "YOUR_MENTOR_NAME" with your exact mentor login name
MENTOR_NAME = "YOUR_MENTOR_NAME"  # e.g. "Dr. Smith"

conn = sqlite3.connect("mentor.db")
cursor = conn.cursor()

# Add tasks where YOUR mentor name appears
data = [
    ("John Doe", MENTOR_NAME, "Python Basics", 85, "2026-03-09"),
    ("John Doe", MENTOR_NAME, "Pandas Project", 92, "2026-03-10"),
    ("Jane Smith", MENTOR_NAME, "Database Task", 78, "2026-03-11"),
]

cursor.executemany("INSERT INTO progress VALUES (NULL, ?, ?, ?, ?, ?)", data)
conn.commit()
conn.close()

print(f"✅ Added data for mentor '{MENTOR_NAME}'!")
