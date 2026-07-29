/**
 * Zustand 全局状态管理
 */
import { create } from 'zustand';

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

  login: (user, token) => {
    localStorage.setItem('auth_token', token);
    localStorage.removeItem('is_guest');
    localStorage.setItem('user_info', JSON.stringify(user));
    set({ user, token, isLoggedIn: true, isGuest: false });
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
    }
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
      });
      return;
    }
    const token = localStorage.getItem('auth_token');
    if (token) {
      set({
        token,
        isLoggedIn: true,
        isGuest: false,
        user: { id: 0, username: '用户', role: 'user' },
      });
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

export const useChatStore = create<ChatState>((set, get) => ({
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

// ==================== 课件生成状态 ====================

interface SlideData {
  title: string;
  subtitle?: string;
  content: string[];
  layout?: string;
  background?: any;
  decorations?: any[];
  image_suggestion?: string;
}

interface CoursewareState {
  topic: string;
  subject: string;
  outline: string;
  slides: SlideData[];
  theme: any;
  fastMode: boolean;
  isGenerating: boolean;
  generationStep: number;
  generationProgress: number;
  coursewareId: number | null;
  generatedImages: any;
  clarificationMessages: { role: string; content: string }[];
  requirements: string[];

  setTopic: (t: string) => void;
  setFastMode: (v: boolean) => void;
  setGenerating: (v: boolean) => void;
  setProgress: (step: number, progress: number) => void;
  setCoursewareResult: (result: any) => void;
  addClarification: (msg: { role: string; content: string }) => void;
  addRequirement: (r: string) => void;
  reset: () => void;
}

const defaultCoursewareState = {
  topic: '',
  subject: '',
  outline: '',
  slides: [] as SlideData[],
  theme: {},
  fastMode: true,
  isGenerating: false,
  generationStep: 0,
  generationProgress: 0,
  coursewareId: null,
  generatedImages: {},
  clarificationMessages: [],
  requirements: [],
};

export const useCoursewareStore = create<CoursewareState>((set) => ({
  ...defaultCoursewareState,

  setTopic: (t) => set({ topic: t }),
  setFastMode: (v) => set({ fastMode: v }),
  setGenerating: (v) => set({ isGenerating: v }),
  setProgress: (step, progress) => set({ generationStep: step, generationProgress: progress }),

  setCoursewareResult: (result) =>
    set({
      subject: result.subject || '',
      outline: result.outline || '',
      slides: result.slides || [],
      theme: result.theme || {},
      coursewareId: result.courseware_id || null,
      generatedImages: result.generated_images || {},
      isGenerating: false,
      generationProgress: 100,
    }),

  addClarification: (msg) =>
    set((state) => ({ clarificationMessages: [...state.clarificationMessages, msg] })),

  addRequirement: (r) =>
    set((state) => ({ requirements: [...state.requirements, r] })),

  reset: () => set(defaultCoursewareState),
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
