import sqlite3

conn = sqlite3.connect('rcagents.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print('Tables:', tables)
for t in tables:
    c.execute(f"SELECT COUNT(*) FROM [{t}]")
    cnt = c.fetchone()[0]
    print(f'  {t}: {cnt} rows')

# Last messages
if 'messages' in tables:
    c.execute("SELECT * FROM messages ORDER BY id DESC LIMIT 8")
    for r in c.fetchall():
        print('  MSG:', r)
elif 'conversations' in tables:
    c.execute("SELECT * FROM conversations ORDER BY updated_at DESC LIMIT 5")
    for r in c.fetchall():
        print('  CONV:', r)

conn.close()
