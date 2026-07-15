/**
 * API 客户端 — React Native 版
 * 从 Web 端 lib/api.ts 移植，适配 React Native
 */
import * as SecureStore from 'expo-secure-store';
import { API_BASE, TIMEOUT, RETRY } from '@/constants/api';

interface RequestOptions {
  method?: string;
  body?: any;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  timeout?: number;
  retries?: number;
}

class ApiClient {
  private token: string | null = null;

  async setToken(token: string | null) {
    this.token = token;
    if (token) {
      await SecureStore.setItemAsync('auth_token', token);
    } else {
      await SecureStore.deleteItemAsync('auth_token');
    }
  }

  async getToken(): Promise<string | null> {
    if (!this.token) {
      this.token = await SecureStore.getItemAsync('auth_token');
    }
    return this.token;
  }

  private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const {
      method = 'GET',
      body,
      headers = {},
      signal,
      timeout = TIMEOUT.default,
      retries = RETRY.maxRetries,
    } = options;

    const token = await this.getToken();
    const isFormData = body instanceof FormData;
    const defaultHeaders: Record<string, string> = {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    };

    const url = `${API_BASE}${endpoint}`;
    const fetchBody = body ? (isFormData ? body : JSON.stringify(body)) : undefined;

    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= retries; attempt++) {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      if (signal) {
        signal.addEventListener('abort', () => controller.abort(), { once: true });
      }

      try {
        const response = await fetch(url, {
          method,
          headers: defaultHeaders,
          body: fetchBody,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (response.status === 401) {
          await this.setToken(null);
          throw new Error('认证已过期，请重新登录');
        }

        if (response.ok) {
          return (await response.json()) as T;
        }

        if (response.status >= 400 && response.status < 500) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(
            errorData.detail || errorData.message || `请求失败 (${response.status})`
          );
        }

        lastError = new Error(`服务端错误 (${response.status})`);
      } catch (err: any) {
        clearTimeout(timeoutId);

        if (err.name === 'AbortError' && signal?.aborted) {
          throw new Error('请求已取消');
        }

        if (err.name === 'AbortError' || err.name === 'TypeError') {
          lastError = new Error('网络连接失败，请检查网络');
        } else {
          lastError = err;
        }
      }

      if (attempt === retries) break;
      await new Promise((r) => setTimeout(r, RETRY.baseDelay * Math.pow(2, attempt)));
    }

    throw lastError || new Error('请求失败');
  }

  private async upload<T>(endpoint: string, formData: FormData): Promise<T> {
    return this.request<T>(endpoint, { method: 'POST', body: formData, timeout: TIMEOUT.upload });
  }

  // ==================== 认证 API ====================

  async login(username: string, password: string) {
    return this.request('/auth/login', { method: 'POST', body: { username, password } });
  }

  async register(username: string, password: string, email?: string) {
    return this.request('/auth/register', { method: 'POST', body: { username, password, email } });
  }

  async guestLogin() {
    return this.request('/auth/guest', { method: 'POST' });
  }

  async getMe() {
    return this.request('/auth/me');
  }

  // ==================== 画像 API ====================

  async buildProfile(conversationLog: any[], basicInfo?: any) {
    return this.request('/agent/build-profile', {
      method: 'POST',
      body: { conversation_log: conversationLog, basic_info: basicInfo },
    });
  }

  async getProfile() {
    return this.request('/agent/get-profile');
  }

  async updateProfileField(field: string, value: any) {
    return this.request('/agent/update-profile-field', { method: 'POST', body: { field, value } });
  }

  // ==================== 学生数据 API ====================

  async saveCourseSchedule(semester: string, courses: any[]) {
    return this.request('/agent/save-course-schedule', { method: 'POST', body: { semester, courses } });
  }

  async getCourseSchedule(semester: string) {
    return this.request(`/agent/get-course-schedule?semester=${encodeURIComponent(semester)}`);
  }

  async listSemesters() {
    return this.request('/agent/list-semesters');
  }

  async saveGrades(semester: string, grades: any[]) {
    return this.request('/agent/save-grades', { method: 'POST', body: { semester, grades } });
  }

  async getGrades(semester?: string) {
    const q = semester ? `?semester=${encodeURIComponent(semester)}` : '';
    return this.request(`/agent/get-grades${q}`);
  }

  async saveErrorNote(note: any) {
    return this.request('/agent/save-error-note', { method: 'POST', body: note });
  }

  async getErrorNotes(subject?: string, mastery?: number) {
    const params = new URLSearchParams();
    if (subject) params.set('subject', subject);
    if (mastery !== undefined) params.set('mastery', String(mastery));
    const q = params.toString() ? `?${params}` : '';
    return this.request(`/agent/get-error-notes${q}`);
  }

  async updateErrorMastery(noteId: number, mastery: number) {
    return this.request('/agent/update-error-mastery', { method: 'POST', body: { note_id: noteId, mastery } });
  }

  async deleteErrorNote(noteId: number) {
    return this.request('/agent/delete-error-note', { method: 'POST', body: { note_id: noteId } });
  }

  async generateStudyPlan(data: any) {
    return this.request('/agent/generate-study-plan', { method: 'POST', body: data, timeout: TIMEOUT.ai });
  }

  async getStudyPlans(semester?: string) {
    const q = semester ? `?semester=${encodeURIComponent(semester)}` : '';
    return this.request(`/agent/get-study-plans${q}`);
  }

  // ==================== 资源 API ====================

  async generateResources(data: any) {
    return this.request('/agent/generate-resources', { method: 'POST', body: data, timeout: TIMEOUT.ai });
  }

  async getResources(params?: { resource_type?: string; subject?: string; limit?: number; offset?: number }) {
    const q = new URLSearchParams();
    if (params?.resource_type) q.set('resource_type', params.resource_type);
    if (params?.subject) q.set('subject', params.subject);
    if (params?.limit) q.set('limit', String(params.limit));
    if (params?.offset) q.set('offset', String(params.offset));
    const qs = q.toString();
    return this.request(`/agent/list-resources${qs ? '?' + qs : ''}`);
  }

  async exportResource(resource: any) {
    return this.request('/agent/export-resource', { method: 'POST', body: { resource } });
  }

  // ==================== 路径 API ====================

  async planPath(data: any) {
    return this.request('/agent/plan-path', { method: 'POST', body: data, timeout: TIMEOUT.ai });
  }

  // ==================== 辅导 API ====================

  async tutor(data: any) {
    return this.request('/agent/tutor', { method: 'POST', body: data, timeout: TIMEOUT.ai });
  }

  // ==================== 评估 API ====================

  async assess(data: any) {
    return this.request('/agent/assess', { method: 'POST', body: data, timeout: TIMEOUT.ai });
  }

  // ==================== 工作台 API ====================

  async getDashboardStats() {
    return this.request('/agent/dashboard/stats');
  }

  async getActivityLogs(limit = 10) {
    return this.request(`/agent/activity-logs?limit=${limit}`);
  }

  async getLearningRecommendations(subject?: string) {
    const q = subject ? `?subject=${encodeURIComponent(subject)}` : '';
    return this.request(`/agent/learning-recommendations${q}`);
  }

  // ==================== RAG API ====================

  async uploadToRag(files: any[], subject?: string) {
    const formData = new FormData();
    files.forEach((f) => formData.append('files', f));
    if (subject) formData.append('subject', subject);
    return this.upload('/agent/upload-to-rag', formData);
  }

  async getRagDocuments() {
    return this.request('/agent/rag-documents');
  }

  // ==================== 高级检索 API ====================

  async advancedSearch(query: string, strategy = 'auto', subject?: string, limit = 5) {
    return this.request('/agent/advanced-search', {
      method: 'POST',
      body: { query, strategy, subject, limit },
    });
  }

  // ==================== 文件导入 API ====================

  async importCoursesFromFile(file: any) {
    const formData = new FormData();
    formData.append('file', file);
    return this.upload('/agent/import-courses-from-file', formData);
  }

  async importGradesFromFile(file: any) {
    const formData = new FormData();
    formData.append('file', file);
    return this.upload('/agent/import-grades-from-file', formData);
  }

  async importErrorsFromFile(file: any) {
    const formData = new FormData();
    formData.append('file', file);
    return this.upload('/agent/import-errors-from-file', formData);
  }
}

export const api = new ApiClient();
export default api;
