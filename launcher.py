"""
AI 学习智能体 - 启动器
管理 Node.js、FastAPI 两个子进程（SQLite 无需独立进程）
"""
import os
import sys
import time
import signal
import subprocess
import socket
import webbrowser
import shutil
from pathlib import Path

# ── 路径配置 ──
if getattr(sys, 'frozen', False):
    # PyInstaller 打包后
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

NODE_DIR = BASE_DIR / "node"
NODE_EXE = NODE_DIR / "node.exe"
FRONTEND_DIR = BASE_DIR / "frontend"
FRONTEND_SERVER = FRONTEND_DIR / "server.js"
LOGS_DIR = BASE_DIR / "logs"
ENV_FILE = BASE_DIR / ".env"
ENV_EXAMPLE = BASE_DIR / ".env.example"
SQLITE_DB_DIR = BASE_DIR / "data" / "databases"

# 端口配置
BACKEND_PORT = 8000
FRONTEND_PORT = 3000

# 子进程列表
processes = []


def log(msg, level="INFO"):
    """打印带时间戳的日志"""
    timestamp = time.strftime("%H:%M:%S")
    prefix = {"INFO": "[*]", "OK": "[+]", "WARN": "[!]", "ERROR": "[-]"}.get(level, "[*]")
    print(f"  {prefix} [{timestamp}] {msg}")


def check_port(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def wait_for_port(port, timeout=60, service_name="service"):
    """等待端口可用"""
    start = time.time()
    while time.time() - start < timeout:
        if check_port(port):
            return True
        time.sleep(1)
    log(f"{service_name} 启动超时 ({timeout}s)", "ERROR")
    return False


def kill_port(port):
    """杀死占用指定端口的进程"""
    try:
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        for line in result.stdout.split('\n'):
            if f':{port}' in line and 'LISTENING' in line:
                pid = line.strip().split()[-1]
                if pid.isdigit():
                    subprocess.run(
                        ['taskkill', '/F', '/PID', pid],
                        capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    log(f"已终止占用端口 {port} 的进程 {pid}")
    except Exception:
        pass


def setup_env():
    """检查并创建 .env 文件"""
    if ENV_FILE.exists():
        log(".env 文件已存在", "OK")
        return True

    if ENV_EXAMPLE.exists():
        shutil.copy(ENV_EXAMPLE, ENV_FILE)
        log("已从 .env.example 创建 .env 文件", "WARN")
        log("请编辑 .env 文件配置 API Key 后重新启动", "WARN")
        return False

    log(".env 和 .env.example 均不存在", "ERROR")
    return False


def init_sqlite():
    """初始化 SQLite 数据目录"""
    SQLITE_DB_DIR.mkdir(parents=True, exist_ok=True)
    log(f"SQLite 数据目录: {SQLITE_DB_DIR}", "OK")
    return True


def init_databases():
    """初始化数据库表"""
    init_script = BASE_DIR / "scripts" / "init_databases_v7.2.py"
    if not init_script.exists():
        log("数据库初始化脚本不存在，跳过", "WARN")
        return True

    log("初始化数据库...")
    try:
        result = subprocess.run(
            [sys.executable, str(init_script)],
            capture_output=True, text=True,
            cwd=str(BASE_DIR),
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode == 0:
            log("数据库初始化完成", "OK")
        else:
            log(f"数据库初始化警告: {result.stderr[:200]}", "WARN")
        return True
    except Exception as e:
        log(f"数据库初始化异常: {e}", "WARN")
        return True


def start_backend():
    """启动 FastAPI 后端"""
    if check_port(BACKEND_PORT):
        log(f"端口 {BACKEND_PORT} 已被占用，尝试释放...")
        kill_port(BACKEND_PORT)
        time.sleep(2)

    log("启动后端服务...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app",
         "--host", "0.0.0.0", "--port", str(BACKEND_PORT)],
        cwd=str(BASE_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    processes.append(("Backend", proc))

    if wait_for_port(BACKEND_PORT, timeout=30, service_name="Backend"):
        log(f"后端启动成功 http://localhost:{BACKEND_PORT}", "OK")
        return True
    else:
        log("后端启动失败", "ERROR")
        return False


def start_frontend():
    """启动 Next.js 前端"""
    if check_port(FRONTEND_PORT):
        log(f"端口 {FRONTEND_PORT} 已被占用，尝试释放...")
        kill_port(FRONTEND_PORT)
        time.sleep(2)

    if not NODE_EXE.exists():
        log("node.exe 不存在，跳过前端启动", "WARN")
        log("请确保 Node.js 已安装", "WARN")
        return True

    if not FRONTEND_SERVER.exists():
        log("frontend/server.js 不存在，跳过前端启动", "WARN")
        return True

    log("启动前端服务...")
    env = os.environ.copy()
    env["NODE_ENV"] = "production"
    env["PORT"] = str(FRONTEND_PORT)

    proc = subprocess.Popen(
        [str(NODE_EXE), "server.js"],
        cwd=str(FRONTEND_DIR),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    processes.append(("Frontend", proc))

    if wait_for_port(FRONTEND_PORT, timeout=30, service_name="Frontend"):
        log(f"前端启动成功 http://localhost:{FRONTEND_PORT}", "OK")
        return True
    else:
        log("前端启动失败", "ERROR")
        return False


def open_browser():
    """打开浏览器"""
    url = f"http://localhost:{FRONTEND_PORT}"
    log(f"打开浏览器: {url}")
    webbrowser.open(url)


def cleanup():
    """清理所有子进程"""
    log("正在关闭所有服务...")
    for name, proc in processes:
        try:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=5)
                log(f"{name} 已关闭")
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


def signal_handler(sig, frame):
    """信号处理"""
    cleanup()
    sys.exit(0)


def main():
    """主函数"""
    print()
    print("=" * 50)
    print("   AI 学习智能体 - 启动中...")
    print("=" * 50)
    print()

    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 创建日志目录
    LOGS_DIR.mkdir(exist_ok=True)

    # 步骤 1: 检查 .env
    log("[1/5] 检查环境配置...")
    if not setup_env():
        input("\n按回车键退出...")
        return

    # 步骤 2: 初始化 SQLite
    log("[2/5] 初始化 SQLite...")
    init_sqlite()

    # 步骤 3: 初始化数据库
    log("[3/5] 初始化数据库...")
    init_databases()

    # 步骤 4: 启动后端
    log("[4/5] 启动后端服务...")
    if not start_backend():
        input("\n按回车键退出...")
        cleanup()
        return

    # 步骤 5: 启动前端
    log("[5/5] 启动前端服务...")
    start_frontend()

    print()
    print("=" * 50)
    print("   系统启动完成!")
    print("=" * 50)
    print()
    print(f"   前端: http://localhost:{FRONTEND_PORT}")
    print(f"   后端: http://localhost:{BACKEND_PORT}")
    print(f"   API:  http://localhost:{BACKEND_PORT}/api/docs")
    print()

    # 打开浏览器
    time.sleep(2)
    open_browser()

    print("按 Ctrl+C 停止所有服务...")
    print()

    # 保持运行
    try:
        while True:
            time.sleep(1)
            # 检查子进程是否还在运行
            for name, proc in processes:
                if proc.poll() is not None:
                    log(f"{name} 已意外退出", "WARN")
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()
        print("\n所有服务已停止。")


if __name__ == "__main__":
    main()
