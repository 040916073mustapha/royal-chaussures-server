import urllib.request
resp = urllib.request.urlopen('https://royal-chaussures-server.onrender.com/static/pos/pos.js')
data = resp.read()
print('Status:', resp.status)
print('Content-Length:', resp.headers.get('Content-Length', 'chunked'))
print('Bytes received:', len(data))
print('First 100 chars:', data[:100])
