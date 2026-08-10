with open('server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, l in enumerate(lines[332:340], start=333):
    r = l.rstrip('\n\r')
    spaces = len(r) - len(r.lstrip())
    print(f'{i:4}: (spaces={spaces}) {r}')
