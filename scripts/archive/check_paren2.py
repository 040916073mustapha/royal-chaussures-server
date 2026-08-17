with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('system_prompt = os.getenv(')

# Count all parens from start to end of file
rest = content[start:]
in_dq = False
in_sq = False
depth = 0
max_depth = 0
last_100 = rest[-100:]

for i, c in enumerate(rest):
    if c == '"' and not in_sq:
        in_dq = not in_dq
    elif c == "'" and not in_dq:
        in_sq = not in_sq
    elif not in_dq and not in_sq:
        if c == '(':
            depth += 1
            max_depth = max(max_depth, depth)
        elif c == ')':
            depth -= 1

print(f"Final depth: {depth}")
print(f"Max depth: {max_depth}")
print(f"Rest starts from: {start}")
print(f"Total chars in rest: {len(rest)}")
