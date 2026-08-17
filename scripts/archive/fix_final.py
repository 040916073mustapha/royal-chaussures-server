with open('server_clean.py', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('system_prompt = os.getenv(')

# Find closing paren
rest = content[start:]
in_dq = False; in_sq = False; depth = 0
for i, c in enumerate(rest):
    if c == '"' and not in_sq: in_dq = not in_dq
    elif c == "'" and not in_sq: in_sq = not in_sq
    elif not in_dq and not in_sq:
        if c == '(': depth += 1
        elif c == ')': 
            depth -= 1
            if depth == 0:
                end = start + i + 1
                break

old_block = content[start:end]

# Extract the inner part of AI_SYSTEM_PROMPT
# The original: os.getenv(\n        "AI_SYSTEM_PROMPT",\n        "[1. ROYAL ...
# We need to take EVERYTHING after "AI_SYSTEM_PROMPT",\n

inner = old_block[len('system_prompt = os.getenv('):-1]  # exclude outer parens
# inner = '\n        "AI_SYSTEM_PROMPT",\n        "[1. ROYAL...'

# Remove the first line (the "AI_SYSTEM_PROMPT", part)
lines = inner.split('\n')
# First line is empty or has AI_SYSTEM_PROMPT
key_line = ''
default_lines = []
found_key = False
for line in lines:
    if '"AI_SYSTEM_PROMPT"' in line:
        found_key = True
        key_line = line
        # Extract everything after the comma
        comma_pos = line.find(',')
        rest_of_line = line[comma_pos+1:].strip()
        if rest_of_line:
            default_lines.append(rest_of_line)
        continue
    if found_key:
        stripped = line.rstrip()
        if stripped:
            default_lines.append(stripped)

print('Key line:', repr(key_line))
print('Default lines (first 3):')
for l in default_lines[:3]:
    print(repr(l))
print(f'Total default lines: {len(default_lines)}')
print('Last 3:')
for l in default_lines[-3:]:
    print(repr(l))

# Build the new block
new_block = 'system_prompt = os.getenv(\n'
new_block += '        "SYSTEM_PROMPT",\n'
new_block += '        os.getenv("AI_SYSTEM_PROMPT",\n'
new_block += '            ' + default_lines[0] + '\n'
for line in default_lines[1:]:
    new_block += '            ' + line.lstrip() + '\n'
new_block += '        )\n'
new_block += '    )'

print('\nNew block (first 300):')
print(new_block[:300])
print('\nNew block (last 300):')
print(new_block[-300:])

# Apply
new_content = content[:start] + new_block + content[end:]

# Verify
try:
    compile(new_content, 'test.py', 'exec')
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('\nSUCCESS: Valid syntax! Written to server.py')
except SyntaxError as e:
    print(f'\nSYNTAX ERROR: {e}')
    lines = new_content.split('\n')
    for i, l in enumerate(lines[330:340]):
        print(f'{331+i}: {l}')
    print('...')
    for i, l in enumerate(lines[380:390]):
        print(f'{381+i}: {l}')
