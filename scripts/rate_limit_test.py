import urllib.request
import json
import time
import concurrent.futures

BASE = 'http://localhost:8000'

def test_login(i):
    start = time.time()
    try:
        data = json.dumps({'username': 'testuser', 'password': 'test123456'}).encode()
        req = urllib.request.Request(f'{BASE}/api/auth/login', data=data, headers={'Content-Type': 'application/json'})
        resp = urllib.request.urlopen(req, timeout=5)
        body = json.loads(resp.read())
        elapsed = (time.time() - start) * 1000
        return (True, elapsed, body.get('success'))
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        code = getattr(e, 'code', 0)
        return (False, elapsed, f'HTTP {code}')

print('=== Login Rate Limit Test: 15 rapid requests ===')
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
    futures = [executor.submit(test_login, i) for i in range(15)]
    for f in concurrent.futures.as_completed(futures):
        results.append(f.result())

success = [r for r in results if r[0]]
rate_limited = [r for r in results if not r[0] and '429' in str(r[2])]
other_fail = [r for r in results if not r[0] and '429' not in str(r[2])]

print(f'Total:        {len(results)}')
print(f'Success:      {len(success)}')
print(f'Rate Limited: {len(rate_limited)}')
print(f'Other Fail:   {len(other_fail)}')

if rate_limited:
    print(f'\nRate limiting working correctly!')
else:
    print(f'\nWarning: Rate limiting may not be active')
