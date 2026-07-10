"""
AI 学习智能体 - 自动化构建脚本
下载便携依赖 -> 构建前端 -> PyInstaller 打包 -> 组装目录
"""
import os
import sys
import shutil
import subprocess
import zipfile
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).parent
DIST_DIR = BASE_DIR / "dist" / "AI学习智能体"
BUILD_DIR = BASE_DIR / "build"
NODE_PORTABLE_DIR = BASE_DIR / "node_portable"

# 便携版下载链接
NODE_VERSION = "v18.20.4"
NODE_URL = f"https://nodejs.org/dist/{NODE_VERSION}/node-{NODE_VERSION}-win-x64.zip"


def log(msg, level="INFO"):
    prefix = {"INFO": "[*]", "OK": "[+]", "WARN": "[!]", "ERROR": "[-]"}.get(level, "[*]")
    print(f"{prefix} {msg}")


def download_file(url, dest):
    """下载文件"""
    if dest.exists():
        log(f"文件已存在: {dest.name}", "OK")
        return True

    log(f"下载: {url}")
    try:
        urllib.request.urlretrieve(url, str(dest))
        log(f"下载完成: {dest.name}", "OK")
        return True
    except Exception as e:
        log(f"下载失败: {e}", "ERROR")
        return False


def extract_zip(zip_path, dest_dir):
    """解压 ZIP 文件"""
    if dest_dir.exists() and any(dest_dir.iterdir()):
        log(f"目录已存在: {dest_dir.name}", "OK")
        return True

    log(f"解压: {zip_path.name}")
    try:
        with zipfile.ZipFile(str(zip_path), 'r') as zip_ref:
            zip_ref.extractall(str(dest_dir))
        log(f"解压完成: {dest_dir.name}", "OK")
        return True
    except Exception as e:
        log(f"解压失败: {e}", "ERROR")
        return False


def setup_node_portable():
    """下载并配置便携 Node.js"""
    log("配置便携 Node.js...")

    zip_file = BASE_DIR / "downloads" / f"node-{NODE_VERSION}-win-x64.zip"
    zip_file.parent.mkdir(exist_ok=True)

    if not download_file(NODE_URL, zip_file):
        log("Node.js 下载失败，请手动下载并放置到 node_portable/", "ERROR")
        log(f"下载地址: {NODE_URL}", "INFO")
        return False

    # 解压
    extract_dir = NODE_PORTABLE_DIR / "temp"
    if not extract_zip(zip_file, extract_dir):
        return False

    # 移动文件（ZIP 内有一层目录）
    extracted_dirs = list(extract_dir.iterdir())
    if extracted_dirs:
        src = extracted_dirs[0]
        for item in src.iterdir():
            dest = NODE_PORTABLE_DIR / item.name
            if item.is_dir():
                shutil.copytree(str(item), str(dest), dirs_exist_ok=True)
            else:
                shutil.copy2(str(item), str(dest))
        shutil.rmtree(str(extract_dir))

    log("便携 Node.js 配置完成", "OK")
    return True


def build_frontend():
    """构建前端"""
    frontend_dir = BASE_DIR / "frontend"
    if not frontend_dir.exists():
        log("frontend 目录不存在", "ERROR")
        return False

    # 检查是否已有 standalone 构建
    standalone = frontend_dir / ".next" / "standalone"
    if standalone.exists() and (standalone / "server.js").exists():
        log("前端 standalone 构建已存在", "OK")
        return True

    log("构建前端...")
    try:
        subprocess.run(
            ["npm", "run", "build"],
            cwd=str(frontend_dir),
            check=True,
            shell=True
        )
        log("前端构建完成", "OK")
        return True
    except subprocess.CalledProcessError as e:
        log(f"前端构建失败: {e}", "ERROR")
        return False


