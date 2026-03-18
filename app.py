from flask import Flask, render_template, request, redirect, session, url_for, flash, send_from_directory, send_file
from werkzeug.utils import secure_filename
import sqlite3
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta
import mimetypes

app = Flask(__name__)
app.secret_key = "secret_key_123"

# File upload config
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('static/uploads/tasks', exist_ok=True)
os.makedirs('static/uploads/submissions', exist_ok=True)  

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 🔥 FIXED PDF ROUTE - Perfectly opens PDFs in browser
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """🔥 WORKS WITH PDFs + ALL FILES in tasks/, submissions/"""
    try:
        print(f"🔍 Looking for: {filename}")
        
        # Multiple possible locations
        possible_paths = [
            os.path.join(app.config['UPLOAD_FOLDER'], filename),
            os.path.join(app.config['UPLOAD_FOLDER'], 'submissions', filename),
            os.path.join(app.config['UPLOAD_FOLDER'], 'tasks', filename),
            os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(filename))
        ]
        
        for full_path in possible_paths:
            print(f"🔍 Checking: {full_path}")
            if os.path.exists(full_path):
                print(f"✅ FOUND: {full_path}")
                
                # 🔥 PDF FIX: Force browser open
                if filename.lower().endswith('.pdf'):
                    return send_file(full_path, 
                                   mimetype='application/pdf',
                                   as_attachment=False,
                                   download_name=os.path.basename(filename))
                
                # Other files
                return send_from_directory(os.path.dirname(full_path), 
                                         os.path.basename(full_path),
                                         as_attachment=False)
        
        print(f"❌ File not found!")
        return "❌ File not found!", 404
        
    except Exception as e:
        print(f"💥 ERROR: {str(e)}")
        return f"❌ Error: {str(e)}", 500

# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("mentor.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, role, email FROM users WHERE email=? AND password=?", (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user"] = {
                "name": user[1],
                "role": user[2],
                "email": user[3]
            }
            return redirect("/dashboard")
        else:
            return "Invalid Login. <a href='/'>Try again</a>"

    return render_template("login.html")

# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        role = request.form["role"]
        email = request.form["email"]
        password = request.form["password"]
        specialization = request.form.get("specialization", "")
        created_at = datetime.today().strftime("%Y-%m-%d")

        conn = sqlite3.connect("mentor.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users(name, role, email, password, specialization, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                      (name, role, email, password, specialization, created_at))
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register.html")

# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
   
    user = session["user"]
   
    avg_score = max_score = min_score = total_tasks = 0
    mentor_mentees = mentor_tasks = mentor_avg = 0
   
    conn = sqlite3.connect("mentor.db")
   
    if user["role"] == "mentee":
        df_stats = pd.read_sql_query("SELECT score FROM progress WHERE student=?", conn, params=(user["name"],))
        if not df_stats.empty:
            scores = pd.to_numeric(df_stats["score"], errors='coerce').dropna()
            if len(scores) > 0:
                avg_score = float(scores.mean())
                max_score = int(scores.max())
                min_score = int(scores.min())
                total_tasks = len(scores)
   
    if user["role"] == "mentor":
        df_mentor = pd.read_sql_query("""
            SELECT COUNT(DISTINCT student) as total_mentees,
                   COUNT(*) as total_tasks,
                   ROUND(AVG(CAST(score AS REAL)), 1) as avg_score
            FROM progress 
            WHERE mentor=? AND score IS NOT NULL AND score != ''
        """, conn, params=(user["name"],))
        
        if not df_mentor.empty:
            row = df_mentor.iloc[0]
            mentor_mentees = int(row['total_mentees']) if pd.notna(row['total_mentees']) else 0
            mentor_tasks = int(row['total_tasks']) if pd.notna(row['total_tasks']) else 0
            mentor_avg = float(row['avg_score']) if pd.notna(row['avg_score']) else 0
   
    conn.close()
   
    # Generate chart
    os.makedirs("static/charts", exist_ok=True)
    plt.ioff()
    plt.style.use('dark_background')
    plt.figure(figsize=(10,6))
   
    chart_conn = sqlite3.connect("mentor.db")
   
    if user["role"] == "mentee":
        df_chart = pd.read_sql_query("SELECT task, score FROM progress WHERE student=? ORDER BY date ASC", 
                                      chart_conn, params=(user["name"],))
        if not df_chart.empty:
            df_chart['score'] = pd.to_numeric(df_chart['score'], errors='coerce')
            valid_data = df_chart.dropna(subset=['score'])
            if not valid_data.empty:
                tasks = valid_data['task'].str[:15].tolist()
                scores = valid_data['score'].tolist()
                plt.plot(range(len(scores)), scores, marker='o', linewidth=3)
                plt.xticks(range(len(tasks)), tasks, rotation=45, ha='right')
                plt.title(f"{user['name']}'s Task Progress", fontsize=16, fontweight='bold')
                plt.ylabel("Score (/100)")
                plt.grid(True, alpha=0.3)
                plt.ylim(0, 105)
            else:
                plt.text(0.5, 0.5, 'No valid scores yet', ha='center', va='center', fontsize=16, 
                        transform=plt.gca().transAxes)
        else:
            plt.text(0.5, 0.5, 'Submit your first task!', ha='center', va='center', fontsize=16, 
                    transform=plt.gca().transAxes)
    else:
        df_chart = pd.read_sql_query("""
            SELECT student, ROUND(AVG(CAST(score AS REAL)), 1) as avg_score
            FROM progress WHERE mentor=? AND score IS NOT NULL 
            GROUP BY student ORDER BY avg_score DESC
        """, chart_conn, params=(user["name"],))
        
        if not df_chart.empty:
            valid_scores = pd.to_numeric(df_chart["avg_score"], errors='coerce').dropna()
            if len(valid_scores) > 0:
                students = df_chart['student'].head(len(valid_scores)).tolist()
                colors = ['#007bff', '#28a745', '#ffc107', '#dc3545'][:len(students)]
                plt.bar(students, valid_scores, color=colors)
                plt.title(f"{user['name']}'s Mentees Performance", fontsize=16, fontweight='bold')
                plt.ylabel("Average Score")
                plt.xticks(rotation=45, ha='right')
                plt.ylim(0, 105)
            else:
                plt.text(0.5, 0.5, 'No mentees data', ha='center', va='center', fontsize=16)
        else:
            plt.text(0.5, 0.5, 'No mentees yet', ha='center', va='center', fontsize=16)
   
    chart_conn.close()
    plt.tight_layout()
    plt.savefig("static/charts/progress.png", dpi=150, bbox_inches='tight')
    plt.close()
   
    return render_template("dashboard.html",
                           user=user,
                           avg_score=avg_score, max_score=max_score,
                           min_score=min_score, total_tasks=total_tasks,
                           mentor_mentees=mentor_mentees, mentor_tasks=mentor_tasks,
                           mentor_avg=mentor_avg)

# SUBMIT TASK
@app.route('/submit_task/<int:task_id>', methods=['POST'])
def submit_task(task_id):
    print("=== DEBUG INFO ===")
    print("request.files:", request.files)
    print("Files available:", list(request.files.keys()))
    print("'file' in request.files:", 'file' not in request.files)
    
    if 'file' not in request.files:
        print("❌ NO FILE FOUND")
        flash('❌ Please upload a file!')
        return redirect(url_for('submit_task', task_id=task_id))
    
    file = request.files['file']
    print("Filename:", file.filename)
    
    if file.filename == '':
        print("❌ EMPTY FILENAME")
        flash('❌ No file selected!')
        return redirect(url_for('submit_task', task_id=task_id))
    
    print("✅ FILE OK - saving...")
    # Add your save logic here
    flash('✅ Debug: File received!')
    return redirect(url_for('dashboard'))


# MESSAGES
@app.route("/messages", methods=["GET", "POST"])
def messages():
    if "user" not in session:
        return redirect("/")
   
    user = session["user"]
    conn = sqlite3.connect("mentor.db")
    cursor = conn.cursor()
   
    active_receiver = None
    
    # 🔥 FIXED: Only process actual messages, not contact clicks
    if request.method == "POST":
        # Check for actual message content first
        if "message" in request.form and request.form["message"].strip():
            sender = user["name"]
            receiver = request.form["receiver"]
            message = request.form["message"].strip()
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO messages(sender, receiver, message, timestamp) VALUES (?, ?, ?, ?)",
                          (sender, receiver, message, timestamp))
            conn.commit()
            active_receiver = receiver  # Stay on same chat
            
        # Handle contact selection (no message field)
        elif "receiver" in request.form:
            active_receiver = request.form["receiver"]
            
    # Get contacts (unchanged)
    cursor.execute("""
        SELECT contact_name, last_message_time
        FROM (
            SELECT 
                CASE 
                    WHEN sender = ? THEN receiver 
                    ELSE sender 
                END as contact_name,
                MAX(timestamp) as last_message_time
            FROM messages 
            WHERE sender = ? OR receiver = ? 
            GROUP BY 
                CASE 
                    WHEN sender = ? THEN receiver 
                    ELSE sender 
                END
        ) 
        ORDER BY last_message_time DESC
    """, (user["name"], user["name"], user["name"], user["name"]))
    
    contacts_raw = cursor.fetchall()
    
    # Default to first contact if none selected
    if not active_receiver and contacts_raw:
        active_receiver = contacts_raw[0][0]
   
    # Get messages for active chat
    messages = []
    if active_receiver:
        cursor.execute("""
            SELECT sender, receiver, message, timestamp 
            FROM messages 
            WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?) 
            ORDER BY timestamp ASC
        """, (user["name"], active_receiver, active_receiver, user["name"]))
        messages = cursor.fetchall()
   
    # Get other users
    cursor.execute("SELECT DISTINCT name FROM users WHERE name != ? ORDER BY name", (user["name"],))
    other_users = [row[0] for row in cursor.fetchall()]
   
    conn.close()
    
    return render_template("messages.html", 
                         user=user, 
                         messages=messages, 
                         other_users=other_users,
                         contacts=[{'name': c[0], 'last_time': c[1]} for c in contacts_raw],
                         active_receiver=active_receiver)


