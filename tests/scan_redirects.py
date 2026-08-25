#!/usr/bin/env python3
"""Scan all templates for redirect sources"""
import os, re

tdir = 'C:\\Users\\Micro-Tech\\.openclaw\\workspace\\templates'
for fname in sorted(os.listdir(tdir)):
    if not fname.endswith('.html'):
        continue
    path = os.path.join(tdir, fname)
    content = open(path, 'r', encoding='utf-8').read()
    lines = content.split('\n')
    
    found_issues = []
    
    # Check for meta refresh redirect
    if 'http-equiv="refresh"' in content.lower() or "http-equiv='refresh'" in content.lower():
        found_issues.append('META REFRESH tag found!')
    
    # Check for onload/onerror JS redirects
    for i, line in enumerate(lines):
        if 'onerror' in line.lower() and ('location' in line or 'redirect' in line.lower()):
            found_issues.append(f'L{i+1}: onerror redirect: {line.strip()[:120]}')
        if 'window.location' in line:
            found_issues.append(f'L{i+1}: window.location: {line.strip()[:120]}')
        if 'location.href' in line:
            found_issues.append(f'L{i+1}: location.href: {line.strip()[:120]}')
        if 'location.replace' in line:
            found_issues.append(f'L{i+1}: location.replace: {line.strip()[:120]}')
        if 'localStorage' in line and ('/' in line or 'redirect' in line.lower()):
            found_issues.append(f'L{i+1}: localStorage + redirect: {line.strip()[:120]}')
    
    if found_issues:
        print(f'\n=== {fname} ===')
        for issue in found_issues:
            print(f'  {issue}')
    else:
        print(f'  {fname}: clean')
