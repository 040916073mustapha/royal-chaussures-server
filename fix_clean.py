with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('system_prompt = os.getenv(')

# Find the closing paren of the original os.getenv
# Original: os.getenv(\n        "AI_SYSTEM_PROMPT",\n        "[1. ROYAL...raw response."\n    )
rest = content[start:]
target_end = 'in your raw response."'
idx = rest.find(target_end)
close_paren = rest.find(')', idx)
end = start + close_paren + 1

old_block = content[start:end]

# Extract the default value (everything after "AI_SYSTEM_PROMPT",)
ai_key = old_block.find('"AI_SYSTEM_PROMPT"')
comma = old_block.find(',', ai_key)
default_val = old_block[comma+1:].lstrip()
if default_val.endswith(')'):
    default_val = default_val[:-1].rstrip()

# Build new: SYSTEM_PROMPT wraps AI_SYSTEM_PROMPT
new_block = '    system_prompt = os.getenv(\n'
new_block += '        "SYSTEM_PROMPT",\n'
new_block += '        os.getenv(\n'
new_block += '            "AI_SYSTEM_PROMPT",\n'
new_block += default_val.lstrip() + '\n'
new_block += '        )\n'
new_block += '    )'

new_content = content[:start] + new_block + content[end:]

try:
    compile(new_content, 'test.py', 'exec')
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('SUCCESS! Valid syntax, file written.')
    print()
    # Show the new block
    lines = new_content.split('\n')
    for i, l in enumerate(lines[333:340]):
        print(f'{i+1:4}: {l}')
except SyntaxError as e:
    print(f'ERROR: {e}')
    lines = new_content.split('\n')
    for i, l in enumerate(lines[330:340]):
        print(f'{331+i}: {l}')
