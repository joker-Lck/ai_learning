/**
 * 暗黑复古科技背景 — 网格 + 扫描线 + 二进制雨 + HUD 准星 + 神经网络
 * 全部通过 CSS 变量取色，夜间/白天主题自动适配
 */
'use client';

import { memo, useMemo } from 'react';

/* 伪随机二进制列（确定性，避免水合抖动） */
function BinaryColumn({ index, total }: { index: number; total: number }) {
  const bits = useMemo(() => {
    let seed = 7919 * (index + 3);
    const rows: string[] = [];
    for (let i = 0; i < 22; i++) {
      let s = '';
      for (let j = 0; j < 10; j++) {
        seed = (seed * 1103515245 + 12345) & 0x7fffffff;
        s += seed % 2;
        if (j % 2 === 1) s += ' ';
      }
      rows.push(s);
    }
    return rows;
  }, [index]);

  const left = 4 + (index * 92) / total;
  const duration = 26 + (index % 5) * 7;

  return (
    <div
      className="absolute top-0 auto-scroll-container hidden md:block"
      style={{
        left: `${left}%`,
        height: '100%',
        opacity: 0.5,
        maskImage: 'linear-gradient(to bottom, transparent, black 20%, black 80%, transparent)',
        WebkitMaskImage: 'linear-gradient(to bottom, transparent, black 20%, black 80%, transparent)',
      }}
      aria-hidden="true"
    >
      <div className="auto-scroll-content" style={{ ['--scroll-duration' as string]: `${duration}s` }}>
        {[...bits, ...bits].map((row, i) => (
          <div key={i} className="binary-row leading-[2.2]">{row}</div>
        ))}
      </div>
    </div>
  );
}

/** HUD 四角括号 */
function HudCorners() {
  const corner = 'absolute w-8 h-8 border-[var(--accent)] opacity-40';
  return (
    <div aria-hidden="true">
      <div className={`${corner} top-4 left-4 border-t border-l`} />
      <div className={`${corner} top-4 right-4 border-t border-r`} />
      <div className={`${corner} bottom-4 left-4 border-b border-l`} />
      <div className={`${corner} bottom-4 right-4 border-b border-r`} />
    </div>
  );
}

export const FullBackground = memo(function FullBackground() {
  return (
    <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden" style={{ contain: 'strict' }}>
      {/* 网格 + 扫描线 */}
      <div className="absolute inset-0 tech-grid-bg" aria-hidden="true" />
      <div className="absolute inset-0 scanline-overlay" aria-hidden="true" />

      {/* 二进制雨 */}
      {Array.from({ length: 7 }).map((_, i) => (
        <BinaryColumn key={i} index={i} total={7} />
      ))}

      {/* 神经网络 — 节点连线 */}
      <svg
        className="absolute top-[8%] right-[4%] w-[560px] h-[420px] opacity-[0.28] svg-float-2 hidden lg:block"
        viewBox="0 0 560 420"
        fill="none"
        aria-hidden="true"
      >
        <g className="deco-stroke" strokeWidth="1">
          <path d="M40 210 L160 80 L300 140 L420 60 L520 160" />
          <path d="M40 210 L150 320 L300 140 L340 300 L520 160" />
          <path d="M160 80 L150 320 M300 140 L340 300 M420 60 L340 300" />
          <path d="M40 210 L300 140 M160 80 L340 300 M150 320 L520 160" />
        </g>
        <g className="deco-fill">
          {[[40, 210], [160, 80], [300, 140], [420, 60], [520, 160], [150, 320], [340, 300]].map(([x, y], i) => (
            <g key={i}>
              <circle cx={x} cy={y} r="6" />
              <circle cx={x} cy={y} r="13" fill="none" className="deco-stroke" strokeWidth="1" />
            </g>
          ))}
        </g>
        {/* 数据脉冲 */}
        <circle r="3" className="deco-fill">
          <animateMotion dur="6s" repeatCount="indefinite" path="M40 210 L160 80 L300 140 L420 60 L520 160" />
        </circle>
        <circle r="3" className="deco-fill">
          <animateMotion dur="8s" repeatCount="indefinite" path="M150 320 L300 140 L340 300 L520 160" />
        </circle>
      </svg>

      {/* 同心圆靶心 */}
      <svg className="absolute bottom-[12%] left-[6%] w-[340px] h-[340px] opacity-[0.2] svg-float-3 hidden md:block" viewBox="0 0 340 340" fill="none" aria-hidden="true">
        <circle cx="170" cy="170" r="160" className="deco-stroke" strokeWidth="1.5" />
        <circle cx="170" cy="170" r="118" className="deco-stroke svg-dash" strokeWidth="1" />
        <circle cx="170" cy="170" r="76" className="deco-stroke" strokeWidth="1" />
        <circle cx="170" cy="170" r="34" className="deco-stroke svg-dash" strokeWidth="1" />
        <line x1="170" y1="0" x2="170" y2="340" className="deco-stroke" strokeWidth="0.8" />
        <line x1="0" y1="170" x2="340" y2="170" className="deco-stroke" strokeWidth="0.8" />
      </svg>

      {/* 十字准星 */}
      <svg className="absolute top-[18%] left-[12%] w-14 h-14 opacity-40" viewBox="0 0 40 40" fill="none" aria-hidden="true">
        <line x1="20" y1="2" x2="20" y2="38" className="deco-stroke" strokeWidth="1" />
        <line x1="2" y1="20" x2="38" y2="20" className="deco-stroke" strokeWidth="1" />
        <circle cx="20" cy="20" r="9" className="deco-stroke" strokeWidth="1" />
      </svg>
      <svg className="absolute top-[62%] right-[10%] w-10 h-10 opacity-35" viewBox="0 0 40 40" fill="none" aria-hidden="true">
        <line x1="20" y1="4" x2="20" y2="36" className="deco-stroke" strokeWidth="1" />
        <line x1="4" y1="20" x2="36" y2="20" className="deco-stroke" strokeWidth="1" />
      </svg>

      {/* 三角 / 菱形科技图形 */}
      <svg className="absolute top-[38%] left-[28%] w-24 h-24 opacity-25 svg-float-1 hidden lg:block" viewBox="0 0 100 100" fill="none" aria-hidden="true">
        <path d="M50 8 L92 88 L8 88 Z" className="deco-stroke" strokeWidth="1.2" />
      </svg>
      <svg className="absolute bottom-[28%] right-[26%] w-20 h-20 opacity-20 svg-float-2 hidden lg:block" viewBox="0 0 100 100" fill="none" aria-hidden="true">
        <path d="M50 6 L94 50 L50 94 L6 50 Z" className="deco-stroke svg-dash" strokeWidth="1.2" />
      </svg>

      {/* 光晕 */}
      <div
        className="absolute -top-40 -right-40 w-[700px] h-[700px] rounded-full opacity-[0.1] will-change-transform"
        style={{ background: 'radial-gradient(circle, var(--accent), transparent 55%)', filter: 'blur(120px)' }}
        aria-hidden="true"
      />
      <div
        className="absolute -bottom-48 -left-32 w-[620px] h-[620px] rounded-full opacity-[0.07] will-change-transform"
        style={{ background: 'radial-gradient(circle, var(--accent), transparent 55%)', filter: 'blur(130px)' }}
        aria-hidden="true"
      />

      <HudCorners />
    </div>
  );
});

