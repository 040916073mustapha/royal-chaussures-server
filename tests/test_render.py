#!/usr/bin/env python3
"""Test rendering agents_dashboard.html"""
import sys, os
sys.path.insert(0, 'C:\\Users\\Micro-Tech\\.openclaw\\workspace')

from flask import Flask

app = Flask(__name__, template_folder='C:\\Users\\Micro-Tech\\.openclaw\\workspace\\templates')

with app.app_context():
    from flask import render_template
    try:
        html = render_template('agents_dashboard.html')
        print(f'Rendered: {len(html)} bytes')
        assert 'agentsDashboard' in html, 'No agentsDashboard function'
        assert 'window.location' not in html, 'Found window.location redirect!'
        assert 'location.href' not in html, 'Found location.href redirect!'
        print('First 200 chars:', repr(html[:200]))
        print('TEMPLATE RENDERS OK')
    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()
