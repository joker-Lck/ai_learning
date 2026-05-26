"""
创建默认管理员账号
用于快速初始化系统管理员
"""

from services.auth_service import auth_service


def create_default_admin():
    """创建默认管理员账号"""
    
    print("=" * 50)
    print("🔑 创建默认管理员账号")
    print("=" * 50)
    
    # 默认管理员信息
    admin_username = "admin"
    admin_password = "admin123"
    admin_email = "admin@teaching.ai"
    admin_role = "admin"
    
    print(f"\n 用户名：{admin_username}")
    print(f" 密码：{admin_password}")
    print(f" 邮箱：{admin_email}")
    print(f" 角色：{admin_role}")
    print("\n⚠️ 请在首次登录后立即修改密码！")
    print("-" * 50)
    
    confirm = input("\n是否继续创建？(y/n): ")
    
    if confirm.lower() != 'y':
        print(" 已取消")
        return
    
    # 尝试创建
    result = auth_service.register_user(
        username=admin_username,
        password=admin_password,
        email=admin_email,
        role=admin_role
    )
    
    if result['success']:
        print("\n✅ 管理员账号创建成功！")
        print(f"   用户 ID: {result['user_id']}")
        print("\n 登录信息：")
        print(f"   用户名：{admin_username}")
        print(f"   密码：{admin_password}")
        print("\n⚠️ 重要提示：")
        print("   1. 请立即修改默认密码")
        print("   2. 妥善保管管理员账号")
        print("   3. 不要将密码泄露给他人")
    else:
        print(f"\n❌ 创建失败：{result['message']}")
        if "已存在" in result['message']:
            print("\n💡 提示：管理员账号已存在，请使用现有账号登录")
    
    print("\n" + "=" * 50)


def create_test_users():
    """创建测试用户（可选）"""
    
    print("\n" + "=" * 50)
    print("🧪 创建测试用户")
    print("=" * 50)
    
    test_users = [
        {
            'username': 'test_teacher',
            'password': '123456',
            'email': 'teacher@test.com',
            'role': 'teacher'
        },
        {
            'username': 'test_student',
            'password': '123456',
            'email': 'student@test.com',
            'role': 'student'
        }
    ]
    
    for user in test_users:
        print(f"\n 创建用户：{user['username']}")
        result = auth_service.register_user(
            username=user['username'],
            password=user['password'],
            email=user['email'],
            role=user['role']
        )
        
        if result['success']:
            print(f"   ✅ 创建成功 (ID: {result['user_id']})")
        else:
            print(f"   ⚠️ {result['message']}")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    # 创建默认管理员
    create_default_admin()
    
    # 询问是否创建测试用户
    print("\n是否创建测试用户？（test_teacher 和 test_student）")
    confirm = input("(y/n): ")
    
    if confirm.lower() == 'y':
        create_test_users()
    
    print("\n✅ 初始化完成！")
    print("\n启动应用：streamlit run streamlit_001.py")
