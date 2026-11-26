// Polyfill for older browsers
import '../polyfill';

import type { Metadata, Viewport } from 'next';
import '@/styles/globals.css';

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  themeColor: '#000000',
};

export const metadata: Metadata = {
  title: {
    default: '启智 · AI 学习助手',
    template: '%s | 启智',
  },
  description: '基于多智能体协作的 AI 自适应学习引擎 — 6大智能体协同，个性化学习路径，班级学情管理',
  icons: { icon: '/favicon.ico' },
  keywords: ['AI教学', '个性化学习', '智能辅导', '学习资源生成', '多智能体', '班级管理', '学情分析'],
  authors: [{ name: 'AI Learning Team' }],
  openGraph: {
    type: 'website',
    locale: 'zh_CN',
    title: '多模态 AI 教学智能体',
    description: '基于多智能体协同架构的个性化学习辅助系统',
    siteName: 'AI 学习助手',
  },
  robots: {
    index: true,
    follow: true,
  },
};

/* 主题初始化：首屏渲染前写入 data-theme，避免闪烁 */
const themeInitScript = `(function(){try{var t=localStorage.getItem('qizhi-theme');if(t!=='light'&&t!=='dark'){t=window.matchMedia&&window.matchMedia('(prefers-color-scheme: light)').matches?'light':'dark';}document.documentElement.setAttribute('data-theme',t);}catch(e){document.documentElement.setAttribute('data-theme','dark');}})();`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="dns-prefetch" href="https://fonts.googleapis.com" />
        <link
          href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
        <meta httpEquiv="x-dns-prefetch-control" content="on" />
      </head>
      <body className="min-h-screen antialiased" style={{ background: 'var(--bg)', color: 'var(--ink)' }}>
        {children}
      </body>
    </html>
  );
}
