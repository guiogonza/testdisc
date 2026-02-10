import sqlite3
conn = sqlite3.connect("/app/data/evaluaciones_rh.db")
c = conn.cursor()
c.execute("SELECT * FROM candidates")
rows = c.fetchall()
print("CANDIDATES:")
for r in rows:
    print(r)
conn.close()
