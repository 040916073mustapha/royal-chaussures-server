import re
with open(r'C:\Users\Micro-Tech\.openclaw\workspace\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all @app.route decorators
routes = re.findall(r"@app\.route\(['\"]([^'\"]+)['\"]", content)
for r in sorted(set(routes)):
    print(r)
