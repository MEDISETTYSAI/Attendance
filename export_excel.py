import sqlite3
from datetime import datetime
from pathlib import Path
from openpyxl import Workbook


# ---------------- BASE PATHS (PROJECT-RELATIVE) ----------------
BASE_DIR = Path(__file__).resolve().parent

# Use the same DB your Flask app uses
DB_PATH = BASE_DIR / "your_database.db"

# Export folder inside your project
EXPORT_DIR = BASE_DIR / "attendance_reports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------- PICK DATE TO EXPORT ----------------
# Default = today. If you want a specific day, set like: EXPORT_DATE = "2026-02-11"
EXPORT_DATE = None  # or "YYYY-MM-DD"

if EXPORT_DATE:
    day = EXPORT_DATE
else:
    day = datetime.now().date().isoformat()


def column_exists(cursor, table: str, col: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    return any(r[1] == col for r in cursor.fetchall())


# ---------------- DB CONNECTION ----------------
if not DB_PATH.exists():
    raise FileNotFoundError(f"Database not found at: {DB_PATH}")

conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

# Check if location columns exist
has_lat = column_exists(cursor, "attendance", "lat")
has_lon = column_exists(cursor, "attendance", "lon")
has_address = column_exists(cursor, "attendance", "address")

# ---------------- FETCH STUDENT DATA (attendance + student_attendance) ----------------
if has_lat and has_lon and has_address:
    student_query = """
        SELECT user_id, timestamp, lat, lon, address
        FROM attendance
        WHERE DATE(timestamp) = ?
        UNION ALL
        SELECT user_id, timestamp, lat, lon, address
        FROM student_attendance
        WHERE DATE(timestamp) = ?
        ORDER BY timestamp
    """
    cursor.execute(student_query, (day, day))
    student_rows = cursor.fetchall()
    student_headers = ["S.No", "Student ID", "Timestamp", "Latitude", "Longitude", "Address", "Map Link"]
else:
    student_query = """
        SELECT user_id, timestamp
        FROM attendance
        WHERE DATE(timestamp) = ?
        UNION ALL
        SELECT user_id, timestamp
        FROM student_attendance
        WHERE DATE(timestamp) = ?
        ORDER BY timestamp
    """
    cursor.execute(student_query, (day, day))
    student_rows = cursor.fetchall()
    student_headers = ["S.No", "Student ID", "Timestamp"]

# ---------------- FETCH STAFF DATA (staff_attendance) ----------------
# Staff table may or may not have location columns too
has_lat_staff = column_exists(cursor, "staff_attendance", "lat")
has_lon_staff = column_exists(cursor, "staff_attendance", "lon")
has_address_staff = column_exists(cursor, "staff_attendance", "address")

if has_lat_staff and has_lon_staff and has_address_staff:
    staff_query = """
        SELECT user_id, timestamp, lat, lon, address
        FROM staff_attendance
        WHERE DATE(timestamp) = ?
        ORDER BY timestamp
    """
    cursor.execute(staff_query, (day,))
    staff_rows = cursor.fetchall()
    staff_headers = ["S.No", "Staff ID", "Timestamp", "Latitude", "Longitude", "Address", "Map Link"]
else:
    staff_query = """
        SELECT user_id, timestamp
        FROM staff_attendance
        WHERE DATE(timestamp) = ?
        ORDER BY timestamp
    """
    cursor.execute(staff_query, (day,))
    staff_rows = cursor.fetchall()
    staff_headers = ["S.No", "Staff ID", "Timestamp"]

conn.close()


# ---------------- CREATE EXCEL ----------------
wb = Workbook()

# ---- Students Sheet ----
ws_students = wb.active
ws_students.title = "Students"
ws_students.append(student_headers)

for idx, row in enumerate(student_rows, start=1):
    if len(row) >= 5:
        user_id, ts, lat, lon, addr = row
        map_link = f"https://www.google.com/maps?q={lat},{lon}" if lat is not None and lon is not None else ""
        ws_students.append([idx, user_id, ts, lat, lon, addr or "", map_link])
    else:
        ws_students.append([idx, row[0], row[1]])

# ---- Staff Sheet ----
ws_staff = wb.create_sheet(title="Staff")
ws_staff.append(staff_headers)

for idx, row in enumerate(staff_rows, start=1):
    if len(row) >= 5:
        user_id, ts, lat, lon, addr = row
        map_link = f"https://www.google.com/maps?q={lat},{lon}" if lat is not None and lon is not None else ""
        ws_staff.append([idx, user_id, ts, lat, lon, addr or "", map_link])
    else:
        ws_staff.append([idx, row[0], row[1]])


# ---------------- SAVE FILE ----------------
file_name = f"attendance_{day}.xlsx"
file_path = EXPORT_DIR / file_name
wb.save(str(file_path))

print(f"✅ Attendance exported successfully: {file_path}")
