@echo off
chcp 65001 >nul 2>&1
title AI Learning Agent
setlocal

:: 切换到项目根目录（scripts/ 的上级目录）
cd /d "%~dp0.."
set "ROOT=%CD%\"

echo ========================================
echo   AI Learning Agent - Starting...
echo ========================================

:: 检查 Python 虚拟环境
if not exist "%ROOT%.venv\Scripts\python.exe" (
    echo [ERROR] .venv not found
    echo        Run scripts\setup.bat first to configure the environment
    pause
    exit /b 1
)
echo [OK] Python venv

:: 检查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found
    pause
    exit /b 1
)
echo [OK] Node.js

:: 检查 .env
if not exist "%ROOT%.env" (
    if exist "%ROOT%.env.example" (
        copy "%ROOT%.env.example" "%ROOT%.env" >nul
        echo [WARN] .env created from .env.example - please edit it
        pause
    ) else (
        echo [ERROR] .env not found and no .env.example
        pause
        exit /b 1
    )
)
echo [OK] .env exists

:: 杀掉占用端口的旧进程
echo [1/5] Cleaning up old processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo        Killing old backend process %%a
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    echo        Killing old frontend process %%a
    taskkill /F /PID %%a >nul 2>&1
)
echo [OK] Ports cleared

:: 检查后端依赖
echo [2/5] Backend deps...
"%ROOT%.venv\Scripts\python.exe" -m pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo        Installing backend packages...
    "%ROOT%.venv\Scripts\python.exe" -m pip install -r "%ROOT%backend\requirements.txt" -q
)
echo [OK] Backend deps

:: 检查前端依赖
echo [3/5] Frontend deps...
if not exist "%ROOT%frontend\node_modules" (
    echo        Installing frontend packages...
    cd /d "%ROOT%frontend"
    call npm install -q
    cd /d "%ROOT%"
)
echo [OK] Frontend deps

:: 启动后端
echo [4/5] Starting backend...
start "Backend" /D "%ROOT%" cmd /k ".venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

:: 等待后端启动
echo        Waiting for backend...
:wait_backend
timeout /t 2 /nobreak >nul
curl -s http://localhost:8000/api/health >nul 2>&1
if errorlevel 1 goto wait_backend
echo [OK] Backend started

:: 启动前端
echo [5/5] Starting frontend...
start "Frontend" /D "%ROOT%frontend" cmd /k "npm run dev"

:: 等待前端启动
echo        Waiting for frontend...
:wait_frontend
timeout /t 2 /nobreak >nul
curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 goto wait_frontend
echo [OK] Frontend started

echo.
echo ========================================
echo   System Started!
echo ========================================
echo.
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo.

:: 自动打开浏览器
timeout /t 2 /nobreak >nul
start http://localhost:3000

pause
