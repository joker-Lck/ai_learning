@echo off
chcp 65001 >nul 2>&1
title AI Learning Agent - Setup
setlocal

:: 切换到项目根目录（scripts/ 的上级目录）
cd /d "%~dp0.."
set "ROOT=%CD%\"

echo ========================================
echo   AI Learning Agent - Environment Setup
echo ========================================
echo.

:: 1. Check Python
echo [1/7] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [OK] Python %PYVER%

:: 2. Check venv
echo [2/7] Checking virtual environment...
if not exist "%ROOT%.venv\Scripts\python.exe" (
    echo [INFO] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment exists
)

:: 3. Install backend dependencies
echo [3/7] Installing backend dependencies...
"%ROOT%.venv\Scripts\python.exe" -m pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing packages...
    "%ROOT%.venv\Scripts\python.exe" -m pip install -r "%ROOT%backend\requirements.txt" -q
    "%ROOT%.venv\Scripts\python.exe" -m pip install pydantic-settings pytest pytest-asyncio pytest-cov pytest-mock httpx -q
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [OK] Backend dependencies installed
) else (
    echo [OK] Backend dependencies already installed
)

:: 4. Check Node.js
echo [4/7] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Please install Node.js 18+
    pause
    exit /b 1
)
for /f %%v in ('node --version') do set NODEVER=%%v
echo [OK] Node.js %NODEVER%

:: 5. Check .env
echo [5/7] Checking environment config...
if not exist "%ROOT%.env" (
    if exist "%ROOT%.env.example" (
        copy "%ROOT%.env.example" "%ROOT%.env" >nul
        echo [WARN] .env created from .env.example
        echo        Please edit .env and set:
        echo        - MIMO_API_KEY (required)
        echo        - JWT_SECRET (required, 32+ chars)
        echo.
        notepad "%ROOT%.env"
        echo Press any key after editing .env...
        pause >nul
    ) else (
        echo [ERROR] .env.example not found
        pause
        exit /b 1
    )
) else (
    echo [OK] .env exists
)

:: 6. Initialize databases
echo [6/7] Initializing databases...
set "PYTHONPATH=%ROOT%"
"%ROOT%.venv\Scripts\python.exe" scripts\init_databases_v7.2.py
if errorlevel 1 (
    echo [WARN] Database initialization had issues (may already exist)
) else (
    echo [OK] Databases initialized
)

:: 7. Install frontend dependencies
echo [7/7] Checking frontend dependencies...
if not exist "%ROOT%frontend\node_modules" (
    echo [INFO] Installing frontend packages...
    cd /d "%ROOT%frontend"
    call npm install -q
    cd /d "%ROOT%"
    echo [OK] Frontend dependencies installed
) else (
    echo [OK] Frontend dependencies already installed
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo   Next steps:
echo   1. Edit .env if needed (MIMO_API_KEY)
echo   2. Run scripts\启动.bat to start the system
echo   3. Open http://localhost:3000
echo.
pause
