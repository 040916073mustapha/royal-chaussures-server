# fix_quote.py
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix: remove trailing lone quote at line 303
old_text = 'return "Merci de nous contacter! Nous reviendrons vers vous bientot."\n"'
new_text = 'return "Merci de nous contacter! Nous reviendrons vers vous bientot."'

if old_text in content:
    content = content.replace(old_text, new_text)
    print("Fixed trailing quote!")
else:
    # Try without newline
    old_text2 = 'return "Merci de nous contacter! Nous reviendrons vers vous bientot."\n"'
    if old_text2 not in content:
        print("Pattern not found, checking...")
        idx = content.find('return "Merci de nous contacter')
        if idx > 0:
            print(f"Found at {idx}")
            print(repr(content[idx:idx+100]))

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)

try:
    compile(content, 'server.py', 'exec')
    print("SYNTAX: 100% OK!")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")
