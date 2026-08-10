with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('system_prompt = os.getenv(')
rest = content[idx:]

depth = 0
in_dq = False
in_sq = False
escape = False
for i, c in enumerate(rest):
    if escape:
        escape = False
        continue
    if c == '\\' and (in_dq or in_sq):
        escape = True
        continue
    if c == '"' and not in_sq:
        in_dq = not in_dq
        continue
    if c == "'" and not in_dq:
        in_sq = not in_sq
        continue
    if in_dq or in_sq:
        continue
    if c == '(':
        depth += 1
    elif c == ')':
        depth -= 1
        if depth == 0:
            print(f'Closing paren at position {i} from start of block')
            context_start = max(0, i-40)
            print(f'Context: ...{repr(rest[context_start:i+10])}...')
            break
else:
    print(f'NEVER FOUND CLOSING PAREN! Last depth: {depth}')
    print('Last 500 chars of region:')
    print(repr(rest[-500:]))
