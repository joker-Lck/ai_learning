@echo off
chcp 65001 >nul 2>&1
title AI Learning Agent System v7.2
setlocal

set "ROOT=%~dp0"
cd /d "%ROOT%"

echo.
echo ========================================
echo   AI Learning Agent System v7.2
echo   基于多智能体的个性化学习资源生成系统
echo ========================================
echo.

:: 使用 venv Python
set "PYEXE=%ROOT%.venv\Scripts\python.exe"
if not exist "%PYEXE%" (
    echo [ERROR] venv not found at .venv
    echo        Run: python -m venv .venv ^&^& .venv\Scripts\pip install -r backend\requirements.txt
    pause
    exit /b 1
)
echo [OK] Python venv found

node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found
    pause
    exit /b 1
)
echo [OK] Node.js found

if not exist "%ROOT%.env" (
    if exist "%ROOT%.env.example" (
        copy "%ROOT%.env.example" "%ROOT%.env" >nul
        echo [WARN] Created .env from .env.example — please fill in your API keys
    )
)

echo.
echo [1/5] Checking backend deps...
"%PYEXE%" -m pip show fastapi >nul 2>&1
if errorlevel 1 goto install_backend
goto check_mysql

:install_backend
echo Installing backend deps...
"%PYEXE%" -m pip install -r "%ROOT%backend\requirements.txt"
if errorlevel 1 (
    echo [ERROR] Backend deps install failed
    pause
    exit /b 1
)

:check_mysql
echo [OK] Backend deps ready
echo [2/5] Checking MySQL connection...
"%PYEXE%" -c "import mysql.connector; mysql.connector.connect(host='localhost',port=3306,user='root',password='root',connect_timeout=3)" >nul 2>&1
if errorlevel 1 (
    echo [WARN] MySQL not reachable. Please ensure MySQL is running.
    echo        The app may not work correctly without a database.
    echo.
)

:check_frontend
echo [3/5] Checking frontend deps...
if exist "%ROOT%frontend\node_modules" goto start_services
echo Installing frontend deps...
cd /d "%ROOT%frontend"
call npm install
if errorlevel 1 (
    echo [ERROR] Frontend deps install failed
    pause
    exit /b 1
)
cd /d "%ROOT%"

:start_services
echo [OK] Frontend deps ready
echo.
echo [4/5] Starting backend on port 8000...
start "Backend-API" /D "%ROOT%" cmd /k "title Backend-API && "%PYEXE%" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 5 /nobreak >nul

echo [5/5] Starting frontend on port 3000...
start "Frontend" /D "%ROOT%frontend" cmd /k "title Frontend && npm run dev"

echo.
echo ========================================
echo   Started!
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo   Login:     请使用 init_admin.py 创建的账号
echo ========================================
echo.

timeout /t 8 /nobreak >nul
start http://localhost:3000

pause
