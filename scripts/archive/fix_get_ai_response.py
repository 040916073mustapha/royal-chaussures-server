# fix_get_ai_response.py - Fix: make get_ai_response accept **kwargs
# and update the 2 remaining agent_route-style calls

path = r'C:\Users\Micro-Tech\.openclaw\workspace\server_complete.py'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Change function definition to accept **kwargs
old_def = 'def get_ai_response(msg, uid, platform="messenger"):'
new_def = 'def get_ai_response(msg=None, uid=None, platform=None, **kwargs):'
content = content.replace(old_def, new_def)

# 2. Replace the two old-style calls (with message=, openclaw_api_url= etc.)
# First call - in webhook handler
old_call1 = '''get_ai_response(
            message=msg,
            platform=platform,
            uid=uid,
            openclaw_api_url=OPENCLAW_API_URL,
            openclaw_token=OPENCLAW_TOKEN
        )'''

new_call1 = '''get_ai_response(
            msg=msg,
            platform=platform,
            uid=uid
        )'''

content = content.replace(old_call1, new_call1)

# Second call - in api_test
old_call2 = '''get_ai_response(
            message=message,
            platform="api_test",
            uid="test_user",
            openclaw_api_url=None,  # Force auto-reply for test
            openclaw_token=None
        )'''

new_call2 = '''get_ai_response(
            msg=message,
            platform="api_test",
            uid="test_user"
        )'''

content = content.replace(old_call2, new_call2)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

# Check results
import re

# Check no more message= or openclaw_ in get_ai_response calls
remaining = re.findall(r'get_ai_response\([^)]*\)', content)
print('All get_ai_response calls:')
for c in remaining:
    print(f'  {c}')

# Final syntax check
import py_compile
try:
    py_compile.compile(path, doraise=True)
    print('\nSyntax: OK')
except py_compile.PyCompileError as e:
    print(f'\nSyntax error: {e}')
