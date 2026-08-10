with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('system_prompt = os.getenv(')
rest = content[start:]
target_end = 'in your raw response."'
idx = rest.find(target_end)
close_paren = rest.find(')', idx)
end = start + close_paren + 1

old_block = content[start:end]

# Extract default value
ai_key = old_block.find('"AI_SYSTEM_PROMPT"')
comma = old_block.find(',', ai_key)
default_val = old_block[comma+1:].lstrip()
if default_val.endswith(')'):
    default_val = default_val[:-1].rstrip()

# Normalize indent of default_val lines to 12 spaces
lines = default_val.split('\n')
fixed_lines = []
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped:  # non-empty
        if i == 0:
            fixed_lines.append('            ' + stripped)
        else:
            fixed_lines.append('            ' + stripped)
    else:
        fixed_lines.append('            ')  # keep empty lines with indent

default_val_fixed = '\n'.join(fixed_lines)

# Build new block
new_block = '    system_prompt = os.getenv(\n'
new_block += '        "SYSTEM_PROMPT",\n'
new_block += '        os.getenv(\n'
new_block += '            "AI_SYSTEM_PROMPT",\n'
new_block += default_val_fixed + '\n'
new_block += '        )\n'
new_block += '    )'

new_content = content[:start] + new_block + content[end:]

try:
    compile(new_content, 'test.py', 'exec')
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('SUCCESS! Valid syntax.')
    print()
    # Show new block
    lines = new_content.split('\n')
    for i, l in enumerate(lines[333:340]):
        print(f'{i+1:4}: {l}')
except SyntaxError as e:
    print(f'ERROR: {e}')
