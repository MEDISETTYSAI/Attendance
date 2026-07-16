"""
daily_export.py
---------------
Exports the day's attendance into an Excel sheet. Run it any time, or let
Windows Task Scheduler run it automatically after office hours (see below).

Manual run:
    python daily_export.py

Automatic run every day at 6:05 PM (Windows Task Scheduler, one-time setup):
    1. Open "Task Scheduler" -> Create Basic Task.
    2. Trigger: Daily, start time 18:05.
    3. Action: Start a program.
         Program/script:  python
         Add arguments:   daily_export.py
         Start in:        C:\\Users\\yuva\\Downloads\\Attendence
    4. Finish. It now writes attendance_reports\\attendance_<date>.xlsx daily,
       even if the web app is closed.
"""

from export_excel import export_today_data, export_month

if __name__ == "__main__":
    day_path = export_today_data()
    month_path = export_month()
    print("Done.")
    print(f"Today's sheet : {day_path}")
    print(f"Month workbook: {month_path}")
