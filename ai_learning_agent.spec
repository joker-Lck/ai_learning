# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置 - AI 学习智能体
"""
import os
import sys
from pathlib import Path

block_cipher = None
BASE_DIR = os.path.dirname(os.path.abspath(SPEC))

# ── 数据文件 ──
datas = []

# 配置文件
if os.path.exists(os.path.join(BASE_DIR, '.env.example')):
    datas.append((os.path.join(BASE_DIR, '.env.example'), '.'))
if os.path.exists(os.path.join(BASE_DIR, 'config')):
    datas.append((os.path.join(BASE_DIR, 'config'), 'config'))

# 脚本
if os.path.exists(os.path.join(BASE_DIR, 'scripts')):
    datas.append((os.path.join(BASE_DIR, 'scripts'), 'scripts'))

# 后端模块
datas.append((os.path.join(BASE_DIR, 'backend'), 'backend'))
datas.append((os.path.join(BASE_DIR, 'core'), 'core'))
datas.append((os.path.join(BASE_DIR, 'services'), 'services'))
datas.append((os.path.join(BASE_DIR, 'data'), 'data'))

# ── 隐藏导入 ──
hiddenimports = [
    # FastAPI / Uvicorn
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'fastapi.responses',
    'fastapi.staticfiles',
    'fastapi.middleware',
    'fastapi.middleware.cors',
    'fastapi.middleware.gzip',

    # 数据库
    'sqlite3',

    # AI
    'openai',

    # 数据处理
    'numpy',
    'faiss',
    'pandas',

    # 文档处理
    'docx',
    'pptx',
    'PyPDF2',
    'fitz',
    'openpyxl',

    # 认证
    'jwt',
    'bcrypt',

    # 速率限制
    'slowapi',

    # 图片
    'PIL',

    # Redis
    'redis',

    # dotenv
    'dotenv',
]

# ── 排除模块 ──
excludes = [
    'tkinter',
    'matplotlib',
    'scipy',
    'IPython',
    'jupyter',
    'notebook',
    'pytest',
    'unittest',
]

a = Analysis(
    ['launcher.py'],
    pathex=[BASE_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI学习智能体',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 保留控制台以便查看日志
    icon=None,  # 可以添加 .ico 图标文件
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AI学习智能体',
)
