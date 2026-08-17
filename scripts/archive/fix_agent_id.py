# fix_agent_id.py - Fix NameError for agent_id in logging/error handling

path = r'C:\Users\Micro-Tech\.openclaw\workspace\server_complete.py'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the logging line that references agent_id in error context
# Pattern: logger.info(f"...agent_id...)
import re

# Find all lines that use agent_id variable
lines = content.split('\n')
print('Lines referencing agent_id:')
for i, line in enumerate(lines):
    if 'agent_id' in line:
        print(f'  {i+1}: {line.strip()[:100]}')

# The problematic line: 
# logger.info(f"[Agent:{agent_id}] AI={used_ai} Platform={platform} UID={uid[:20]}")
# This was in get_atlas_response but might remain elsewhere

# Replace this specific pattern in any get_atlas_response or similar functions
old_pattern = "logger.info(f\"[Agent:{agent_id}] AI={used_ai} Platform={platform} UID={uid[:20]}\")"
# Since agent_id and used_ai are undefined, remove this log line or fix it
new_pattern = "# logger.info(f\"[Agent:default] AI=deepseek Platform={platform} UID={uid[:20]}\")"

if old_pattern in content:
    content = content.replace(old_pattern, new_pattern)
    print('\nFixed agent_id reference in logger line')
else:
    # Try without f-string - raw string
    print('\nExact pattern not found - looking for similar...')
    for i, line in enumerate(lines):
        if 'agent_id' in line and 'logger' in line:
            lines[i] = '# ' + line.rstrip() + '  # commented: agent_id undefined'
            print(f'  Commented line {i+1}: {line.strip()[:80]}')
    content = '\n'.join(lines)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

# Also check for agent_id in test functions
test_count = len(re.findall(r'agent_id', content))
print(f'\nTotal agent_id references remaining: {test_count}')

import py_compile
try:
    py_compile.compile(path, doraise=True)
    print('Syntax: OK')
except py_compile.PyCompileError as e:
    print(f'Syntax error: {e}')
