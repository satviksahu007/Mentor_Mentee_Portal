# fix_app_compatibility.py
import sqlite3

conn = sqlite3.connect("mentor.db")
cursor = conn.cursor()

# Fix existing data - convert TEXT scores to INTEGER
cursor.execute("UPDATE progress SET score = CAST(score AS INTEGER) WHERE score IS NOT NULL")
cursor.execute("UPDATE progress SET score = NULL WHERE score > 100 OR score < 0")

# Add feedback column if missing (safety)
try:
    cursor.execute("ALTER TABLE progress ADD COLUMN feedback TEXT")
except:
    pass

conn.commit()
conn.close()
print("✅ App compatibility fixed!")
