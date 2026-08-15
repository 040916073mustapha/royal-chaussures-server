with open('server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the start and end of the try block
conn_line = None
conn_commit_line = None
except_line = None

for i, line in enumerate(lines):
    if 'conn = get_orders_db()' in line and i > 90:
        conn_line = i
    if conn_line and i > conn_line and 'conn.commit()' in line:
        conn_commit_line = i
    if conn_commit_line and i > conn_commit_line and 'except' in line.strip():
        except_line = i
        break

print(f"conn = get_orders_db() at line {conn_line}")
print(f"conn.commit() at line {conn_commit_line}")
print(f"except at line {except_line}")

if conn_line and conn_commit_line and except_line:
    indent = '        '
    
    # Create new lines
    new_lines = lines[:conn_line + 1]  # up to and including 'conn = get_orders_db()'
    new_lines.append(indent + 'try:\n')
    
    # Lines from conn.execute to conn.close - indent them
    # Actually we need to lines[conn_line+1] to except_line-1 as is, just make sure commmit is indented
    for j in range(conn_line + 1, conn_commit_line + 1):
        new_lines.append('    ' + lines[j])
    
    # The old conn.close() line should be between conn_commit_line and except_line
    # Skip it, we'll add finally
    # except Exception... + logger.error stays as is
    new_lines.append(indent + 'except Exception as e:\n')
    # Note: the logger.error line is at except_line+1 (or except_line+1+1 for blank)
    # Let's find it
    for j in range(except_line, except_line + 3):
        if 'logger.error' in lines[j]:
            new_lines.append(8*' ' + lines[j])
            
    new_lines.append(indent + 'finally:\n')
    new_lines.append(indent + '    try:\n')
    new_lines.append(indent + '        conn.close()\n')
    new_lines.append(indent + '    except:\n')
    new_lines.append(indent + '        pass\n')
    
    # Skip remaining lines up to the blank line
    # Find blank line after except block
    after_except = except_line + 3
    while after_except < len(lines) and lines[after_except].strip():
        after_except += 1
    
    # Add remaining lines
    new_lines.extend(lines[after_except:])
    
    with open('server.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("File updated successfully")
    
    # Verify syntax
    import ast
    try:
        with open('server.py', 'r', encoding='utf-8') as f2:
            ast.parse(f2.read())
        print("Syntax OK!")
    except SyntaxError as e:
        print(f"SyntaxError: {e}")
else:
    print("Could not find block")
