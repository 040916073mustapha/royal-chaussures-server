"""Add try/finally to all get_orders_db() callers without it"""
import re

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all functions where get_orders_db() is used without a try/finally
# We need to wrap: 
#   conn = get_orders_db()
#   ... operations ...
#   conn.close()
# Into:
#   conn = get_orders_db()
#   try:
#       ... operations (indented) ..
#   finally:
#       conn.close()

lines = content.split('\n')
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    s = line.strip()
    
    # Check if this line has conn = get_orders_db()
    if '= get_orders_db()' in s and not s.startswith('#'):
        # Look ahead to find if the next lines have try/finally
        has_try = False
        for j in range(i+1, min(i+3, len(lines))):
            if lines[j].strip().startswith('try:'):
                has_try = True
                break
        
        # Also check if conn.close() is at same indent level
        if not has_try:
            indent = line[:len(line) - len(line.lstrip())]
            # Find matching conn.close()
            for j in range(i+1, len(lines)):
                js = lines[j].strip()
                jindent = lines[j][:len(lines[j]) - len(lines[j].lstrip())]
                if js.startswith('conn.close()') and jindent == indent:
                    # This function doesn't have try/finally around get_orders_db
                    # Wrap the block between get_orders_db() and conn.close()
                    new_lines.append(line)  # conn = get_orders_db()
                    new_lines.append(indent + 'try:')
                    
                    # Everything between (i+1) and j should be indented one more level
                    for k in range(i+1, j):
                        kl = lines[k]
                        if kl.strip() and not kl.strip().startswith('#'):
                            new_lines.append('    ' + kl)
                        else:
                            new_lines.append(kl)
                    
                    # Close with finally
                    new_lines.append(indent + 'finally:')
                    new_lines.append(indent + '    try:')
                    new_lines.append(indent + '        conn.close()')
                    new_lines.append(indent + '    except:')
                    new_lines.append(indent + '        pass')
                    
                    i = j  # Skip to after conn.close()
                    break
                elif js.strip() == '':
                    continue
                elif jindent <= indent and not js.startswith('#'):
                    # We reached end of this block without finding conn.close
                    # Probably already has try/finally or different pattern
                    # Just pass through
                    new_lines.append(line)
                    break
    
    if i >= len(new_lines):
        new_lines.append(lines[i])
    i += 1

content = '\n'.join(new_lines)

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done adding try/finally wrappers")
