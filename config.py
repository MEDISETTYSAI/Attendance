from datetime import time
import socket

# ================= OFFICE SETTINGS =================

def get_local_ip():
    """
    Returns the local IP address of the Windows laptop
    """
    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except:
        return None


LOCAL_IP = get_local_ip()

OFFICE_START_TIME = time(9, 0)     # 09:00 AM
OFFICE_END_TIME = time(18, 0)      # 06:00 PM

# ================= EXPORT SETTINGS =================
EXPORT_TIME = "18:00"              # 6 PM

# ================= DATABASE =================
DB = "attendance.db"
