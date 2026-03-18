import sqlite3

conn = sqlite3.connect("mentor.db")
cursor = conn.cursor()

# ----------------- Users table -----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    role TEXT CHECK(role IN ('mentor', 'mentee')) NOT NULL,
    email TEXT UNIQUE,
    password TEXT NOT NULL,
    specialization TEXT,
    created_at TEXT
)
""")

# ----------------- Messages table -----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT NOT NULL,
    receiver TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    is_read BOOLEAN DEFAULT 0
)
""")

# ----------------- Progress table (FULLY PRODUCTION-READY) -----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student TEXT NOT NULL,
    mentor TEXT NOT NULL,
    task TEXT NOT NULL,
    score INTEGER CHECK(score >= 0 AND score <= 100),
    date TEXT NOT NULL,
    file_path TEXT,
    status TEXT DEFAULT 'submitted' CHECK(status IN ('pending', 'submitted', 'graded')),
    feedback TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# ----------------- Notifications table -----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT DEFAULT 'info' CHECK(type IN ('info', 'success', 'warning', 'error')),
    is_read BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# ----------------- Tasks table -----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mentor_name TEXT NOT NULL,
    student_name TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    deadline DATE,
    file_path TEXT,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'submitted', 'completed', 'cancelled')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# ----------------- TRIGGERS for data integrity -----------------
cursor.execute("""
CREATE TRIGGER IF NOT EXISTS update_progress_updated_at
    AFTER UPDATE ON progress
    FOR EACH ROW
BEGIN
    UPDATE progress SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
""")

cursor.execute("""
CREATE TRIGGER IF NOT EXISTS update_tasks_updated_at
    AFTER UPDATE ON tasks
    FOR EACH ROW
BEGIN
    UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
""")

# ----------------- INDEXES for performance -----------------
cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_progress_student ON progress(student)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_progress_mentor ON progress(mentor)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_progress_status ON progress(status)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_mentor ON tasks(mentor_name)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_student ON tasks(student_name)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_name)")

conn.commit()
conn.close()

print("✅ PRODUCTION-READY Database Created!")
print("✅ Tables: users, messages, progress, notifications, tasks")
print("✅ Added: CHECK constraints, triggers, indexes")
print("✅ File uploads + grading fully supported!")
print("\n🚀 Your mentor grading system is now DATABASE READY!")
