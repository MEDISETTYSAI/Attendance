from openpyxl import Workbook
from pathlib import Path
import sqlite3
from datetime import date

from database import DB_PATH  # single shared DB location

BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "attendance_reports"


def export_today_data():
    today = date.today().isoformat()

    REPORTS_DIR.mkdir(exist_ok=True)
    EXCEL_PATH = REPORTS_DIR / f"attendance_{today}.xlsx"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Make sure the table exists even if no one has marked yet.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employee_attendance (
            user_id TEXT, timestamp TEXT, lat REAL, lon REAL,
            address TEXT, ip_address TEXT
        )
    """)

    wb = Workbook()
    ws = wb.active
    ws.title = f"Attendance {today}"

    ws.append(["Employee ID", "Role", "Timestamp", "Latitude", "Longitude", "Address"])

    # Employee data
    cursor.execute("""
        SELECT user_id, timestamp, lat, lon, address
        FROM employee_attendance
        WHERE DATE(timestamp) = ?
    """, (today,))

    for row in cursor.fetchall():
        ws.append([row[0], "Employee", row[1], row[2], row[3], row[4]])

    conn.close()
    wb.save(EXCEL_PATH)

    print(f"[export] Excel updated: {EXCEL_PATH}")
    return EXCEL_PATH
