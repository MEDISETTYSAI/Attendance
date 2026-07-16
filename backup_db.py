"""
backup_db.py
------------
Makes a safe copy of the attendance database so data is never lost if the
main file gets corrupted, deleted, or the laptop dies.

- Uses SQLite's online backup API (safe to run while the server is live).
- One dated copy per day in the backups/ folder:
      backups/attendance_backup_YYYY-MM-DD.db
- Keeps the most recent KEEP_DAYS backups and deletes older ones.

Tip: point BACKUP_DIR at a OneDrive folder so backups sync OFF the laptop
automatically:
      BACKUP_DIR=C:\\Users\\yuva\\OneDrive\\OfficeAttendance\\backups
"""

import os
import sqlite3
from pathlib import Path
from datetime import date

from database import DB_PATH

BASE_DIR = Path(__file__).resolve().parent
BACKUP_DIR = Path(os.environ.get("BACKUP_DIR", BASE_DIR / "backups"))

# How many daily backups to keep before deleting the oldest.
KEEP_DAYS = int(os.environ.get("BACKUP_KEEP_DAYS", "30"))


def backup_database():
    """Create today's backup and prune old ones. Returns the backup path."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if not Path(DB_PATH).exists():
        print("[backup] No database file yet, nothing to back up.")
        return None

    today = date.today().isoformat()
    dest = BACKUP_DIR / f"attendance_backup_{today}.db"

    # Safe online backup (copies a consistent snapshot even mid-write).
    src = sqlite3.connect(str(DB_PATH))
    dst = sqlite3.connect(str(dest))
    try:
        with dst:
            src.backup(dst)
    finally:
        dst.close()
        src.close()

    print(f"[backup] Database backed up to {dest}")
    _prune_old_backups()
    return dest


def _prune_old_backups():
    backups = sorted(BACKUP_DIR.glob("attendance_backup_*.db"))
    for old in backups[:-KEEP_DAYS] if KEEP_DAYS > 0 else []:
        try:
            old.unlink()
            print(f"[backup] Removed old backup {old.name}")
        except OSError:
            pass


if __name__ == "__main__":
    backup_database()
