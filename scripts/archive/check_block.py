with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('system_prompt = os.getenv(')
end_marker = 'in your raw response."'
end = content.find(end_marker, start) + len(end_marker)

print('After end marker:')
print(repr(content[end:end+50]))

# Show the block from start to end+50
block = content[start:end+50]
print('\nFirst 120 chars:', repr(block[:120]))
print('\nLast 120 chars:', repr(block[-120:]))
