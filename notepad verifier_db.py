import sqlite3

db = "db_recup_14_aout.sqlite3"

conn = sqlite3.connect(db)

tables = conn.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name
""").fetchall()

print("TABLES :")
for table in tables:
    print("-", table[0])

conn.close()