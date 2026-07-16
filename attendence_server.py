import os
import re
from datetime import date

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file

from database import get_attendance_list, mark_attendance
from wifi_guard import is_on_office_wifi, get_client_ip, OFFICE_NETWORKS_RAW
import schedule
import time
import threading
from export_excel import export_today_data


# Time of day (24h "HH:MM") for the automatic daily Excel export.
EXPORT_TIME = os.environ.get("EXPORT_TIME", "18:00")


# ---------------- Scheduler ----------------
def run_scheduler():
    # Write a full copy of the day's sheet at the configured time every day.
    schedule.every().day.at(EXPORT_TIME).do(export_today_data)

    while True:
        schedule.run_pending()
        time.sleep(60)


# ---------------- Flask Setup ----------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "CHANGE_ME_TO_RANDOM_SECRET")

# Company / office short-code used inside every employee ID.
OFFICE_NAME = os.environ.get("OFFICE_NAME", "BIXBI")
# Employee ID format, e.g. "BIXBI-EMP001"
EMP_ID_REGEX = rf"^{OFFICE_NAME}-[A-Za-z0-9]{{1,15}}$"

# Admin accounts that can view the attendance dashboard.
ADMIN_USERS = {
    os.environ.get("ADMIN_USER", "BIXBI"): os.environ.get("ADMIN_PASSWORD", "BIXBI-123")
}


# ---------------- Home ----------------
@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Office Attendance</title>
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
            <a href="/employees">Mark / View Attendance</a>
        </div>
    </body>
    </html>
    """


# ---------------- Whoami (setup helper) ----------------
@app.route("/whoami")
def whoami():
    """
    Open this URL on a device connected to the office Wi-Fi to discover the IP
    the server sees. Copy that IP into the OFFICE_NETWORKS env var to whitelist
    your office. Also tells you whether you are currently recognised as office.
    """
    allowed, client_ip = is_on_office_wifi(request)
    return jsonify({
        "your_ip": client_ip,
        "on_office_wifi": allowed,
        "whitelisted_networks": OFFICE_NETWORKS_RAW,
        "hint": "Add 'your_ip' to the OFFICE_NETWORKS setting to allow this network."
    })


# ---------------- Employee Dashboard ----------------
@app.route("/employees")
def employees():
    day = request.args.get("date")
    if not day:
        day = date.today().isoformat()

    attendance = get_attendance_list("employee", day)

    return render_template(
        "attendance_html.html",
        attendance=attendance,
        role="employee",
        title="Employee Attendance",
        selected_date=day
    )


# Keep the old /students URL working -> redirect to /employees
@app.route("/students")
def students_redirect():
    return redirect(url_for("employees", **request.args))


# ---------------- Admin Login ----------------
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        login_id = request.form.get("login_id")
        password = request.form.get("password")

        if ADMIN_USERS.get(login_id) == password:
            session["admin"] = True
            session["admin_user"] = login_id
            return redirect(url_for("admin"))

        return "Invalid Admin Login ID or Password", 403

    return render_template("staff_html.html")


# ---------------- Admin Logout ----------------
@app.route("/admin-logout")
def admin_logout():
    session.clear()
    return redirect(url_for("employees"))


# ---------------- Admin Dashboard ----------------
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    day = request.args.get("date") or date.today().isoformat()
    attendance = get_attendance_list("employee", day)
    return render_template(
        "attendance_html.html",
        attendance=attendance,
        role="employee",
        title="Employee Attendance (Admin)",
        selected_date=day,
        show_download=True
    )


# ---------------- Download Excel (Admin) ----------------
@app.route("/download-excel")
def download_excel():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    excel_path = export_today_data()
    return send_file(excel_path, as_attachment=True)


# ---------------- Mark Attendance ----------------
@app.route("/mark-attendance", methods=["POST"])
def mark_attendance_api():
    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")
    lat = data.get("lat")
    lon = data.get("lon")
    address = data.get("address")

    if not user_id:
        return jsonify({"error": "Employee ID is required"}), 400

    if not re.match(EMP_ID_REGEX, user_id):
        return jsonify({
            "error": f"Invalid Employee ID. Expected format: {OFFICE_NAME}-XXXX"
        }), 400

    # 🔒 Office Wi-Fi check -----------------------------------------------
    allowed, client_ip = is_on_office_wifi(request)
    print("Client IP:", client_ip, "| On office Wi-Fi:", allowed)

    if not allowed:
        return jsonify({
            "error": "You must be connected to the OFFICE Wi-Fi to mark attendance"
        }), 403
    # ---------------------------------------------------------------------

    result = mark_attendance(user_id, "employee", lat, lon, address, client_ip)

    if result == "SUCCESS":
        # Keep today's Excel sheet up to date after every mark.
        try:
            export_today_data()
        except Exception as e:
            print("Excel export failed:", e)
        return jsonify({"message": "Attendance marked successfully"}), 200

    elif result == "USER_ALREADY":
        return jsonify({"message": "You have already marked attendance today"}), 409

    elif result == "IP_BLOCKED":
        return jsonify({"message": "This device already marked attendance today"}), 403

    return jsonify({"error": "Unknown error"}), 500


# ---------------- Run Server ----------------
if __name__ == "__main__":
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()

    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
