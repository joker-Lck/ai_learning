"""
QA服务 - 提供Kimi API调用功能
向后兼容模块，供各智能体使用
"""

import os
from typing import Optional
from openai import OpenAI
from core.logger import info, error

class QAService:
    """QA服务，提供Kimi API调用"""
    
    def __init__(self):
        api_key = os.getenv('KIMI_API_KEY', '')
        if not api_key:
            error("KIMI_API_KEY 未设置")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.moonshot.cn/v1"
        )
        info("QA服务初始化完成")
    
    def call_kimi_api(self, prompt: str, max_tokens: int = 2000, system_prompt: str = None) -> str:
        """
        调用Kimi API
        
        Args:
            prompt: 用户提示词
            max_tokens: 最大token数
            system_prompt: 系统提示词
            
        Returns:
            API响应文本
        """
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model="moonshot-v1-8k",
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            error(f"Kimi API调用失败: {str(e)}")
            return f"错误: {str(e)}"

# 单例
qa_service = QAService()
