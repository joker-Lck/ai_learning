"""
UI 组件模块（已迁移至 frontend/ Next.js 前端）
此文件保留作为历史参考，不再被使用。
"""


class CustomCSS:
    """自定义 CSS 样式管理"""
    
    @staticmethod
    def get_custom_css():
        """返回自定义 CSS 样式"""
        return """
<style>
/* 全局背景 - 纯白色 */
.stApp {
    background: #ffffff;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* 聊天消息样式 */
.chat-user {
    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
    color: #333;
    padding: 15px;
    border-radius: 15px;
}
.chat-assistant {
    background: white;
    color: #333;
    padding: 15px;
    border-radius: 15px;
}

/* 卡片样式 */
.card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.05);
}

/* 状态指示器 */
.status-indicator {
    background: linear-gradient(135deg, #ffe0b2 0%, #ffcc80 100%);
    padding: 15px;
    border-radius: 10px;
    color: #555;
}

/* 输入框样式 */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background-color: white !important;
    border: 2px solid #4a90e2 !important;
    border-radius: 8px !important;
    font-size: 16px !important;
    padding: 12px !important;
    box-shadow: 0 2px 4px rgba(74,144,226,0.1) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #2196f3 !important;
    box-shadow: 0 4px 8px rgba(33,150,243,0.2) !important;
}

/* Selectbox 样式 */
.stSelectbox > div > div > select {
    background-color: white !important;
    border: 2px solid #4a90e2 !important;
    border-radius: 8px !important;
}

/* 按钮样式 */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
}
</style>
"""


class PageLayout:
    """页面布局组件"""
    
    @staticmethod
    def render_sidebar():
        """渲染侧边栏导航"""
        with st.sidebar:
            st.markdown("### 🎓 AI 教学助手")
            st.divider()
            
            menu = st.radio(
                "导航菜单",
                ["智能答疑", "课件生成", "知识库管理", "学情分析"],
                index=0,
                key="main_menu"
            )
            
            st.divider()
            
            # 系统状态
            st.markdown("### 📊 系统状态")
            if st.session_state.get('db_connected'):
                st.success("✅ 数据库已连接")
            else:
                st.error("❌ 数据库未连接")
            
            if st.session_state.get('rag_kb_connected'):
                st.success("✅ RAG 知识库就绪")
            else:
                st.warning("⚠️ RAG 知识库未连接")
        
        return menu
    
    @staticmethod
    def render_header(title, subtitle=""):
        """渲染页面头部"""
        st.title(title)
        if subtitle:
            st.caption(subtitle)
        st.divider()


class UIComponents:
    """通用 UI 组件"""
    
    @staticmethod
    def show_status_card(title, status, icon="ℹ️"):
        """显示状态卡片"""
        st.markdown(f"""
        <div class="card">
            <h3>{icon} {title}</h3>
            <p>{status}</p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def show_info_box(message, icon="💡"):
        """显示信息提示框"""
        st.info(f"{icon} {message}")
    
    @staticmethod
    def show_success_box(message, icon="✅"):
        """显示成功提示框"""
        st.success(f"{icon} {message}")
    
    @staticmethod
    def show_error_box(message, icon="❌"):
        """显示错误提示框"""
        st.error(f"{icon} {message}")
    
    @staticmethod
    def show_warning_box(message, icon="⚠️"):
        """显示警告提示框"""
        st.warning(f"{icon} {message}")
    
    @staticmethod
    def create_action_buttons(actions):
        """创建操作按钮组"""
        cols = st.columns(len(actions))
        for col, action in zip(cols, actions):
            with col:
                if st.button(action['label'], type=action.get('type', 'secondary'), use_container_width=True):
                    if 'callback' in action:
                        action['callback']()
