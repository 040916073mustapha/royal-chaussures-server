with open('server.py', 'rb') as f:
    raw = f.read()

print(f'BOM UTF-8: {raw[:3] == b"\xef\xbb\xbf"}')
print(f'BOM UTF-16LE: {raw[:2] == b"\xff\xfe"}')

lines = raw.split(b'\n')
line124 = lines[123]
print(f'Raw line 124: {line124}')
print(f'Hex: {line124.hex()}')
