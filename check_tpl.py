import re

tpl = open('rcagents_saas_core/frontend/templates/dashboard.html', 'r', encoding='utf-8').read()

# Count occurrences
print("Occurrences of x-data= :", tpl.count("x-data="))

# Find the full x-data line
for i, line in enumerate(tpl.split('\n')[:5]):
    print(f"Line {i+1}: {line[:80]}")
