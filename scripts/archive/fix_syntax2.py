import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Strategy: replace the entire block from 'system_prompt = os.getenv(' 
# to 'in your raw response."' — but properly nested this time

start_marker = 'system_prompt = os.getenv('
end_marker = 'in your raw response."'

idx = content.find(start_marker)
end_idx = content.find(end_marker, idx) + len(end_marker)

# Read the full existing fallback text (everything between quotes)
text_start = content.find('"[1. ROYAL IDENTITY]\\n"', idx)
# The fallback text starts from the quote and includes all concatenated strings 
# up to and including 'in your raw response."'
raw_fallback = content[text_start:end_idx]
print(f"Fallback text ({len(raw_fallback)} chars):")
print(repr(raw_fallback[:100]))
print("...")
print(repr(raw_fallback[-100:]))

# Build correct structure:
# system_prompt = os.getenv(
#     "SYSTEM_PROMPT",
#     os.getenv("AI_SYSTEM_PROMPT", "[1. ROYAL IDENTITY]\n" ... "in your raw response.")
# )

new_block = (
    'system_prompt = os.getenv(\n'
    '        "SYSTEM_PROMPT",\n'
    '        os.getenv("AI_SYSTEM_PROMPT",\n'
    + raw_fallback + ')\n'
    '    )'
)

print("\nNew block (first 200):")
print(new_block[:200])
print("...")
print("New block (last 200):")
print(new_block[-200:])

# Replace
new_content = content[:idx] + new_block + content[end_idx:]

# Verify syntax
try:
    compile(new_content, 'server.py', 'exec')
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('✅ SUCCESS: Compiled and written!')
except SyntaxError as e:
    print(f'❌ SYNTAX ERROR: {e}')
    sys.exit(1)
