/**
 * 绿色跑马灯横幅 — 模板签名元素
 * 内容无缝循环滚动，悬停暂停
 */
'use client';

export default function Marquee({
  items,
  duration = 32,
  className = '',
}: {
  items: string[];
  duration?: number;
  className?: string;
}) {
  const doubled = [...items, ...items];
  return (
    <div className={`marquee ${className}`} aria-hidden="true">
      <div className="marquee-track" style={{ ['--marquee-duration' as string]: `${duration}s` }}>
        {doubled.map((text, i) => (
          <span key={i} className="inline-flex items-center whitespace-nowrap">
            <span className="px-5">{text}</span>
            <span className="opacity-60">◆</span>
          </span>
        ))}
      </div>
    </div>
  );
}
