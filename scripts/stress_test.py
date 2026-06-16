import urllib.request
import json
import time
import concurrent.futures
import threading

BASE = 'http://localhost:8000'
TOKEN = None
LOCK = threading.Lock()
ERRORS = []

def login():
    global TOKEN
    data = json.dumps({'username': 'testuser', 'password': 'test123456'}).encode()
    req = urllib.request.Request(f'{BASE}/api/auth/login', data=data, headers={'Content-Type': 'application/json'})
    resp = json.loads(urllib.request.urlopen(req).read())
    TOKEN = resp.get('token', '')
    print(f'Login: OK')

def get_headers():
    return {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}

def test_one(i, name, path):
    start = time.time()
    try:
        req = urllib.request.Request(f'{BASE}{path}', headers=get_headers())
        resp = urllib.request.urlopen(req, timeout=10)
        body = resp.read()
        elapsed = (time.time() - start) * 1000
        return (True, name, elapsed, None)
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return (False, name, elapsed, str(e)[:80])

login()

tests = [
    ('health', '/api/health'),
    ('info', '/api/info'),
    ('profile', '/api/agent/get-profile'),
    ('semesters', '/api/agent/list-semesters'),
    ('rag_docs', '/api/agent/rag-documents'),
    ('activity', '/api/agent/activity-logs?limit=5'),
]

print()
print('=== Stress Test: 500 requests, 50 concurrent ===')
results = []
start = time.time()

with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
    futures = []
    for i in range(500):
        name, path = tests[i % len(tests)]
        futures.append(executor.submit(test_one, i, name, path))
    for f in concurrent.futures.as_completed(futures):
        results.append(f.result())

total_time = (time.time() - start) * 1000

success = [r for r in results if r[0]]
failed = [r for r in results if not r[0]]

print(f'Total:   {len(results)}')
print(f'Success: {len(success)}')
print(f'Failed:  {len(failed)}')
print(f'Time:    {total_time:.0f}ms')
print()

if success:
    times = [r[2] for r in success]
    avg = sum(times) / len(times)
    p50 = sorted(times)[len(times)//2]
    p95 = sorted(times)[int(len(times)*0.95)]
    print(f'Success stats:')
    print(f'  Avg: {avg:.1f}ms  P50: {p50:.1f}ms  P95: {p95:.1f}ms  Max: {max(times):.1f}ms')
    print(f'  RPS: {len(success)/(total_time/1000):.0f}')

if failed:
    print(f'\nFailed requests:')
    errors = {}
    for ok, name, ms, err in failed:
        key = err or 'unknown'
        errors[key] = errors.get(key, 0) + 1
    for err, count in sorted(errors.items(), key=lambda x: -x[1]):
        print(f'  [{count}x] {err}')
