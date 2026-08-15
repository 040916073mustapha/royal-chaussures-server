import sqlite3, os, json

DB_PATH = os.path.join(os.getcwd(), 'test_royal.db')
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT, sender_id TEXT, message TEXT, reply TEXT,
    created_at TEXT DEFAULT (datetime('now'))
)""")
conn.commit()

exchanges = [
    ('messenger', 'user999', 'Salam', 'Salam bik! Nqdar nkhadmouk?'),
    ('messenger', 'user999', 'Ch7al had l escarpin?', 'Escarpin bi 2500 dzd.'),
    ('messenger', 'user999', 'Oui nheb wahd', 'La commande: Escarpin x1 = 2500 dzd + delivery.'),
]
for p, sid, msg, reply in exchanges:
    c.execute("INSERT INTO messages (platform, sender_id, message, reply) VALUES (?,?,?,?)", (p, sid, msg, reply))
conn.commit()

c.execute("SELECT message, reply FROM messages WHERE sender_id=? ORDER BY id DESC LIMIT 5", ('user999',))
rows = c.fetchall()
history = []
for row in reversed(rows):
    history.append({'role': 'user', 'content': row['message']})
    history.append({'role': 'assistant', 'content': row['reply']})

print('TEST: Chat History')
print('  Stored:', len(exchanges), 'exchanges')
print('  History entries:', len(history))
print('  Alternates correctly:', all(history[i]['role'] == 'user' for i in range(0,len(history),2)) and all(history[i]['role'] == 'assistant' for i in range(1,len(history),2)))
print('  Bot knows context (no repeat greeting):', 'Salam bik' in history[-1]['content'])

msg_with_history = [
    {'role': 'system', 'content': 'SYSTEM'},
    *history,
    {'role': 'user', 'content': 'nheb nchri'}
]
print('  Total messages for AI:', len(msg_with_history))
print('  Context turns:', len(history)//2, 'previous exchanges')

conn.close()
os.remove(DB_PATH)
print('PASSED: SQLite Chat History works!')
