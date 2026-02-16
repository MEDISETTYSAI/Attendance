from datetime import date
import sqlite3

DB_NAME = "attendance.db"

def process_attendance(user_id):
    if not user_id:
        return {"message": "User ID is required"}, 400

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    today = date.today().isoformat()

    # Check if attendance already marked today
    cursor.execute("""
        SELECT 1 FROM attendance
        WHERE user_id = ?
        AND DATE(timestamp) = ?
    """, (user_id, today))

    already_marked = cursor.fetchone()

    if already_marked:
        conn.close()
        return {
            "message": "Today's attendance already completed"
        }, 409

    # Insert attendance
    cursor.execute("""
        INSERT INTO attendance (user_id)
        VALUES (?)
    """, (user_id,))

    conn.commit()
    conn.close()

    return {
        "message": "Attendance marked successfully"
    }, 200
