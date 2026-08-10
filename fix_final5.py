with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('system_prompt = os.getenv(')
rest = content[start:]
target_end = 'in your raw response."'
idx = rest.find(target_end)
close_paren = rest.find(')', idx)
end = start + close_paren + 1

old_block = content[start:end]

# Extract everything after the first line (which has "AI_SYSTEM_PROMPT",)
# and BEFORE the closing paren
lines = old_block.split('\n')

# First line: '    system_prompt = os.getenv('
# Need to find "AI_SYSTEM_PROMPT" line and extract everything from there
key_line_idx = None
for i, line in enumerate(lines):
    if '"AI_SYSTEM_PROMPT"' in line:
        key_line_idx = i
        break

# The default value starts on key_line_idx after the comma
key_line = lines[key_line_idx]
comma_pos = key_line.find(',')
first_default = key_line[comma_pos+1:].strip()

# All subsequent lines until the closing paren line
default_lines = [first_default]
for line in lines[key_line_idx+1:-1]:  # exclude the last ')' line
    stripped = line.rstrip()
    if stripped.strip():
        default_lines.append(stripped)

# Now build new block
new_block = '    system_prompt = os.getenv(\n'
new_block += '        "SYSTEM_PROMPT",\n'
new_block += '        os.getenv(\n'
new_block += '            "AI_SYSTEM_PROMPT",\n'
for dl in default_lines:
    new_block += '            ' + dl.strip() + '\n'
new_block += '        )\n'
new_block += '    )'

new_content = content[:start] + new_block + content[end:]

try:
    compile(new_content, 'test.py', 'exec')
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('SUCCESS! Valid syntax.')
    print()
    lines_out = new_content.split('\n')
    for i, l in enumerate(lines_out[332:342], start=333):
        r = l.rstrip('\n\r')
        spaces = len(r) - len(r.lstrip())
        print(f'{i:4}: (spaces={spaces}) {r}')
except SyntaxError as e:
    print(f'ERROR: {e}')
