"""
安全 JSON 解析工具
处理 LLM 返回的 JSON 中常见的非法转义、markdown 包裹等问题
"""

import json
import re
from typing import Any

# 预编译正则表达式以提升性能
_CODE_FENCE_RE = re.compile(r'```(?:json)?\s*\n(.*?)\n\s*```', re.DOTALL)
_JSON_OBJECT_RE = re.compile(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', re.DOTALL)
_JSON_ARRAY_RE = re.compile(r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]', re.DOTALL)


def safe_parse_json(text: str) -> Any | None:
    """
    安全解析 LLM 返回的 JSON 文本
    
    处理常见问题：
    1. markdown 代码块包裹 (```json ... ```)
    2. 非法反斜杠转义 (\\s, \\d, \frac 等)
    3. 前后多余文字
    
    Args:
        text: LLM 返回的原始文本
        
    Returns:
        解析后的对象，失败返回 None
    """
    if not text or not isinstance(text, str):
        return None

    text = text.strip()

    # 快速路径：如果文本以 { 或 [ 开头，直接尝试解析
    if text and text[0] in ('{', '['):
        result = _try_loads(text)
        if result is not None:
            return result

    # 1. 尝试直接解析
    result = _try_loads(text)
    if result is not None:
        return result

    # 2. 去掉 markdown 代码块包裹
    cleaned = _strip_code_fences(text)
    result = _try_loads(cleaned)
    if result is not None:
        return result

    # 3. 修复非法反斜杠转义后重试
    fixed = _fix_invalid_escapes(cleaned)
    result = _try_loads(fixed)
    if result is not None:
        return result

    # 4. 提取第一个 JSON 对象或数组
    extracted = _extract_json(fixed)
    if extracted:
        result = _try_loads(extracted)
        if result is not None:
            return result
        # 对提取内容再修一次转义
        fixed_extracted = _fix_invalid_escapes(extracted)
        result = _try_loads(fixed_extracted)
        if result is not None:
            return result

    return None


def _try_loads(text: str) -> Any | None:
    """尝试 json.loads，失败返回 None"""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


def _strip_code_fences(text: str) -> str:
    """去掉 ```json ... ``` 或 ``` ... ``` 包裹"""
    match = _CODE_FENCE_RE.search(text)
    if match:
        return match.group(1).strip()
    return text


def _fix_invalid_escapes(text: str) -> str:
    """
    修复 JSON 字符串中非法的反斜杠转义
    
    JSON 合法转义: \\" \\\\ \\/ \\b \\f \\n \\r \\t \\uXXXX
    其他如 \\s \\d \\w \\frac \\( 等都需要将 \\ 替换为 \\\\
    """
    result = []
    i = 0
    in_string = False
    escape_next = False

    while i < len(text):
        ch = text[i]

        if escape_next:
            escape_next = False
            result.append(ch)
            i += 1
            continue

        if ch == '\\' and in_string:
            # 看下一个字符
            next_ch = text[i + 1] if i + 1 < len(text) else ''
            if next_ch in ('"', '\\', '/', 'b', 'f', 'n', 'r', 't'):
                # 合法 JSON 转义
                result.append(ch)
                result.append(next_ch)
                i += 2
                continue
            elif next_ch == 'u' and i + 5 < len(text):
                # \uXXXX
                hex_part = text[i + 2:i + 6]
                if all(c in '0123456789abcdefABCDEF' for c in hex_part):
                    result.append(text[i:i + 6])
                    i += 6
                    continue
            # 非法转义 → 转义反斜杠本身
            result.append('\\\\')
            i += 1
            continue

        if ch == '"' and not escape_next:
            in_string = not in_string

        if ch == '\\' and not in_string:
            # 字符串外不应该有反斜杠，跳过
            result.append(ch)
            i += 1
            continue

        result.append(ch)
        i += 1

    return ''.join(result)


def _extract_json(text: str) -> str | None:
    """从文本中提取第一个 JSON 对象或数组"""
    # 找第一个 { 或 [
    for start_ch, end_ch in [('{', '}'), ('[', ']')]:
        start = text.find(start_ch)
        if start == -1:
            continue

        depth = 0
        in_str = False
        escape = False
        for i in range(start, len(text)):
            c = text[i]
            if escape:
                escape = False
                continue
            if c == '\\' and in_str:
                escape = True
                continue
            if c == '"' and not escape:
                in_str = not in_str
                continue
            if not in_str:
                if c == start_ch:
                    depth += 1
                elif c == end_ch:
                    depth -= 1
                    if depth == 0:
                        return text[start:i + 1]

    return None
