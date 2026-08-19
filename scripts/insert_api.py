#!/usr/bin/env python3
"""Insert /api/store/<id> endpoint in server.py"""
import re

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Target: before @app.route('/api/webhooks/registered'
target = "@app.route('/api/webhooks/registered', methods=['GET'])"
idx = content.find(target)
if idx < 0:
    print("ERROR: Target not found")
    exit(1)

new_api = """@app.route('/api/store/<int:store_id>')
def api_store_info(store_id):
    try:
        from database.db import get_store
        store = get_store(store_id)
        if store:
            return json_utf8({"id": store["id"], "name": store["name"], "slug": store["slug"]})
        return json_utf8({"error": "Store not found"}, 404)
    except Exception as e:
        return json_utf8({"error": _safe_str(e)}, 500)


"""  # 3 newlines before the existing target

# Insert before the target
new_content = content[:idx] + new_api + content[idx:]

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("API endpoint added successfully!")
print(f"Added /api/store/<int:store_id> before /api/webhooks/registered")