# MENTORS LIST
@app.route("/mentors")
def mentors():
    conn = sqlite3.connect("mentor.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, specialization FROM users WHERE role='mentor'")
    mentors_list = cursor.fetchall()
    conn.close()
    return render_template("mentors.html", mentors=mentors_list)

# MY MENTEES
@app.route("/my_mentees")
def my_mentees():
    if "user" not in session or session["user"]["role"] != "mentor":
        return redirect("/dashboard")
   
    mentor_name = session["user"]["name"]
    conn = sqlite3.connect("mentor.db")
   
    # Existing mentees query
    df = pd.read_sql_query("""
        SELECT student,
               ROUND(AVG(CAST(score AS REAL)), 1) as avg_score,
               COUNT(*) as total_tasks,
               MAX(CAST(score AS REAL)) as best_score,
               MIN(CAST(score AS REAL)) as worst_score
        FROM progress
        WHERE mentor=?
        GROUP BY student
        ORDER BY avg_score DESC
    """, conn, params=(mentor_name,))
   
    df['best_score'] = pd.to_numeric(df['best_score'], errors='coerce').fillna(0).astype(int)
    df['worst_score'] = pd.to_numeric(df['worst_score'], errors='coerce').fillna(0).astype(int)
    
    # 🔥 NEW: Get pending submissions
    df_pending = pd.read_sql_query("""
        SELECT id, student, task, date, file_path
        FROM progress 
        WHERE mentor=? AND status='submitted' AND (score IS NULL OR score = 0)
        ORDER BY date DESC
        LIMIT 6
    """, conn, params=(mentor_name,))
    pending_submissions = df_pending.to_dict('records')
   
    conn.close()
   
    return render_template("my_mentees.html",
                           mentor_name=mentor_name,
                           mentees=df.to_dict('records'),
                           pending_submissions=pending_submissions)  # 🔥 NEW

