# Deploying the Office Attendance System to the Cloud (Render)

Result: one permanent link (e.g. `https://attendance-xxxx.onrender.com`) that
works without any laptop running. Attendance can still only be marked from the
**office Wi-Fi**. Data lives in a permanent cloud Postgres database.

Hosting = **Render** (free, doesn't expire — just sleeps when idle).
Database = **Supabase** (free Postgres, does NOT expire). Keeping the database
off Render avoids Render's time-limited free database.

## One-time setup

1. **Push the code to GitHub** (already done — repo: `MEDISETTYSAI/Attendance`).

2. **Create the database on Supabase** — https://supabase.com (free, GitHub login):
   - New project → choose any name + a strong database password → wait ~2 min.
   - **Connect** (top bar) → **Session pooler** → copy the URI. It looks like:
     `postgresql://postgres.xxxx:PASSWORD@aws-0-region.pooler.supabase.com:5432/postgres`
   - Put your real database password where it says `PASSWORD`.
   - (No need to create tables — the app creates them automatically.)

3. **Create a Render account** — https://render.com (sign in with GitHub, free).

4. **New → Blueprint** → select this repo. Render reads `render.yaml`.

5. When prompted, set the values marked "sync: false":
   - `DATABASE_URL` → paste the Supabase URI from step 2.
   - `ADMIN_PASSWORD` → choose your own admin password.
   - `OFFICE_NETWORKS` → leave blank for now; fill it in step 7.

6. Click **Apply / Deploy** and wait for it to go live.

7. **Whitelist your office Wi-Fi (important):**
   - On a device connected to the **office Wi-Fi**, open
     `https://<your-app>.onrender.com/whoami`
   - Copy the `your_ip` value (this is your office's public IP).
   - In Render → your service → **Environment** → set
     `OFFICE_NETWORKS = <that IP>` → **Save** (it redeploys).

Done. Share `https://<your-app>.onrender.com/employees` with staff.

## Daily use

- Employees: open the link **on office Wi-Fi**, enter Employee ID, Mark Attendance.
- Admin: `/admin-login` (user `BIXBI`, your password) → view + **Download Excel**.

## Notes / limits (free tier)

- The app **sleeps after ~15 min idle**; the first visit then takes ~30–50s to
  wake. Paid plans remove this.
- The office **public IP can change** if your ISP is dynamic. If marking suddenly
  fails for everyone, re-check `/whoami` and update `OFFICE_NETWORKS`. You can
  list several: `OFFICE_NETWORKS=1.2.3.4,5.6.7.8`.
- **Supabase** free tier pauses a project after ~1 week of *zero* activity; the
  data stays and any visit wakes it. Daily office use keeps it always awake.
- Your attendance data is permanent — it lives in Supabase, not on Render's
  temporary disk.

## Running locally (unchanged)

No `DATABASE_URL` set → uses local SQLite (`your_database.db`) automatically:

```powershell
python attendence_server.py
```
