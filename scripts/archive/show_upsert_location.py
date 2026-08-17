"""Replace upsert_order_from_shopify try/finally - line by line"""
import ast

with open('server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the block we need to replace
start = None
end = None

for i, line in enumerate(lines):
    s = line.strip()
    if s == 'conn = get_orders_db()' and i > 90:
        start = i
    if start and s.startswith('except Exception as e:') and i > start + 5:
        # This is the UPSERT's except (not the outer try's except)
        # Check if the line BEFORE has 'conn.close()'
        if i > 0 and 'conn.close()' in lines[i-1]:
            end = i + 1  # include this line
            # Also include the next line if it's logger.error
            if i + 1 < len(lines) and 'logger.error' in lines[i+1]:
                end = i + 2

print(f'start={start}, end={end}')
if start and end:
    # Verify we found the right block
    print('Found block:')
    for j in range(start-1, min(end+8, len(lines))):
        print(f'{j+1}: {repr(lines[j])}')