def run_pyinstaller():
    """运行 PyInstaller"""
    spec_file = BASE_DIR / "ai_learning_agent.spec"
    if not spec_file.exists():
        log("ai_learning_agent.spec 不存在", "ERROR")
        return False

    log("运行 PyInstaller...")
    try:
        subprocess.run(
            [sys.executable, "-m", "PyInstaller",
             str(spec_file),
             "--clean",
             "-y",
             "--distpath", str(BASE_DIR / "dist"),
             "--workpath", str(BUILD_DIR)],
            check=True
        )
        log("PyInstaller 打包完成", "OK")
        return True
    except subprocess.CalledProcessError as e:
        log(f"PyInstaller 打包失败: {e}", "ERROR")
        return False


def assemble_dist():
    """组装最终分发目录"""
    log("组装分发目录...")

    pyinstaller_dist = BASE_DIR / "dist" / "AI学习智能体"
    if not pyinstaller_dist.exists():
        log("PyInstaller 输出目录不存在", "ERROR")
        return False

    # 复制前端
    frontend_src = BASE_DIR / "frontend"
    frontend_dest = DIST_DIR / "frontend"
    if frontend_dest.exists():
        shutil.rmtree(str(frontend_dest))

    standalone_src = frontend_src / ".next" / "standalone"
    if standalone_src.exists():
        shutil.copytree(str(standalone_src), str(frontend_dest))
        # 复制 public 目录
        public_src = frontend_src / "public"
        if public_src.exists():
            shutil.copytree(str(public_src), str(frontend_dest / "public"), dirs_exist_ok=True)
        # 复制 static 文件
        static_src = frontend_src / ".next" / "static"
        if static_src.exists():
            static_dest = frontend_dest / ".next" / "static"
            shutil.copytree(str(static_src), str(static_dest), dirs_exist_ok=True)
        log("前端文件复制完成", "OK")

    # 复制便携 Node.js
    node_dest = DIST_DIR / "node"
    if NODE_PORTABLE_DIR.exists():
        if node_dest.exists():
            shutil.rmtree(str(node_dest))
        shutil.copytree(str(NODE_PORTABLE_DIR), str(node_dest))
        log("便携 Node.js 复制完成", "OK")

    # 复制数据文件
    for dirname in ["data", "exports", "config", "scripts"]:
        src = BASE_DIR / dirname
        if src.exists():
            dest = DIST_DIR / dirname
            if dest.exists():
                shutil.rmtree(str(dest))
            shutil.copytree(str(src), str(dest))

    # 确保 SQLite 数据库目录存在
    sqlite_dir = DIST_DIR / "data" / "databases"
    sqlite_dir.mkdir(parents=True, exist_ok=True)

    # 复制 .env.example
    env_example = BASE_DIR / ".env.example"
    if env_example.exists():
        shutil.copy2(str(env_example), str(DIST_DIR / ".env.example"))

    log("分发目录组装完成", "OK")
    return True


def main():
    print()
    print("=" * 50)
    print("   AI 学习智能体 - 构建脚本")
    print("=" * 50)
    print()

    # 检查依赖
    log("[1/4] 检查构建依赖...")
    try:
        import PyInstaller
        log(f"PyInstaller {PyInstaller.__version__}", "OK")
    except ImportError:
        log("PyInstaller 未安装，正在安装...", "WARN")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    # 构建前端
    log("[2/4] 构建前端...")
    if not build_frontend():
        log("前端构建失败，但将继续打包", "WARN")

    # 下载便携依赖
    log("[3/4] 准备便携 Node.js...")
    setup_node_portable()

    # PyInstaller 打包
    log("[4/4] PyInstaller 打包...")
    if not run_pyinstaller():
        log("PyInstaller 打包失败", "ERROR")
        return

    # 组装目录
    if not assemble_dist():
        log("目录组装失败", "ERROR")
        return

    print()
    print("=" * 50)
    print("   构建完成!")
    print("=" * 50)
    print()
    print(f"   输出目录: {DIST_DIR}")
    print()
    print("   下一步:")
    print("   1. 检查 dist/AI学习智能体/ 目录")
    print("   2. 双击 AI学习智能体.exe 测试启动")
    print("   3. 使用 NSIS 打包为安装程序")
    print()


if __name__ == "__main__":
    main()