export const DashboardBackground = memo(function DashboardBackground() {
  return (
    <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden" style={{ contain: 'strict' }}>
      <div className="absolute inset-0 tech-grid-bg" aria-hidden="true" />
      <div className="absolute inset-0 scanline-overlay" aria-hidden="true" />

      {Array.from({ length: 4 }).map((_, i) => (
        <BinaryColumn key={i} index={i} total={4} />
      ))}

      {/* 同心圆 — 弱装饰 */}
      <svg className="absolute top-[6%] right-[2%] w-[420px] h-[420px] opacity-[0.14] svg-float-3 hidden xl:block" viewBox="0 0 420 420" fill="none" aria-hidden="true">
        <circle cx="210" cy="210" r="195" className="deco-stroke" strokeWidth="1.2" />
        <circle cx="210" cy="210" r="145" className="deco-stroke svg-dash" strokeWidth="1" />
        <circle cx="210" cy="210" r="95" className="deco-stroke" strokeWidth="1" />
        <line x1="210" y1="8" x2="210" y2="412" className="deco-stroke" strokeWidth="0.7" />
        <line x1="8" y1="210" x2="412" y2="210" className="deco-stroke" strokeWidth="0.7" />
      </svg>

      {/* 节点连线 */}
      <svg className="absolute bottom-[6%] left-[3%] w-[420px] h-[300px] opacity-[0.18] svg-float-1 hidden lg:block" viewBox="0 0 420 300" fill="none" aria-hidden="true">
        <g className="deco-stroke" strokeWidth="1">
          <path d="M20 160 L120 60 L240 110 L360 40" />
          <path d="M20 160 L110 250 L240 110 L280 230 L360 40" />
          <path d="M120 60 L110 250 M240 110 L280 230" />
        </g>
        <g className="deco-fill">
          {[[20, 160], [120, 60], [240, 110], [360, 40], [110, 250], [280, 230]].map(([x, y], i) => (
            <circle key={i} cx={x} cy={y} r="4.5" />
          ))}
        </g>
      </svg>

      {/* 光晕 */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[900px] rounded-full opacity-[0.05] will-change-transform"
        style={{ background: 'radial-gradient(circle, var(--accent), transparent 50%)', filter: 'blur(140px)' }}
        aria-hidden="true"
      />

      <HudCorners />
    </div>
  );
});
