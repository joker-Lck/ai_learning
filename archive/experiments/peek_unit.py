# -*- coding: utf-8 -*-
"""查看教材内容文件的单元标记真实格式"""
import os
import re

ROOT = r"F:\项目\ai教学辅助系统\experiments\corpus_textbook"
# 只看内容小节文件（X.Y 标题式），跳过教学计划/设计/习题
target = os.path.join(ROOT, "第一章 随机事件及其概率", "1.5 概率加法定理.md")
t = open(target, encoding="utf-8").read()
print("=== 1.5 概率加法定理.md 全文 ===")
print(t)
