import urllib.request, json

BASE = 'http://localhost:8000'
data = json.dumps({'username': 'testuser', 'password': 'test123456'}).encode()
req = urllib.request.Request(f'{BASE}/api/auth/login', data=data, headers={'Content-Type': 'application/json'})
resp = json.loads(urllib.request.urlopen(req).read())
token = resp['token']

headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# Test advanced search
body = json.dumps({'query': '机器学习', 'strategy': 'rag_fusion', 'limit': 3}).encode()
req = urllib.request.Request(f'{BASE}/api/agent/advanced-search', data=body, headers=headers, method='POST')
resp = json.loads(urllib.request.urlopen(req, timeout=120).read())

print(f'Success: {resp["success"]}')
print(f'Message: {resp["message"]}')
if resp.get('data') and resp['data'].get('results'):
    for r in resp['data']['results']:
        title = r.get('title', '')
        method = r.get('retrieval_method', '')
        score = r.get('similarity', 0)
        print(f'  - {title} (method: {method}, score: {score:.3f})')
else:
    print('No results')
