@echo off
chcp 65001 >nul 2>&1
title AI Teaching Assistant v6.0
setlocal

set "ROOT=%~dp0"
cd /d "%ROOT%"

echo.
echo ========================================
echo   AI Teaching Assistant v6.0
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)
echo [OK] Python found

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
        echo [WARN] Created .env from .env.example
    )
)

echo.
echo [1/4] Checking backend deps...
pip show fastapi >nul 2>&1
if errorlevel 1 goto install_backend
goto check_frontend

:install_backend
echo Installing backend deps...
pip install -r "%ROOT%backend\requirements.txt"
if errorlevel 1 (
    echo [ERROR] Backend deps install failed
    pause
    exit /b 1
)

:check_frontend
echo [OK] Backend deps ready
echo [2/4] Checking frontend deps...
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
echo [3/4] Starting backend on port 8000...
start "Backend-API" /D "%ROOT%" cmd /k "title Backend-API && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 5 /nobreak >nul

echo [4/4] Starting frontend on port 3000...
start "Frontend" /D "%ROOT%frontend" cmd /k "title Frontend && npm run dev"

echo.
echo ========================================
echo   Started!
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo   Login:     admin / admin123
echo ========================================
echo.

timeout /t 8 /nobreak >nul
start http://localhost:3000

pause
