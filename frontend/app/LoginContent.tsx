'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuthStore } from '@/stores';
import api from '@/lib/api';
import {
  GraduationCap, Eye, EyeOff, User, Lock, Mail,
  ArrowRight, Cpu, ShieldCheck, Zap,
} from 'lucide-react';
import { FullBackground } from '@/components/shared/BackgroundEffects';
import ThemeToggle from '@/components/shared/ThemeToggle';
import Marquee from '@/components/shared/Marquee';

/* ═══════════════════════════════════════════
   登录页面 — 暗黑复古科技风
   ═══════════════════════════════════════════ */

export default function LoginPage() {
  const { login, setGuest } = useAuthStore();
  const router = useRouter();
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [guestPrompt, setGuestPrompt] = useState(false);

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [regUsername, setRegUsername] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regRole, setRegRole] = useState<'student' | 'teacher'>('student');

  useEffect(() => {
    if (sessionStorage.getItem('guest_prompt') === '1') {
      sessionStorage.removeItem('guest_prompt');
      setGuestPrompt(true);
      setIsLogin(false);
    }
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) { setError('请输入用户名和密码'); return; }
    setLoading(true); setError('');

    // 清除旧的游客标志
    localStorage.removeItem('is_guest');

    try {
      const res: any = await api.login(username, password);
      const token = res.token || res.access_token;
      const user = res.user;
      if (token && user) {
        api.setToken(token);
        localStorage.setItem('user_info', JSON.stringify(user));
        login(user, token);
        sessionStorage.removeItem('new_user_register');
        sessionStorage.removeItem('new_user_name');
        sessionStorage.removeItem('new_user_pass');

        // 按角色跳转
        const role = user.role;
        if (role === 'teacher' || role === 'admin') {
          window.location.href = '/teacher';
          return;
        }
        // 学生：检查是否已有画像，决定跳转目标
        try {
          const profileRes: any = await api.getProfile();
          const hasProfile = profileRes?.success && profileRes?.data?.has_profile;
          window.location.href = hasProfile ? '/dashboard' : '/assessment-quiz';
        } catch {
          window.location.href = '/dashboard';
        }
        return;
      } else {
        setError(res.message || '登录失败，请检查用户名和密码');
      }
    } catch (err: any) {
      setError(err.message || '网络错误，请检查后端服务是否启动');
    }
    setLoading(false);
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regUsername || !regPassword) { setError('请填写必填项'); return; }
    if (regUsername.length < 3) { setError('用户名至少 3 个字符'); return; }
    if (regPassword.length < 6) { setError('密码至少 6 位'); return; }
    setLoading(true); setError('');
    try {
      const res: any = await api.register(regUsername, regPassword, regEmail || undefined, regRole);
      if (res.success) {
        // 注册成功后自动登录
        if (res.token) {
          localStorage.removeItem('is_guest');
          const userRole = res.user?.role || regRole;
          localStorage.setItem('user_info', JSON.stringify({ id: res.user?.id || 0, username: regUsername, role: userRole }));
          localStorage.setItem('auth_token', res.token);
          sessionStorage.setItem('new_user_register', '1');
          // 老师直接进老师端，学生进测评
          if (userRole === 'teacher') {
            window.location.href = '/teacher';
          } else {
            window.location.href = '/assessment-quiz';
          }
        } else {
          // 兜底：手动调用登录
          sessionStorage.setItem('new_user_register', '1');
          setIsLogin(true);
          setUsername(regUsername);
          setPassword('');
          setError('注册成功，正在自动登录...');
          setTimeout(() => { handleLoginAuto(regUsername, regPassword); }, 800);
        }
      }
      else { setError(res.message || '注册失败'); }
    } catch (err: any) { setError(err.message || '网络错误'); }
    finally { setLoading(false); }
  };

  const handleLoginAuto = async (u: string, p: string) => {
    setLoading(true); setError('');
    localStorage.removeItem('is_guest');
    try {
      const res: any = await api.login(u, p);
      if (res.success && res.token) {
        api.setToken(res.token);
        localStorage.setItem('user_info', JSON.stringify(res.user));
        login(res.user, res.token);
        sessionStorage.removeItem('new_user_register');
        window.location.href = '/assessment-quiz';
        return;
      }
      setError(res.message || '自动登录失败，请手动输入密码登录');
      setPassword('');
    } catch {
      setError('自动登录失败，请手动输入密码登录');
      setPassword('');
    }
    setLoading(false);
  };

  const handleGuest = async () => {
    setLoading(true);
    // 游客模式不调用后端 API，纯前端本地状态
    setGuest();
    window.location.href = '/dashboard';
  };

  /* 输入框样式 — 终端质感 */
  const inputCls = `
    w-full pl-11 pr-4 py-3 rounded-sm
    bg-white/[0.03] border border-white/[0.1]
    text-white text-sm font-mono placeholder:text-white/20
    focus:border-[var(--accent)] focus:bg-white/[0.05]
    focus:shadow-[0_0_0_2px_var(--accent-soft)]
    outline-none transition-all duration-200
  `;

  const labelCls = 'flex items-center gap-2 text-[11px] font-mono font-medium tracking-[0.18em] uppercase text-white/40 mb-2';

  return (
    <div className="min-h-screen flex flex-col relative" style={{ background: 'var(--bg)', color: 'var(--ink)' }}>
      <FullBackground />

      {/* ══ 顶栏 ══ */}
      <header className="relative z-20 w-full border-b border-[var(--line)]" style={{ background: 'var(--glass-bg)', backdropFilter: 'blur(12px)' }}>
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* 像素风 Logo */}
            <div
              className="w-9 h-9 grid grid-cols-3 grid-rows-3 gap-[2px] p-[3px] border border-[var(--accent)]"
              style={{ boxShadow: 'var(--glow)' }}
              aria-hidden="true"
            >
              {Array.from({ length: 9 }).map((_, i) => (
                <span
                  key={i}
                  className="block"
                  style={{
                    background: [0, 2, 4, 6, 8, 3].includes(i) ? 'var(--accent)' : 'transparent',
                  }}
                />
              ))}
            </div>
            <div className="leading-none">
              <div className="font-display font-bold text-lg tracking-[0.22em] text-[var(--ink)]">
                QIZHI<span className="text-[var(--accent)]">.AI</span>
              </div>
              <div className="text-[9px] font-mono tracking-[0.28em] text-[var(--ink-3)] mt-1">
                AI LEARNING AGENT SYSTEM
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="hidden md:flex items-center gap-2 text-[10px] font-mono tracking-[0.18em] text-[var(--accent)]">
              <span className="w-1.5 h-1.5 rounded-full animate-blink" style={{ background: 'var(--accent)', boxShadow: 'var(--glow)' }} />
              SYSTEM.ONLINE
            </span>
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* ══ 主体双栏 ══ */}
      <main className="relative z-10 flex-1 flex items-center">
        <div className="max-w-7xl w-full mx-auto px-6 py-10 grid lg:grid-cols-[1.05fr_0.95fr] gap-12 items-center">

          {/* — 左：品牌 / 终端 — */}
          <div className="hidden lg:flex flex-col gap-8">
            <div>
              <div className="tech-kicker mb-4">{'// MULTI-AGENT CORE · V9.1'}</div>
              <h1 className="glitch font-display font-bold text-[clamp(2.2rem,4.2vw,3.6rem)] leading-[1.12] tracking-wide">
                <span className="block" data-text="多模态 AI">多模态 AI</span>
                <span className="block text-[var(--accent)]" data-text="教学智能体">教学智能体</span>
              </h1>
              <p className="mt-5 text-base text-[var(--ink-2)] leading-relaxed max-w-md">
                6 大智能体协同，个性化学习路径规划、智能辅导、资源生成与班级学情管理，
                让每一次学习都被精准看见。
              </p>
            </div>

            {/* 终端状态窗口 */}
            <div className="terminal max-w-lg">
              <div className="terminal-bar">
                <span className="terminal-dot" style={{ background: '#ff5f57' }} />
                <span className="terminal-dot" style={{ background: '#febc2e' }} />
                <span className="terminal-dot" style={{ background: '#28c840' }} />
                <span className="tech-mono text-[11px] tracking-[0.14em] text-[var(--ink-3)] ml-2">
                  qizhi-core — agents/status
                </span>
              </div>
              <div className="terminal-body">
                <div><span className="text-[var(--accent)]">$</span> connect --agents multi_core</div>
                <div className="text-[var(--ink-3)]">Establishing neural links…</div>
                <div className="mt-2 space-y-1">
                  <div className="status-line"><span className="k">TUTOR.STATUS</span> = &quot;ONLINE&quot;</div>
                  <div className="status-line"><span className="k">PATH.PLANNER</span> = &quot;ONLINE&quot;</div>
                  <div className="status-line"><span className="k">RESOURCE.GEN</span> = &quot;ONLINE&quot;</div>
                  <div className="status-line"><span className="k">CLASS.ANALYTICS</span> = &quot;ONLINE&quot;</div>
                </div>
                <div className="mt-2">
                  <span className="text-[var(--accent)]">$</span> _<span className="blink">▊</span>
                </div>
              </div>
            </div>

            {/* 特性速览 */}
            <div className="flex flex-wrap gap-3">
              {[
                { icon: Cpu, label: '六大智能体协同' },
                { icon: Zap, label: '个性化学习路径' },
                { icon: ShieldCheck, label: '数据主权隔离' },
              ].map(({ icon: Icon, label }) => (
                <span
                  key={label}
                  className="inline-flex items-center gap-2 px-3.5 py-2 border border-[var(--line)] rounded-sm text-xs font-mono tracking-[0.1em] text-[var(--ink-2)]"
                  style={{ background: 'var(--glass-bg)' }}
                >
                  <Icon className="w-3.5 h-3.5 text-[var(--accent)]" />
                  {label}
                </span>
              ))}
            </div>

            {/* 二进制装饰 */}
            <div className="binary-row select-none hidden xl:block">
              [01010001 01001001 01011010 01001000 01001001]
            </div>
          </div>

          {/* — 右：认证卡片 — */}
          <div className="w-full max-w-lg mx-auto lg:mx-0">
            {/* 移动端品牌 */}
            <div className="lg:hidden text-center mb-8">
              <div className="tech-kicker mb-3">{'// MULTI-AGENT CORE'}</div>
              <h1 className="font-display font-bold text-3xl tracking-wide">
                多模态 AI <span className="text-[var(--accent)]">教学智能体</span>
              </h1>
              <p className="mt-2 text-sm text-[var(--ink-2)]">6 大智能体协同，个性化学习体验</p>
            </div>

            <motion.div
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, ease: [0.25, 0.46, 0.45, 0.94] }}
            >
              <div className="tech-card p-8" style={{ boxShadow: 'var(--shadow-card)' }}>
                {/* 卡片头 */}
                <div className="flex items-center justify-between mb-6 pb-4 border-b border-[var(--line)]">
                  <div>
                    <div className="tech-kicker mb-1.5">01 / ACCESS TERMINAL</div>
                    <h2 className="font-display font-bold text-xl tracking-wide">
                      {isLogin ? '登录系统' : '注册账号'}
                    </h2>
                  </div>
                  <GraduationCap className="w-7 h-7 text-[var(--accent)]" />
                </div>

                {/* 游客模式提示 */}
                {guestPrompt && (
                  <motion.div
                    initial={{ opacity: 0, y: -8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-5 px-4 py-3 rounded-sm border border-[var(--warn)]/40 flex items-center gap-3"
                    style={{ background: 'color-mix(in srgb, var(--warn) 10%, transparent)' }}
                  >
                    <span className="text-[var(--warn)] font-mono text-sm">!</span>
                    <p className="text-sm text-[var(--ink-2)]">该功能需要注册账号后才能使用，请先注册或登录</p>
                  </motion.div>
                )}

                {/* 切换标签 — 终端 Tab */}
                <div className="flex border border-[var(--line)] rounded-sm p-1 mb-6">
                  {['登录', '注册'].map((tab, i) => (
                    <button
                      key={tab}
                      onClick={() => { setIsLogin(i === 0); setError(''); }}
                      className={`relative flex-1 py-2.5 rounded-sm text-sm font-medium transition-all duration-200 ${
                        (i === 0 ? isLogin : !isLogin)
                          ? 'text-[var(--on-accent)]'
                          : 'text-[var(--ink-3)] hover:text-[var(--ink)]'
                      }`}
                      style={
                        (i === 0 ? isLogin : !isLogin)
                          ? { background: 'var(--accent)', boxShadow: 'var(--glow)' }
                          : undefined
                      }
                    >
                      {tab}
                    </button>
                  ))}
                </div>

                {/* 表单 */}
                <AnimatePresence>
                  {isLogin ? (
                    <motion.form
                      key="login"
                      onSubmit={handleLogin}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="space-y-5"
                    >
                      <div>
                        <label className={labelCls}><span className="text-[var(--accent)]">01</span> 用户名 / USERNAME</label>
                        <div className="relative group">
                          <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20 group-focus-within:text-[var(--accent)] transition-colors" />
                          <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="请输入用户名"
                            className={inputCls}
                          />
                        </div>
                      </div>

                      <div>
                        <label className={labelCls}><span className="text-[var(--accent)]">02</span> 密码 / PASSWORD</label>
                        <div className="relative group">
                          <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20 group-focus-within:text-[var(--accent)] transition-colors" />
                          <input
                            type={showPassword ? 'text' : 'password'}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="请输入密码"
                            className={inputCls}
                          />
                          <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-3.5 top-1/2 -translate-y-1/2 text-white/20 hover:text-[var(--accent)] transition-colors"
                          >
                            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>
                        </div>
                      </div>

                      <AnimatePresence>
                        {error && (
                          <motion.p
                            initial={{ opacity: 0, y: -8, height: 0 }}
                            animate={{ opacity: 1, y: 0, height: 'auto' }}
                            exit={{ opacity: 0, y: -8, height: 0 }}
                            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                            className="text-[var(--danger)] text-xs flex items-center gap-2 font-mono"
                          >
                            <span className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--danger)' }} />
                            {error}
                          </motion.p>
                        )}
                      </AnimatePresence>

                      <motion.button
                        type="submit"
                        disabled={loading}
                        whileTap={{ scale: 0.98 }}
                        className="btn-solid w-full py-3.5 text-sm disabled:opacity-40"
                      >
                        {loading ? (
                          <div className="w-5 h-5 border-2 border-[var(--on-accent)]/30 border-t-[var(--on-accent)] rounded-full animate-spin" />
                        ) : (
                          <>
                            登录系统 <ArrowRight className="w-4 h-4" />
                          </>
                        )}
                      </motion.button>

                      <motion.button
                        type="button"
                        onClick={handleGuest}
                        disabled={loading}
                        whileTap={{ scale: 0.98 }}
                        className="btn-ghost w-full py-3 text-sm disabled:opacity-40"
                      >
                        {loading ? (
                          <div className="w-4 h-4 border-2 border-[var(--ink-3)]/40 border-t-[var(--ink)] rounded-full animate-spin" />
                        ) : (
                          '游客模式体验'
                        )}
                      </motion.button>
                    </motion.form>
                  ) : (
                    <motion.form
                      key="register"
                      onSubmit={handleRegister}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="space-y-5"
                    >
                      <div>
                        <label className={labelCls}><span className="text-[var(--accent)]">01</span> 身份 / ROLE</label>
                        <div className="grid grid-cols-2 gap-2">
                          {[
                            { value: 'student', label: '我是学生', desc: '个性化学习' },
                            { value: 'teacher', label: '我是老师', desc: '班级管理与学情' },
                          ].map(({ value, label, desc }) => (
                            <button
                              key={value}
                              type="button"
                              onClick={() => setRegRole(value as 'student' | 'teacher')}
                              className={`
                                px-3 py-2.5 rounded-sm border text-left transition-all duration-200
                                ${regRole === value
                                  ? 'text-[var(--on-accent)]'
                                  : 'border-[var(--line)] bg-white/[0.02] text-white/40 hover:border-[var(--accent)]/50 hover:text-white/70'
                                }
                              `}
                              style={
                                regRole === value
                                  ? { background: 'var(--accent)', borderColor: 'var(--accent)', boxShadow: 'var(--glow)' }
                                  : undefined
                              }
                            >
                              <span className="block text-sm font-medium">{label}</span>
                              <span className="block text-[10px] mt-0.5 opacity-70">{desc}</span>
                            </button>
                          ))}
                        </div>
                      </div>

                      <div>
                        <label className={labelCls}><span className="text-[var(--accent)]">02</span> 用户名 / USERNAME</label>
                        <div className="relative group">
                          <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20 group-focus-within:text-[var(--accent)] transition-colors" />
                          <input
                            type="text"
                            value={regUsername}
                            onChange={(e) => setRegUsername(e.target.value)}
                            placeholder="3-20 个字符"
                            className={inputCls}
                          />
                        </div>
                      </div>

                      <div>
                        <label className={labelCls}><span className="text-[var(--accent)]">03</span> 密码 / PASSWORD</label>
                        <div className="relative group">
                          <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20 group-focus-within:text-[var(--accent)] transition-colors" />
                          <input
                            type="password"
                            value={regPassword}
                            onChange={(e) => setRegPassword(e.target.value)}
                            placeholder="至少 6 位"
                            className={inputCls}
                          />
                        </div>
                      </div>

                      <div>
                        <label className={labelCls}><span className="text-[var(--accent)]">04</span> 邮箱 / EMAIL（可选）</label>
                        <div className="relative group">
                          <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20 group-focus-within:text-[var(--accent)] transition-colors" />
                          <input
                            type="email"
                            value={regEmail}
                            onChange={(e) => setRegEmail(e.target.value)}
                            placeholder="your@email.com"
                            className={inputCls}
                          />
                        </div>
                      </div>

                      <AnimatePresence>
                        {error && (
                          <motion.p
                            initial={{ opacity: 0, y: -8, height: 0 }}
                            animate={{ opacity: 1, y: 0, height: 'auto' }}
                            exit={{ opacity: 0, y: -8, height: 0 }}
                            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                            className="text-[var(--danger)] text-xs flex items-center gap-2 font-mono"
                          >
                            <span className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--danger)' }} />
                            {error}
                          </motion.p>
                        )}
                      </AnimatePresence>

                      <motion.button
                        type="submit"
                        disabled={loading}
                        whileTap={{ scale: 0.98 }}
                        className="btn-solid w-full py-3.5 text-sm disabled:opacity-40"
                      >
                        {loading ? (
                          <div className="w-5 h-5 border-2 border-[var(--on-accent)]/30 border-t-[var(--on-accent)] rounded-full animate-spin" />
                        ) : '创建账号'}
                      </motion.button>
                    </motion.form>
                  )}
                </AnimatePresence>

                {/* 底部状态 */}
                <div className="mt-6 pt-4 border-t border-[var(--line)] flex items-center justify-between">
                  <p className="text-[10px] font-mono text-[var(--ink-4)] tracking-[0.18em]">
                    POWERED BY MULTI-AGENT AI
                  </p>
                  <p className="text-[10px] font-mono text-[var(--accent)] tracking-[0.18em]">
                    ENCRYPTED · LOCAL
                  </p>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </main>

      {/* ══ 底部跑马灯 ══ */}
      <div className="relative z-10">
        <Marquee
          items={[
            '六大智能体协同',
            '个性化学习路径',
            '智能辅导 TUTOR',
            '学情分析 ANALYTICS',
            '资源生成 RESOURCE',
            '班级管理 CLASS',
            '数据主权隔离',
            'AI-POWERED LEARNING',
          ]}
          duration={36}
        />
        <div className="border-t border-[var(--line)] py-4 text-center">
          <p className="text-[10px] font-mono tracking-[0.22em] text-[var(--ink-4)]">
            © 2026 QIZHI.AI · MULTI-AGENT LEARNING SYSTEM
          </p>
        </div>
      </div>
    </div>
  );
}
