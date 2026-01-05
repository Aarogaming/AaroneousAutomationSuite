import sqlite3
import os

db_path = "artifacts/aas.db"

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(0)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check tasks table for artifacts_path
try:
    cursor.execute("SELECT id, artifacts_path FROM tasks WHERE artifacts_path IS NOT NULL")
    tasks = cursor.fetchall()
    
    updated_count = 0
    for task_id, path in tasks:
        if path and "artifacts/" in path and "artifacts/handoff/" not in path:
            new_path = path.replace("artifacts/", "artifacts/handoff/")
            cursor.execute("UPDATE tasks SET artifacts_path = ? WHERE id = ?", (new_path, task_id))
            print(f"Updated task {task_id}: {path} -> {new_path}")
            updated_count += 1
            
    conn.commit()
    print(f"Updated {updated_count} task paths.")
except sqlite3.OperationalError as e:
    print(f"Error accessing tasks table: {e}")

conn.close()
