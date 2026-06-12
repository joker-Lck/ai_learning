'use client';

import { useAuthStore } from '@/stores';
import { GraduationCap, LogIn, LogOut, User } from 'lucide-react';
import { useEffect, useState } from 'react';

export default function FloatingMenu() {
  const { user, logout } = useAuthStore();
  const [loggedIn, setLoggedIn] = useState(false);
  const [username, setUsername] = useState('');

  useEffect(() => {
    const check = () => {
      const hasToken = !!localStorage.getItem('auth_token');
      const isGuest = localStorage.getItem('is_guest') === 'true';
      setLoggedIn(hasToken && !isGuest);
      const storedUser = localStorage.getItem('user_info');
      if (storedUser) {
        try {
          const parsed = JSON.parse(storedUser);
          setUsername(parsed.username || '用户');
        } catch {
          setUsername(user?.username || '用户');
        }
      } else {
        setUsername(user?.username || '用户');
      }
    };
    check();
    const interval = setInterval(check, 300);
    return () => clearInterval(interval);
  }, [user]);

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('is_guest');
    localStorage.removeItem('user_info');
    logout();
    window.location.href = '/';
  };

  const handleLogin = () => {
    window.location.href = '/';
  };

  return (
    <div className="fixed top-6 right-6 z-50 flex items-center gap-3">
      {/* Logo */}
      <div className="flex items-center gap-3 mr-4">
        <div className="w-10 h-10 rounded-lg bg-purple-500/15 flex items-center justify-center">
          <GraduationCap className="w-5 h-5 text-purple-400" />
        </div>
        <span className="text-lg font-semibold text-white/70 hidden sm:block">AI 学习助手</span>
      </div>

      {/* 用户状态 */}
      {loggedIn ? (
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-white/[0.04] border border-white/[0.06]">
            <User className="w-4 h-4 text-white/40" />
            <span className="text-sm text-white/50">{username}</span>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-medium hover:bg-red-500/20 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>退出登录</span>
          </button>
        </div>
      ) : (
        <button
          onClick={handleLogin}
          className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-purple-500 text-white text-sm font-medium hover:bg-purple-400 transition-colors"
        >
          <LogIn className="w-4 h-4" />
          <span>登录</span>
        </button>
      )}
    </div>
  );
}
