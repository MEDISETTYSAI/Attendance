import os
import re
import socket
from datetime import date
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from database import get_attendance_list, mark_attendance

# -------------------------------------------------
# APP SETUP
# -------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "CHANGE_ME_TO_RANDOM_SECRET")

# -------------------------------------------------
# OFFICE SETTINGS
# -------------------------------------------------
OFFICE_NAME = "BIXBI"
ROLL_REGEX = rf"^{OFFICE_NAME}-[A-Za-z0-9]{{1,15}}$"

# -------------------------------------------------
# STAFF LOGIN CREDENTIALS
# -------------------------------------------------
STAFF_USERS = {
    "BIXBI": "BIXBI-123"
}

ALLOW_MULTIPLE_STUDENTS_PER_SYSTEM = True

# -------------------------------------------------
# HOME PAGE
# -------------------------------------------------
@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MakeMyTechnology</title>
        <style>
            body {
                margin: 0;
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                font-family: Arial, sans-serif;
                background: #f5f7fa;
            }
            .container { text-align: center; }
            h1 { font-size: 48px; margin-bottom: 20px; }
            a {
                display: inline-block;
                padding: 12px 30px;
                font-size: 18px;
                text-decoration: none;
                background-color: #007bff;
                color: white;
                border-radius: 6px;
            }
            a:hover { background-color: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>MAKE<span style="color:red">MY</span>TECHNOLOGY</h1>
            <a href="/dashboard">Go to Dashboard</a>
        </div>
    </body>
    </html>
    """

# -------------------------------------------------
# DASHBOARD
# -------------------------------------------------
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# -------------------------------------------------
# STUDENT DASHBOARD
# -------------------------------------------------
@app.route("/students")
def students():
    day = request.args.get("date")
    if not day:
        day = date.today().isoformat()

    attendance = get_attendance_list("student", day)

    return render_template(
        "attendance_html.html",
        attendance=attendance,
        role="student",
        title="Student Attendance",
        selected_date=day
    )

# -------------------------------------------------
# STAFF LOGIN
# -------------------------------------------------
@app.route("/staff-login", methods=["GET", "POST"])
def staff_login():
    if request.method == "POST":
        login_id = request.form.get("login_id")
        password = request.form.get("password")

        if STAFF_USERS.get(login_id) == password:
            session["staff"] = True
            session["staff_user"] = login_id
            return redirect(url_for("staff"))

        return "Invalid Staff Login ID or Password", 403

    return render_template("staff_html.html")

# -------------------------------------------------
# STAFF LOGOUT
# -------------------------------------------------
@app.route("/staff-logout")
def staff_logout():
    session.clear()
    return redirect(url_for("dashboard"))

# -------------------------------------------------
# STAFF DASHBOARD
# -------------------------------------------------
@app.route("/staff")
def staff():
    if not session.get("staff"):
        return redirect(url_for("staff_login"))

    attendance = get_attendance_list("staff")
    return render_template(
        "attendance_html.html",
        attendance=attendance,
        role="staff",
        title="Staff Attendance"
    )

# -------------------------------------------------
# MARK ATTENDANCE API
# -------------------------------------------------
@app.route("/mark-attendance", methods=["POST"])
def mark_attendance_api():
    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")
    role = data.get("role")
    lat = data.get("lat")
    lon = data.get("lon")
    address = data.get("address")

    if not user_id:
        return jsonify({"error": "ID is required"}), 400

    if role == "student":
        if not re.match(ROLL_REGEX, user_id):
            return jsonify({"error": "Invalid Student ID format"}), 400

        result = mark_attendance(user_id, role, lat, lon, address)

        if result:
            return jsonify({"message": "Student attendance marked successfully"}), 200

        return jsonify({"message": "Attendance already marked today"}), 409

    if role == "staff":
        if not session.get("staff"):
            return jsonify({"error": "Unauthorized"}), 403

        if not re.match(ROLL_REGEX, user_id):
            return jsonify({"error": "Invalid Staff ID format"}), 400

        result = mark_attendance(user_id, role)

        return jsonify({
            "message": "Staff attendance marked successfully"
            if result else "Attendance already marked today"
        }), 200

    return jsonify({"error": "Invalid role"}), 400

# -------------------------------------------------
# CLOUD SERVER START
# -------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
