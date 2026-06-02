/**
 * 背景特效系统 — Spline 3D + 高性能粒子/光标/光球
 * 所有动态元素合并到单个 canvas，减少 DOM 操作和事件监听
 */
'use client';
import { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Zap, Cpu, Atom, Orbit, Sparkles } from 'lucide-react';

/* ═══════════════════════════════════════════
   Spline 3D 场景
   ═══════════════════════════════════════════ */
export function SplineBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    let app: any = null;
    let cancelled = false;

    (async () => {
      const { Application } = await import('@splinetool/runtime');
      if (cancelled || !canvasRef.current) return;
      app = new Application(canvasRef.current);
      await app.load('https://prod.spline.design/eqtbmmRpUBNRvFku/scene.splinecode');
    })();

    return () => {
      cancelled = true;
      if (app) { try { app.dispose(); } catch {} }
    };
  }, []);

  return (
    <div className="fixed inset-0 z-0 pointer-events-none" style={{ transform: 'scale(1.3)', transformOrigin: 'center center' }}>
      <canvas ref={canvasRef} style={{ width: '100%', height: '100%' }} />
      <div className="absolute inset-0 bg-[#060d1f]/40" />
    </div>
  );
}

/* ═══════════════════════════════════════════
   高性能粒子 + 光标跟随（单 canvas 合并渲染）
   ═══════════════════════════════════════════ */

interface Particle {
  x: number; y: number;
  vx: number; vy: number;
  size: number; life: number;
  color: string;
}

const COLORS = ['#64ffda', '#00d4ff', '#f59e0b', '#3b82f6', '#8b5cf6'];
const CURSOR_ICONS = [Zap, Cpu, Atom, Orbit, Sparkles];

export function ParticleCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d', { alpha: true });
    if (!ctx) return;

    // 状态
    let w = 0, h = 0;
    let mx = -100, my = -100;          // 鼠标位置
    let cx = -100, cy = -100;          // 光标平滑位置 (lerp)
    let frame = 0;
    let lastParticleFrame = 0;
    const particles: Particle[] = [];
    const MAX_PARTICLES = 40;

    // 光标图标 SVG 路径缓存
    const iconPaths = [
      // Zap
      'M13 2L3 14h9l-1 10 10-12h-9l1-10z',
      // Cpu (简化为方形+短线)
      'M4 4h16v16H4zM9 1v3M15 1v3M9 20v3M15 20v3M1 9h3M1 15h3M20 9h3M20 15h3',
      // Atom (简化为圆)
      'M12 12m-3 0a3 3 0 1 0 6 0 3 3 0 1 0-6 0',
      // Orbit
      'M12 12m-8 0a8 8 0 1 0 16 0 8 8 0 1 0-16 0M12 12m-3 0a3 3 0 1 0 6 0 3 3 0 1 0-6 0',
      // Sparkles
      'M12 2l1.5 4.5L18 8l-4.5 1.5L12 14l-1.5-4.5L6 8l4.5-1.5z',
    ];
    let iconIdx = 0;
    let iconTimer = 0;

    const resize = () => {
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
    };
    resize();

    // 节流 mousemove — 每帧最多处理一次
    let pendingMouse: { x: number; y: number } | null = null;
    const onMouse = (e: MouseEvent) => {
      pendingMouse = { x: e.clientX, y: e.clientY };
    };
    const onResize = () => resize();

    window.addEventListener('mousemove', onMouse, { passive: true });
    window.addEventListener('resize', onResize, { passive: true });

    let raf: number;
    const animate = () => {
      frame++;
      ctx.clearRect(0, 0, w, h);

      // — 更新鼠标位置 —
      if (pendingMouse) {
        mx = pendingMouse.x;
        my = pendingMouse.y;
        pendingMouse = null;
      }

      // — 光标 lerp (比 framer-motion spring 轻量得多) —
      cx += (mx - cx) * 0.15;
      cy += (my - cy) * 0.15;

      // — 生成粒子 (降频: 每4帧1个) —
      if (frame - lastParticleFrame >= 4 && mx > 0 && particles.length < MAX_PARTICLES) {
        lastParticleFrame = frame;
        const angle = Math.random() * Math.PI * 2;
        const speed = 0.3 + Math.random() * 1;
        particles.push({
          x: mx + (Math.random() - 0.5) * 16,
          y: my + (Math.random() - 0.5) * 16,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          size: 1.5 + Math.random() * 3,
          life: 1,
          color: COLORS[Math.floor(Math.random() * 5)]!,
        });
      }

      // — 渲染粒子 (纯圆，不用 gradient) —
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i]!;
        p.x += p.vx;
        p.y += p.vy;
        p.life -= 0.025;
        if (p.life <= 0) { particles.splice(i, 1); continue; }

        ctx.globalAlpha = p.life * 0.7;
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size * p.life, 0, 6.2832);
        ctx.fill();
      }

      // — 渲染光标图标 —
      iconTimer++;
      if (iconTimer >= 180) { iconTimer = 0; iconIdx = (iconIdx + 1) % 5; }

      if (cx > 0) {
        ctx.save();
        ctx.translate(cx, cy);
        ctx.globalAlpha = 0.5;
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 1.5;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        // 绘制简化的闪电图标 (最轻量)
        const s = 10;
        ctx.beginPath();
        if (iconIdx === 0) {
          // Zap
          ctx.moveTo(s * 0.3, -s);
          ctx.lineTo(-s * 0.2, s * 0.1);
          ctx.lineTo(s * 0.1, s * 0.1);
          ctx.lineTo(-s * 0.3, s);
          ctx.lineTo(s * 0.2, -s * 0.1);
          ctx.lineTo(-s * 0.1, -s * 0.1);
          ctx.closePath();
          ctx.fillStyle = 'rgba(245,158,11,0.3)';
          ctx.fill();
          ctx.stroke();
        } else {
          // 其他图标用圆点+十字代替
          ctx.arc(0, 0, 5, 0, 6.2832);
          ctx.stroke();
          ctx.beginPath();
          ctx.moveTo(-8, 0); ctx.lineTo(8, 0);
          ctx.moveTo(0, -8); ctx.lineTo(0, 8);
          ctx.stroke();
        }
        ctx.restore();
      }

      ctx.globalAlpha = 1;
      raf = requestAnimationFrame(animate);
    };
    raf = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('mousemove', onMouse);
      window.removeEventListener('resize', onResize);
      cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-[55]"
      style={{ mixBlendMode: 'screen', willChange: 'transform' }}
    />
  );
}

