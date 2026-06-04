/**
 * 背景特效系统 — Canvas 3D 光球 + CSS 浮动光球
 *
 * 用 canvas 2D 绘制 Spline 风格的发光小球，无需远程加载 3D 模型
 * 性能友好: 光球 ~30fps，全部 GPU 合成层
 */
'use client';
import { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

/* ═══════════════════════════════════════════
   Canvas 3D 光球场景 — 模拟 Spline 风格
   ═══════════════════════════════════════════ */

interface OrbDef {
  x: number; y: number; z: number;
  vx: number; vy: number; vz: number;
  radius: number;
  color: [number, number, number]; // RGB
  glow: number; // glow radius multiplier
}

const ORB_DEFS: Omit<OrbDef, 'vx' | 'vy' | 'vz'>[] = [
  { x: 0.25, y: 0.35, z: 0.5,  radius: 90,  color: [100, 255, 218], glow: 2.5 },  // cyan
  { x: 0.72, y: 0.55, z: 0.3,  radius: 70,  color: [0, 212, 255],   glow: 2.2 },  // blue
  { x: 0.50, y: 0.20, z: 0.7,  radius: 55,  color: [139, 92, 246],  glow: 2.0 },  // purple
  { x: 0.15, y: 0.70, z: 0.4,  radius: 65,  color: [245, 158, 11],  glow: 2.3 },  // amber
  { x: 0.80, y: 0.25, z: 0.6,  radius: 50,  color: [59, 130, 246],  glow: 1.8 },  // blue-light
  { x: 0.45, y: 0.75, z: 0.2,  radius: 80,  color: [16, 185, 129],  glow: 2.1 },  // emerald
  { x: 0.60, y: 0.45, z: 0.8,  radius: 40,  color: [236, 72, 153],  glow: 1.6 },  // pink
];

export function OrbScene() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d', { alpha: true });
    if (!ctx) return;

    let w = 0, h = 0;
    const resize = () => {
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize, { passive: true });

    // 初始化光球
    const orbs: OrbDef[] = ORB_DEFS.map(d => ({
      ...d,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      vz: (Math.random() - 0.5) * 0.15,
    }));

    let lastTime = 0;
    const FPS_INTERVAL = 1000 / 30; // 30fps

    const animate = (now: number) => {
      requestAnimationFrame(animate);
      if (now - lastTime < FPS_INTERVAL) return;
      lastTime = now;

      ctx.clearRect(0, 0, w, h);

      // 更新 + 绘制
      for (const orb of orbs) {
        // 运动
        orb.x += orb.vx * 0.002;
        orb.y += orb.vy * 0.002;
        orb.z += orb.vz * 0.002;

        // 边界反弹
        if (orb.x < 0.05 || orb.x > 0.95) orb.vx *= -1;
        if (orb.y < 0.05 || orb.y > 0.95) orb.vy *= -1;
        if (orb.z < 0.1 || orb.z > 0.9) orb.vz *= -1;

        // 3D 透视
        const scale = 0.5 + orb.z * 0.8;
        const px = orb.x * w;
        const py = orb.y * h;
        const r = orb.radius * scale;

        // 外层光晕
        const glowGrad = ctx.createRadialGradient(px, py, r * 0.2, px, py, r * orb.glow);
        glowGrad.addColorStop(0, `rgba(${orb.color[0]},${orb.color[1]},${orb.color[2]},${0.15 * orb.z})`);
        glowGrad.addColorStop(0.5, `rgba(${orb.color[0]},${orb.color[1]},${orb.color[2]},${0.06 * orb.z})`);
        glowGrad.addColorStop(1, `rgba(${orb.color[0]},${orb.color[1]},${orb.color[2]},0)`);
        ctx.fillStyle = glowGrad;
        ctx.beginPath();
        ctx.arc(px, py, r * orb.glow, 0, Math.PI * 2);
        ctx.fill();

        // 核心球体
        const coreGrad = ctx.createRadialGradient(
          px - r * 0.25, py - r * 0.25, r * 0.05,
          px, py, r
        );
        coreGrad.addColorStop(0, `rgba(255,255,255,${0.5 * orb.z})`);
        coreGrad.addColorStop(0.3, `rgba(${orb.color[0]},${orb.color[1]},${orb.color[2]},${0.6 * orb.z})`);
        coreGrad.addColorStop(0.7, `rgba(${orb.color[0]},${orb.color[1]},${orb.color[2]},${0.25 * orb.z})`);
        coreGrad.addColorStop(1, `rgba(${orb.color[0]},${orb.color[1]},${orb.color[2]},0)`);
        ctx.fillStyle = coreGrad;
        ctx.beginPath();
        ctx.arc(px, py, r, 0, Math.PI * 2);
        ctx.fill();

        // 高光点
        const hlGrad = ctx.createRadialGradient(
          px - r * 0.3, py - r * 0.3, 0,
          px - r * 0.3, py - r * 0.3, r * 0.4
        );
        hlGrad.addColorStop(0, `rgba(255,255,255,${0.35 * orb.z})`);
        hlGrad.addColorStop(1, `rgba(255,255,255,0)`);
        ctx.fillStyle = hlGrad;
        ctx.beginPath();
        ctx.arc(px - r * 0.3, py - r * 0.3, r * 0.4, 0, Math.PI * 2);
        ctx.fill();
      }

      // 连接线（距离近的光球之间）
      for (let i = 0; i < orbs.length; i++) {
        for (let j = i + 1; j < orbs.length; j++) {
          const a = orbs[i], b = orbs[j];
          const ax = a.x * w, ay = a.y * h;
          const bx = b.x * w, by = b.y * h;
          const dist = Math.hypot(ax - bx, ay - by);
          const maxDist = 400;
          if (dist < maxDist) {
            const alpha = (1 - dist / maxDist) * 0.08 * ((a.z + b.z) / 2);
            ctx.strokeStyle = `rgba(100,255,218,${alpha})`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(ax, ay);
            ctx.lineTo(bx, by);
            ctx.stroke();
          }
        }
      }
    };

    requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-[1]"
      style={{ opacity: 0.85 }}
    />
  );
}

/* ═══════════════════════════════════════════
   浮动光球 (CSS) + 网格点阵 + 扫描线
   ═══════════════════════════════════════════ */

const cssOrbs = [
  { size: 320, color: 'from-blue-600/20 to-cyan-400/10', x: '5%', y: '10%', dur: 22 },
  { size: 260, color: 'from-amber-500/15 to-orange-400/10', x: '75%', y: '60%', dur: 18 },
  { size: 200, color: 'from-violet-500/15 to-blue-400/10', x: '60%', y: '5%', dur: 25 },
  { size: 180, color: 'from-cyan-400/10 to-emerald-400/10', x: '20%', y: '70%', dur: 20 },
];

export function FloatingOrbs() {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
      {cssOrbs.map((orb, i) => (
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
   背景组合
   ═══════════════════════════════════════════ */

export function FullBackground() {
  return (
    <>
      <FloatingOrbs />
      <OrbScene />
    </>
  );
}

export function DashboardBackground() {
  return (
    <>
      <FloatingOrbs />
      <OrbScene />
    </>
  );
}
