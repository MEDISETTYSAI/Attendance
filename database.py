import os
import sqlite3
from datetime import datetime, date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# When DATABASE_URL is present (e.g. Render Postgres) we use Postgres so data
# is PERMANENT in the cloud. Otherwise we fall back to a local SQLite file,
# which keeps local development simple.
DATABASE_URL = os.environ.get("DATABASE_URL")
USE_POSTGRES = bool(DATABASE_URL)

# One-device-per-day rule.
#   On-premise (each device has its own private LAN IP) -> safe to enable ("1").
#   Cloud / shared office Wi-Fi (everyone shares one public IP) -> keep off.
ENFORCE_ONE_PER_IP = os.environ.get("ENFORCE_ONE_PER_IP", "0") == "1"

if USE_POSTGRES:
    import psycopg2  # only needed/installed on the cloud
    DB_PATH = DATABASE_URL  # for reference/logging only
else:
    # Local SQLite file. Point ATTENDANCE_DB at a shared/OneDrive folder to
    # share one database across laptops.
    DB_PATH = Path(os.environ.get("ATTENDANCE_DB", BASE_DIR / "your_database.db"))
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _connect():
    if USE_POSTGRES:
        # Managed Postgres (Supabase/Render) requires SSL. Add it if missing.
        if "sslmode" in DATABASE_URL:
            return psycopg2.connect(DATABASE_URL)
        return psycopg2.connect(DATABASE_URL, sslmode="require")
    return sqlite3.connect(DB_PATH)


def _q(sql):
    """SQLite uses ? placeholders; Postgres uses %s."""
    return sql.replace("?", "%s") if USE_POSTGRES else sql


def get_connection():
    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employee_attendance (
            user_id TEXT,
            timestamp TEXT,
            day TEXT,
            lat REAL,
            lon REAL,
            address TEXT,
            ip_address TEXT
        )
    """)

    # Ensure the 'day' column exists on older databases.
    if USE_POSTGRES:
        cursor.execute("ALTER TABLE employee_attendance ADD COLUMN IF NOT EXISTS day TEXT")
    else:
        cols = [r[1] for r in cursor.execute("PRAGMA table_info(employee_attendance)").fetchall()]
        if "day" not in cols:
            cursor.execute("ALTER TABLE employee_attendance ADD COLUMN day TEXT")
            cursor.execute("UPDATE employee_attendance SET day = substr(timestamp,1,10) WHERE day IS NULL")

    conn.commit()
    return conn


# ----------------------------------
# MARK ATTENDANCE
# ----------------------------------
def mark_attendance(user_id, role="employee", lat=None, lon=None, address=None, ip_address=None):
    conn = get_connection()
    cursor = conn.cursor()

    today = date.today().isoformat()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ❌ Rule 1: Same employee cannot mark twice in one day
    cursor.execute(_q("SELECT 1 FROM employee_attendance WHERE user_id = ? AND day = ?"),
                   (user_id, today))
    if cursor.fetchone():
        conn.close()
        return "USER_ALREADY"

    # ❌ Rule 2 (optional): Same device/IP cannot mark twice in one day.
    if ENFORCE_ONE_PER_IP and ip_address:
        cursor.execute(_q("SELECT 1 FROM employee_attendance WHERE ip_address = ? AND day = ?"),
                       (ip_address, today))
        if cursor.fetchone():
            conn.close()
            return "IP_BLOCKED"

    # ✅ Insert attendance
    cursor.execute(_q("""
        INSERT INTO employee_attendance
        (user_id, timestamp, day, lat, lon, address, ip_address)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """), (user_id, now, today, lat, lon, address, ip_address))

    conn.commit()
    conn.close()
    return "SUCCESS"


# ----------------------------------
# GET ATTENDANCE
# ----------------------------------
def get_attendance_list(role="employee", day=None):
    conn = get_connection()
    cursor = conn.cursor()

    if day:
        cursor.execute(_q("""
            SELECT user_id, timestamp, lat, lon, address
            FROM employee_attendance
            WHERE day = ?
            ORDER BY timestamp DESC
        """), (day,))
    else:
        cursor.execute("""
            SELECT user_id, timestamp, lat, lon, address
            FROM employee_attendance
            ORDER BY timestamp DESC
        """)

    data = cursor.fetchall()
    conn.close()
    return data


def get_days(month_prefix=None):
    """Return the distinct dates (YYYY-MM-DD) that have attendance.

    Pass month_prefix like '2026-07' to limit to one month.
    """
    conn = get_connection()
    cursor = conn.cursor()

    if month_prefix:
        cursor.execute(_q("""
            SELECT DISTINCT day FROM employee_attendance
            WHERE day LIKE ? ORDER BY day
        """), (month_prefix + "%",))
    else:
        cursor.execute("SELECT DISTINCT day FROM employee_attendance ORDER BY day")

    days = [r[0] for r in cursor.fetchall() if r[0]]
    conn.close()
    return days
