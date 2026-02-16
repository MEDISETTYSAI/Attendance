import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "your_database.db"
today = datetime.now().date().isoformat()  # YYYY-MM-DD

conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

# Delete only today's rows (local date based on timestamp)
cur.execute("DELETE FROM student_attendance WHERE DATE(timestamp) = ?", (today,))
cur.execute("DELETE FROM staff_attendance WHERE DATE(timestamp) = ?", (today,))

# If you still have old table
try:
    cur.execute("DELETE FROM attendance WHERE DATE(timestamp) = ?", (today,))
except sqlite3.OperationalError:
    pass  # table doesn't exist

conn.commit()
conn.close()

print(f"✅ Deleted only today's data ({today}) from attendance tables.")
