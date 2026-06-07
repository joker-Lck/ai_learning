r"""
环境检查脚本 — 启动前自动检测配置和依赖是否完整
运行: .venv\Scripts\python.exe check_env.py
"""

import sys
import os

# 将项目根目录加入 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_env_file():
    """检查 .env 文件是否存在且关键字段已填写"""
    print("\n📋 检查 .env 配置文件...")

    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_path):
        print("  ❌ .env 文件不存在！")
        print("     请执行: cp .env.example .env  然后编辑填入实际值")
        return False

    from dotenv import load_dotenv
    load_dotenv(env_path)

    required = {
        "JWT_SECRET": "JWT 密钥（用于登录 Token 签名）",
        "KIMI_API_KEY": "Kimi API Key（在 platform.moonshot.cn 获取）",
    }

    db_groups = [
        ("AUTH_DB", "认证数据库"),
        ("PROFILE_DB", "学生画像数据库"),
        ("ASSESSMENTS_DB", "学习评估数据库"),
    ]

    all_ok = True

    # 检查必需字段
    for key, desc in required.items():
        val = os.getenv(key, "")
        if not val or val.startswith("your_"):
            print(f"  ❌ {key} 未填写 — {desc}")
            all_ok = False
        else:
            print(f"  ✅ {key} 已配置")

    # 检查数据库密码
    for prefix, name in db_groups:
        pwd_key = f"{prefix}_PASSWORD"
        val = os.getenv(pwd_key, "")
        if not val or val.startswith("your_"):
            print(f"  ❌ {pwd_key} 未填写 — {name}密码")
            all_ok = False
        else:
            print(f"  ✅ {name} 密码已配置")

    return all_ok


def check_mysql_connection():
    """检查 MySQL 连接和数据库是否存在"""
    print("\n🗄️  检查 MySQL 数据库...")

    try:
        import mysql.connector
    except ImportError:
        print("  ❌ mysql-connector-python 未安装")
        print("     请执行: pip install mysql-connector-python")
        return False

    from dotenv import load_dotenv
    load_dotenv()

    host = os.getenv("AUTH_DB_HOST", "localhost")
    port = int(os.getenv("AUTH_DB_PORT", "3306"))
    user = os.getenv("AUTH_DB_USER", "root")
    password = os.getenv("AUTH_DB_PASSWORD", "")

    # 测试连接
    try:
        conn = mysql.connector.connect(
            host=host, port=port, user=user, password=password, use_pure=True
        )
        conn.close()
        print(f"  ✅ MySQL 连接成功 ({host}:{port})")
    except Exception as e:
        print(f"  ❌ MySQL 连接失败: {e}")
        print("     请确保 MySQL 已启动，且密码正确")
        return False

    # 检查数据库是否存在
    required_dbs = [
        ("ai_auth", "认证库"),
        ("ai_profiles", "学生画像库"),
        ("ai_resources", "学习资源库"),
        ("ai_paths", "学习路径库"),
        ("ai_tutor", "智能辅导库"),
        ("ai_assessments", "学习评估库"),
        ("ai_agents", "智能体协作库"),
        ("ai_rag_knowledge", "RAG 知识库"),
    ]

    try:
        conn = mysql.connector.connect(
            host=host, port=port, user=user, password=password, use_pure=True
        )
        cur = conn.cursor()
        cur.execute("SHOW DATABASES")
        existing = {r[0] for r in cur.fetchall()}
        conn.close()
    except Exception as e:
        print(f"  ❌ 查询数据库列表失败: {e}")
        return False

    all_ok = True
    for db_name, desc in required_dbs:
        if db_name in existing:
            print(f"  ✅ {db_name} ({desc})")
        else:
            print(f"  ❌ {db_name} ({desc}) — 数据库不存在")
            all_ok = False

    if not all_ok:
        print("\n  ⚠️  缺少数据库，请执行:")
        print("     .venv\\Scripts\\python.exe init_databases_v7.2.py")

    return all_ok


