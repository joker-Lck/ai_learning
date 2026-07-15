@echo off
chcp 65001 >nul 2>&1
title AI学习智能体 - 移动端

echo ========================================
echo    AI学习智能体 - 移动端启动器
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 未安装
    pause
    exit /b 1
)

:: Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js 未安装
    pause
    exit /b 1
)

:: 切换到项目根目录
cd /d "%~dp0.."
set "SCRIPT_DIR=%CD%\"

echo [1/3] 启动后端服务...
start "AI学习智能体-后端" cmd /c "cd /d "%SCRIPT_DIR%" && .venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"

:: Wait for backend to start
echo [2/3] 等待后端启动...
timeout /t 5 /nobreak >nul

:: Check if backend is running
curl -s http://127.0.0.1:8000/api/health >nul 2>&1
if errorlevel 1 (
    echo [WARN] 后端可能还在启动中，继续...
)

echo [3/3] 启动移动端界面...
echo.
echo ========================================
echo    启动完成！
echo ========================================
echo.
echo    移动端: http://localhost:3001
echo    后端API: http://localhost:8000
echo    API文档: http://localhost:8000/docs
echo.
echo    默认账号: admin / admin123
echo.
echo    按 Ctrl+C 停止服务
echo ========================================
echo.

:: Start mobile web server
cd /d "%SCRIPT_DIR%mobile\web-dist"
npx serve -s . -l 3001 --no-clipboard

:: Cleanup on exit
echo.
echo 正在停止服务...
taskkill /FI "WINDOWTITLE eq AI学习智能体-后端" >nul 2>&1
echo 已停止
pause
