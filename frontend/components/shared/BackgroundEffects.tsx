/**
 * 背景特效系统 — Spline 3D + 粒子 + 光标跟随 + 浮动光球
 *
 * 性能关键: 光标跟随用独立 DOM + CSS transform (GPU 合成层)
 * 不受 canvas/Spline 帧率影响，保证 60fps 丝滑
 */
'use client';
import { useEffect, useRef, useState } from 'react';
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
   鼠标光标跟随 — 独立 DOM 元素，CSS transform GPU 加速
   不依赖 canvas 帧率，保证丝滑
   ═══════════════════════════════════════════ */

const ICONS = [Zap, Cpu, Atom, Orbit, Sparkles];

export function MouseFollower() {
  const ref = useRef<HTMLDivElement>(null);
  const [iconIdx, setIconIdx] = useState(0);

  useEffect(() => {
    let mx = -100, my = -100;
    let cx = -100, cy = -100;
    let raf: number;

    const onMouse = (e: MouseEvent) => {
      mx = e.clientX - 12;
      my = e.clientY - 12;
    };

    // 独立 raf 循环，只更新一个 div 的 transform
    const tick = () => {
      cx += (mx - cx) * 0.18;
      cy += (my - cy) * 0.18;
      if (ref.current) {
        ref.current.style.transform = `translate3d(${cx}px, ${cy}px, 0)`;
      }
      raf = requestAnimationFrame(tick);
    };

    window.addEventListener('mousemove', onMouse, { passive: true });
    raf = requestAnimationFrame(tick);

    // 图标轮换
    const interval = setInterval(() => {
      setIconIdx(prev => (prev + 1) % 5);
    }, 3000);

    return () => {
      window.removeEventListener('mousemove', onMouse);
      cancelAnimationFrame(raf);
      clearInterval(interval);
    };
  }, []);

  const Icon = ICONS[iconIdx] ?? Zap;

  return (
    <div
      ref={ref}
      className="fixed top-0 left-0 pointer-events-none z-[60] mix-blend-screen"
      style={{ willChange: 'transform', transform: 'translate3d(-100px, -100px, 0)' }}
    >
      <Icon className="w-6 h-6 text-amber-400/60" />
    </div>
  );
}

/* ═══════════════════════════════════════════
   粒子系统 — 独立 canvas，降频到 ~20fps
   ═══════════════════════════════════════════ */

interface Particle {
  x: number; y: number;
  vx: number; vy: number;
  size: number; life: number;
  color: string;
}

const COLORS = ['#64ffda', '#00d4ff', '#f59e0b', '#3b82f6', '#8b5cf6'];

export function ParticleCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d', { alpha: true });
    if (!ctx) return;

    let w = 0, h = 0;
    let mx = -100, my = -100;
    let frame = 0;
    const particles: Particle[] = [];

    const resize = () => {
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
    };
    resize();

    const onMouse = (e: MouseEvent) => {
      mx = e.clientX;
      my = e.clientY;
    };

    window.addEventListener('mousemove', onMouse, { passive: true });
    window.addEventListener('resize', resize, { passive: true });

    let lastTime = 0;
    const FPS_INTERVAL = 1000 / 20; // 20fps 足够粒子效果

    const animate = (now: number) => {
      requestAnimationFrame(animate);
      if (now - lastTime < FPS_INTERVAL) return;
      lastTime = now;

      frame++;
      ctx.clearRect(0, 0, w, h);

      // 生成粒子 (每3帧1个，上限25)
      if (frame % 3 === 0 && mx > 0 && particles.length < 25) {
        const angle = Math.random() * 6.2832;
        const speed = 0.3 + Math.random() * 0.8;
        particles.push({
          x: mx + (Math.random() - 0.5) * 14,
          y: my + (Math.random() - 0.5) * 14,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          size: 1.5 + Math.random() * 2.5,
          life: 1,
          color: COLORS[Math.floor(Math.random() * 5)]!,
        });
      }

      // 渲染 + 更新 (swap-pop 移除，避免 splice)
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i]!;
        p.x += p.vx;
        p.y += p.vy;
        p.life -= 0.03;
        if (p.life <= 0) {
          // swap-pop
          particles[i] = particles[particles.length - 1]!;
          particles.pop();
          continue;
        }
        ctx.globalAlpha = p.life * 0.6;
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size * p.life, 0, 6.2832);
        ctx.fill();
      }
      ctx.globalAlpha = 1;
    };

    requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('mousemove', onMouse);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-[55]"
      style={{ mixBlendMode: 'screen' }}
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
      <MouseFollower />
    </>
  );
}

export function DashboardBackground() {
  return (
    <>
      <FloatingOrbs />
      <ParticleCanvas />
      <MouseFollower />
    </>
  );
}
