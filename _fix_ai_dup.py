# -*- coding: utf-8 -*-
import sys

with open('templates/pos/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find duplicate AI agent button
# The original sidebar already has one (correct), the script added another outside
# We need to find and remove the second one that's NOT in the sidebar

# Count occurrences of data-view="ai-agent"
count = content.count('data-view="ai-agent"')
print(f'Before: {count} occurrences of ai-agent')

if count > 1:
    # Find the second occurrence (which is the duplicate)
    idx1 = content.find('data-view="ai-agent"')
    idx2 = content.find('data-view="ai-agent"', idx1 + 1)
    
    # Go back to find the button tag start
    btn_start = content.rfind('<button', 0, idx2)
    btn_end = content.find('</button>', idx2) + 9
    
    # Find line boundaries
    line_start = content.rfind('\n', 0, btn_start)
    line_end = content.find('\n', btn_end)
    
    print(f'Removing from {line_start} to {line_end}')
    print(f'Context: {repr(content[btn_start:btn_end])}')
    
    # Remove the duplicate line
    content = content[:line_start] + content[line_end:]
    
    count_after = content.count('data-view="ai-agent"')
    print(f'After: {count_after} occurrences')

with open('templates/pos/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed!')
