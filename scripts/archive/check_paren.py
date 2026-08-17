with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('system_prompt = os.getenv(')

# Find the closing paren that belongs to this block
rest = content[start:]
in_dq = False
in_sq = False
depth = 0
for i, c in enumerate(rest):
    if c == '"' and not in_sq:
        in_dq = not in_dq
    elif c == "'" and not in_dq:
        in_sq = not in_sq
    elif not in_dq and not in_sq:
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                end = start + i + 1
                break

print(f'Block from {start} to {end}')
print('After closing paren:', repr(content[end:end+30]))

# Count indent of the first line
indent = 0
for c in content[start:]:
    if c == ' ':
        indent += 1
    else:
        break
print(f'Base indent: {indent} spaces')
