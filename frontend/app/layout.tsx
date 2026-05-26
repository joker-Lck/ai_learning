import type { Metadata } from 'next';
import '@/styles/globals.css';

export const metadata: Metadata = {
  title: '多模态 AI 教学智能体',
  description: '基于 Kimi 大模型的智能教学辅助系统',
  icons: { icon: '/favicon.ico' },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-surface-secondary antialiased">
        {children}
      </body>
    </html>
  );
}
