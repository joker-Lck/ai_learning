'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import { useAuthStore, useUIStore } from '@/stores';
import {
  LogOut, ChevronLeft, ChevronRight, GraduationCap,
  LayoutDashboard, Brain, Route,
  Target, Lightbulb, TrendingUp
} from 'lucide-react';

// 功能模块导航（不跳转页面，在Dashboard内切换）
const menuItems = [
  { path: '/dashboard', label: '工作台', icon: LayoutDashboard, module: null },
  { path: '/dashboard?module=profile', label: '学生画像', icon: Target, module: 'profile' },
  { path: '/dashboard?module=resources', label: '资源生成', icon: Brain, module: 'resources' },
  { path: '/dashboard?module=path', label: '学习路径', icon: Route, module: 'path' },
  { path: '/dashboard?module=tutor', label: '智能辅导', icon: Lightbulb, module: 'tutor' },
  { path: '/dashboard?module=assessment', label: '效果评估', icon: TrendingUp, module: 'assessment' },
];

export default function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { user, isGuest, logout } = useAuthStore();
  const { sidebarOpen, toggleSidebar } = useUIStore();
  
  // 获取当前模块参数
  const currentModule = searchParams.get('module');

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  // 处理导航点击 - 使用URL参数而非页面跳转
  const handleNavClick = (item: typeof menuItems[0]) => {
    if (item.module === null) {
      // 工作台：清除module参数
      router.push('/dashboard');
    } else {
      // 功能模块：设置module参数
      router.push(`/dashboard?module=${item.module}`);
    }
  };

  const roleLabel: Record<string, string> = {
    user: '用户',
    admin: '管理员',
    guest: '游客',
  };

  const roleIcon: Record<string, string> = {
    teacher: '👨‍🏫',
    student: '🎓',
    admin: '👑',
    guest: '👤',
  };

  return (
    <motion.aside
      className="fixed left-0 top-0 h-full bg-gradient-to-b from-primary-500 to-primary-700 text-white z-50 flex flex-col"
      animate={{ width: sidebarOpen ? 256 : 80 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
    >
      {/* Logo */}
      <div className="p-4 flex items-center gap-3 border-b border-white/10">
        <div className="w-10 h-10 rounded-xl bg-accent-cyan/20 flex items-center justify-center flex-shrink-0">
          <GraduationCap className="w-6 h-6 text-accent-cyan" />
        </div>
        <AnimatePresence>
          {sidebarOpen && (
            <motion.div
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: 'auto' }}
              exit={{ opacity: 0, width: 0 }}
              className="overflow-hidden whitespace-nowrap"
            >
              <h1 className="text-lg font-bold">AI 教学助手</h1>
              <p className="text-xs text-white/50">v7.2</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 导航菜单 */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {menuItems.map((item) => {
          const Icon = item.icon;
          // 判断是否激活：工作台看pathname和无module参数，其他模块看URL参数
          const isActive = item.module === null 
            ? pathname === '/dashboard' && !currentModule
            : currentModule === item.module;

          return (
            <motion.button
              key={item.path}
              onClick={() => handleNavClick(item)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group relative ${
                isActive
                  ? 'bg-accent-cyan/20 text-accent-cyan'
                  : 'text-white/70 hover:bg-white/10 hover:text-white'
              }`}
              whileHover={{ x: 4 }}
              whileTap={{ scale: 0.98 }}
            >
              {isActive && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-accent-cyan rounded-r-full"
                />
              )}
              <Icon className="w-5 h-5 flex-shrink-0" />
              <AnimatePresence>
                {sidebarOpen && (
                  <motion.span
                    initial={{ opacity: 0, width: 0 }}
                    animate={{ opacity: 1, width: 'auto' }}
                    exit={{ opacity: 0, width: 0 }}
                    className="text-sm font-medium overflow-hidden whitespace-nowrap"
                  >
                    {item.label}
                  </motion.span>
                )}
              </AnimatePresence>
            </motion.button>
          );
        })}
      </nav>

      {/* 用户信息 */}
      <div className="p-3 border-t border-white/10">
        <div className="flex items-center gap-3 px-3 py-2 mb-2">
          <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0">
            <span className="text-sm">{roleIcon[user?.role || 'guest']}</span>
          </div>
          <AnimatePresence>
            {sidebarOpen && (
              <motion.div
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 'auto' }}
                exit={{ opacity: 0, width: 0 }}
                className="overflow-hidden whitespace-nowrap flex-1 min-w-0"
              >
                <p className="text-sm font-medium truncate">{user?.username || '用户'}</p>
                <p className="text-xs text-white/50">{roleLabel[user?.role || 'guest']}</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-white/60 hover:text-white hover:bg-white/10 transition-all"
        >
          <LogOut className="w-4 h-4 flex-shrink-0" />
          <AnimatePresence>
            {sidebarOpen && (
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-sm"
              >
                退出登录
              </motion.span>
            )}
          </AnimatePresence>
        </button>
      </div>

      {/* 折叠按钮 */}
      <button
        onClick={toggleSidebar}
        className="absolute top-1/2 -right-3 w-6 h-6 bg-white rounded-full shadow-md flex items-center justify-center text-primary-500 hover:bg-gray-50 transition-colors z-50"
      >
        {sidebarOpen ? <ChevronLeft className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
      </button>
    </motion.aside>
  );
}