def check_key_tables():
    """检查关键表是否存在"""
    print("\n📊 检查关键数据表...")

    from dotenv import load_dotenv
    load_dotenv()

    import mysql.connector

    checks = [
        ("ai_auth", "users", "用户表"),
        ("ai_profiles", "student_profiles", "学生画像表"),
        ("ai_profiles", "course_schedules", "课程表"),
        ("ai_profiles", "student_grades", "成绩表"),
        ("ai_assessments", "learning_assessments", "评估表"),
    ]

    all_ok = True
    for db_name, table_name, desc in checks:
        try:
            conn = mysql.connector.connect(
                host=os.getenv(f"PROFILE_DB_HOST", "localhost"),
                port=int(os.getenv(f"PROFILE_DB_PORT", "3306")),
                user=os.getenv(f"PROFILE_DB_USER", "root"),
                password=os.getenv(f"PROFILE_DB_PASSWORD", ""),
                database=db_name,
                use_pure=True,
            )
            cur = conn.cursor()
            cur.execute(f"SHOW TABLES LIKE '{table_name}'")
            exists = cur.fetchone() is not None
            conn.close()

            if exists:
                print(f"  ✅ {db_name}.{table_name} ({desc})")
            else:
                print(f"  ❌ {db_name}.{table_name} ({desc}) — 表不存在")
                all_ok = False
        except Exception as e:
            print(f"  ⚠️  {db_name}.{table_name} — 无法检查: {e}")
            all_ok = False

    return all_ok


def check_python_deps():
    """检查 Python 依赖"""
    print("\n📦 检查 Python 依赖...")

    deps = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("openai", "OpenAI SDK"),
        ("mysql.connector", "MySQL Connector"),
        ("dotenv", "python-dotenv"),
        ("PIL", "Pillow"),
        ("pandas", "Pandas"),
    ]

    all_ok = True
    for module, name in deps:
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name} — 未安装")
            all_ok = False

    if not all_ok:
        print("\n  ⚠️  缺少依赖，请执行:")
        print("     pip install -r requirements.txt")

    return all_ok


def check_kimi_api():
    """快速测试 Kimi API 连通性"""
    print("\n🤖 检查 Kimi API 连通性...")

    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("KIMI_API_KEY", "")
    base_url = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")

    if not api_key or api_key.startswith("your_"):
        print("  ⏭️  跳过（KIMI_API_KEY 未配置）")
        return False

    try:
        from openai import OpenAI
        import httpx
        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=httpx.Timeout(10.0, connect=5.0),
        )
        # 发一个最简请求测试连通性
        resp = client.chat.completions.create(
            model="kimi-k2.5",
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=5,
        )
        content = resp.choices[0].message.content or ""
        if content or hasattr(resp.choices[0].message, 'reasoning_content'):
            print(f"  ✅ Kimi API 连接成功 (model=kimi-k2.5)")
            return True
        else:
            print(f"  ⚠️  Kimi API 返回空内容，可能模型不可用")
            return False
    except Exception as e:
        err_msg = str(e)
        if "401" in err_msg or "auth" in err_msg.lower():
            print(f"  ❌ API Key 无效 — 请检查 KIMI_API_KEY")
        elif "timeout" in err_msg.lower() or "connect" in err_msg.lower():
            print(f"  ❌ 网络连接超时 — 请检查网络或代理")
        else:
            print(f"  ❌ API 调用失败: {e}")
        return False


def main():
    print("=" * 55)
    print("  AI 学习助手 — 环境检查")
    print("=" * 55)

    results = {
        "Python 依赖": check_python_deps(),
        ".env 配置": check_env_file(),
        "MySQL 连接": check_mysql_connection(),
        "数据表": check_key_tables(),
        "Kimi API": check_kimi_api(),
    }

    print("\n" + "=" * 55)
    print("  检查结果汇总")
    print("=" * 55)

    all_pass = True
    for name, ok in results.items():
        status = "✅ 通过" if ok else "❌ 未通过"
        print(f"  {name:12s} {status}")
        if not ok:
            all_pass = False

    print("=" * 55)
    if all_pass:
        print("  🎉 所有检查通过！可以启动系统: 启动.bat")
    else:
        print("  ⚠️  部分检查未通过，请按上方提示修复后重试")
    print()

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
