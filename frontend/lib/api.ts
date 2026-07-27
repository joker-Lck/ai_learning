/**
 * API 客户端 — 企业级
 * 特性：自动重试、超时控制、统一错误处理、请求取消
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';
const DEFAULT_TIMEOUT = 30000; // 30s
const MAX_RETRIES = 2;
const RETRY_DELAY = 1000; // 1s base delay

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

  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('auth_token', token);
      } else {
        localStorage.removeItem('auth_token');
      }
    }
  }

  getToken(): string | null {
    if (!this.token && typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token');
    }
    return this.token;
  }

  /**
   * 处理 401 认证失败
   */
  private handleAuthError(): never {
    if (typeof window !== 'undefined' && localStorage.getItem('is_guest') === 'true') {
      throw new Error('游客模式无法使用此功能');
    }
    this.setToken(null);
    if (typeof window !== 'undefined') {
      window.location.href = '/';
    }
    throw new Error('认证已过期，请重新登录');
  }

  /**
   * 核心请求方法 — 带重试和超时
   */
  private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const {
      method = 'GET',
      body,
      headers = {},
      signal,
      timeout = DEFAULT_TIMEOUT,
      retries = MAX_RETRIES,
    } = options;

    const token = this.getToken();
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
      // 合并外部 signal 和超时 signal
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      // 如果外部有 signal，监听其 abort
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

        // 401 认证失败
        if (response.status === 401) {
          this.handleAuthError();
        }

        // 成功
        if (response.ok) {
          return (await response.json()) as T;
        }

        // 4xx 客户端错误不重试
        if (response.status >= 400 && response.status < 500) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(
            errorData.detail || errorData.message || `请求失败 (${response.status})`
          );
        }

        // 5xx 服务端错误，可重试
        lastError = new Error(`服务端错误 (${response.status})`);
      } catch (err: any) {
        clearTimeout(timeoutId);

        // 用户主动取消，不重试
        if (err.name === 'AbortError' && signal?.aborted) {
          throw new Error('请求已取消');
        }

        // 超时或网络错误
        if (err.name === 'AbortError' || err.name === 'TypeError') {
          lastError = new Error('网络连接失败，请检查网络');
        } else {
          lastError = err;
        }
      }

      // 最后一次尝试失败，直接抛出
      if (attempt === retries) {
        break;
      }

      // 指数退避等待
      await new Promise((r) => setTimeout(r, RETRY_DELAY * Math.pow(2, attempt)));
    }

    throw lastError || new Error('请求失败');
  }

  /**
   * 文件上传（FormData）— 统一 401 处理
   */
  private async upload<T>(endpoint: string, formData: FormData): Promise<T> {
    return this.request<T>(endpoint, { method: 'POST', body: formData, timeout: 60000 });
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

  // ==================== 多智能体 API ====================

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

  async evaluateProfile() {
    return this.request('/agent/evaluate-profile', { method: 'POST' });
  }

  // ── 课程表 ──
  async saveCourseSchedule(semester: string, courses: any[]) {
    return this.request('/agent/save-course-schedule', { method: 'POST', body: { semester, courses } });
  }
  async getCourseSchedule(semester: string) {
    return this.request(`/agent/get-course-schedule?semester=${encodeURIComponent(semester)}`);
  }
  async listSemesters() {
    return this.request('/agent/list-semesters');
  }

  // ── 成绩 ──
  async saveGrades(semester: string, grades: any[]) {
    return this.request('/agent/save-grades', { method: 'POST', body: { semester, grades } });
  }
  async getGrades(semester?: string) {
    const q = semester ? `?semester=${encodeURIComponent(semester)}` : '';
    return this.request(`/agent/get-grades${q}`);
  }

  // ── 错题 ──
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

  // ── 学习计划 ──
  async generateStudyPlan(data: { semester: string; plan_type: string; custom_goal?: string; exam_date?: string; exam_subjects?: string[] }) {
    return this.request('/agent/generate-study-plan', { method: 'POST', body: data, timeout: 60000 });
  }
  async getStudyPlans(semester?: string) {
    const q = semester ? `?semester=${encodeURIComponent(semester)}` : '';
    return this.request(`/agent/get-study-plans${q}`);
  }

  async generateResources(data: any) {
    return this.request('/agent/generate-resources', { method: 'POST', body: data, timeout: 120000 });
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

  async getLearningRecommendations(subject?: string) {
    const q = subject ? `?subject=${encodeURIComponent(subject)}` : '';
    return this.request(`/agent/learning-recommendations${q}`);
  }

  async getDashboardStats() {
    return this.request('/agent/dashboard/stats');
  }

  async getActivityLogs(limit = 10) {
    return this.request(`/agent/activity-logs?limit=${limit}`);
  }

  generateResourcesStream(
    params: { subject: string; topic: string; resource_types: string[]; difficulty?: string },
    callbacks: {
      onProgress: (data: any) => void;
      onResource: (data: any) => void;
      onError: (data: any) => void;
      onComplete: (data: any) => void;
      onFetchError: (err: Error) => void;
    },
  ): AbortController {
    const controller = new AbortController();
    const token = this.getToken();
    const qs = new URLSearchParams({
      subject: params.subject,
      topic: params.topic,
      resource_types: params.resource_types.join(','),
      difficulty: params.difficulty || 'intermediate',
    });

    (async () => {
      try {
        const response = await fetch(`${API_BASE}/stream/generate-resources-real?${qs}`, {
          method: 'GET',
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          signal: controller.signal,
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || `请求失败 (${response.status})`);
        }

        const body = response.body;
        if (!body) throw new Error('Response body is null');

        const reader = body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'progress') callbacks.onProgress(data);
              else if (data.type === 'resource') callbacks.onResource(data);
              else if (data.type === 'resource_error') callbacks.onError(data);
              else if (data.type === 'complete') callbacks.onComplete(data);
            } catch {
              /* skip malformed lines */
            }
          }
        }
      } catch (err: any) {
        if (err.name !== 'AbortError') callbacks.onFetchError(err);
      }
    })();

    return controller;
  }

  async planPath(data: any) {
    return this.request('/agent/plan-path', { method: 'POST', body: data, timeout: 60000 });
  }

  async tutor(data: any) {
    return this.request('/agent/tutor', { method: 'POST', body: data, timeout: 120000 });
  }

  async assess(data: any) {
    return this.request('/agent/assess', { method: 'POST', body: data, timeout: 60000 });
  }

  async exportResource(resource: any) {
    return this.request('/agent/export-resource', { method: 'POST', body: { resource } });
  }

  // ── 文件上传（统一使用 upload 方法）──

  async uploadAndAnalyze(files: File[], context: { subject?: string; topic?: string; difficulty?: string } = {}) {
    const formData = new FormData();
    files.forEach((f) => formData.append('files', f));
    if (context.subject) formData.append('subject', context.subject);
    if (context.topic) formData.append('topic', context.topic);
    if (context.difficulty) formData.append('difficulty', context.difficulty);
    return this.upload('/agent/analyze-documents', formData);
  }

  async uploadToRag(files: File[], subject?: string) {
    const formData = new FormData();
    files.forEach((f) => formData.append('files', f));
    if (subject) formData.append('subject', subject);
    return this.upload('/agent/upload-to-rag', formData);
  }

  async getRagDocuments() {
    return this.request('/agent/rag-documents');
  }

  // ==================== 流式 API ====================

  async askQuestionStream(
    question: string,
    scenario: string,
    onChunk: (chunk: string) => void,
    onDone: (data: { diagram?: any; example?: any }) => void,
    onError: (error: string) => void,
  ) {
    const token = this.getToken();
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 180000);

    try {
      const response = await fetch(`${API_BASE}/stream/tutor`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ question, subject: scenario }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `请求失败 (${response.status})`);
      }

      const body = response.body;
      if (!body) throw new Error('Response body is null');

      const reader = body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let resultData: { diagram?: any; example?: any } = {};

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.slice(6));
            switch (data.type) {
              case 'text_delta':
                onChunk(data.content);
                break;
              case 'diagram':
                resultData.diagram = data.data;
                break;
              case 'example':
                resultData.example = data.data;
                break;
              case 'complete':
                onDone(resultData);
                break;
              case 'error':
                onError(data.message || '生成失败');
                return;
            }
          } catch {
            /* skip malformed lines */
          }
        }
      }

      if (Object.keys(resultData).length > 0 || buffer === '') {
        onDone(resultData);
      }
    } catch (err: any) {
      clearTimeout(timeoutId);
      if (err.name === 'AbortError') {
        onError('请求超时，请稍后重试');
      } else {
        onError(err.message || '网络错误，请确认后端服务已启动');
      }
    }
  }

  async generateCoursewareStream(
    topic: string,
    requirements: string,
    fastMode: boolean,
    onChunk: (chunk: string) => void,
    onDone: (data: any) => void,
    onError: (error: string) => void,
  ) {
    try {
      onChunk('正在识别学科...\n');

      const prompt = `请为我生成一个关于"${topic}"的教学课件。
要求：${requirements}
请严格按照以下 JSON 格式返回（不要包含其他文字），每张幻灯片包含 title 和 content（数组）：
{
  "slides": [
    {"title": "课件标题", "subtitle": "副标题", "content": ["要点1", "要点2"]},
    {"title": "第一部分标题", "content": ["知识点1", "知识点2", "知识点3"]},
    {"title": "总结", "content": ["总结要点1", "总结要点2"]}
  ]
}
生成${fastMode ? '8-10' : '10-15'}页幻灯片内容。`;

      const result = await this.request<any>('/agent/tutor', {
        method: 'POST',
        body: { question: prompt, subject: '课件生成', preferred_format: 'text' },
        timeout: 180000,
      });

      onChunk('正在构建幻灯片...\n');

      if (result.success && result.data) {
        let slides: any[] = [];
        const answer = result.data.text_answer || {};
        const rawText = answer.summary || answer.detailed_explanation || '';

        const jsonMatch = rawText.match(/\{[\s\S]*"slides"[\s\S]*\}/);
        if (jsonMatch) {
          try {
            const parsed = JSON.parse(jsonMatch[0]);
            slides = parsed.slides || [];
          } catch {
            /* fallback */
          }
        }

        if (slides.length === 0) {
          const sections = rawText.split(/\n(?=##?\s|第[一二三四五六七八九十\d]+[章节部分]|[\d]+[.、])/);
          slides = sections
            .filter((s: string) => s.trim())
            .slice(0, fastMode ? 10 : 15)
            .map((section: string, idx: number) => {
              const lines = section.trim().split('\n');
              const title = lines[0]!.replace(/^#+\s*|^\d+[.、]\s*/, '').trim() || `第 ${idx + 1} 页`;
              const content = lines.slice(1)
                .map((l: string) => l.replace(/^[-*•]\s*/, '').trim())
                .filter((l: string) => l.length > 0);
              return { title, content: content.length > 0 ? content : ['内容生成中...'] };
            });
        }

        if (slides.length === 0) {
          slides = [
            { title: topic, subtitle: 'AI 教学课件', content: ['基于多智能体系统生成'] },
            { title: '知识点概述', content: [rawText.slice(0, 200) || '内容生成中...'] },
            { title: '总结', content: ['感谢观看'] },
          ];
        }

        onDone({
          subject: answer.subject || '通用',
          outline: slides.map((s: any) => s.title).join(' → '),
          slides,
          theme: {
            primary_color: '#0a192f',
            secondary_color: '#64ffda',
            accent_color: '#00d4ff',
            bg_color: '#f8fafc',
            text_color: '#333333',
            template_style: 'tech',
          },
          courseware_id: null,
          generated_images: {},
        });
      } else {
        onError(result.message || '课件生成失败');
      }
    } catch (err: any) {
      onError(err.message || '网络错误');
    }
  }

  getCoursewareDownloadUrl(coursewareId: number, format: string): string {
    return `${API_BASE}/courseware/${coursewareId}/download?format=${format}`;
  }

  async importCoursesFromFile(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    return this.upload('/agent/import-courses-from-file', formData);
  }

  async importGradesFromFile(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    return this.upload('/agent/import-grades-from-file', formData);
  }

  async importErrorsFromFile(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    return this.upload('/agent/import-errors-from-file', formData);
  }

  // ==================== 高级检索 API ====================

  async advancedSearch(query: string, strategy = 'auto', subject?: string, limit = 5) {
    return this.request('/agent/advanced-search', {
      method: 'POST',
      body: { query, strategy, subject, limit },
    });
  }

  // ==================== Bilibili 视频搜索 API ====================

  async searchBilibiliVideos(keyword: string, page = 1, pageSize = 12, order = 'totalrank', duration = 0) {
    const params = new URLSearchParams({
      keyword,
      page: String(page),
      page_size: String(pageSize),
      order,
      duration: String(duration),
    });
    return this.request(`/agent/bilibili/search?${params}`);
  }

  async getBilibiliRecommend(category = 'all', limit = 8) {
    const params = new URLSearchParams({
      category,
      limit: String(limit),
    });
    return this.request(`/agent/bilibili/recommend?${params}`);
  }
}

export const api = new ApiClient();
export default api;
