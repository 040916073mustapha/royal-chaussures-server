# fix_indent.py - Fix indentation in server_complete.py
import re

path = r'C:\Users\Micro-Tech\.openclaw\workspace\server_complete.py'

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix line 875 (index 874) - has 24 spaces, should be 12
line_num = 874
old = lines[line_num]
# Calculate current leading spaces
stripped = old.lstrip()
new_line = '            ' + stripped  # 12 spaces
lines[line_num] = new_line

print(f'Fixed line {line_num+1}:')
print(f'  Before: "{old.rstrip()}"')
print(f'  After:  "{new_line.rstrip()}"')

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

# Test syntax
import py_compile
try:
    py_compile.compile(path, doraise=True)
    print('\nSyntax: OK')
except py_compile.PyCompileError as e:
    print(f'\nSyntax error remaining: {e}')
