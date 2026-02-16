import sqlite3

conn = sqlite3.connect("your_database.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM attendance")
rows = cursor.fetchall()

print("ID | USER_ID | TIMESTAMP")
print("-" * 40)

for row in rows:
    print(row)

conn.close()
