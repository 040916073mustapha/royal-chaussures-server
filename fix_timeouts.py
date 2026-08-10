# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'C:\Users\Micro-Tech\.openclaw\workspace')

content = open('C:\\Users\\Micro-Tech\\.openclaw\\workspace\\server_complete.py', 'r', encoding='utf-8').read()

# Update send_whatsapp_message timeout + debug
old1 = 'timeout=10)\n        logger.info'
new1 = 'timeout=8)\n        logger.info'
content = content.replace(old1, new1)

# Update send_instagram_message timeouts
content = content.replace('timeout=10)\n        if resp.status_code == 200:\n            logger.info', 'timeout=8)\n        if resp.status_code == 200:\n            logger.info')

# Make sure all timeouts are consistent
content = content.replace('timeout=(10, 25)', 'timeout=(8, 20)')

open('C:\\Users\\Micro-Tech\\.openclaw\\workspace\\server_complete.py', 'w', encoding='utf-8').write(content)
print('Done')

import ast
ast.parse(content)
print('Syntax OK')
