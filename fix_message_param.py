# fix_message_param.py - Fix get_ai_response calls using 'message=' param

path = r'C:\Users\Micro-Tech\.openclaw\workspace\server_complete.py'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all 'message=msg' with just 'msg' in get_ai_response calls
content = content.replace('get_ai_response(message=msg,', 'get_ai_response(msg,')
content = content.replace('get_ai_response(message=text,', 'get_ai_response(text,')

# Also check for any remaining message= pattern
import re
count = len(re.findall(r'get_ai_response\(message=', content))
print(f'Remaining message= refs: {count}')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

import py_compile
try:
    py_compile.compile(path, doraise=True)
    print('Syntax: OK')
except py_compile.PyCompileError as e:
    print(f'Syntax error: {e}')
