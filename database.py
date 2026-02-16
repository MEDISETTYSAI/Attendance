import sqlite3
from datetime import datetime, date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# IMPORTANT: you said your data is in your_database.db
DB_PATH = BASE_DIR / "your_database.db"


def _ensure_columns(conn, table):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    cols = {row[1] for row in cur.fetchall()}

    if "lat" not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN lat REAL")
    if "lon" not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN lon REAL")
    if "address" not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN address TEXT")

    conn.commit()

def get_connection():
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Main table (already exists in your_database.db with user_id, timestamp)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        user_id TEXT,
        timestamp TEXT,
        lat REAL,
        lon REAL,
        address TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_attendance (
        user_id TEXT,
        timestamp TEXT,
        lat REAL,
        lon REAL,
        address TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS staff_attendance (
        user_id TEXT,
        timestamp TEXT,
        lat REAL,
        lon REAL,
        address TEXT
    )
    """)


    conn.commit()
    _ensure_columns(conn, "attendance")
    _ensure_columns(conn, "student_attendance")
    _ensure_columns(conn, "staff_attendance")
    return conn

def get_attendance_list(role, day=None):
    conn = get_connection()
    cursor = conn.cursor()

    where = ""
    params = ()
    if day:
        where = "WHERE DATE(timestamp) = ?"
        params = (day,)

    if role == "student":
        cursor.execute(f"""
            SELECT user_id, timestamp, lat, lon, address FROM attendance {where}
            UNION ALL
            SELECT user_id, timestamp, lat, lon, address FROM student_attendance {where}
            ORDER BY timestamp
        """, params * 2 if day else ())
    else:
        cursor.execute(f"""
            SELECT user_id, timestamp, lat, lon, address FROM staff_attendance {where}
            ORDER BY timestamp
        """, params)

    data = cursor.fetchall()
    conn.close()
    return data

def mark_attendance(user_id, role, lat=None, lon=None, address=None):
    conn = get_connection()
    cursor = conn.cursor()

    today = date.today().isoformat()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    table = "staff_attendance" if role == "staff" else "student_attendance"

    cursor.execute(f"""
        SELECT 1 FROM {table}
        WHERE user_id = ?
        AND DATE(timestamp) = ?
    """, (user_id, today))

    if cursor.fetchone():
        conn.close()
        return False

    cursor.execute(f"""
        INSERT INTO {table} (user_id, timestamp, lat, lon, address)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, now, lat, lon, address))

    conn.commit()
    conn.close()
    return True