# GRADING QUEUE
@app.route("/grading_queue")
def grading_queue():
    if "user" not in session or session["user"]["role"] != "mentor":
        return redirect("/dashboard")
  
    mentor_name = session["user"]["name"]
    conn = sqlite3.connect("mentor.db")
  
    df = pd.read_sql_query("""
        SELECT p.id, p.student, p.task, p.date, p.file_path, p.status,
               t.title as task_title, t.deadline
        FROM progress p
        LEFT JOIN tasks t ON p.task = t.title AND t.mentor_name=?
        WHERE p.mentor=? AND p.status='submitted' AND (p.score IS NULL OR p.score = 0)
        ORDER BY p.date ASC
    """, conn, params=(mentor_name, mentor_name))
  
    submissions = df.to_dict('records')
    conn.close()
  
    return render_template("grading_queue.html", 
                           submissions=submissions, 
                           mentor_name=mentor_name)

# MENTEE TASKS DETAIL
@app.route("/mentee_tasks/<mentee_name>")
def mentee_tasks(mentee_name):
    if "user" not in session or session["user"]["role"] != "mentor":
        return redirect("/dashboard")
  
    real_name = mentee_name.replace('_', ' ')
    mentor_name = session["user"]["name"]
  
    conn = sqlite3.connect("mentor.db")
  
    df_tasks = pd.read_sql_query("""
        SELECT task, score, date 
        FROM progress 
        WHERE student=? AND mentor=? 
        ORDER BY date ASC
    """, conn, params=(real_name, mentor_name))
  
    task_count = len(df_tasks)
    if task_count > 0:
        df_tasks['score_num'] = pd.to_numeric(df_tasks['score'], errors='coerce')
        best_score = int(df_tasks['score_num'].max()) if not df_tasks['score_num'].isna().all() else 0
        worst_score = int(df_tasks['score_num'].min()) if not df_tasks['score_num'].isna().all() else 0
        avg_score = float(df_tasks['score_num'].mean()) if not df_tasks['score_num'].isna().all() else 0
    else:
        best_score = worst_score = avg_score = 0

    # Generate mentee chart
    os.makedirs("static/charts", exist_ok=True)
    plt.ioff()
    plt.figure(figsize=(12,6))
  
    if task_count > 0 and not df_tasks['score_num'].isna().all():
        valid_scores = df_tasks['score_num'].dropna()
        tasks_short = [str(t)[:12]+"..." if len(str(t))>12 else str(t) for t in df_tasks["task"][:len(valid_scores)]]
        
        plt.plot(range(len(valid_scores)), valid_scores, 'o-', linewidth=3, markersize=10, 
                color='#28a745', markerfacecolor='#20c997')
        plt.xticks(range(len(tasks_short)), tasks_short, rotation=45, ha='right')
        plt.title(f"{real_name}'s Task Progress", fontsize=16, fontweight='bold')
        plt.ylabel("Score (/100)")
        plt.grid(True, alpha=0.3)
        plt.ylim(0, 105)
    else:
        plt.text(0.5, 0.5, f'No tasks from {real_name} yet', ha='center', va='center', fontsize=16)
  
    plt.tight_layout()
    plt.savefig("static/charts/mentee_progress.png", dpi=150, bbox_inches='tight')
    plt.close()
  
    conn.close()
  
    return render_template("mentee_tasks.html",
                           mentor_name=mentor_name,
                           mentee_name=real_name,
                           tasks=df_tasks.to_dict('records'),
                           task_count=task_count,
                           best_score=best_score,
                           worst_score=worst_score,
                           avg_score=avg_score)

