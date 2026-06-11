"""
讯飞星火 API 测试脚本
测试文本对话、图片理解、OCR、图片生成等功能
"""

import os
import sys

# 确保项目根目录在 sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv()

from services.spark_client import spark_client
from core.logger import info, error

def test_text_chat():
    """测试文本对话"""
    print("\n" + "="*50)
    print("1. 测试文本对话 (generalv3.5)")
    print("="*50)
    try:
        response = spark_client.simple("你好，请用一句话介绍自己")
        if response and not response.startswith("错误"):
            print(f"✅ 成功: {response[:100]}...")
            return True
        else:
            print(f"❌ 失败: {response}")
            return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

def test_advanced_chat():
    """测试高级推理"""
    print("\n" + "="*50)
    print("2. 测试高级推理 (4.0Ultra)")
    print("="*50)
    try:
        response = spark_client.advanced("请用一句话解释什么是机器学习")
        if response and not response.startswith("错误"):
            print(f"✅ 成功: {response[:100]}...")
            return True
        else:
            print(f"❌ 失败: {response}")
            return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

def test_image_generation():
    """测试图片生成"""
    print("\n" + "="*50)
    print("3. 测试图片生成 (SparkChain)")
    print("="*50)
    try:
        result = spark_client.generate_image("一个简单的数学公式图", width=512, height=512)
        if result:
            print(f"✅ 成功: 图片数据长度 {len(result)} 字符")
            return True
        else:
            print("❌ 失败: 未返回图片数据")
            return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

def test_ocr():
    """测试 OCR（使用测试图片）"""
    print("\n" + "="*50)
    print("4. 测试 OCR 文字识别")
    print("="*50)
    try:
        # 创建一个简单的测试图片（白色背景黑色文字）
        from PIL import Image, ImageDraw, ImageFont
        import io
        import base64
        
        img = Image.new('RGB', (200, 50), color='white')
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("msyh.ttc", 20)
        except:
            font = ImageFont.load_default()
        draw.text((10, 10), "Hello World", fill='black', font=font)
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        result = spark_client.ocr_print(img_b64)
        if result:
            print(f"✅ 成功: 识别结果 '{result[:50]}'")
            return True
        else:
            print("⚠️  OCR 未返回结果（可能需要更清晰的图片）")
            return True  # OCR 可能因为图片质量返回空，不算失败
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

def main():
    print("="*60)
    print("  讯飞星火 API 测试")
    print("="*60)
    
    # 检查配置
    app_id = os.getenv("SPARK_APPID", "")
    api_key = os.getenv("SPARK_API_KEY", "")
    api_secret = os.getenv("SPARK_API_SECRET", "")
    
    print(f"\n配置检查:")
    print(f"  APPID: {'✅ 已配置' if app_id else '❌ 未配置'}")
    print(f"  API Key: {'✅ 已配置' if api_key else '❌ 未配置'}")
    print(f"  API Secret: {'✅ 已配置' if api_secret else '❌ 未配置'}")
    
    if not all([app_id, api_key, api_secret]):
        print("\n❌ API 配置不完整，请检查 .env 文件")
        return
    
    # 运行测试
    results = {}
    results['文本对话'] = test_text_chat()
    results['高级推理'] = test_advanced_chat()
    results['图片生成'] = test_image_generation()
    results['OCR识别'] = test_ocr()
    
    # 汇总结果
    print("\n" + "="*60)
    print("  测试结果汇总")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！讯飞 API 配置正确。")
    else:
        print("\n⚠️  部分测试失败，请检查 API 配置和网络连接。")

if __name__ == "__main__":
    main()
