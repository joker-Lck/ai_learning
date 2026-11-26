'use client';

import { useAuthStore } from '@/stores';
import { LogIn, LogOut, User } from 'lucide-react';
import { useEffect, useState } from 'react';
import ThemeToggle from '@/components/shared/ThemeToggle';

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
    <div className="fixed top-5 right-5 z-50 flex items-center gap-2.5">
      {/* 品牌标识 */}
      <div className="flex items-center gap-2.5 mr-2">
        <div
          className="w-8 h-8 grid grid-cols-3 grid-rows-3 gap-[2px] p-[2px] border border-[var(--accent)]"
          aria-hidden="true"
        >
          {Array.from({ length: 9 }).map((_, i) => (
            <span
              key={i}
              className="block"
              style={{ background: [0, 2, 4, 6, 8, 3].includes(i) ? 'var(--accent)' : 'transparent' }}
            />
          ))}
        </div>
        <span className="font-display font-bold text-sm tracking-[0.22em] text-[var(--ink)] hidden sm:block">
          QIZHI<span className="text-[var(--accent)]">.AI</span>
        </span>
      </div>

      {/* 昼夜切换 */}
      <ThemeToggle />

      {/* 用户状态 */}
      {loggedIn ? (
        <div className="flex items-center gap-2">
          <div
            className="flex items-center gap-2 px-3.5 py-2 rounded-sm border border-[var(--line)]"
            style={{ background: 'var(--glass-bg)', backdropFilter: 'blur(12px)' }}
          >
            <User className="w-3.5 h-3.5 text-[var(--accent)]" />
            <span className="text-xs font-mono tracking-[0.08em] text-[var(--ink-2)]">{username}</span>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 px-4 py-2 rounded-sm border text-xs font-mono tracking-[0.12em] uppercase transition-colors duration-200"
            style={{
              background: 'var(--glass-bg)',
              borderColor: 'color-mix(in srgb, var(--danger) 45%, transparent)',
              color: 'var(--danger)',
            }}
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>退出</span>
          </button>
        </div>
      ) : (
        <button
          onClick={handleLogin}
          className="btn-solid px-5 py-2 text-xs"
        >
          <LogIn className="w-3.5 h-3.5" />
          <span>登录</span>
        </button>
      )}
    </div>
  );
}
