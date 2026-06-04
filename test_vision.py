import httpx
from openai import OpenAI

client = OpenAI(
    api_key='sk-kBwNRlGIRsLBtfEP3Bc2KAk1xq4tfxv0lRTKFoaNQ2LGRQZq',
    base_url='https://api.moonshot.cn/v1',
    timeout=httpx.Timeout(60.0, connect=10.0)
)

try:
    resp = client.chat.completions.create(
        model='moonshot-v1-32k-vision-preview',
        messages=[{'role': 'user', 'content': 'hello'}],
        max_tokens=10
    )
    print(f'OK: {resp.choices[0].message.content}')
except Exception as e:
    print(f'Error: {type(e).__name__}: {str(e)[:200]}')
