from openpyxl import Workbook
from pathlib import Path
from datetime import date

from database import get_attendance_list

BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "attendance_reports"


def export_today_data():
    today = date.today().isoformat()

    REPORTS_DIR.mkdir(exist_ok=True)
    EXCEL_PATH = REPORTS_DIR / f"attendance_{today}.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.title = f"Attendance {today}"

    ws.append(["Employee ID", "Role", "Timestamp", "Latitude", "Longitude", "Address"])

    for row in get_attendance_list("employee", today):
        ws.append([row[0], "Employee", row[1], row[2], row[3], row[4]])

    wb.save(EXCEL_PATH)

    print(f"[export] Excel updated: {EXCEL_PATH}")
    return EXCEL_PATH


def export_all_data():
    """Export the FULL attendance history (all days) into one Excel file."""
    REPORTS_DIR.mkdir(exist_ok=True)
    EXCEL_PATH = REPORTS_DIR / "attendance_full_report.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.title = "All Attendance"

    ws.append(["Employee ID", "Role", "Timestamp", "Latitude", "Longitude", "Address"])

    for row in get_attendance_list("employee", None):
        ws.append([row[0], "Employee", row[1], row[2], row[3], row[4]])

    wb.save(EXCEL_PATH)

    print(f"[export] Full report written: {EXCEL_PATH}")
    return EXCEL_PATH
