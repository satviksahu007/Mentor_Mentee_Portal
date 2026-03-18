import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os


DB_PATH = "mentor.db"
CHART_DIR = os.path.join("static", "charts")
CHART_PATH = os.path.join(CHART_DIR, "progress.png")


# ----------------- Create / Update Progress Chart -----------------
def create_chart(user_name=None):
    # Ensure charts directory exists
    os.makedirs(CHART_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM progress", conn)
    conn.close()

    if df.empty:
        return

    # Filter only this mentee if a user_name is provided
    if user_name:
        df = df[df["student"] == user_name]

    if df.empty:
        return

    # Sort tasks alphabetically for better plotting
    df = df.sort_values(by="task")

    # --------- Matplotlib plot using pandas DataFrame ---------
    plt.figure(figsize=(7, 4))
    plt.plot(df["task"], df["score"], marker="o", linestyle="-", color="blue")

    plt.title(f"{user_name} Progress" if user_name else "All Mentees Progress")
    plt.xlabel("Task")
    plt.ylabel("Score")
    plt.ylim(0, 100)
    plt.grid(True)

    # Save into static folder so Flask can serve it
    plt.tight_layout()
    plt.savefig(CHART_PATH)
    plt.close()


# ----------------- Analyze Progress (uses numpy + DataFrame) -----------------
def analyze_progress(user_name=None):
    conn = sqlite3.connect("mentor.db")
    df = pd.read_sql_query("SELECT * FROM progress", conn)
    conn.close()

    if df.empty or len(df) == 0:
        print("DEBUG: No data in progress table")  # Check console
        return None, None, None, None

    # Filter for specific user
    if user_name:
        user_df = df[df["student"] == user_name]
        if user_df.empty:
            print(f"DEBUG: No data for user {user_name}")
            return None, None, None, None
        df = user_df

    # Convert to numpy array and calculate
    scores = np.array(df["score"])
    
    if len(scores) == 0:
        return None, None, None, None
    
    avg_score = float(np.mean(scores))
    max_score = int(np.max(scores))
    min_score = int(np.min(scores))
    
    print(f"DEBUG: Stats - Avg:{avg_score}, Max:{max_score}, Min:{min_score}")  # Check console
    
    return df, avg_score, max_score, min_score

def create_chart_mentor(mentor_name):
    import os
    os.makedirs("static/charts", exist_ok=True)
    
    conn = sqlite3.connect("mentor.db")
    df = pd.read_sql_query("""
        SELECT student, AVG(score) as avg_score 
        FROM progress 
        WHERE mentor=? 
        GROUP BY student
    """, conn, params=(mentor_name,))
    conn.close()
    
    if df.empty:
        return
    
    plt.figure(figsize=(8, 5))
    plt.bar(df["student"], df["avg_score"], color='orange')
    plt.title(f"{mentor_name}'s Mentees Average Scores")
    plt.ylabel("Average Score")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("static/charts/progress.png")
    plt.close()


