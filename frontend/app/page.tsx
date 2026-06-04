'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuthStore } from '@/stores';
import api from '@/lib/api';
import {
  GraduationCap, Eye, EyeOff, User, Lock, Mail,
  ArrowRight, Sparkles, BookOpen, Brain, BarChart3,
} from 'lucide-react';
import { FullBackground } from '@/components/shared/BackgroundEffects';

/* ═══════════════════════════════════════════
   功能特性卡片（可交互展开）
   ═══════════════════════════════════════════ */

const features = [
  {
    icon: Brain,
    title: '智能问答',
    desc: '基于 RAG 知识库的精准答疑，支持多轮对话与上下文理解',
    detail: '融合讯飞星火大模型与向量检索，实现教学知识的精准匹配。支持多模态理解，让每个问题都得到专业回答。',
    gradient: 'from-blue-500 to-cyan-400',
    glow: 'shadow-blue-500/20',
  },
  {
    icon: BookOpen,
    title: '个性学习路径',
    desc: 'AI 驱动的自适应学习规划，7 维度深度画像分析',
    detail: '通过分析学习行为、知识掌握度、认知风格等 7 个维度，动态生成个性化学习路径。实时调整难度与节奏，确保最优学习效率。',
    gradient: 'from-amber-500 to-orange-400',
    glow: 'shadow-amber-500/20',
  },
  {
    icon: BarChart3,
    title: '学情分析',
    desc: '多维度数据可视化，精准定位薄弱知识点',
    detail: '整合学习时长、正确率、知识点覆盖率等数据，生成可视化分析报告。AI 自动识别学习瓶颈，推荐针对性练习。',
    gradient: 'from-violet-500 to-purple-400',
    glow: 'shadow-violet-500/20',
  },
  {
    icon: Sparkles,
    title: '智能资源生成',
    desc: '一键生成 7 种学习资源，涵盖文档、测验、思维导图等',
    detail: '支持文档、测验、思维导图、视频脚本、动画脚本、代码案例、阅读材料 7 种类型的智能生成。基于学生画像自动调整内容难度与风格。',
    gradient: 'from-emerald-500 to-teal-400',
    glow: 'shadow-emerald-500/20',
  },
];

