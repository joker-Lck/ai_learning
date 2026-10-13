/**
 * Zustand 全局状态管理
 */
import { create } from 'zustand';
import api from '@/lib/api';

// ==================== 认证状态 ====================

interface User {
  id: number;
  username: string;
  role: string;
  email?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isLoggedIn: boolean;
  isGuest: boolean;
  isTeacher: boolean;
  isStudent: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
  setGuest: () => void;
  restoreAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isLoggedIn: false,
  isGuest: false,
  isTeacher: false,
  isStudent: false,

  login: (user, token) => {
    localStorage.setItem('auth_token', token);
    localStorage.removeItem('is_guest');
    localStorage.setItem('user_info', JSON.stringify(user));
    api.setToken(token);
    set({
      user, token, isLoggedIn: true, isGuest: false,
      isTeacher: user.role === 'teacher' || user.role === 'admin',
      isStudent: user.role === 'student' || user.role === 'user',
    });
  },

  logout: () => {
    const oldUser = localStorage.getItem('user_info');
    let username = '';
    try { username = oldUser ? JSON.parse(oldUser).username : ''; } catch {}
    localStorage.removeItem('auth_token');
    localStorage.removeItem('is_guest');
    localStorage.removeItem('user_info');
    localStorage.removeItem('session_start');
    if (username) {
      localStorage.removeItem(`activity_logs_${username}`);
      localStorage.removeItem(`generated_resources_${username}`);
      localStorage.removeItem(`profile_${username}`);
      localStorage.removeItem(`radar_ai_scores_${username}`);
      localStorage.removeItem(`onboarding_done_${username}`);
      // 清理所有学期的课程/成绩缓存
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i);
        if (k && (k.startsWith(`courses_${username}_`) || k.startsWith(`grades_${username}_`))) {
          localStorage.removeItem(k);
        }
      }
    }
    api.setToken(null);
    set({ user: null, token: null, isLoggedIn: false, isGuest: false });
  },

  setGuest: () => {
    localStorage.setItem('is_guest', 'true');
    localStorage.setItem('user_info', JSON.stringify({ id: 0, username: '游客', role: 'guest' }));
    set({
      user: { id: 0, username: '游客', role: 'guest' },
      token: null,
      isLoggedIn: true,
      isGuest: true,
      isTeacher: false,
      isStudent: false,
    });
  },

  restoreAuth: () => {
    const isGuest = localStorage.getItem('is_guest') === 'true';
    if (isGuest) {
      set({
        user: { id: 0, username: '游客', role: 'guest' },
        token: null,
        isLoggedIn: true,
        isGuest: true,
        isTeacher: false,
        isStudent: false,
      });
      return;
    }
    const token = localStorage.getItem('auth_token');
    if (token) {
      api.setToken(token);
      let user = { id: 0, username: '用户', role: 'student' };
      try {
        const payload = JSON.parse(atob(token.split('.')[1] ?? ''));
        user = { id: payload.user_id || 0, username: payload.username || '用户', role: payload.role || 'student' };
      } catch {}
      try {
        const stored = localStorage.getItem('user_info');
        if (stored) user = JSON.parse(stored);
      } catch {}
      set({
        token,
        isLoggedIn: true,
        isGuest: false,
        user,
        isTeacher: user.role === 'teacher' || user.role === 'admin',
        isStudent: user.role === 'student' || user.role === 'user',
      });
    }
  },
}));

// ==================== UI 状态 ====================

interface UIState {
  sidebarOpen: boolean;
  currentPage: string;
  theme: 'light' | 'dark';
  toggleSidebar: () => void;
  setCurrentPage: (page: string) => void;
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  currentPage: 'dashboard',
  theme: 'light',

  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setCurrentPage: (page) => set({ currentPage: page }),
  setTheme: (theme) => set({ theme }),
}));
