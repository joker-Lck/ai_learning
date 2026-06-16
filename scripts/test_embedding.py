import requests
import json
import base64
import hmac
import hashlib
import numpy as np
from datetime import datetime, timezone
from urllib.parse import urlencode, urlparse

APPID = 'c614eb5c'
API_KEY = 'e9f77aa2e9135cdfbadc38c996f70b1c'
API_SECRET = 'ZTUxMWMxYzY0Yjc5ZmM5YjBiN2YzYmZk'

def format_date(dt):
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    return f'{days[dt.weekday()]}, {dt.day:02d} {months[dt.month-1]} {dt.year} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d} GMT'

def create_auth_url(base_url, api_key, api_secret):
    parsed = urlparse(base_url)
    host = parsed.hostname
    path = parsed.path
    
    now = datetime.now(timezone.utc)
    date = format_date(now)
    
    # 注意：用POST而不是GET
    signature_origin = f'host: {host}\ndate: {date}\nPOST {path} HTTP/1.1'
    
    signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(signature_sha).decode('utf-8')
    
    authorization_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
    
    v = {
        'authorization': authorization,
        'date': date,
        'host': host,
    }
    return f'{base_url}?{urlencode(v)}'

text = '机器学习基础'
text_json = json.dumps({'messages': [{'content': text, 'role': 'user'}]})
text_base64 = base64.b64encode(text_json.encode('utf-8')).decode('utf-8')

body = {
    'header': {'app_id': APPID, 'uid': 'test_user', 'status': 3},
    'parameter': {
        'emb': {
            'domain': 'query',
            'feature': {'encoding': 'utf8', 'compress': 'raw', 'format': 'plain'}
        }
    },
    'payload': {
        'messages': {
            'encoding': 'utf8',
            'compress': 'raw',
            'format': 'json',
            'status': 3,
            'text': text_base64
        }
    }
}

print('=== 测试 Embedding HTTP 端点（POST鉴权）===')

urls = [
    'https://emb-cn-huabei-1.xf-yun.com/',
    'http://emb-cn-huabei-1.xf-yun.com/',
]

for base_url in urls:
    print(f'\nTesting: {base_url}')
    try:
        url = create_auth_url(base_url, API_KEY, API_SECRET)
        resp = requests.post(url, json=body, timeout=15)
        print(f'  Status: {resp.status_code}')
        print(f'  Response: {resp.text[:300]}')
        
        if resp.status_code == 200:
            result = resp.json()
            code = result.get('header', {}).get('code', -1)
            if code == 0:
                text_b64 = result['payload']['feature']['text']
                text_data = base64.b64decode(text_b64)
                dt = np.dtype(np.float32).newbyteorder('<')
                vector = np.frombuffer(text_data, dtype=dt)
                print(f'  SUCCESS! Dimension: {len(vector)}')
                print(f'  First 5 values: {vector[:5]}')
                break
    except Exception as e:
        print(f'  Error: {type(e).__name__}: {e}')
