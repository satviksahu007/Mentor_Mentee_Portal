import os
import sqlite3

# Delete old database
if os.path.exists("mentor.db"):
    os.remove("mentor.db")
    print("Old database deleted")

# Run your database creation
exec(open("database.py").read())
print("New database created with all columns")
