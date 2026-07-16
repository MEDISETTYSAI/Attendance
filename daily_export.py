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

from export_excel import export_today_data

if __name__ == "__main__":
    path = export_today_data()
    print(f"Done. Today's attendance saved to:\n{path}")
