import urllib.request, json
boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
body = ('--' + boundary + '\r\nContent-Disposition: form-data; name="files"; filename="test.csv"\r\nContent-Type: text/csv\r\n\r\nid,age,salary,department\n1,45,100000,Sales\n2,50,120000,HR\n3,55,130000,Sales\n4,25,75000,Engineering\n5,28,85000,Engineering\r\n--' + boundary + '--\r\n').encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/upload', data=body, headers={'Content-Type': 'multipart/form-data; boundary=' + boundary})
res = urllib.request.urlopen(req)
session = json.loads(res.read().decode())['session_id']

# Test stats endpoint
req2 = urllib.request.Request(f'http://127.0.0.1:8000/dashboard/{session}/stats')
res2 = urllib.request.urlopen(req2)
stats = json.loads(res2.read().decode())
print(f"Stats loaded successfully! KPIs: {stats['kpis']}")
print(f"Top categoricals: {stats['categorical_tops']}")
