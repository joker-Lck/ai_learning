/**
 * 背景特效系统 — Spline 3D + 粒子 + 鼠标跟随 + 浮动光球
 * 登录页和主页面复用同一套动画
 */
'use client';
import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, useMotionValue, useSpring } from 'framer-motion';
import { Zap, Cpu, Atom, Orbit, Sparkles } from 'lucide-react';
import dynamic from 'next/dynamic';

const Spline = dynamic(() => import('@splinetool/react-spline/next'), { ssr: false });

/* ═══════════════════════════════════════════
   Spline 3D 场景
   ═══════════════════════════════════════════ */
export function SplineBackground() {
  return (
    <div className="fixed inset-0 z-0 pointer-events-none">
      <Spline
        scene="https://prod.spline.design/eqtbmmRpUBNRvFku/scene.splinecode"
        style={{ width: '100%', height: '100%', opacity: 0.6 }}
      />
      {/* 暗色遮罩，确保内容可读 */}
      <div className="absolute inset-0 bg-[#060d1f]/40" />
    </div>
  );
}

/* ═══════════════════════════════════════════
   粒子系统 — 鼠标跟随 + 背景漂浮粒子
   ═══════════════════════════════════════════ */

interface Particle {
  id: number;
  x: number;
  y: number;
  size: number;
  opacity: number;
  vx: number;
  vy: number;
  life: number;
  color: string;
}

const PARTICLE_COLORS = ['#64ffda', '#00d4ff', '#f59e0b', '#3b82f6', '#8b5cf6'];

export function useMouseParticles() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouseRef = useRef({ x: 0, y: 0 });
  const particlesRef = useRef<Particle[]>([]);
  const frameRef = useRef(0);
  const nextIdRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const handleMouse = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY };
      if (frameRef.current % 2 === 0) {
        const angle = Math.random() * Math.PI * 2;
        const speed = 0.5 + Math.random() * 1.5;
        particlesRef.current.push({
          id: nextIdRef.current++,
          x: e.clientX + (Math.random() - 0.5) * 20,
          y: e.clientY + (Math.random() - 0.5) * 20,
          size: 2 + Math.random() * 4,
          opacity: 0.8,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          life: 1,
          color: PARTICLE_COLORS[Math.floor(Math.random() * PARTICLE_COLORS.length)]!,
        });
        if (particlesRef.current.length > 80) {
          particlesRef.current = particlesRef.current.slice(-60);
        }
      }
    };
    window.addEventListener('mousemove', handleMouse);

    let raf: number;
    const animate = () => {
      frameRef.current++;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particlesRef.current = particlesRef.current.filter(p => {
        p.x += p.vx;
        p.y += p.vy;
        p.life -= 0.02;
        p.opacity = p.life * 0.8;
        p.size *= 0.98;
        if (p.life <= 0) return false;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = p.opacity;
        ctx.fill();

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size * 2, 0, Math.PI * 2);
        const grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.size * 2);
        grad.addColorStop(0, p.color);
        grad.addColorStop(1, 'transparent');
        ctx.fillStyle = grad;
        ctx.globalAlpha = p.opacity * 0.3;
        ctx.fill();

        ctx.globalAlpha = 1;
        return true;
      });

      raf = requestAnimationFrame(animate);
    };
    raf = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', handleMouse);
      cancelAnimationFrame(raf);
    };
  }, []);

  return canvasRef;
}

/* ═══════════════════════════════════════════
   鼠标光标跟随图标
   ═══════════════════════════════════════════ */

export function MouseFollower() {
  const mouseX = useMotionValue(-100);
  const mouseY = useMotionValue(-100);
  const springX = useSpring(mouseX, { stiffness: 500, damping: 28 });
  const springY = useSpring(mouseY, { stiffness: 500, damping: 28 });
  const [icon, setIcon] = useState(0);
  const icons = [Zap, Cpu, Atom, Orbit, Sparkles];

  useEffect(() => {
    const handleMouse = (e: MouseEvent) => {
      mouseX.set(e.clientX - 12);
      mouseY.set(e.clientY - 12);
    };
    window.addEventListener('mousemove', handleMouse);

    const interval = setInterval(() => {
      setIcon(prev => (prev + 1) % icons.length);
    }, 3000);

    return () => {
      window.removeEventListener('mousemove', handleMouse);
      clearInterval(interval);
    };
  }, [mouseX, mouseY, icons.length]);

  const IconComp = icons[icon] ?? Zap;

  return (
    <motion.div
      className="fixed top-0 left-0 pointer-events-none z-[60] mix-blend-screen"
      style={{ x: springX, y: springY }}
    >
      <motion.div
        key={icon}
        initial={{ scale: 0, rotate: -180 }}
        animate={{ scale: 1, rotate: 0 }}
        exit={{ scale: 0, rotate: 180 }}
        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      >
        <IconComp className="w-6 h-6 text-amber-400/60" />
      </motion.div>
    </motion.div>
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
          style={{ width: orb.size, height: orb.size, left: orb.x, top: orb.y }}
          animate={{
            x: [0, 60 * (i % 2 === 0 ? 1 : -1), 0],
            y: [0, -40 * (i % 2 === 0 ? -1 : 1), 0],
            scale: [1, 1.15, 1],
          }}
          transition={{ duration: orb.dur, repeat: Infinity, ease: 'easeInOut' }}
        />
      ))}
      {/* 网格点阵 */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: 'radial-gradient(circle, #64ffda 1px, transparent 1px)',
          backgroundSize: '48px 48px',
        }}
      />
      {/* 扫描线 */}
      <motion.div
        className="absolute left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan-400/20 to-transparent"
        animate={{ top: ['0%', '100%'] }}
        transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
      />
    </div>
  );
}

/* ═══════════════════════════════════════════
   粒子 Canvas 组件（独立使用）
   ═══════════════════════════════════════════ */

export function ParticleCanvas() {
  const canvasRef = useMouseParticles();
  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-[55]"
      style={{ mixBlendMode: 'screen' }}
    />
  );
}

/* ═══════════════════════════════════════════
   完整背景组合 — 登录页使用（含 Spline）
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

/* ═══════════════════════════════════════════
   轻量背景组合 — Dashboard 使用（无 Spline，性能更好）
   ═══════════════════════════════════════════ */

export function DashboardBackground() {
  return (
    <>
      <FloatingOrbs />
      <ParticleCanvas />
      <MouseFollower />
    </>
  );
}
