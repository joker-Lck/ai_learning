'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores';
import api from '@/lib/api';
import {
  GraduationCap, Eye, EyeOff, User, Lock, Mail,
  ArrowRight, Sparkles, BookOpen, Brain, BarChart3
} from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const { login, setGuest } = useAuthStore();
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // 登录表单
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  // 注册表单
  const [regUsername, setRegUsername] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regEmail, setRegEmail] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setError('请输入用户名和密码');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const res: any = await api.login(username, password);
      if (res.success && res.user) {
        api.setToken(res.token);
        login(res.user, res.token);
        router.push('/dashboard');
      } else {
        setError(res.message || '登录失败');
      }
    } catch (err: any) {
      setError(err.message || '网络错误');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regUsername || !regPassword) {
      setError('请填写必填项');
      return;
    }
    if (regUsername.length < 3) {
      setError('用户名至少 3 个字符');
      return;
    }
    if (regPassword.length < 6) {
      setError('密码至少 6 位');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const res: any = await api.register(regUsername, regPassword, regEmail || undefined);
      if (res.success) {
        setIsLogin(true);
        setError('');
        setUsername(regUsername);
      } else {
        setError(res.message || '注册失败');
      }
    } catch (err: any) {
      setError(err.message || '网络错误');
    } finally {
      setLoading(false);
    }
  };

  const handleGuest = async () => {
    try {
      const res: any = await api.guestLogin();
      if (res.token) api.setToken(res.token);
      setGuest();
      router.push('/dashboard');
    } catch {
      setGuest();
      router.push('/dashboard');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden bg-gradient-to-br from-primary-500 via-primary-600 to-primary-700">
      {/* 背景装饰 */}
      <div className="absolute inset-0 overflow-hidden">
        <motion.div
          className="absolute w-96 h-96 rounded-full bg-accent-cyan/10 blur-3xl"
          animate={{ x: [0, 100, 0], y: [0, -50, 0] }}
          transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
          style={{ top: '10%', left: '10%' }}
        />
        <motion.div
          className="absolute w-80 h-80 rounded-full bg-accent-blue/10 blur-3xl"
          animate={{ x: [0, -80, 0], y: [0, 60, 0] }}
          transition={{ duration: 15, repeat: Infinity, ease: 'linear' }}
          style={{ bottom: '10%', right: '10%' }}
        />
        <motion.div
          className="absolute w-64 h-64 rounded-full bg-accent-purple/10 blur-3xl"
          animate={{ x: [0, 50, 0], y: [0, -30, 0] }}
          transition={{ duration: 18, repeat: Infinity, ease: 'linear' }}
          style={{ top: '50%', left: '50%' }}
        />
        {/* 网格装饰 */}
        <div
          className="absolute inset-0 opacity-5"
          style={{
            backgroundImage: 'radial-gradient(circle, #64ffda 1px, transparent 1px)',
            backgroundSize: '40px 40px',
          }}
        />
      </div>

      <div className="relative z-10 w-full max-w-5xl mx-4 flex flex-col lg:flex-row items-center gap-8">
        {/* 左侧品牌区域 */}
        <motion.div
          className="flex-1 text-center lg:text-left text-white"
          initial={{ opacity: 0, x: -40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
        >
          <motion.div
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm mb-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Sparkles className="w-4 h-4 text-accent-cyan" />
            <span className="text-sm text-accent-cyan">AI 赋能教育 v6.0</span>
          </motion.div>

          <h1 className="text-4xl lg:text-5xl font-bold mb-4 leading-tight">
            多模态 AI
            <br />
            <span className="text-gradient">教学智能体</span>
          </h1>

          <p className="text-lg text-white/70 mb-8 max-w-md">
            智能答疑 · 课件生成 · 学情分析 · 知识管理
          </p>

          <div className="hidden lg:flex flex-col gap-4">
            {[
              { icon: Brain, text: 'RAG 优先策略，准确率提升 30%' },
              { icon: BookOpen, text: '一键生成专业 PPT 课件' },
              { icon: BarChart3, text: '7 维度深度学情分析' },
            ].map((item, i) => (
              <motion.div
                key={i}
                className="flex items-center gap-3 text-white/60"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.5 + i * 0.15 }}
              >
                <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center">
                  <item.icon className="w-4 h-4 text-accent-cyan" />
                </div>
                <span className="text-sm">{item.text}</span>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* 右侧表单区域 */}
        <motion.div
          className="w-full max-w-md"
          initial={{ opacity: 0, x: 40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <div className="glass rounded-2xl p-8 shadow-2xl">
            {/* Logo */}
            <div className="flex items-center justify-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent-cyan to-accent-blue flex items-center justify-center">
                <GraduationCap className="w-7 h-7 text-primary-500" />
              </div>
              <span className="text-xl font-bold text-primary-500">AI 教学助手</span>
            </div>

            {/* 登录/注册切换 */}
            <div className="flex bg-gray-100 rounded-xl p-1 mb-6">
              {['登录', '注册'].map((tab, i) => (
                <button
                  key={tab}
                  onClick={() => { setIsLogin(i === 0); setError(''); }}
                  className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all duration-300 ${
                    (i === 0 ? isLogin : !isLogin)
                      ? 'bg-white text-primary-500 shadow-sm'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            <AnimatePresence mode="wait">
              {isLogin ? (
                <motion.form
                  key="login"
                  onSubmit={handleLogin}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-4"
                >
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">用户名</label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <input
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder="请输入用户名"
                        className="w-full pl-10 pr-4 py-3 rounded-xl border-2 border-gray-200 focus:border-accent-blue focus:ring-2 focus:ring-accent-blue/20 outline-none transition-all"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">密码</label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="请输入密码"
                        className="w-full pl-10 pr-12 py-3 rounded-xl border-2 border-gray-200 focus:border-accent-blue focus:ring-2 focus:ring-accent-blue/20 outline-none transition-all"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  {error && (
                    <motion.p
                      initial={{ opacity: 0, y: -5 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="text-red-500 text-sm"
                    >
                      ❌ {error}
                    </motion.p>
                  )}

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-3 rounded-xl bg-gradient-to-r from-primary-500 to-primary-600 text-white font-medium hover:shadow-lg transition-all duration-300 flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {loading ? (
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <>
                        登录 <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>

                  <button
                    type="button"
                    onClick={handleGuest}
                    className="w-full py-2.5 rounded-xl border-2 border-gray-200 text-gray-600 font-medium hover:bg-gray-50 transition-all text-sm"
                  >
                    👤 游客模式体验
                  </button>
                </motion.form>
              ) : (
                <motion.form
                  key="register"
                  onSubmit={handleRegister}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-4"
                >
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">用户名</label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <input
                        type="text"
                        value={regUsername}
                        onChange={(e) => setRegUsername(e.target.value)}
                        placeholder="3-20 个字符"
                        className="w-full pl-10 pr-4 py-3 rounded-xl border-2 border-gray-200 focus:border-accent-blue focus:ring-2 focus:ring-accent-blue/20 outline-none transition-all"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">密码</label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <input
                        type="password"
                        value={regPassword}
                        onChange={(e) => setRegPassword(e.target.value)}
                        placeholder="至少 6 位"
                        className="w-full pl-10 pr-4 py-3 rounded-xl border-2 border-gray-200 focus:border-accent-blue focus:ring-2 focus:ring-accent-blue/20 outline-none transition-all"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">邮箱（可选）</label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <input
                        type="email"
                        value={regEmail}
                        onChange={(e) => setRegEmail(e.target.value)}
                        placeholder="your@email.com"
                        className="w-full pl-10 pr-4 py-3 rounded-xl border-2 border-gray-200 focus:border-accent-blue focus:ring-2 focus:ring-accent-blue/20 outline-none transition-all"
                      />
                    </div>
                  </div>

                  {error && (
                    <motion.p
                      initial={{ opacity: 0, y: -5 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="text-red-500 text-sm"
                    >
                      ❌ {error}
                    </motion.p>
                  )}

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-3 rounded-xl bg-gradient-to-r from-primary-500 to-primary-600 text-white font-medium hover:shadow-lg transition-all duration-300 flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {loading ? (
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      '注册账号'
                    )}
                  </button>
                </motion.form>
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
