import sqlite3
conn = sqlite3.connect("/app/data/evaluaciones_rh.db")
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("TABLES:", c.fetchall())
c.execute("SELECT * FROM test_sessions ORDER BY id DESC LIMIT 10")
rows = c.fetchall()
print("RECENT SESSIONS:")
for r in rows:
    print(r)
conn.close()
