'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import { useAuthStore, useUIStore } from '@/stores';
import {
  LogOut, ChevronLeft, ChevronRight, GraduationCap,
  LayoutDashboard, Brain, Route,
  Target, Lightbulb, TrendingUp, Sparkles, Eye
} from 'lucide-react';

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

  const currentModule = searchParams.get('module');

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  const handleNavClick = (item: typeof menuItems[0]) => {
    if (item.module === null) {
      router.push('/dashboard');
    } else {
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
      className="fixed left-0 top-0 h-full z-50 flex flex-col"
      style={{
        background: 'rgba(10, 25, 47, 0.85)',
        backdropFilter: 'blur(24px)',
        WebkitBackdropFilter: 'blur(24px)',
        borderRight: '1px solid rgba(100, 255, 218, 0.06)',
      }}
      animate={{ width: sidebarOpen ? 256 : 80 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
    >
      {/* Logo */}
      <div className="p-4 flex items-center gap-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center flex-shrink-0 shadow-lg" style={{ boxShadow: '0 0 20px rgba(6,182,212,0.2)' }}>
          <GraduationCap className="w-6 h-6 text-white" />
        </div>
        <AnimatePresence>
          {sidebarOpen && (
            <motion.div
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: 'auto' }}
              exit={{ opacity: 0, width: 0 }}
              className="overflow-hidden whitespace-nowrap"
            >
              <h1 className="text-lg font-bold text-white">AI 学习助手</h1>
              <p className="text-[10px] text-white/30 tracking-widest">MULTI-AGENT</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 导航菜单 */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = item.module === null
            ? pathname === '/dashboard' && !currentModule
            : currentModule === item.module;

          return (
            <motion.button
              key={item.path}
              onClick={() => handleNavClick(item)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group relative ${
                isActive
                  ? 'text-cyan-400'
                  : 'text-white/40 hover:text-white/70'
              }`}
              style={isActive ? { background: 'rgba(100, 255, 218, 0.08)' } : undefined}
              whileHover={{ x: 4 }}
              whileTap={{ scale: 0.98 }}
            >
              {isActive && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-cyan-400 rounded-r-full"
                  transition={{ type: 'spring', stiffness: 400, damping: 30 }}
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

      {/* 游客模式提示 */}
      {isGuest && (
        <div className="mx-3 mb-2 px-3 py-2.5 rounded-xl border border-amber-400/20 bg-amber-400/5">
          <div className="flex items-center gap-2 mb-1">
            <Eye className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
            {sidebarOpen && (
              <span className="text-xs font-medium text-amber-400">游客模式</span>
            )}
          </div>
          {sidebarOpen && (
            <p className="text-[11px] text-amber-300/50 leading-relaxed">
              仅可浏览界面，无法使用任何功能。请登录后体验完整功能。
            </p>
          )}
        </div>
      )}

      {/* 用户信息 */}
      <div className="p-3" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="flex items-center gap-3 px-3 py-2 mb-2">
          <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center flex-shrink-0 border border-white/10">
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
                <p className="text-sm font-medium text-white/80 truncate">{user?.username || '用户'}</p>
                <p className="text-xs text-white/30">{roleLabel[user?.role || 'guest']}</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-white/30 hover:text-white/60 hover:bg-white/5 transition-all"
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
        className="absolute top-1/2 -right-3 w-6 h-6 rounded-full shadow-md flex items-center justify-center text-cyan-400 transition-colors z-50"
        style={{ background: 'rgba(10, 25, 47, 0.9)', border: '1px solid rgba(100, 255, 218, 0.2)' }}
      >
        {sidebarOpen ? <ChevronLeft className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
      </button>
    </motion.aside>
  );
}