/* ═══════════════════════════════════════════
   浮动光球 + 网格点阵 + 扫描线
   ═══════════════════════════════════════════ */

const orbs = [
  { size: 320, color: 'from-blue-600/20 to-cyan-400/10', x: '5%', y: '10%', dur: 22 },
  { size: 260, color: 'from-amber-500/15 to-orange-400/10', x: '75%', y: '60%', dur: 18 },
  { size: 200, color: 'from-violet-500/15 to-blue-400/10', x: '60%', y: '5%', dur: 25 },
  { size: 180, color: 'from-cyan-400/10 to-emerald-400/10', x: '20%', y: '70%', dur: 20 },
];

export function FloatingOrbs() {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
      {orbs.map((orb, i) => (
        <motion.div
          key={i}
          className={`absolute rounded-full bg-gradient-to-br ${orb.color} blur-3xl`}
          style={{ width: orb.size, height: orb.size, left: orb.x, top: orb.y, willChange: 'transform' }}
          animate={{
            x: [0, 60 * (i % 2 === 0 ? 1 : -1), 0],
            y: [0, -40 * (i % 2 === 0 ? -1 : 1), 0],
            scale: [1, 1.15, 1],
          }}
          transition={{ duration: orb.dur, repeat: Infinity, ease: 'easeInOut' }}
        />
      ))}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: 'radial-gradient(circle, #64ffda 1px, transparent 1px)',
          backgroundSize: '48px 48px',
        }}
      />
      <motion.div
        className="absolute left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan-400/20 to-transparent"
        animate={{ top: ['0%', '100%'] }}
        transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
      />
    </div>
  );
}

/* ═══════════════════════════════════════════
   背景组合
   ═══════════════════════════════════════════ */

export function FullBackground() {
  return (
    <>
      <SplineBackground />
      <FloatingOrbs />
      <ParticleCanvas />
    </>
  );
}

export function DashboardBackground() {
  return (
    <>
      <FloatingOrbs />
      <ParticleCanvas />
    </>
  );
}
