with open('server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line with "conn = get_orders_db()" in upsert (after "variant =")
in_upsert = False
upsert_conn_line = None
upsert_commit_line = None

for i, line in enumerate(lines):
    if 'def upsert_order_from_shopify' in line:
        in_upsert = True
    if in_upsert and "conn = get_orders_db()" in line:
        upsert_conn_line = i
    if in_upsert and "conn.commit()" in line:
        upsert_commit_line = i
    if in_upsert and "def " in line and i > upsert_conn_line if upsert_conn_line else False:
        break

print(f"conn = get_orders_db() at line {upsert_conn_line}")
print(f"conn.commit() at line {upsert_commit_line}")

if upsert_conn_line is not None and upsert_commit_line is not None:
    # Check if try already exists
    if 'try:' not in lines[upsert_conn_line + 1]:
        # Get the indent level
        indent = lines[upsert_conn_line][:len(lines[upsert_conn_line]) - len(lines[upsert_conn_line].lstrip())]
        
        # Add try: after conn = get_orders_db()
        lines.insert(upsert_conn_line + 1, indent + 'try:\n')
        
        # Shift the commit/close line indices
        upsert_commit_line += 1  # because we inserted try
        
        # Indent lines between try and commit by adding one more level
        conn_close_line = None
        for j in range(upsert_conn_line + 2, len(lines)):
            if lines[j].strip().startswith('conn.close()') and lines[j].startswith(indent):
                conn_close_line = j
                break
            # Indent this line (inside try block)
            if lines[j].strip() and not lines[j].strip().startswith('except') and not lines[j].strip().startswith('finally'):
                # Only indent at the same level as the initial block
                if lines[j].startswith(indent) and not lines[j].strip().startswith('#'):
                    before = lines[j][:len(lines[j]) - len(lines[j].lstrip())]
                    if before == indent:
                        lines[j] = '    ' + lines[j]
        
        if conn_close_line:
            # Replace "    conn.commit()\n    conn.close()" with just "    conn.commit()"
            lines[upsert_commit_line] = indent + '    conn.commit()\n'
            # Remove the old conn.close() line
            if conn_close_line > upsert_commit_line:
                close_content = lines[conn_close_line].strip()
                if close_content.startswith('conn.close()'):
                    # Replace it with except/finally block
                    lines[conn_close_line] = indent + 'except Exception as e:\n'
                    lines[conn_close_line] += indent + '    logger.error(f"upsert error: {_safe_str(e)}")\n'
                    lines.insert(conn_close_line + 2, indent + 'finally:\n')
                    lines.insert(conn_close_line + 3, indent + '    try:\n')
                    lines.insert(conn_close_line + 4, indent + '        conn.close()\n')
                    lines.insert(conn_close_line + 5, indent + '    except:\n')
                    lines.insert(conn_close_line + 6, indent + '        pass\n')
                    print("Added try/finally block")
        
        with open('server.py', 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("Done - file written")
    else:
        print("try already exists")
else:
    print("Could not find upsert block")
