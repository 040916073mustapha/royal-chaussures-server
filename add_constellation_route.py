#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

with open('C:\\Users\\Micro-Tech\\.openclaw\\workspace\\render_deploy\\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = """@app.route('/dashboard/orders/<order_id>')
def dashboard_order_detail(order_id):"""

new = """@app.route('/dashboard/constellation')
def dashboard_constellation():
    \"\"\"Agent Constellation interactive page\"\"\"
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'constellation.html'), 'r', encoding='utf-8') as f:
            html = f.read()
        return render_template_string(html), 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        _log_safe(logger.error, "Constellation template error", e)
        return json_utf8({"error": _safe_str(e)}, 500)


@app.route('/dashboard/orders/<order_id>')
def dashboard_order_detail(order_id):"""

if old in content:
    content = content.replace(old, new, 1)
    with open('C:\\Users\\Micro-Tech\\.openclaw\\workspace\\render_deploy\\server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("OK - constellation route added")
else:
    print("FAIL")
