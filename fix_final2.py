with open('server_clean.py', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('system_prompt = os.getenv(')
rest = content[start:]

# Show first 200 chars
print("First 200 chars of rest:")
print(repr(rest[:200]))
print()

# Count parens WITHOUT parsing strings — just dumb count
open_parens = rest.count('(')
close_parens = rest.count(')')
print(f"Open parens: {open_parens}, Close parens: {close_parens}")
print(f"Difference: {open_parens - close_parens}")

# Try to parse... maybe the issue is the backslash in strings
# Let's just search for the closing \n    )\n\n pattern
# The original ends with: "...in your raw response."\n    )"
target = 'in your raw response.'
idx = rest.find(target)
if idx >= 0:
    after = rest[idx+len(target):idx+len(target)+30]
    print(f"\nAfter target: {repr(after)}")
    # The closing ) is right after this
    end = start + idx + len(target)
    # Skip to after the )
    close_paren = rest.find(')', idx)
    end = start + close_paren + 1
    print(f"Closing paren at offset {close_paren}, total end = {end}")
    
    old_block = content[start:end]
    print(f"\nOld block length: {len(old_block)}")
    print("Verifying...")
    
    # Build new block
    # Extract the arguments after "AI_SYSTEM_PROMPT",
    ai_key_pos = old_block.find('"AI_SYSTEM_PROMPT"')
    comma_after_key = old_block.find(',', ai_key_pos)
    default_value = old_block[comma_after_key+1:].lstrip()
    # default_value starts with "[1. ROYAL IDENTITY]\n"
    # The closing \n    ) at the end
    # Remove trailing )
    if default_value.endswith(')'):
        default_value = default_value[:-1].rstrip()
    
    print(f"\nDefault value (first 100): {repr(default_value[:100])}")
    print(f"Default value (last 100): {repr(default_value[-100:])}")
    
    new_block = 'system_prompt = os.getenv(\n'
    new_block += '        "SYSTEM_PROMPT",\n'
    new_block += '        os.getenv("AI_SYSTEM_PROMPT",\n'
    new_block += '            ' + default_value.lstrip() + '\n'
    new_block += '        )\n'
    new_block += '    )'
    
    print(f"\nNew block:\n{new_block[:200]}\n...\n{new_block[-200:]}")
    
    # Apply
    new_content = content[:start] + new_block + content[end:]
    
    try:
        compile(new_content, 'test.py', 'exec')
        with open('server.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print('\nSUCCESS! File written.')
    except SyntaxError as e:
        print(f'\nSYNTAX ERROR: {e}')
        lines = new_content.split('\n')
        for i, l in enumerate(lines[330:340]):
            print(f'{331+i}: {l}')
