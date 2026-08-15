import urllib.request
resp = urllib.request.urlopen('https://royal-chaussures-server.onrender.com/static/pos/pos.js')
data = resp.read().decode('utf-8')

if '/api/v1/store/pos/sales' in data:
    print('recordSale uses NEW URL OK')
else:
    print('recordSale uses OLD URL - PROBLEM')

if '/api/v1/store/sales' in data:
    if '/api/v1/store/pos/sales' in data:
        old = data.count('/api/v1/store/sales')
        new = data.count('/api/v1/store/pos/sales')
        print(f'Old occurrences: {old}, New occurrences: {new}')
    else:
        print('WARNING: Only old URL found!')

import re
for m in re.finditer(r'.{0,20}recordSale.{0,60}', data):
    print('recordSale:', m.group())
for m in re.finditer(r'.{0,20}loadSalesList.{0,60}', data):
    print('loadSalesList:', m.group())
