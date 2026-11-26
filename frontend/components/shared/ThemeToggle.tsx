'use client';

import { useCallback, useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';

type Theme = 'light' | 'dark';

const STORAGE_KEY = 'qizhi-theme';

function readTheme(): Theme {
  if (typeof document === 'undefined') return 'dark';
  const attr = document.documentElement.getAttribute('data-theme');
  return attr === 'light' ? 'light' : 'dark';
}

function applyTheme(theme: Theme) {
  document.documentElement.setAttribute('data-theme', theme);
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    /* 隐私模式下忽略 */
  }
}

/**
 * 昼夜切换开关 — 硬件拨杆风格
 * variant: 'bar'（顶栏内嵌） / 'float'（独立悬浮）
 */
export default function ThemeToggle({
  variant = 'bar',
  className = '',
}: {
  variant?: 'bar' | 'float';
  className?: string;
}) {
  const [theme, setTheme] = useState<Theme>('dark');

  useEffect(() => {
    setTheme(readTheme());
  }, []);

  const toggle = useCallback(() => {
    const next: Theme = theme === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    setTheme(next);
  }, [theme]);

  const isDark = theme === 'dark';

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={isDark ? '切换到白天模式' : '切换到夜间模式'}
      title={isDark ? '切换到白天模式' : '切换到夜间模式'}
      className={[
        'group relative inline-flex items-center gap-2 select-none',
        'border border-[var(--line)] bg-[var(--glass-bg)] hover:border-[var(--accent)]',
        'transition-colors duration-200 rounded-sm',
        variant === 'float'
          ? 'px-3 py-2.5 shadow-[var(--shadow-card)]'
          : 'px-2.5 py-1.5',
        className,
      ].join(' ')}
    >
      {/* 拨杆轨道 */}
      <span
        className="relative inline-flex items-center w-[38px] h-[18px] rounded-full border border-[var(--line-strong)] overflow-hidden"
        style={{ background: 'var(--panel-3)' }}
      >
        <span
          className="absolute top-[2px] h-[12px] w-[12px] rounded-full transition-all duration-300"
          style={{
            left: isDark ? '3px' : '21px',
            background: 'var(--accent)',
            boxShadow: 'var(--glow)',
          }}
        />
        <span className="absolute inset-0 flex items-center justify-between px-[4px] pointer-events-none">
          <Sun className="w-[9px] h-[9px]" style={{ color: isDark ? 'var(--ink-4)' : 'var(--accent)' }} />
          <Moon className="w-[9px] h-[9px]" style={{ color: isDark ? 'var(--accent)' : 'var(--ink-4)' }} />
        </span>
      </span>

      <span
        className="tech-mono text-[10px] tracking-[0.18em] uppercase hidden sm:inline"
        style={{ color: 'var(--ink-3)' }}
      >
        {isDark ? 'NIGHT' : 'DAY'}
      </span>
    </button>
  );
}

/** 供服务端组件 / 非交互场景使用的主题脚本工具 */
export function setTheme(theme: Theme) {
  applyTheme(theme);
}
