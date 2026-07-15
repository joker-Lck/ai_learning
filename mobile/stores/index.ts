/**
 * Zustand 状态管理 — 移动端
 */
import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
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
  isLoading: boolean;
  login: (user: User, token: string) => Promise<void>;
  logout: () => Promise<void>;
  setGuest: () => void;
  restoreAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isLoggedIn: false,
  isGuest: false,
  isLoading: true,

  login: async (user, token) => {
    await api.setToken(token);
    await SecureStore.setItemAsync('user_info', JSON.stringify(user));
    set({ user, token, isLoggedIn: true, isGuest: false, isLoading: false });
  },

  logout: async () => {
    await api.setToken(null);
    await SecureStore.deleteItemAsync('user_info');
    await SecureStore.deleteItemAsync('is_guest');
    set({ user: null, token: null, isLoggedIn: false, isGuest: false, isLoading: false });
  },

  setGuest: () => {
    set({
      user: { id: 0, username: '游客', role: 'guest' },
      token: null,
      isLoggedIn: true,
      isGuest: true,
      isLoading: false,
    });
  },

  restoreAuth: async () => {
    try {
      const isGuest = await SecureStore.getItemAsync('is_guest');
      if (isGuest === 'true') {
        set({
          user: { id: 0, username: '游客', role: 'guest' },
          token: null,
          isLoggedIn: true,
          isGuest: true,
          isLoading: false,
        });
        return;
      }

      const token = await api.getToken();
      if (token) {
        const userInfoStr = await SecureStore.getItemAsync('user_info');
        const user = userInfoStr ? JSON.parse(userInfoStr) : { id: 0, username: '用户', role: 'user' };
        set({ user, token, isLoggedIn: true, isGuest: false, isLoading: false });
      } else {
        set({ isLoading: false });
      }
    } catch {
      set({ isLoading: false });
    }
  },
}));

// ==================== 聊天状态 ====================

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  source?: string;
  ragDocs?: { title: string; subject: string }[];
  isStreaming?: boolean;
}

interface ChatState {
  messages: ChatMessage[];
  isGenerating: boolean;
  currentScenario: string;
  addMessage: (msg: ChatMessage) => void;
  updateLastMessage: (content: string) => void;
  appendToLastMessage: (chunk: string) => void;
  setGenerating: (v: boolean) => void;
  setScenario: (s: string) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isGenerating: false,
  currentScenario: '智能辅导',

  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),

  updateLastMessage: (content) =>
    set((state) => {
      const messages = [...state.messages];
      const last = messages[messages.length - 1];
      if (last) {
        messages[messages.length - 1] = { ...last, content };
      }
      return { messages };
    }),

  appendToLastMessage: (chunk) =>
    set((state) => {
      const messages = [...state.messages];
      const last = messages[messages.length - 1];
      if (last) {
        messages[messages.length - 1] = { ...last, content: last.content + chunk };
      }
      return { messages };
    }),

  setGenerating: (v) => set({ isGenerating: v }),
  setScenario: (s) => set({ currentScenario: s }),
  clearMessages: () => set({ messages: [] }),
}));

// ==================== UI 状态 ====================

interface UIState {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const useUIStore = create<UIState>((set) => ({
  activeTab: 'index',
  setActiveTab: (tab) => set({ activeTab: tab }),
}));
