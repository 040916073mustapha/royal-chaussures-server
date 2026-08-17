with open('server_clean.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

start = content.find('system_prompt = os.getenv(')
rest = content[start:]

target = 'in your raw response.'
idx = rest.find(target)
close_paren = rest.find(')', idx)
end = start + close_paren + 1

old_block = content[start:end]

# Extract default value (everything after "AI_SYSTEM_PROMPT",)
ai_key_pos = old_block.find('"AI_SYSTEM_PROMPT"')
comma_after_key = old_block.find(',', ai_key_pos)
default_value = old_block[comma_after_key+1:].lstrip()
if default_value.endswith(')'):
    default_value = default_value[:-1].rstrip()

new_block = 'system_prompt = os.getenv(\n'
new_block += '        "SYSTEM_PROMPT",\n'
new_block += '        os.getenv("AI_SYSTEM_PROMPT",\n'
new_block += '            ' + default_value.lstrip() + '\n'
new_block += '        )\n'
new_block += '    )'

new_content = content[:start] + new_block + content[end:]

try:
    compile(new_content, 'test.py', 'exec')
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('SUCCESS! Valid syntax. Written to server.py')
except SyntaxError as e:
    print(f'SYNTAX ERROR: {e}')
    lines = new_content.split('\n')
    for i, l in enumerate(lines[330:340]):
        print(f'{331+i}: {l}')
