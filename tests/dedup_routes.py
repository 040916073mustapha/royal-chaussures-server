#!/usr/bin/env python3
"""Remove third bloc of dashboard route duplicates"""
with open('C:\\Users\\Micro-Tech\\.openclaw\\workspace\\server.py', 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')

# Third bloc is the one near Phase 2 section. Let's find exact boundaries
# It starts around the comment "# PHASE 2: AI AGENTS MANAGEMENT API" and
# includes duplicate routes like /dashboard/analytics, /dashboard/agents etc.

# Find the specific comment that marks Phase 2 agent API section
phase2_start = None
for i, line in enumerate(lines):
    if 'PHASE 2: AI AGENTS MANAGEMENT API' in line:
        phase2_start = i
        break

print(f'Phase 2 section at line {phase2_start+1}')

# Find where the dashboard route duplicates end in this section
# They end right before the "Main" comment (if __name__)
main_start = None
for i in range(phase2_start, len(lines)) if phase2_start else []:
    if "if __name__ == '__main__':" in lines[i]:
        main_start = i
        break

print(f'Main starts at line {main_start+1}')

# The third bloc routes are between Phase 2 header and the analytics API endpoints
# Let's find all dashboard routes in this area
if phase2_start:
    # Find where the ENGAGEMENT API section starts (after the last duplicate)
    engagement_start = None
    for i in range(phase2_start, phase2_start + 200 if phase2_start + 200 < len(lines) else len(lines)):
        if 'ENGAGEMENT AGENT API' in lines[i]:
            engagement_start = i
            break
    
    print(f'Engagement section at line {engagement_start+1}')
    
    # Remove duplicate dashboard routes between Phase 2 section and engagement section
    if engagement_start:
        # Find the actual first duplicate route in this area
        first_dup = None
        for i in range(phase2_start, engagement_start):
            if '@app.route' in lines[i] and 'dashboard' in lines[i]:
                first_dup = i
                break
        
        if first_dup:
            print(f'First duplicate dashboard route in Phase 2 area at line {first_dup+1}: {lines[first_dup].strip()}')
            # Remove from first_dup to just before engagement_start
            new_lines = lines[:first_dup] + lines[engagement_start:]
            print(f'Removed lines {first_dup+1} to {engagement_start}')
            
            with open('C:\\Users\\Micro-Tech\\.openclaw\\workspace\\server.py', 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            print(f'New line count: {len(new_lines)}')

# Final verification
with open('C:\\Users\\Micro-Tech\\.openclaw\\workspace\\server.py', 'r', encoding='utf-8') as f:
    final = f.read().split('\n')

import re
routes = {}
has_dupes = False
for i, line in enumerate(final):
    m = re.search(r"@app\.route\('([^']+)'\)", line)
    if m:
        route = m.group(1)
        if route in routes:
            print(f'DUPLICATE: {route} at line {i+1} (also at {routes[route]})')
            has_dupes = True
        else:
            routes[route] = i + 1

if not has_dupes:
    print(f'No duplicate routes! Total unique routes: {len(routes)}')
else:
    print(f'Total unique routes: {len(routes)} - Some duplicates remain')
