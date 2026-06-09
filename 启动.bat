@echo off
title AI Learning Agent
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"
echo ========================================
echo   AI Learning Agent - Starting...
echo ========================================
if not exist "%ROOT%.venv\Scripts\python.exe" (
    echo [ERROR] .venv not found
    pause
    exit /b 1
)
echo [OK] Python venv
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found
    pause
    exit /b 1
)
echo [OK] Node.js
if not exist "%ROOT%.env" (
    if exist "%ROOT%.env.example" (
        copy "%ROOT%.env.example" "%ROOT%.env" >nul
        echo [WARN] .env created from .env.example - please edit it
        pause
    )
)
echo [1/5] Backend deps...
"%ROOT%.venv\Scripts\python.exe" -m pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing...
    "%ROOT%.venv\Scripts\python.exe" -m pip install -r "%ROOT%backend\requirements.txt"
)
echo [OK] Backend deps
echo [2/5] MySQL check...
"%ROOT%.venv\Scripts\python.exe" -c "from dotenv import load_dotenv; import os; load_dotenv(); import mysql.connector; mysql.connector.connect(host=os.getenv('PROFILE_DB_HOST','localhost'),port=int(os.getenv('PROFILE_DB_PORT',3306)),user=os.getenv('PROFILE_DB_USER','root'),password=os.getenv('PROFILE_DB_PASSWORD',''),connect_timeout=3)" >nul 2>&1
if errorlevel 1 (
    echo [WARN] MySQL not reachable - check .env password and MySQL service
    echo        Run: .venv\Scripts\python.exe check_env.py
)
echo [3/5] Frontend deps...
if not exist "%ROOT%frontend\node_modules" (
    cd /d "%ROOT%frontend"
    call npm install
    cd /d "%ROOT%"
)
echo [OK] Frontend deps
echo [4/5] Starting backend...
start "Backend" /D "%ROOT%" cmd /k ".venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 5 /nobreak >nul
echo [5/5] Starting frontend...
start "Frontend" /D "%ROOT%frontend" cmd /k "npm run dev"
echo.
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo.
timeout /t 8 /nobreak >nul
start http://localhost:3000
pause
