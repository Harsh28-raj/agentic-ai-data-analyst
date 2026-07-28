import urllib.request, json
boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
body = ('--' + boundary + '\r\nContent-Disposition: form-data; name="files"; filename="test.csv"\r\nContent-Type: text/csv\r\n\r\npatient_id,age,blood_pressure,score\n1,45,120,5.5\n2,50,130,6.0\n3,55,140,5.2\n4,25,115,8.1\n5,200,900,1.0\r\n--' + boundary + '--\r\n').encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/upload', data=body, headers={'Content-Type': 'multipart/form-data; boundary=' + boundary})
res = urllib.request.urlopen(req)
session = json.loads(res.read().decode())['session_id']

# Test 1: Dataset Summary
print("--- TEST 1: Dataset Summary ---")
data = json.dumps({'session_id': session, 'query': 'tell me about dataset'}).encode('utf-8')
req2 = urllib.request.Request('http://127.0.0.1:8000/chat', data=data, headers={'Content-Type': 'application/json'})
res2 = urllib.request.urlopen(req2)
print(res2.read().decode())

# Test 2: Anomaly Detection
print("\n--- TEST 2: Anomaly Detection ---")
data = json.dumps({'session_id': session, 'query': 'run anomaly detection'}).encode('utf-8')
req3 = urllib.request.Request('http://127.0.0.1:8000/chat', data=data, headers={'Content-Type': 'application/json'})
res3 = urllib.request.urlopen(req3)
print(res3.read().decode())
