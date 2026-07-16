# Deploying the Office Attendance System to the Cloud (Render)

Result: one permanent link (e.g. `https://attendance-xxxx.onrender.com`) that
works without any laptop running. Attendance can still only be marked from the
**office Wi-Fi**. Data lives in a permanent cloud Postgres database.

## One-time setup

1. **Push the code to GitHub** (already done — repo: `MEDISETTYSAI/Attendance`).

2. **Create a Render account** — https://render.com (sign in with GitHub, free).

3. **New → Blueprint** → select this repo. Render reads `render.yaml` and creates
   both the **web service** and a **free Postgres database**, already linked.

4. When prompted, set the two values marked "sync: false":
   - `ADMIN_PASSWORD` → choose your own admin password.
   - `OFFICE_NETWORKS` → leave blank for now; you'll fill it in step 6.

5. Click **Apply / Deploy** and wait for it to go live.

6. **Whitelist your office Wi-Fi (important):**
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
- Render's **free Postgres expires after 90 days** — before then, upgrade the DB
  or export your data. (Supabase is a free alternative with no expiry.)

## Running locally (unchanged)

No `DATABASE_URL` set → uses local SQLite (`your_database.db`) automatically:

```powershell
python attendence_server.py
```
