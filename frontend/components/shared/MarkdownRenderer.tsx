/**
 * Markdown 渲染器 — react-markdown + 代码高亮 + XSS防护
 * 优化：使用React.memo减少不必要的重渲染
 * 安全：rehype-sanitize 防止 XSS 注入
 */
'use client';
import React, { useState, memo, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check, ChevronDown, ChevronUp, Image as ImageIcon } from 'lucide-react';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

/** 检测图片 URL */
function isImageUrl(url: string): boolean {
  return /\.(png|jpe?g|gif|webp|svg|bmp)(\?.*)?$/i.test(url);
}

/** 检测视频 URL */
function isVideoUrl(url: string): boolean {
  return /\.(mp4|webm|ogg|mov)(\?.*)?$/i.test(url);
}

/** 代码块组件 — 语法高亮 + 复制按钮 + 折叠 */
const CodeBlock = memo(function CodeBlock({ language, children }: { language: string; children: string }) {
  const [copied, setCopied] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const lineCount = children.split('\n').length;
  const isLong = lineCount > 20;

  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(children);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [children]);

  return (
    <div className="group relative my-3 rounded-xl overflow-hidden glass">
      {/* 语言标签 + 操作栏 */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#0d1117] border-b border-glass">
        <span className="text-xs text-white/30 font-mono">{language || 'text'}</span>
        <div className="flex items-center gap-2">
          {isLong && (
            <button
              onClick={() => setCollapsed(!collapsed)}
              className="text-xs text-white/30 hover:text-cyan-400 flex items-center gap-1 transition-colors"
            >
              {collapsed ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />}
              {collapsed ? `展开 ${lineCount} 行` : '折叠'}
            </button>
          )}
          <button
            onClick={handleCopy}
            className="text-xs text-white/30 hover:text-cyan-400 flex items-center gap-1 transition-colors"
          >
            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            {copied ? '已复制' : '复制'}
          </button>
        </div>
      </div>
      {/* 代码内容 */}
      <div style={collapsed ? { maxHeight: 120, overflow: 'hidden' } : undefined}>
        <SyntaxHighlighter
          language={language || 'text'}
          style={vscDarkPlus}
          customStyle={{
            margin: 0,
            borderRadius: 0,
            background: '#0d1117',
            fontSize: '0.85em',
            lineHeight: '1.6',
            padding: '1em',
          }}
          showLineNumbers={lineCount > 5}
          lineNumberStyle={{ color: 'rgba(255,255,255,0.15)', fontSize: '0.75em', minWidth: '2.5em' }}
        >
          {children}
        </SyntaxHighlighter>
      </div>
      {/* 折叠遮罩 */}
      {collapsed && (
        <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-[#0d1117] to-transparent pointer-events-none" />
      )}
    </div>
  );
});
function MdImage({ src, alt }: { src: string; alt?: string }) {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);

  if (error) {
    return (
      <span className="inline-flex items-center gap-2 px-3 py-2 rounded-lg glass text-white/40 text-sm">
        <ImageIcon className="w-4 h-4" /> 图片加载失败: {alt || src}
      </span>
    );
  }

  return (
    <span className="block my-3">
      {!loaded && (
        <span className="flex items-center gap-2 text-white/30 text-sm py-4">
          <ImageIcon className="w-4 h-4 animate-pulse" /> 加载图片中...
        </span>
      )}
      <img
        src={src}
        alt={alt || ''}
        onLoad={() => setLoaded(true)}
        onError={() => setError(true)}
        className={`max-w-full rounded-xl glass shadow-lg transition-opacity ${loaded ? 'opacity-100' : 'opacity-0 h-0'}`}
        style={{ maxHeight: 500, objectFit: 'contain' }}
      />
    </span>
  );
}

/** 视频组件 */
function MdVideo({ src }: { src: string }) {
  return (
    <span className="block my-3">
      <video
        controls
        src={src}
        className="max-w-full rounded-xl glass shadow-lg"
        style={{ maxHeight: 400 }}
      />
    </span>
  );
}

export default memo(function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  if (!content) return null;

  return (
    <div className={`markdown-body ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize]}
        components={{
          // 代码块
          code({ node, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            const codeString = String(children).replace(/\n$/, '');
            const isBlock = codeString.includes('\n') || !!match;

            if (isBlock) {
              return <CodeBlock language={match?.[1] || ''} children={codeString} />;
            }
            // 行内代码
            return (
              <code className={className} {...props}>
                {children}
              </code>
            );
          },
          // 链接 — 外部链接新窗口打开，图片/视频链接特殊处理
          a({ href, children, ...props }) {
            if (!href) return <a {...props}>{children}</a>;

            if (isImageUrl(href)) {
              return <MdImage src={href} alt={String(children)} />;
            }
            if (isVideoUrl(href)) {
              return <MdVideo src={href} />;
            }
            return (
              <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
                {children}
              </a>
            );
          },
          // 图片
          img({ src, alt, ...props }) {
            if (!src) return null;
            return <MdImage src={src} alt={alt} />;
          },
          // 表格 — 添加横向滚动
          table({ children, ...props }) {
            return (
              <div className="overflow-x-auto my-3 rounded-lg glass">
                <table {...props}>{children}</table>
              </div>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
});
