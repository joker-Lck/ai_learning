import sys
sys.path.insert(0, '.')

from services.spark_client import spark_client
from core.json_utils import safe_parse_json

print("Testing video script generation...")
prompt = """请为数学课程的"线性回归"主题生成一个教学视频脚本。

要求：
1. 生成 4 个场景
2. 每个场景包含：标题、讲解文字、关键要点
3. 输出严格JSON格式

只输出JSON，不要其他文字。"""

try:
    response = spark_client.chat(prompt, max_tokens=3000)
    print(f"Response length: {len(response)}")
    print(f"Response: {response[:500]}")
    
    # Try to parse JSON
    data = safe_parse_json(response)
    if data:
        print(f"\nParsed JSON successfully!")
        print(f"Title: {data.get('title')}")
        scenes = data.get('scenes', [])
        print(f"Scenes: {len(scenes)}")
        for s in scenes[:2]:
            print(f"  - {s.get('title')}: {s.get('narration', '')[:50]}...")
    else:
        print("\nFailed to parse JSON")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
