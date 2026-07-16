import os
import sqlite3
from datetime import datetime, date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "your_database.db"

# One-device-per-day rule.
#   On-premise (each device has its own private LAN IP) -> safe to enable ("1").
#   Cloud deploy (ALL office devices share the office's single public IP)
#       -> MUST stay off ("0"), otherwise only the first employee could mark.
ENFORCE_ONE_PER_IP = os.environ.get("ENFORCE_ONE_PER_IP", "0") == "1"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employee_attendance (
        user_id TEXT,
        timestamp TEXT,
        lat REAL,
        lon REAL,
        address TEXT,
        ip_address TEXT
    )
    """)

    conn.commit()
    return conn


def _table_for(role):
    # Every role currently maps to employees; kept as a hook for future roles.
    return "employee_attendance"


# ----------------------------------
# MARK ATTENDANCE
# ----------------------------------
def mark_attendance(user_id, role="employee", lat=None, lon=None, address=None, ip_address=None):
    conn = get_connection()
    cursor = conn.cursor()

    today = date.today().isoformat()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    table = _table_for(role)

    # ❌ Rule 1: Same employee cannot mark twice in one day
    cursor.execute(f"""
        SELECT 1 FROM {table}
        WHERE user_id = ?
        AND DATE(timestamp) = ?
    """, (user_id, today))

    if cursor.fetchone():
        conn.close()
        return "USER_ALREADY"

    # ❌ Rule 2 (optional): Same device/IP cannot mark twice in one day.
    # Disabled by default because a shared office Wi-Fi presents one public IP
    # for everyone. Enable only when the server runs on the office LAN.
    if ENFORCE_ONE_PER_IP and ip_address:
        cursor.execute(f"""
            SELECT 1 FROM {table}
            WHERE ip_address = ?
            AND DATE(timestamp) = ?
        """, (ip_address, today))

        if cursor.fetchone():
            conn.close()
            return "IP_BLOCKED"

    # ✅ Insert attendance
    cursor.execute(f"""
        INSERT INTO {table}
        (user_id, timestamp, lat, lon, address, ip_address)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, now, lat, lon, address, ip_address))

    conn.commit()
    conn.close()

    return "SUCCESS"


# ----------------------------------
# GET ATTENDANCE
# ----------------------------------
def get_attendance_list(role="employee", day=None):
    conn = get_connection()
    cursor = conn.cursor()

    table = _table_for(role)

    if day:
        cursor.execute(f"""
            SELECT user_id, timestamp, lat, lon, address
            FROM {table}
            WHERE DATE(timestamp) = ?
            ORDER BY timestamp DESC
        """, (day,))
    else:
        cursor.execute(f"""
            SELECT user_id, timestamp, lat, lon, address
            FROM {table}
            ORDER BY timestamp DESC
        """)

    data = cursor.fetchall()
    conn.close()
    return data
