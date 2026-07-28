import requests

# Upload a simple CSV
csv_data = "id,age,salary,department\n1,45,100000,Sales\n2,50,120000,HR\n3,55,130000,Sales\n4,25,75000,Engineering\n5,28,85000,Engineering"
files = {'files': ('test.csv', csv_data, 'text/csv')}
res = requests.post('http://127.0.0.1:8000/upload', files=files)
session = res.json()['session_id']
print(f"Session: {session}")

# Get dashboard stats
res2 = requests.get(f'http://127.0.0.1:8000/dashboard/{session}/stats')
print(f"Status: {res2.status_code}")
if res2.status_code == 200:
    stats = res2.json()
    print(f"KPIs: {stats['kpis']}")
    print(f"Distributions: {list(stats['distributions'].keys())}")
else:
    print(f"Error: {res2.text}")
