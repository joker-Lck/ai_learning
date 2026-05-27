/**
 * API 客户端 - 封装与后端的所有通信
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

interface RequestOptions {
  method?: string;
  body?: any;
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  }

  getToken(): string | null {
    if (!this.token) {
      this.token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    }
    return this.token;
  }

  private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { method = 'GET', body, headers = {}, signal } = options;

    const token = this.getToken();
    const defaultHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    };

    const response = await fetch(`${API_BASE}${endpoint}`, {
      method,
      headers: defaultHeaders,
      body: body ? JSON.stringify(body) : undefined,
      signal,
    });

    if (response.status === 401) {
      this.setToken(null);
      if (typeof window !== 'undefined') {
        window.location.href = '/';
      }
      throw new Error('认证已过期，请重新登录');
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || errorData.message || `请求失败 (${response.status})`
      );
    }

    const data = await response.json();
    return data as T;
  }

  // ==================== 认证 API ====================

  async login(username: string, password: string) {
    return this.request('/auth/login', {
      method: 'POST',
      body: { username, password },
    });
  }

  async register(username: string, password: string, email?: string) {
    return this.request('/auth/register', {
      method: 'POST',
      body: { username, password, email },
    });
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

  async generateResources(data: any) {
    return this.request('/agent/generate-resources', {
      method: 'POST',
      body: data,
    });
  }

  /**
   * 流式生成多种资源 — SSE 实时进度
   * 返回 AbortController，调用方可通过 controller.abort() 取消
   */
  generateResourcesStream(
    params: { subject: string; topic: string; resource_types: string[]; difficulty?: string },
    callbacks: {
      onProgress: (data: { resource_type: string; current: number; total: number; progress: number; message: string }) => void;
      onResource: (data: { resource_type: string; title: string; content_data: any; duration_minutes?: number; elapsed_seconds?: number; message: string }) => void;
      onError: (data: { resource_type: string; error: string }) => void;
      onComplete: (data: { message: string }) => void;
      onFetchError: (err: Error) => void;
    }
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
        const response = await fetch(`${API_BASE}/api/stream/generate-resources-real?${qs}`, {
          method: 'GET',
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          signal: controller.signal,
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || `请求失败 (${response.status})`);
        }

        const reader = response.body!.getReader();
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
            } catch { /* skip malformed lines */ }
          }
        }
      } catch (err: any) {
        if (err.name !== 'AbortError') callbacks.onFetchError(err);
      }
    })();

    return controller;
  }

  async planPath(data: any) {
    return this.request('/agent/plan-path', {
      method: 'POST',
      body: data,
    });
  }

  async tutor(data: any) {
    return this.request('/agent/tutor', {
      method: 'POST',
      body: data,
    });
  }

  async assess(data: any) {
    return this.request('/agent/assess', {
      method: 'POST',
      body: data,
    });
  }

  async exportResource(resource: any) {
    return this.request('/agent/export-resource', {
      method: 'POST',
      body: { resource },
    });
  }

  /**
   * 上传学习资料并进行AI分析
   * @param files 文件列表
   * @param context { subject, topic, difficulty }
   */
  async uploadAndAnalyze(
    files: File[],
    context: { subject?: string; topic?: string; difficulty?: string } = {},
  ) {
    const token = this.getToken();
    const formData = new FormData();
    files.forEach((f) => formData.append('files', f));
    if (context.subject) formData.append('subject', context.subject);
    if (context.topic) formData.append('topic', context.topic);
    if (context.difficulty) formData.append('difficulty', context.difficulty);

    const response = await fetch(`${API_BASE}/agent/analyze-documents`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });

    if (response.status === 401) {
      this.setToken(null);
      if (typeof window !== 'undefined') window.location.href = '/';
      throw new Error('认证已过期，请重新登录');
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || `请求失败 (${response.status})`);
    }

    return response.json();
  }

  // ==================== 流式 API ====================

  /**
   * 流式智能答疑 - 调用 tutor 接口并模拟逐字输出
   */
  async askQuestionStream(
    question: string,
    scenario: string,
    onChunk: (chunk: string) => void,
    onDone: (data: any) => void,
    onError: (error: string) => void,
  ) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 120000); // 120秒超时

      const result = await this.request<any>('/agent/tutor', {
        method: 'POST',
        body: {
          question,
          subject: scenario,
          preferred_format: 'text',
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      // 后端 BaseResponse 格式: { success, message, data: { answer: { text_answer, formats, ... } } }
      if (result.success && result.data) {
        const answerObj = result.data.answer || result.data;
        const textAnswer = answerObj.text_answer || {};
        const parts: string[] = [];

        if (textAnswer.summary) parts.push(textAnswer.summary);
        if (textAnswer.detailed_explanation) parts.push(textAnswer.detailed_explanation);
        if (textAnswer.key_points?.length) {
          parts.push('\n**重点知识：**\n' + textAnswer.key_points.map((p: string) => `- ${p}`).join('\n'));
        }
        if (textAnswer.examples?.length) {
          parts.push('\n**示例：**\n' + textAnswer.examples.map((e: string) => `- ${e}`).join('\n'));
        }
        if (textAnswer.common_mistakes?.length) {
          parts.push('\n**常见错误：**\n' + textAnswer.common_mistakes.map((m: string) => `- ${m}`).join('\n'));
        }

        // 如果 text_answer 是字符串而非对象
        if (typeof textAnswer === 'string' && textAnswer) parts.push(textAnswer);
        // 兜底：直接用 answer 字符串
        if (parts.length === 0 && typeof answerObj.answer === 'string') parts.push(answerObj.answer);
        if (parts.length === 0 && typeof answerObj === 'string') parts.push(answerObj);

        const fullText = parts.filter(Boolean).join('\n\n') || result.message || '暂无回答';

        // 模拟流式逐字输出
        let idx = 0;
        const chunkSize = 3;
        const timer = setInterval(() => {
          const end = Math.min(idx + chunkSize, fullText.length);
          onChunk(fullText.slice(idx, end));
          idx = end;
          if (idx >= fullText.length) {
            clearInterval(timer);
            onDone(result.data);
          }
        }, 15);
      } else {
        onError(result.message || '请求失败，请检查后端日志');
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        onError('请求超时，请稍后重试');
      } else {
        onError(err.message || '网络错误，请确认后端服务已启动');
      }
    }
  }

  /**
   * 流式课件生成 - 调用资源生成接口并转换为幻灯片格式
   */
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

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 180000); // 180秒超时

      const result = await this.request<any>('/agent/tutor', {
        method: 'POST',
        body: {
          question: prompt,
          subject: '课件生成',
          preferred_format: 'text',
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      onChunk('正在构建幻灯片...\n');

      if (result.success && result.data) {
        let slides: any[] = [];
        const answer = result.data.text_answer || {};
        const rawText = answer.summary || answer.detailed_explanation || '';

        // 尝试从返回文本中解析 JSON
        const jsonMatch = rawText.match(/\{[\s\S]*"slides"[\s\S]*\}/);
        if (jsonMatch) {
          try {
            const parsed = JSON.parse(jsonMatch[0]);
            slides = parsed.slides || [];
          } catch {
            // JSON 解析失败，使用备用方案
          }
        }

        // 备用方案：将回答文本转换为幻灯片
        if (slides.length === 0) {
          const sections = rawText.split(/\n(?=##?\s|第[一二三四五六七八九十\d]+[章节部分]|[\d]+[.、])/);
          slides = sections
            .filter((s: string) => s.trim())
            .slice(0, fastMode ? 10 : 15)
            .map((section: string, idx: number) => {
              const lines = section.trim().split('\n');
              const title = lines[0].replace(/^#+\s*|^\d+[.、]\s*/, '').trim() || `第 ${idx + 1} 页`;
              const content = lines.slice(1)
                .map((l: string) => l.replace(/^[-*•]\s*/, '').trim())
                .filter((l: string) => l.length > 0);
              return { title, content: content.length > 0 ? content : ['内容生成中...'] };
            });
        }

        // 如果仍然没有幻灯片，创建默认结构
        if (slides.length === 0) {
          slides = [
            { title: topic, subtitle: 'AI 教学课件', content: ['基于多智能体系统生成'] },
            { title: '知识点概述', content: [rawText.slice(0, 200) || '内容生成中...'] },
            { title: '总结', content: ['感谢观看'] },
          ];
        }

        const coursewareData = {
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
        };

        onDone(coursewareData);
      } else {
        onError(result.message || '课件生成失败，请检查后端日志');
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        onError('生成超时，请稍后重试');
      } else {
        onError(err.message || '网络错误，请确认后端服务已启动');
      }
    }
  }

  /**
   * 获取课件下载 URL
   */
  getCoursewareDownloadUrl(coursewareId: number, format: string): string {
    return `${API_BASE}/courseware/${coursewareId}/download?format=${format}`;
  }
}

// 单例导出
export const api = new ApiClient();
export default api;
