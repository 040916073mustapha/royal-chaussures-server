import urllib.request
resp = urllib.request.urlopen('https://royal-chaussures-server.onrender.com/')
html = resp.read().decode('utf-8')
import re
m = re.search(r'src="/static/pos/pos\.js[^"]*"', html)
if m:
    print('Found:', m.group())
else:
    print('pos.js not found in HTML')
