'use client';

import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * 防抖 Hook — 延迟更新值，减少频繁触发
 * @param value 要防抖的值
 * @param delay 延迟毫秒数（默认300ms）
 */
export function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

/**
 * 防抖回调 Hook — 延迟执行函数
 * @param callback 要防抖的回调函数
 * @param delay 延迟毫秒数（默认300ms）
 */
export function useDebouncedCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number = 300
): T {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const callbackRef = useRef(callback);
  callbackRef.current = callback;

  const debouncedCallback = useCallback(
    (...args: Parameters<T>) => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      timerRef.current = setTimeout(() => {
        callbackRef.current(...args);
      }, delay);
    },
    [delay]
  ) as T;

  return debouncedCallback;
}

/**
 * 节流 Hook — 限制函数执行频率
 * @param callback 要节流的回调函数
 * @param delay 节流间隔毫秒数（默认100ms）
 */
export function useThrottledCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number = 100
): T {
  const lastCallRef = useRef(0);
  const callbackRef = useRef(callback);
  callbackRef.current = callback;

  const throttledCallback = useCallback(
    (...args: Parameters<T>) => {
      const now = Date.now();
      if (now - lastCallRef.current >= delay) {
        lastCallRef.current = now;
        callbackRef.current(...args);
      }
    },
    [delay]
  ) as T;

  return throttledCallback;
}
