#!/usr/bin/env python3
"""Fix blueprint registration position"""
path = 'C:\\Users\\Micro-Tech\\.openclaw\\workspace\\server.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the insertion inside the try block and move it outside
old = '        app.register_blueprint(store_bp, url_prefix="/api/v1/store")\n\n# ===== DASHBOARD BLUEPRINT (Clean Rebuild v2) =====\napp.register_blueprint(dashboard_bp)\n        _store_bp_ok = True'
new = '        app.register_blueprint(store_bp, url_prefix="/api/v1/store")\n        _store_bp_ok = True'

if old in content:
    content = content.replace(old, new)
    # Now add blueprint registration at a safe location (after the except block)
    search_insert = '        logger.error(f"[Store POS] Store blueprint FAILED: {e}\\n{_tb.format_exc()}")'
    insert_code = '\n\n# ===== DASHBOARD BLUEPRINT (Clean Rebuild v2) =====\napp.register_blueprint(dashboard_bp)'
    content = content.replace(search_insert, search_insert + insert_code)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Blueprint moved to correct position!')
else:
    print('Pattern not found!')
    # Show what's around that area
    idx = content.find('register_blueprint(dashboard_bp)')
    if idx >= 0:
        print(f'Found at char {idx}')
        print(content[idx-50:idx+100])
