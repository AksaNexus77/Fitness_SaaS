import urllib.request
import urllib.parse
import json
from http.cookiejar import CookieJar

base = 'http://127.0.0.1:5000'
cj = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Test login page loads
r = opener.open(base + '/login')
print('Login page:', r.status)

# Login as admin
req = urllib.request.Request(base + '/login', data=urllib.parse.urlencode({'email': 'admin@fitness.com', 'password': 'admin123'}).encode())
r = opener.open(req)
print('Login:', r.status)

# Test AI routes
for path in ['/ai/workout-plan', '/ai/chatbot', '/ai/payment-reminders']:
    r = opener.open(base + path)
    print(path, ':', r.status)

# Test chatbot API
req = urllib.request.Request(base + '/api/chatbot', data=json.dumps({'message': 'hello'}).encode(), headers={'Content-Type': 'application/json'})
r = opener.open(req)
print('/api/chatbot:', r.status)
if r.status == 200:
    data = json.loads(r.read().decode())
    print('Response:', data.get('response', '')[:60])

# Test generate workout plan
req = urllib.request.Request(base + '/ai/workout-plan/generate', data=urllib.parse.urlencode({'member_id': '1', 'duration_weeks': '4'}).encode())
r = opener.open(req)
print('/ai/workout-plan/generate:', r.status)

print('Smoke tests complete!')

