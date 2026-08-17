with open('server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start = None
end = None
for i, line in enumerate(lines):
    if 'def upsert_order_from_shopify' in line:
        start = i
    if start is not None and i > start and line.strip() == '':
        prev = lines[i-1].strip() if i > 0 else ''
        if 'logger.error' in prev:
            end = i
            break

print(f'Function lines {start} to {end}')
for i in range(start, end):
    print(f'{i}: {repr(lines[i])}')
