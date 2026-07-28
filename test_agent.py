import urllib.request
import json
boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
body = ('--' + boundary + '\r\nContent-Disposition: form-data; name="files"; filename="test.csv"\r\nContent-Type: text/csv\r\n\r\nid,name\n1,alice\n2,bob\r\n--' + boundary + '--\r\n').encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/upload', data=body, headers={'Content-Type': 'multipart/form-data; boundary=' + boundary})
res = urllib.request.urlopen(req)
session = json.loads(res.read().decode())['session_id']
data = json.dumps({'session_id': session, 'query': 'Hello, what is your model name?'}).encode('utf-8')
req2 = urllib.request.Request('http://127.0.0.1:8000/chat', data=data, headers={'Content-Type': 'application/json'})
res2 = urllib.request.urlopen(req2)
print(res2.read().decode())
