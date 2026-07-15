import { useState, useCallback, useEffect } from 'react';
import * as SecureStore from 'expo-secure-store';

/**
 * SSE 流式输出 Hook
 */
export function useSSE() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const stream = useCallback(async (
    url: string,
    body: any,
    onChunk: (chunk: string) => void,
    onComplete?: () => void,
    onError?: (err: string) => void,
  ) => {
    setIsStreaming(true);
    setError(null);

    try {
      const token = await SecureStore.getItemAsync('auth_token');
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error(`请求失败 (${response.status})`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('无法读取响应');

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
            if (data.type === 'text_delta' && data.content) {
              onChunk(data.content);
            } else if (data.type === 'complete') {
              onComplete?.();
            } else if (data.type === 'error') {
              const errMsg = data.message || '生成失败';
              setError(errMsg);
              onError?.(errMsg);
            }
          } catch {
            // skip malformed lines
          }
        }
      }

      onComplete?.();
    } catch (err: any) {
      const errMsg = err.message || '网络错误';
      setError(errMsg);
      onError?.(errMsg);
    } finally {
      setIsStreaming(false);
    }
  }, []);

  return { stream, isStreaming, error };
}
