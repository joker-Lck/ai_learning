"""
工具函数模块
"""
import re


def clean_json_string(text):
    """清理 JSON 字符串中的控制字符"""
    if not text:
        return ""
    if not isinstance(text, str):
        text = str(text)
    
    # 移除 Unicode 控制字符
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\x80-\x9f]', '', text)
    
    # 移除 BOM
    text = text.replace('\ufeff', '')
    
    # 移除零宽字符
    text = re.sub(r'[\u200b-\u200f\u2028-\u202f\u205f-\u206f\ufeff]', '', text)
    
    # 替换不可见字符为空格
    text = re.sub(r'[\u00a0\u1680\u180e\u2000-\u200a\u2028-\u2029\u202f\u205f\u3000]', ' ', text)
    
    return text.strip()


def safe_json_loads(text):
    """安全解析 JSON，自动处理常见格式问题"""
    import json
    
    if not text:
        return None
    
    text = clean_json_string(text)
    
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # 使用宽松模式
    try:
        return json.loads(text, strict=False)
    except json.JSONDecodeError:
        pass
    
    # 手动转义控制字符
    def escape_control_chars(match):
        """转义控制字符"""
        char = match.group(0)
        escape_map = {
            '\n': '\\n',
            '\t': '\\t',
            '\r': '\\r',
            '\b': '\\b',
            '\f': '\\f',
        }
        return escape_map.get(char, f'\\u{ord(char):04x}')
    
    def process_json_string(match):
        """处理 JSON 字符串值"""
        content = match.group(0)
        content = re.sub(r'[\x00-\x1f]', escape_control_chars, content)
        return content
    
    text = re.sub(r'"([^"\\]*(?:\\.[^"\\]*)*)"', process_json_string, text)
    
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"无法解析 JSON：{str(e)}")


def format_file_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def extract_urls(text):
    """从文本中提取 URL"""
    import re
    urls = re.findall(r'http[s]?://\S+', text)
    return urls


def truncate_text(text, max_length=50, suffix="..."):
    """截断文本到指定长度"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + suffix


def safe_get(dictionary, key, default=None):
    """安全获取字典值"""
    try:
        return dictionary.get(key, default)
    except (AttributeError, TypeError):
        return default


def validate_email(email):
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def generate_filename(prefix, extension, timestamp_format="%Y%m%d_%H%M%S"):
    """生成带时间戳的文件名"""
    from datetime import datetime
    timestamp = datetime.now().strftime(timestamp_format)
    return f"{prefix}_{timestamp}.{extension}"
