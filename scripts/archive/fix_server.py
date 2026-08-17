#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

original = content

# Replace each known *** pattern with the correct code
replacements = [
    ('AI_API_KEY = ***"AI_API_KEY", "")', 'AI_API_KEY = os.getenv("AI_API_KEY", "")'),
    ('FB_SYSTEM_USER_TOKEN = ***"FB_SYSTEM_USER_TOKEN", "")', 'FB_SYSTEM_USER_TOKEN = os.getenv("FB_SYSTEM_USER_TOKEN", "")'),
    ('FB_VERIFY_TOKEN = ***"FB_VERIFY_TOKEN", "ROYAL-ROYAL-CH2026")', 'FB_VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN", "ROYAL-ROYAL-CH2026")'),
    ('INSTAGRAM_ACCESS_TOKEN = ***"INSTAGRAM_ACCESS_TOKEN", "")', 'INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")'),
    ('WHATSAPP_ACCESS_TOKEN = ***"WHATSAPP_ACCESS_TOKEN", "")', 'WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")'),
    ('_FB_PAGE_ACCESS_TOKEN = ***', '_FB_PAGE_ACCESS_TOKEN = None'),
    ('        *** _FB_PAGE_ACCESS_TOKEN', '        return _FB_PAGE_ACCESS_TOKEN'),
    ('                        _FB_PAGE_ACCESS_TOKEN = ***"access_token"]', '                        _FB_PAGE_ACCESS_TOKEN = page["access_token"]'),
    ('                _FB_PAGE_ACCESS_TOKEN = ***"data"][0]["access_token"]', '                _FB_PAGE_ACCESS_TOKEN = data["data"][0]["access_token"]'),
    ('        ***"AI_API_KEY not set, returning default greeting")', '        logger.warning("AI_API_KEY not set, returning default greeting")'),
    ('            ***"Webhook verified!")', '            logger.info("Webhook verified!")'),
    ('            *** Response(challenge, status=200, content_type=\'text/plain\')', '            return Response(challenge, status=200, content_type=\'text/plain\')'),
    # Also fix the Facebook URL pattern which has *** in it
    ('url = f"https://graph.facebook.com/v18.0/me/messages?access_token=***}"', 'url = f"https://graph.facebook.com/v18.0/me/messages?access_token=***}"'),
]

for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        print(f'Fixed: {old[:50]}...')
    else:
        # Try to find partial match
        for line in content.split('\n'):
            if old.split('=')[0].strip() in line and '***' in line:
                print(f'  NEED FIX: {line.strip()[:70]}')

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)

# Verify
with open('server.py', 'r', encoding='utf-8') as f:
    content2 = f.read()

remaining = sum(1 for line in content2.split('\n') if '***' in line)
print(f'\nRemaining corrupted lines: {remaining}')

# Check syntax
try:
    compile(content2, 'server.py', 'exec')
    print('Syntax: OK!')
except SyntaxError as e:
    print(f'Syntax error: {e}')

print(f'\nTotal chars: {len(content2)}')
