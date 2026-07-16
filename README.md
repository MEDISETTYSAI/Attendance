# Office Employee Attendance System

A small web app that runs on an **office laptop**. Employees open a link in
their browser and mark attendance — but only if their device is **connected to
the office Wi-Fi**. Every mark is saved to a database and written into
**monthly Excel workbooks** automatically.

---

## 1. How it works (overview)

1. You run the app on the office laptop.
2. Employees on the **office Wi-Fi** open the link, type their Employee ID, and
   click **Mark Attendance**.
3. The server checks the ID and confirms the device is on office Wi-Fi, then
   saves the record.
4. Excel reports refresh automatically; a database backup is taken daily.

Anyone **not** on the office Wi-Fi is refused — that is the core rule.

> **Why Wi-Fi = IP:** a website cannot read the Wi-Fi name. It only sees the
> device's IP address. Your office router gives every connected device an IP
> like `192.168.1.x`, so the app whitelists that range. On office Wi-Fi → allowed.
> On mobile data / other Wi-Fi → blocked.

---

## 2. Setup (one time)

Python must be installed.

```powershell
cd C:\Users\yuva\Downloads\Attendence
pip install -r requirements.txt
```

---

## 3. Run it

```powershell
python attendence_server.py
```

The terminal prints an address such as `http://192.168.1.15:8000`.
Share **`http://<that-ip>:8000/employees`** with employees on the office Wi-Fi.

Stop the server with `Ctrl + C`.

---

## 4. Pages

| URL | Who | Purpose |
|-----|-----|---------|
| `/employees` | Employees | Enter ID → Mark Attendance |
| `/whoami` | Setup | Shows the IP the server sees + whether it counts as office |
| `/admin-login` | Admin | Log in (`BIXBI` / password) |
| `/admin` | Admin | View list, filter by date, download Excel |
| `/download-excel` | Admin | Download today's sheet |
| `/download-month` | Admin | Download the whole month's workbook |

---

## 5. Rules enforced when marking

- ID must match the format `BIXBI-XXXX`.
- Device must be on the office Wi-Fi (IP in the whitelist).
- Each employee can mark **once per day**.

---

## 6. Automatic tasks (while the app runs)

- **After every mark** → Excel reports refresh instantly.
- **Daily 6:00 PM** → the month's workbook is rebuilt.
- **Daily 6:05 PM** → a safe database backup is saved.

You can also export any time without the app running:

```powershell
python daily_export.py
```

(Optionally schedule that with Windows Task Scheduler — see the top of
`daily_export.py`.)

---

## 7. Where data is stored

| What | Location |
|------|----------|
| Live database (source of truth) | `your_database.db` |
| Monthly Excel reports | `attendance_reports/attendance_YYYY-MM.xlsx` |
| Daily database backups (30 kept) | `backups/attendance_backup_YYYY-MM-DD.db` |

### Monthly Excel structure

```
attendance_2026-07.xlsx
├── Summary          ← each date + how many present
├── Employee Totals  ← per employee: days present, working days, attendance %
├── 2026-07-16       ← everyone who marked on the 16th
├── 2026-07-17       ← the 17th…
└── …                ← a new tab each day
```

A new file starts automatically each month; older months stay untouched.

---

## 8. Settings (environment variables, optional)

| Variable | Default | Meaning |
|----------|---------|---------|
| `OFFICE_NETWORKS` | `192.168.1.0/24` | Allowed office network(s). Set to your Wi-Fi's IP range. |
| `OFFICE_NAME` | `BIXBI` | Prefix in every Employee ID. |
| `ADMIN_USER` / `ADMIN_PASSWORD` | `BIXBI` / `BIXBI-123` | Admin login. |
| `EXPORT_TIME` | `18:00` | Time of the daily Excel export. |
| `ATTENDANCE_DB` | (local file) | Point at a shared/OneDrive path to share one DB across laptops. |

Example (PowerShell, before running):

```powershell
$env:OFFICE_NETWORKS = "192.168.1.0/24"
python attendence_server.py
```

---

## 9. Troubleshooting

- **"You must be connected to the OFFICE Wi-Fi"** even though you are:
  open `/whoami`, copy `your_ip`, and set `OFFICE_NETWORKS` to match
  (e.g. `192.168.0.0/24` or `10.0.0.0/24`).
- **Nobody can reach the link:** the laptop must be running the app and stay on
  the office Wi-Fi. If the laptop's IP changed, share the new address (reserve a
  static IP on the router to keep it fixed).
- **"Failed to load" right after starting:** the server was mid-restart — just
  refresh.
```
