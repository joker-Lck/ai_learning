'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuthStore } from '@/stores';
import api from '@/lib/api';
import {
  GraduationCap, Eye, EyeOff, User, Lock, Mail,
  ArrowRight,
} from 'lucide-react';
import { FullBackground } from '@/components/shared/BackgroundEffects';

/* ═══════════════════════════════════════════
   登录页面
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
        // 检查是否是新注册用户
        const isNew = sessionStorage.getItem('new_user_register') === '1';
        sessionStorage.removeItem('new_user_register');
        sessionStorage.removeItem('new_user_name');
        sessionStorage.removeItem('new_user_pass');
        window.location.href = isNew ? '/assessment-quiz' : '/dashboard';
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
      const res: any = await api.register(regUsername, regPassword, regEmail || undefined);
      if (res.success) {
        // 注册成功后自动登录
        if (res.token) {
          // 后端返回了 token，直接登录
          localStorage.removeItem('is_guest');
          localStorage.setItem('user_info', JSON.stringify({ id: res.user?.id || 0, username: regUsername, role: 'user' }));
          localStorage.setItem('auth_token', res.token);
          sessionStorage.setItem('new_user_register', '1');
          window.location.href = '/assessment-quiz';
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

  return (
    <div className="min-h-screen flex items-center justify-center relative bg-[#0a0a0a]">
      <FullBackground />

      <div className="relative z-10 w-full max-w-lg mx-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
        >
          <div className="rounded-xl bg-white/[0.04] border border-white/[0.06] p-8">
            {/* Logo */}
            <div className="flex items-center justify-center gap-3 mb-8">
              <div className="w-12 h-12 rounded-lg bg-purple-500/15 flex items-center justify-center">
                <GraduationCap className="w-6 h-6 text-purple-400" />
              </div>
              <div>
                <span className="text-xl font-semibold text-white block leading-tight">AI 学习助手</span>
                <span className="text-xs text-white/25 tracking-widest">MULTI-AGENT LEARNING</span>
              </div>
            </div>

            {/* 标题 */}
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-white mb-3">多模态 AI 教学智能体</h1>
              <p className="text-lg text-white/35">6 大智能体协同，个性化学习体验</p>
            </div>

            {/* 游客模式提示 */}
            {guestPrompt && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-5 px-4 py-3 rounded-lg border border-amber-400/20 bg-amber-400/5 flex items-center gap-3"
              >
                <span className="text-amber-400 text-sm">!</span>
                <p className="text-sm text-amber-300/80">该功能需要注册账号后才能使用，请先注册或登录</p>
              </motion.div>
            )}

            {/* 切换标签 */}
            <div className="flex bg-white/[0.03] rounded-lg p-1 mb-6 border border-white/[0.05]">
              {['登录', '注册'].map((tab, i) => (
                <button
                  key={tab}
                  onClick={() => { setIsLogin(i === 0); setError(''); }}
                  className={`relative flex-1 py-2 rounded-md text-sm font-medium transition-colors ${
                    (i === 0 ? isLogin : !isLogin) ? 'text-white bg-white/[0.06]' : 'text-white/30 hover:text-white/50'
                  }`}
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
                  className="space-y-4"
                >
                  <div>
                    <label className="block text-xs font-medium text-white/40 mb-1.5 tracking-wide">用户名</label>
                    <div className="relative group">
                      <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20 group-focus-within:text-cyan-400/60 transition-colors" />
                      <input
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder="请输入用户名"
                        className="
                          w-full pl-11 pr-4 py-2.5 rounded-lg
                          bg-white/[0.04] border border-white/[0.06]
                          text-white text-sm placeholder:text-white/20
                          focus:border-white/[0.15] focus:bg-white/[0.06]
                          outline-none transition-colors
                        "
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-white/40 mb-1.5 tracking-wide">密码</label>
                    <div className="relative group">
                      <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20 group-focus-within:text-cyan-400/60 transition-colors" />
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="请输入密码"
                        className="
                          w-full pl-11 pr-12 py-3 rounded-xl
                          bg-white/[0.04] border border-white/[0.08]
                          text-white text-sm placeholder:text-white/15
                          focus:border-cyan-400/30 focus:bg-white/[0.06]
                          focus:ring-1 focus:ring-cyan-400/20
                          outline-none transition-all duration-200
                        "
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3.5 top-1/2 -translate-y-1/2 text-white/20 hover:text-white/40 transition-colors"
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
                        className="text-red-400/80 text-xs flex items-center gap-1.5"
                      >
                        <span className="w-1 h-1 rounded-full bg-red-400" />
                        {error}
                      </motion.p>
                    )}
                  </AnimatePresence>

                  <motion.button
                    type="submit"
                    disabled={loading}
                    className="
                      w-full py-3 rounded-lg
                      bg-purple-500 hover:bg-purple-400
                      text-white font-medium text-sm
                      flex items-center justify-center gap-2
                      disabled:opacity-40 transition-colors
                    "
                  >
                    {loading ? (
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <>
                        登录 <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </motion.button>

                  <motion.button
                    type="button"
                    onClick={handleGuest}
                    disabled={loading}
                    className="
                      w-full py-2.5 rounded-lg
                      border border-white/[0.06] bg-transparent
                      text-white/40 text-sm
                      flex items-center justify-center gap-2
                      disabled:opacity-40 hover:text-white/60 hover:bg-white/[0.03] transition-colors
                    "
                  >
                    {loading ? (
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
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
                  className="space-y-4"
                >
                  <div>
                    <label className="block text-xs font-medium text-white/40 mb-1.5 tracking-wide">用户名</label>
                    <div className="relative group">
                      <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20 group-focus-within:text-cyan-400/60 transition-colors" />
                      <input
                        type="text"
                        value={regUsername}
                        onChange={(e) => setRegUsername(e.target.value)}
                        placeholder="3-20 个字符"
                        className="
                          w-full pl-11 pr-4 py-2.5 rounded-lg
                          bg-white/[0.04] border border-white/[0.06]
                          text-white text-sm placeholder:text-white/20
                          focus:border-white/[0.15] focus:bg-white/[0.06]
                          outline-none transition-colors
                        "
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-white/40 mb-1.5 tracking-wide">密码</label>
                    <div className="relative group">
                      <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20 group-focus-within:text-cyan-400/60 transition-colors" />
                      <input
                        type="password"
                        value={regPassword}
                        onChange={(e) => setRegPassword(e.target.value)}
                        placeholder="至少 6 位"
                        className="
                          w-full pl-11 pr-4 py-2.5 rounded-lg
                          bg-white/[0.04] border border-white/[0.06]
                          text-white text-sm placeholder:text-white/20
                          focus:border-white/[0.15] focus:bg-white/[0.06]
                          outline-none transition-colors
                        "
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-white/40 mb-1.5 tracking-wide">邮箱（可选）</label>
                    <div className="relative group">
                      <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20 group-focus-within:text-cyan-400/60 transition-colors" />
                      <input
                        type="email"
                        value={regEmail}
                        onChange={(e) => setRegEmail(e.target.value)}
                        placeholder="your@email.com"
                        className="
                          w-full pl-11 pr-4 py-2.5 rounded-lg
                          bg-white/[0.04] border border-white/[0.06]
                          text-white text-sm placeholder:text-white/20
                          focus:border-white/[0.15] focus:bg-white/[0.06]
                          outline-none transition-colors
                        "
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
                        className="text-red-400/80 text-xs flex items-center gap-1.5"
                      >
                        <span className="w-1 h-1 rounded-full bg-red-400" />
                        {error}
                      </motion.p>
                    )}
                  </AnimatePresence>

                  <motion.button
                    type="submit"
                    disabled={loading}
                    className="
                      w-full py-3 rounded-lg
                      bg-purple-500 hover:bg-purple-400
                      text-white font-medium text-sm
                      flex items-center justify-center gap-2
                      disabled:opacity-40 transition-colors
                    "
                  >
                    {loading ? (
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : '注册账号'}
                  </motion.button>
                </motion.form>
              )}
            </AnimatePresence>

            {/* 底部 */}
            <div className="mt-6 pt-4 border-t border-white/[0.04] text-center">
              <p className="text-[10px] text-white/20 tracking-widest">
                POWERED BY MULTI-AGENT AI
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
