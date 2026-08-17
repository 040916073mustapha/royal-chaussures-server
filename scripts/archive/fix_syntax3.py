import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find line with "system_prompt = os.getenv("
start_line = None
end_line = None
for i, line in enumerate(lines):
    if 'system_prompt = os.getenv(' in line:
        start_line = i
    if start_line and i > start_line and 'in your raw response.' in line:
        end_line = i
        break

print(f"Block from line {start_line+1} to {end_line+1}")

# Approach: chop everything from start_line to end_line, 
# reconstruct with proper nesting

# Read the original version from git
import subprocess
result = subprocess.run(
    ['git', 'show', 'HEAD~1:server.py'],
    capture_output=True, text=True
)
old_content = result.stdout

# Find the original system_prompt block
old_idx = old_content.find('system_prompt = os.getenv(')
old_end = old_content.find('in your raw response."', old_idx) + len('in your raw response."')

old_block = old_content[old_idx:old_end+1]
print("\nORIGINAL block from git (first 100, last 100):")
print(repr(old_block[:100]))
print("...")
print(repr(old_block[-100:]))

# The original ends with 'in your raw response."\n    )'
# Now add SYSTEM_PROMPT on top
new_block = (
    '    system_prompt = os.getenv(\n'
    '        "SYSTEM_PROMPT",\n'
    '        os.getenv("AI_SYSTEM_PROMPT",\n'
    '            '
)

# Extract just the fallback text from the old block (after the first "AI_SYSTEM_PROMPT",)
old_def_start = old_content.find('"AI_SYSTEM_PROMPT"', old_idx)
# Skip to the default argument
after_key = old_content.find(',', old_def_start)
fallback_text = old_content[after_key+1:].lstrip()
# But we need from the "AI_SYSTEM_PROMPT", line's default value
# Find the second string (the default)
lines_old = old_block.split('\n')
fallback_lines = []
found_key = False
for line in lines_old:
    if '"AI_SYSTEM_PROMPT"' in line:
        found_key = True
        # Get the default value part: after the comma
        comma_idx = line.find(',')
        if comma_idx >= 0:
            rest = line[comma_idx+1:].strip()
            if rest:
                fallback_lines.append('        ' + rest)
        continue
    if found_key:
        # Any subsequent line that's part of the string (implicit concat)
        stripped = line.rstrip()
        if stripped and not stripped.endswith(')') and not stripped == '':
            fallback_lines.append('        ' + stripped)
        elif stripped == '' or stripped == ')':
            continue
        elif stripped.endswith(')'):
            break

print("\nFallback lines:")
for l in fallback_lines[:5]:
    print(repr(l))
print(f"... total {len(fallback_lines)} lines")

# Build the complete replacement
replacement = '    system_prompt = os.getenv(\n'
replacement += '        "SYSTEM_PROMPT",\n'
replacement += '        os.getenv("AI_SYSTEM_PROMPT",\n'
for fl in fallback_lines:
    replacement += fl + '\n'
replacement += '        )\n'
replacement += '    )'

print("\nReplacement (first 300):")
print(replacement[:300])
print("\nReplacement (last 300):")
print(replacement[-300:])

# Replace in file
new_lines = lines[:start_line]
new_lines.append(replacement + '\n')
# Skip the old block + add remaining after end_line
sub_end = end_line + 1
# But also skip the old closing paren )\n line
if sub_end < len(lines) and lines[sub_end].strip() == ')':
    sub_end += 1
    if sub_end < len(lines) and lines[sub_end].strip() == '':
        sub_end += 1

new_lines.extend(lines[sub_end:])
new_content = ''.join(new_lines)

# Verify
try:
    compile(new_content, 'server.py', 'exec')
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('✅ SUCCESS: Compiled and written!')
except SyntaxError as e:
    print(f'❌ SYNTAX ERROR: {e}')
    
    # Try a more aggressive approach
    lines_new = new_content.split('\n')
    for i, l in enumerate(lines_new[332:390], start=333):
        print(f'{i:4}: {l}')
