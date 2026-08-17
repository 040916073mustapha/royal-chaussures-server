import urllib.request
resp = urllib.request.urlopen('https://royal-chaussures-server.onrender.com/api/v1/store/pos')
html = resp.read().decode('utf-8')
import re
m = re.search(r'src="/static/pos/pos\.js[^"]*"', html)
if m:
    print('Found:', m.group())
else:
    print('pos.js not found in POS HTML')
    m2 = re.search(r'pos\.js', html)
    if m2:
        ctx = html[max(0,m2.start()-200):m2.end()+200]
        print('Context:', ctx)
