"""Fix: add missing outer except for upsert_order_from_shopify try block"""
import ast

with open('server.py', 'rb') as f:
    raw = f.read()

# The pattern shows:                pass\r\n\r\n\r\ndef get_zr_shipments()
# We need to insert outer except after the 'pass' line

pass_marker = b'                pass\r\n\r\n\r\ndef get_zr_shipments'
idx = raw.find(pass_marker)

if idx >= 0:
    # Insert after '                pass\r\n'
    insert_point = idx + len(b'                pass\r\n')
    
    insert_text = (
        b'    except Exception as e:\r\n'
        b'        logger.error(f"upsert error: {_safe_str(e)}")\r\n'
        b'\r\n'
        b'\r\n'
    )
    
    raw = raw[:insert_point] + insert_text + raw[insert_point:]
    
    with open('server.py', 'wb') as f:
        f.write(raw)
    
    with open('server.py', 'r', encoding='utf-8') as f:
        ast.parse(f.read())
    print('Syntax OK!')
else:
    print('Pattern not found')
    print(f'Found around pass: {repr(raw[pidx:pidx+200])}')
