import requests

# Upload a simple CSV
csv_data = "id,age,salary,department\n1,45,100000,Sales\n2,50,120000,HR\n3,55,130000,Sales\n4,25,75000,Engineering\n5,28,85000,Engineering"
files = {'files': ('test.csv', csv_data, 'text/csv')}
res = requests.post('http://127.0.0.1:8000/upload', files=files)
session = res.json()['session_id']
print(f"Session: {session}")

# Test CSV Query
sql = "SELECT department, AVG(salary) as avg_salary FROM test GROUP BY department"
res2 = requests.post('http://127.0.0.1:8000/query/csv', json={"session_id": session, "sql_code": sql})
print(f"Status CSV: {res2.status_code}")
if res2.status_code == 200:
    print(res2.text)
else:
    print(res2.text)
