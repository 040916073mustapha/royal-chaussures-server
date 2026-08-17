# fix_unpack.py - Fix "too many values to unpack (expected 3)" error
# The old code expected: reply, agent_id, used_ai = get_ai_response(...)
# But get_ai_response returns only 1 value (the reply string)

path = r'C:\Users\Micro-Tech\.openclaw\workspace\server_complete.py'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find all occurrences where return value is unpacked into 3
# Pattern: variable1, variable2, variable3 = get_ai_response(
import re

# Find all patterns like "x, y, z = get_ai_response("
pattern = r'(\w+),\s*(\w+),\s*(\w+)\s*=\s*get_ai_response\s*\('
matches = list(re.finditer(pattern, content))

print(f'Found {len(matches)} unpack patterns:')
for m in matches:
    # Find the start of the line
    line_start = content.rfind('\n', 0, m.start()) + 1
    line_num = content[:m.start()].count('\n') + 1
    print(f'  Line {line_num}: {m.group(0)[:60]}...')
    
    # Replace with single variable = get_ai_response(
    # Use the first variable name to store the result
    first_var = m.group(1)
    old = m.group(0)
    new = f'{first_var} = get_ai_response('
    content = content.replace(old, new)

# Count remaining unpack patterns
remaining = re.findall(pattern, content)
print(f'Remaining unpack patterns: {len(remaining)}')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

import py_compile
try:
    py_compile.compile(path, doraise=True)
    print('Syntax: OK')
except py_compile.PyCompileError as e:
    print(f'Syntax error: {e}')
