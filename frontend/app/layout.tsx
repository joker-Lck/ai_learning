import type { Metadata, Viewport } from 'next';
import '@/styles/globals.css';

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  themeColor: '#0a0a0a',
};

export const metadata: Metadata = {
  title: {
    default: '多模态 AI 教学智能体',
    template: '%s | AI 学习助手',
  },
  description: '基于讯飞星火大模型的智能教学辅助系统 — 6大智能体协同，7种资源类型，个性化学习路径',
  icons: { icon: '/favicon.ico' },
  keywords: ['AI教学', '个性化学习', '智能辅导', '学习资源生成', '多智能体'],
  authors: [{ name: 'AI Learning Team' }],
  openGraph: {
    type: 'website',
    locale: 'zh_CN',
    title: '多模态 AI 教学智能体',
    description: '基于多智能体协同架构的个性化学习资源生成系统',
    siteName: 'AI 学习助手',
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="dns-prefetch" href="https://fonts.googleapis.com" />
        <link
          href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
        <meta httpEquiv="x-dns-prefetch-control" content="on" />
        <meta httpEquiv="x-dns-prefetch-control" content="on" />
      </head>
      <body className="min-h-screen antialiased" style={{ background: '#0a0a0a' }}>
        {children}
      </body>
    </html>
  );
}