# TASK ASSIGNMENT
@app.route("/assign_task", methods=["GET", "POST"])
def assign_task():
    if "user" not in session or session["user"]["role"] != "mentor":
        return redirect("/dashboard")
  
    if request.method == "POST":
        mentor = session["user"]["name"]
        student = request.form["student"]
        title = request.form["title"]
        description = request.form["description"]
        deadline = request.form["deadline"]
        file = request.files.get("file")
        
        file_path = None
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{student}_{title}_{file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'tasks', filename)
            file.save(file_path)
        
        conn = sqlite3.connect("mentor.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (mentor_name, student_name, title, description, deadline, file_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (mentor, student, title, description, deadline, file_path))
        conn.commit()
        conn.close()
        
        flash(f"Task assigned to {student} successfully!")
        return redirect("/my_mentees")
  
    conn = sqlite3.connect("mentor.db")
    df = pd.read_sql_query("""
        SELECT DISTINCT student as name FROM progress WHERE mentor=?
        UNION
        SELECT name FROM users WHERE role='mentee'
    """, conn, params=(session["user"]["name"],))
    mentees = df['name'].tolist()
    conn.close()
  
    return render_template("assign_task.html", mentees=mentees)

# MY TASKS
@app.route("/my_tasks")
def my_tasks():
    if "user" not in session:
        return redirect("/")

    user = session["user"]
    conn = sqlite3.connect("mentor.db")
    today = datetime.now().strftime("%Y-%m-%d")
    cursor = conn.cursor()  # ✅ Move cursor OUTSIDE loop

    try:
        if user["role"] == "mentor":
            df = pd.read_sql_query("""
                SELECT t.*, u.name as student_name 
                FROM tasks t 
                LEFT JOIN users u ON t.student_name = u.name 
                WHERE t.mentor_name=?
                ORDER BY t.created_at DESC
            """, conn, params=(user["name"],))
        else:
            df = pd.read_sql_query("""
                SELECT * FROM tasks 
                WHERE student_name=?
                ORDER BY deadline ASC
            """, conn, params=(user["name"],))

        tasks_list = []
        for row in df.to_dict('records'):
            # ✅ Fix file_path FIRST
            if row.get('file_path'):
                row['file_path'] = os.path.relpath(row['file_path'], 'static/uploads')
            
            # ✅ Get LATEST progress status + score
            cursor.execute("""
                SELECT status, score 
                FROM progress 
                WHERE student=? AND task=? 
                ORDER BY date DESC 
                LIMIT 1
            """, (user["name"], row['title']))
            latest = cursor.fetchone()
            
            if latest and latest[0]:  # ✅ Check if record exists AND has status
                row['status'] = latest[0]  # 'submitted', 'graded', etc.
                row['score'] = latest[1] or ''  # Pass actual score or empty
            else:
                row['status'] = row.get('status', 'pending')  # Default from tasks table
                row['score'] = ''  # ✅ No score = empty
            
            tasks_list.append(row)

    except Exception as e:
        print(f"❌ Database error: {e}")
        tasks_list = []

    finally:
        conn.close()

    return render_template("my_tasks.html", user=user, tasks=tasks_list, today=today)


# TASK SUBMIT
@app.route("/task_submit/<int:task_id>", methods=["GET", "POST"])
def task_submit(task_id):
    if "user" not in session or session["user"]["role"] != "mentee":
        return redirect("/dashboard")
  
    user = session["user"]
    conn = sqlite3.connect("mentor.db")
    cursor = conn.cursor()
  
    cursor.execute("SELECT * FROM tasks WHERE id=? AND student_name=?", (task_id, user["name"]))
    task = cursor.fetchone()
  
    if not task:
        flash("Task not found or not assigned to you!")
        conn.close()
        return redirect("/my_tasks")
  
    task_dict = {
        "id": task[0], "mentor_name": task[1], "student_name": task[2],
        "title": task[3], "description": task[4], "deadline": task[5],
        "file_path": task[6], "status": task[7], "created_at": task[8]
    }
  
    # 🔹 Get latest progress status from progress table
    cursor.execute("""
        SELECT status 
        FROM progress 
        WHERE student=? AND task=? 
        ORDER BY date DESC LIMIT 1
    """, (user["name"], task_dict["title"]))
    latest = cursor.fetchone()
    if latest:
        task_dict["status"] = latest[0]  # replace tasks.status with latest progress.status

    if request.method == "POST":
        student_file = request.files.get("student_file")
        submission_file = None
        
        if student_file and allowed_file(student_file.filename):
            filename = secure_filename(f"sub_{user['name']}_{task_id}_{student_file.filename}")
            submission_file = os.path.join(app.config['UPLOAD_FOLDER'], 'submissions', filename)
            os.makedirs(os.path.dirname(submission_file), exist_ok=True)
            student_file.save(submission_file)
        
        if submission_file:
            cursor.execute("""
                INSERT INTO progress(student, mentor, task, date, file_path, status)
                VALUES (?, ?, ?, ?, ?, 'submitted')
            """, (user["name"], task_dict["mentor_name"], task_dict["title"], 
                  datetime.now().strftime("%Y-%m-%d"), submission_file))
            
            cursor.execute("UPDATE tasks SET status='submitted' WHERE id=?", (task_id,))
            conn.commit()
            flash("✅ Submission uploaded! Awaiting mentor review.", "success")
            conn.close()
            return redirect("/my_tasks")
        else:
            flash("❌ Please upload a file!", "warning")
  
    conn.close()
    return render_template("submit_task.html", task=task_dict, user=user)

# GRADE SUBMISSION
@app.route("/grade_submission/<int:submission_id>", methods=["GET", "POST"])
def grade_submission(submission_id):
    if "user" not in session or session["user"]["role"] != "mentor":
        return redirect("/dashboard")
  
    mentor_name = session["user"]["name"]
    conn = sqlite3.connect("mentor.db")
    cursor = conn.cursor()
  
    cursor.execute("""
        SELECT p.id, p.student, p.mentor, p.task, p.score, p.date, 
               p.file_path, p.status, p.feedback
        FROM progress p
        WHERE p.id=? AND p.mentor=?
    """, (submission_id, mentor_name))
  
    submission = cursor.fetchone()
    conn.close()
  
    if not submission:
        flash("❌ Submission not found!")
        return redirect("/my_mentees")
  
    submission_dict = {
        "id": submission[0],
        "student": submission[1],
        "mentor": submission[2],
        "task": submission[3],
        "score": submission[4],
        "date": submission[5],
        "file_path": submission[6],
        "status": submission[7],
        "feedback": submission[8] if len(submission) > 8 else ""
    }
  
    if request.method == "POST":
        new_score = int(request.form["score"])
        feedback = request.form.get("feedback", "")

        conn = sqlite3.connect("mentor.db")
        cursor = conn.cursor()

        # 1️⃣ Update progress table (submission)
        cursor.execute("""
            UPDATE progress 
            SET score=?, status='graded', feedback=?
            WHERE id=?
        """, (new_score, feedback, submission_id))

        # 2️⃣ Update tasks table for the corresponding student and task
        cursor.execute("""
            UPDATE tasks
            SET status='graded'
            WHERE id=? AND student_name=?
        """, (submission_dict["task"], submission_dict["student"]))

        conn.commit()
        conn.close()

        flash(f"✅ Graded - {new_score}/100")
        return redirect("/my_mentees")

# GET request: show the grading page
    return render_template("grade_submission.html", submission=submission_dict, user=session["user"])

# LOGOUT
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

# DEBUG UPLOADS
@app.route('/debug_uploads')
def debug_uploads():
    output = []
    upload_base = app.config['UPLOAD_FOLDER']
    
    if not os.path.exists(upload_base):
        return f"<h1>❌ UPLOADS FOLDER MISSING: {upload_base}</h1>"
    
    output.append(f"<h2>📁 Uploads folder: {upload_base}</h2>")
    
    for root, dirs, files in os.walk(upload_base):
        output.append(f"<h3>📂 {root}</h3>")
        for f in files:
            full_path = os.path.join(root, f)
            output.append(f"✅ {f} ({full_path}) | <a href='/uploads/{os.path.relpath(full_path, upload_base)}'>OPEN</a><br>")
        if not files:
            output.append("❌ <b>EMPTY</b><br>")
    
    return "<pre>" + "".join(output) + "</pre>"

if __name__ == "__main__":
    app.run(debug=True)
