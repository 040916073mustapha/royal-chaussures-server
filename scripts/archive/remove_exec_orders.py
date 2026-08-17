import ast

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = (
    'def exec_orders(sql, params=None, fetch=False, fetchone=False):\n'
    '    """Execute SQL on orders DB with auto-close"""\n'
    '    conn = get_orders_db()\n'
    '    try:\n'
    '        c = conn.cursor()\n'
    '        if params:\n'
    '            c.execute(sql, params)\n'
    '        else:\n'
    '            c.execute(sql)\n'
    '        if fetchone:\n'
    '            result = c.fetchone()\n'
    '        elif fetch:\n'
    '            result = c.fetchall()\n'
    '        else:\n'
    '            conn.commit()\n'
    '            result = c.lastrowid\n'
    '        return result\n'
    '    finally:\n'
    '        conn.close()\n'
    '\n'
    '\n'
)

if old in content:
    content = content.replace(old, '', 1)
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Removed exec_orders')
    ast.parse(content)
    print('Syntax OK!')
else:
    print('exec_orders NOT found')
    # try with \r\n
    old_cr = old.replace('\n', '\r\n')
    if old_cr in content:
        print('Found with CRLF')
    else:
        print('Not found with CRLF either')