function FeatureCard({ feature, index }: { feature: typeof features[0]; index: number }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        type: 'spring',
        stiffness: 200,
        damping: 25,
        delay: 0.6 + index * 0.1,
      }}
      onClick={() => setExpanded(!expanded)}
      className={`
        relative cursor-pointer group
        rounded-2xl border border-white/10
        bg-white/5 backdrop-blur-xl
        p-5 transition-colors duration-300
        hover:bg-white/10 hover:border-white/20
        ${expanded ? `shadow-lg ${feature.glow}` : ''}
      `}
      style={{ willChange: 'transform' }}
    >
      {/* 顶部高光条 */}
      <motion.div
        className={`absolute top-0 left-4 right-4 h-px bg-gradient-to-r ${feature.gradient}`}
        initial={{ scaleX: 0 }}
        animate={{ scaleX: expanded ? 1 : 0 }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      />

      <div className="flex items-start gap-4">
        <motion.div
          className={`
            w-11 h-11 rounded-xl bg-gradient-to-br ${feature.gradient}
            flex items-center justify-center flex-shrink-0
          `}
          whileHover={{ scale: 1.1, rotate: 5 }}
          whileTap={{ scale: 0.95 }}
          transition={{ type: 'spring', stiffness: 400, damping: 15 }}
        >
          <feature.icon className="w-5 h-5 text-white" />
        </motion.div>

        <div className="flex-1 min-w-0">
          <h3 className="text-white font-semibold text-sm mb-1">{feature.title}</h3>
          <p className="text-white/50 text-xs leading-relaxed">{feature.desc}</p>
        </div>

        <motion.div
          animate={{ rotate: expanded ? 90 : 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        >
          <ArrowRight className="w-4 h-4 text-white/30 flex-shrink-0 mt-1" />
        </motion.div>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 250, damping: 25 }}
            className="overflow-hidden"
          >
            <div className="pt-4 mt-4 border-t border-white/10">
              <p className="text-white/60 text-xs leading-relaxed">{feature.detail}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

/* ═══════════════════════════════════════════
   主页面
   ═══════════════════════════════════════════ */

export default function LoginPage() {
  const { login, setGuest } = useAuthStore();
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [regUsername, setRegUsername] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regEmail, setRegEmail] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) { setError('请输入用户名和密码'); return; }
    setLoading(true); setError('');
    try {
      const res: any = await api.login(username, password);
      if (res.success && res.user) {
        api.setToken(res.token);
        login(res.user, res.token);
        // 使用 location.href 确保状态完全更新后再跳转
        window.location.href = '/dashboard';
      } else { setError(res.message || '登录失败'); }
    } catch (err: any) { setError(err.message || '网络错误'); }
    finally { setLoading(false); }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regUsername || !regPassword) { setError('请填写必填项'); return; }
    if (regUsername.length < 3) { setError('用户名至少 3 个字符'); return; }
    if (regPassword.length < 6) { setError('密码至少 6 位'); return; }
    setLoading(true); setError('');
    try {
      const res: any = await api.register(regUsername, regPassword, regEmail || undefined);
      if (res.success) { setIsLogin(true); setError(''); setUsername(regUsername); }
      else { setError(res.message || '注册失败'); }
    } catch (err: any) { setError(err.message || '网络错误'); }
    finally { setLoading(false); }
  };

  const handleGuest = async () => {
    try {
      const res: any = await api.guestLogin();
      if (res.token) api.setToken(res.token);
      setGuest(); window.location.href = '/dashboard';
    } catch { setGuest(); window.location.href = '/dashboard'; }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden bg-[#060d1f]">
      {/* 粒子 + 光球背景 */}
      <FullBackground />

      {/* 主内容 */}
      <div className="relative z-10 w-full max-w-6xl mx-4 flex flex-col lg:flex-row items-center gap-10 lg:gap-16 py-8">

        {/* ═══ 左侧：品牌 + 特性卡片 ═══ */}
        <motion.div
          className="flex-1 text-center lg:text-left w-full"
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ type: 'spring', stiffness: 100, damping: 20 }}
        >
          {/* 标签 */}
          <motion.div
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-cyan-400/20 bg-cyan-400/5 backdrop-blur-sm mb-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ type: 'spring', stiffness: 200, damping: 20, delay: 0.2 }}
          >
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-xs text-cyan-300 tracking-wide">AI 多智能体 · 个性化学习</span>
          </motion.div>

          {/* 标题 */}
          <motion.h1
            className="text-4xl lg:text-5xl xl:text-6xl font-bold text-white mb-4 leading-tight"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ type: 'spring', stiffness: 100, damping: 20, delay: 0.3 }}
          >
            <span className="bg-gradient-to-r from-white via-white to-white/70 bg-clip-text text-transparent">
              多模态 AI
            </span>
            <br />
            <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-amber-400 bg-clip-text text-transparent">
              教学智能体
            </span>
          </motion.h1>

          <motion.p
            className="text-white/40 text-base lg:text-lg mb-8 max-w-lg mx-auto lg:mx-0"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            6 大智能体协同工作，7 种资源类型一键生成，
            <br className="hidden lg:block" />
            构建专属你的沉浸式学习体验
          </motion.p>

          {/* 特性卡片 */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg mx-auto lg:mx-0">
            {features.map((f, i) => (
              <FeatureCard key={f.title} feature={f} index={i} />
            ))}
          </div>
        </motion.div>

        {/* ═══ 右侧：登录/注册表单 ═══ */}
        <motion.div
          className="w-full max-w-md"
          initial={{ opacity: 0, x: 50, scale: 0.95 }}
          animate={{ opacity: 1, x: 0, scale: 1 }}
          transition={{ type: 'spring', stiffness: 100, damping: 20, delay: 0.2 }}
        >
          <div className="
            relative rounded-3xl overflow-hidden
            bg-white/[0.06] backdrop-blur-2xl
            border border-white/[0.08]
            shadow-2xl shadow-black/40
            p-8
          ">
            {/* 卡片顶部光晕 */}
            <div className="absolute -top-20 left-1/2 -translate-x-1/2 w-60 h-20 bg-gradient-to-b from-cyan-400/10 to-transparent rounded-full blur-2xl" />

            {/* Logo */}
            <motion.div
              className="flex items-center justify-center gap-3 mb-8"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 300, damping: 20, delay: 0.4 }}
            >
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
                <GraduationCap className="w-6 h-6 text-white" />
              </div>
              <div>
                <span className="text-lg font-bold text-white block leading-tight">AI 学习助手</span>
                <span className="text-[10px] text-white/30 tracking-widest">INTELLIGENT LEARNING</span>
              </div>
            </motion.div>

            {/* 切换标签 */}
            <div className="flex bg-white/[0.04] rounded-xl p-1 mb-6 border border-white/[0.06]">
              {['登录', '注册'].map((tab, i) => (
                <motion.button
                  key={tab}
                  onClick={() => { setIsLogin(i === 0); setError(''); }}
                  className={`relative flex-1 py-2.5 rounded-lg text-sm font-medium transition-colors duration-200 ${
                    (i === 0 ? isLogin : !isLogin) ? 'text-white' : 'text-white/30 hover:text-white/50'
                  }`}
                  whileTap={{ scale: 0.97 }}
                >
                  {(i === 0 ? isLogin : !isLogin) && (
                    <motion.div
                      layoutId="tab-bg"
                      className="absolute inset-0 rounded-lg bg-white/[0.1] border border-white/[0.1]"
                      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                    />
                  )}
                  <span className="relative z-10">{tab}</span>
                </motion.button>
              ))}
            </div>

            {/* 表单 */}
            <AnimatePresence mode="wait">
              {isLogin ? (
                <motion.form
                  key="login"
                  onSubmit={handleLogin}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ type: 'spring', stiffness: 300, damping: 25 }}
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
                          w-full pl-11 pr-4 py-3 rounded-xl
                          bg-white/[0.04] border border-white/[0.08]
                          text-white text-sm placeholder:text-white/15
                          focus:border-cyan-400/30 focus:bg-white/[0.06]
                          focus:ring-1 focus:ring-cyan-400/20
                          outline-none transition-all duration-200
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
                      w-full py-3.5 rounded-xl
                      bg-gradient-to-r from-cyan-500 to-blue-500
                      text-white font-medium text-sm
                      shadow-lg shadow-cyan-500/20
                      flex items-center justify-center gap-2
                      disabled:opacity-40
                    "
                    whileHover={{ scale: 1.01, boxShadow: '0 0 30px rgba(6,182,212,0.3)' }}
                    whileTap={{ scale: 0.98 }}
                    transition={{ type: 'spring', stiffness: 400, damping: 20 }}
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
                    className="
                      w-full py-3 rounded-xl
                      border border-white/[0.08] bg-white/[0.02]
                      text-white/40 text-sm
                      flex items-center justify-center gap-2
                    "
                    whileHover={{ scale: 1.01, backgroundColor: 'rgba(255,255,255,0.04)' }}
                    whileTap={{ scale: 0.98 }}
                    transition={{ type: 'spring', stiffness: 400, damping: 20 }}
                  >
                    游客模式体验
                  </motion.button>
                </motion.form>
              ) : (
                <motion.form
                  key="register"
                  onSubmit={handleRegister}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ type: 'spring', stiffness: 300, damping: 25 }}
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
                          w-full pl-11 pr-4 py-3 rounded-xl
                          bg-white/[0.04] border border-white/[0.08]
                          text-white text-sm placeholder:text-white/15
                          focus:border-cyan-400/30 focus:bg-white/[0.06]
                          focus:ring-1 focus:ring-cyan-400/20
                          outline-none transition-all duration-200
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
                          w-full pl-11 pr-4 py-3 rounded-xl
                          bg-white/[0.04] border border-white/[0.08]
                          text-white text-sm placeholder:text-white/15
                          focus:border-cyan-400/30 focus:bg-white/[0.06]
                          focus:ring-1 focus:ring-cyan-400/20
                          outline-none transition-all duration-200
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
                          w-full pl-11 pr-4 py-3 rounded-xl
                          bg-white/[0.04] border border-white/[0.08]
                          text-white text-sm placeholder:text-white/15
                          focus:border-cyan-400/30 focus:bg-white/[0.06]
                          focus:ring-1 focus:ring-cyan-400/20
                          outline-none transition-all duration-200
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
                      w-full py-3.5 rounded-xl
                      bg-gradient-to-r from-cyan-500 to-blue-500
                      text-white font-medium text-sm
                      shadow-lg shadow-cyan-500/20
                      flex items-center justify-center gap-2
                      disabled:opacity-40
                    "
                    whileHover={{ scale: 1.01, boxShadow: '0 0 30px rgba(6,182,212,0.3)' }}
                    whileTap={{ scale: 0.98 }}
                    transition={{ type: 'spring', stiffness: 400, damping: 20 }}
                  >
                    {loading ? (
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : '注册账号'}
                  </motion.button>
                </motion.form>
              )}
            </AnimatePresence>

            {/* 底部装饰线 */}
            <div className="mt-6 pt-4 border-t border-white/[0.04] text-center">
              <p className="text-[10px] text-white/15 tracking-widest">
                POWERED BY MULTI-AGENT AI SYSTEM
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
