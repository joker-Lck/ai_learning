'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores';
import api from '@/lib/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Send, User, Brain, Target, BookOpen,
  Lightbulb, Code, BarChart3, Clock,
  Sparkles, Loader2, CheckCircle, ChevronRight, ChevronLeft,
  FileText
} from 'lucide-react';

// 画像维度定义
const PROFILE_DIMENSIONS = [
  {
    id: 'basic_info',
    title: '基本信息',
    icon: User,
    color: 'from-cyan-500 to-blue-500',
    questions: [
      '请问您的专业是什么？',
      '您目前是大几的学生？'
    ],
    placeholder: '例如：计算机科学与技术，大三'
  },
  {
    id: 'knowledge_base',
    title: '知识基础',
    icon: BookOpen,
    color: 'from-violet-500 to-purple-500',
    questions: [
      '您对当前学科的基础如何？（初学者/有一定基础/较扎实）',
      '您已经学习了哪些相关课程或知识点？'
    ],
    placeholder: '例如：我已经学习了Python编程、数据结构，对机器学习有初步了解'
  },
  {
    id: 'cognitive_style',
    title: '认知风格',
    icon: Brain,
    color: 'from-emerald-500 to-teal-500',
    questions: [
      '您更喜欢哪种学习方式？（视觉型：看图表视频 / 听觉型：听讲解 / 动觉型：动手实践）',
      '您喜欢独自学习还是小组讨论？'
    ],
    placeholder: '例如：我更喜欢看图表和视频来理解概念，也喜欢动手实践'
  },
  {
    id: 'learning_goals',
    title: '学习目标',
    icon: Target,
    color: 'from-amber-500 to-orange-500',
    questions: [
      '您学习这门课程的主要目标是什么？',
      '您希望在多长时间内达到什么水平？'
    ],
    placeholder: '例如：我希望在3个月内掌握机器学习基础，能够独立完成简单项目'
  },
  {
    id: 'weak_points',
    title: '薄弱点与困难',
    icon: Lightbulb,
    color: 'from-rose-500 to-red-500',
    questions: [
      '您在学习中遇到的最大困难是什么？',
      '有哪些知识点让您感到困惑？'
    ],
    placeholder: '例如：我对数学推导感到困难，特别是微积分和线性代数部分'
  },
  {
    id: 'interest_areas',
    title: '兴趣领域',
    icon: Sparkles,
    color: 'from-indigo-500 to-violet-500',
    questions: [
      '您对哪些应用领域最感兴趣？（如：自然语言处理、计算机视觉、推荐系统等）',
      '您有没有特别想做的个人项目？'
    ],
    placeholder: '例如：我对计算机视觉很感兴趣，想做一个人脸识别的项目'
  }
];

interface DimensionChat {
  dimensionId: string;
  messages: Array<{ role: 'user' | 'assistant'; content: string }>;
  completed: boolean;
}

interface ProfileData {
  knowledge_base: any;
  cognitive_style: string;
  learning_goals: any;
  weak_points: string[];
  learning_history: any[];
  interest_areas: string[];
  preferred_resources: string[];
  major: string;
  grade_level: string;
  update_time?: string;
  summary?: string;
}

export default function ProfilePage() {
  const router = useRouter();
  const { user, isGuest } = useAuthStore();

  // 当前步骤索引
  const [currentStep, setCurrentStep] = useState(0);

  // 每个维度的聊天记录
  const [dimensionChats, setDimensionChats] = useState<Record<string, DimensionChat>>({});

  // 当前输入值
  const [inputValue, setInputValue] = useState('');

  // 加载状态
  const [loading, setLoading] = useState(false);
  const [profileLoading, setProfileLoading] = useState(false);

  // 最终画像数据
  const [profile, setProfile] = useState<ProfileData | null>(null);

  // 初始化当前维度的聊天
  const currentDimension = PROFILE_DIMENSIONS[currentStep];
  const currentChat = dimensionChats[currentDimension.id] || {
    dimensionId: currentDimension.id,
    messages: [{
      role: 'assistant',
      content: currentDimension.questions[0]
    }],
    completed: false
  };

  // 更新当前维度的聊天
  const updateCurrentChat = (messages: Array<{ role: 'user' | 'assistant'; content: string }>, completed = false) => {
    setDimensionChats(prev => ({
      ...prev,
      [currentDimension.id]: {
        dimensionId: currentDimension.id,
        messages,
        completed
      }
    }));
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || loading) return;

    const userMessage = { role: 'user' as const, content: inputValue.trim() };
    const newMessages = [...currentChat.messages, userMessage];

    setInputValue('');
    setLoading(true);

    try {
      // 模拟AI回复
      setTimeout(() => {
        let aiResponse = '';

        // 根据当前问题生成回复
        const currentQuestionIndex = currentChat.messages.filter(m => m.role === 'assistant').length - 1;

        if (currentQuestionIndex < currentDimension.questions.length - 1) {
          // 还有下一个问题
          aiResponse = currentDimension.questions[currentQuestionIndex + 1];
        } else {
          // 该维度完成
          aiResponse = `✅ 好的，我已经记录了您的${currentDimension.title}信息。`;
          updateCurrentChat([...newMessages, { role: 'assistant', content: aiResponse }], true);
          setLoading(false);
          return;
        }

        updateCurrentChat([...newMessages, { role: 'assistant', content: aiResponse }]);
        setLoading(false);
      }, 800);
    } catch (err) {
      setLoading(false);
    }
  };

  const handleNext = () => {
    if (!currentChat.completed) {
      alert('请先完成当前维度的对话');
      return;
    }

    if (currentStep < PROFILE_DIMENSIONS.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const buildProfile = async () => {
    // 检查是否所有维度都完成
    const allCompleted = PROFILE_DIMENSIONS.every(dim =>
      dimensionChats[dim.id]?.completed
    );

    if (!allCompleted) {
      alert('请完成所有维度的对话后再构建画像');
      return;
    }

    setProfileLoading(true);

    try {
      // 收集所有维度的对话记录
      const conversationLog = Object.values(dimensionChats).flatMap(chat => chat.messages);

      console.log('🚀 开始构建学生画像（后端智能体）...');

      // 通过后端画像智能体构建（经过验证 + 持久化）
      const response: any = await api.buildProfile(conversationLog);

      if (response?.success && response?.data?.profile) {
        const profileData = response.data.profile;
        console.log('✅ 画像构建成功:', profileData);
        setProfile(profileData);
      } else {
        console.warn('画像构建返回异常:', response?.message);
        alert(response?.message || '画像构建失败，请重试');
      }
    } catch (err: any) {
      console.error('构建画像失败:', err);
      alert('构建画像失败：' + (err.message || '网络错误'));
    } finally {
      setProfileLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* 页面标题 */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: 'spring', stiffness: 200, damping: 25 }}
        className="mb-6"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
            <Target className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">对话式学生画像构建</h1>
            <p className="text-sm text-white/60">通过6个维度的对话，自动构建个性化学习画像</p>
          </div>
        </div>
      </motion.div>

      {/* 进度指示器 */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ type: 'spring', stiffness: 200, damping: 25 }}
        className="mb-6 bg-white/[0.04] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-4"
      >
        <div className="flex items-center justify-between">
          {PROFILE_DIMENSIONS.map((dim, idx) => {
            const Icon = dim.icon;
            const isCompleted = dimensionChats[dim.id]?.completed;
            const isCurrent = idx === currentStep;

            return (
              <div key={dim.id} className="flex items-center">
                <div className="flex flex-col items-center">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                    isCompleted ? 'bg-emerald-500 text-white' :
                    isCurrent ? `bg-gradient-to-r ${dim.color} text-white` :
                    'bg-white/[0.06] text-white/30'
                  }`}>
                    {isCompleted ? <CheckCircle className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
                  </div>
                  <span className={`text-xs mt-1 ${isCurrent ? 'font-semibold text-white' : 'text-white/40'}`}>
                    {dim.title}
                  </span>
                </div>
                {idx < PROFILE_DIMENSIONS.length - 1 && (
                  <div className={`w-8 h-0.5 mx-2 ${
                    isCompleted ? 'bg-emerald-500' : 'bg-white/[0.08]'
                  }`} />
                )}
              </div>
            );
          })}
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 左侧：当前维度对话区域 */}
        <motion.div
          key={currentDimension.id}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ type: 'spring', stiffness: 200, damping: 25 }}
          className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.06] rounded-2xl overflow-hidden"
        >
          <div className={`p-4 border-b border-white/[0.06] bg-gradient-to-r ${currentDimension.color} text-white`}>
            <div className="flex items-center gap-2">
              <currentDimension.icon className="w-5 h-5" />
              <h2 className="font-bold">{currentDimension.title}</h2>
              <span className="text-xs opacity-80 ml-auto">
                步骤 {currentStep + 1}/{PROFILE_DIMENSIONS.length}
              </span>
            </div>
          </div>

          {/* 对话消息列表 */}
          <div className="h-96 overflow-y-auto p-4 space-y-4">
            <AnimatePresence mode="wait">
              {currentChat.messages.map((msg, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ type: 'spring', stiffness: 200, damping: 25 }}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    msg.role === 'user'
                      ? `bg-gradient-to-r ${currentDimension.color} text-white`
                      : 'bg-white/[0.06] text-white/80'
                  }`}>
                    <p className="text-sm">{msg.content}</p>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {loading && (
              <div className="flex justify-start">
                <div className="bg-white/[0.06] rounded-2xl px-4 py-3">
                  <Loader2 className="w-5 h-5 animate-spin text-white/40" />
                </div>
              </div>
            )}
          </div>

          {/* 输入区域 */}
          <div className="p-4 border-t border-white/[0.06]">
            <div className="flex gap-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={currentDimension.placeholder}
                className="flex-1 px-4 py-2 bg-white/[0.04] border border-white/[0.08] text-white text-sm placeholder:text-white/15 focus:border-cyan-400/30 focus:ring-1 focus:ring-cyan-400/20 outline-none rounded-xl"
                disabled={loading || isGuest || currentChat.completed}
              />
              <button
                onClick={handleSendMessage}
                disabled={loading || isGuest || !inputValue.trim() || currentChat.completed}
                className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>

            {/* 导航按钮 */}
            <div className="flex gap-2 mt-3">
              <button
                onClick={handlePrevious}
                disabled={currentStep === 0}
                className="flex-1 px-4 py-2 border border-white/[0.08] bg-white/[0.02] text-white/40 rounded-xl hover:bg-white/[0.06] transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm flex items-center justify-center gap-2"
              >
                <ChevronLeft className="w-4 h-4" />
                上一步
              </button>

              {currentStep < PROFILE_DIMENSIONS.length - 1 ? (
                <button
                  onClick={handleNext}
                  disabled={!currentChat.completed}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm flex items-center justify-center gap-2"
                >
                  下一步
                  <ChevronRight className="w-4 h-4" />
                </button>
              ) : (
                <button
                  onClick={buildProfile}
                  disabled={profileLoading || isGuest}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-violet-500 to-purple-500 text-white rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm flex items-center justify-center gap-2"
                >
                  {profileLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      构建中...
                    </>
                  ) : (
                    <>
                      <Brain className="w-4 h-4" />
                      构建画像
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </motion.div>

        {/* 右侧：画像展示 */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ type: 'spring', stiffness: 200, damping: 25 }}
          className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-6"
        >
          <div className="mb-4">
            <h2 className="font-bold text-white flex items-center gap-2">
              <Target className="w-5 h-5 text-cyan-400" />
              学生画像
            </h2>
            <p className="text-xs text-white/30 mt-1">
              8维度动态画像特征
            </p>
          </div>

          {!profile ? (
            <div className="text-center text-white/30 py-12">
              <Brain className="w-16 h-16 mx-auto mb-4 opacity-20" />
              <p>完成对话后构建画像</p>
              <p className="text-xs mt-2">画像将展示8维度学习特征</p>
            </div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ type: 'spring', stiffness: 200, damping: 25 }}
              className="space-y-4"
            >
              {/* 画像综合分析报告 (Markdown) */}
              {profile.summary && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ type: 'spring', stiffness: 200, damping: 25 }}
                  className="p-5 bg-gradient-to-br from-cyan-400/[0.06] via-violet-400/[0.06] to-pink-400/[0.06] rounded-xl border border-white/[0.06]">
                  <div className="flex items-center gap-2 mb-3">
                    <FileText className="w-4 h-4 text-violet-400" />
                    <span className="text-sm font-bold text-white">画像综合分析报告</span>
                  </div>
                  <div className="prose prose-sm max-w-none prose-invert prose-headings:text-white prose-h3:text-base prose-p:text-white/60 prose-li:text-white/60 prose-strong:text-white/80">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{profile.summary}</ReactMarkdown>
                  </div>
                </motion.div>
              )}

              {/* 基本信息 */}
              <div className="p-4 bg-cyan-400/[0.06] rounded-xl border border-white/[0.06]">
                <div className="flex items-center gap-2 mb-2">
                  <User className="w-4 h-4 text-cyan-400" />
                  <span className="text-sm font-semibold text-white">基本信息</span>
                </div>
                <p className="text-sm text-white/60">
                  {profile.major} - {profile.grade_level}
                </p>
              </div>

              {/* 知识基础 */}
              <div className="p-4 bg-violet-400/[0.06] rounded-xl border border-white/[0.06]">
                <div className="flex items-center gap-2 mb-2">
                  <BookOpen className="w-4 h-4 text-violet-400" />
                  <span className="text-sm font-semibold text-white">知识基础</span>
                </div>
                <p className="text-sm text-white/60">
                  {typeof profile.knowledge_base === 'string'
                    ? profile.knowledge_base
                    : JSON.stringify(profile.knowledge_base)}
                </p>
              </div>

              {/* 认知风格 */}
              <div className="p-4 bg-emerald-400/[0.06] rounded-xl border border-white/[0.06]">
                <div className="flex items-center gap-2 mb-2">
                  <Brain className="w-4 h-4 text-emerald-400" />
                  <span className="text-sm font-semibold text-white">认知风格</span>
                </div>
                <p className="text-sm text-white/60">{profile.cognitive_style}</p>
              </div>

              {/* 学习目标 */}
              <div className="p-4 bg-amber-400/[0.06] rounded-xl border border-white/[0.06]">
                <div className="flex items-center gap-2 mb-2">
                  <Target className="w-4 h-4 text-amber-400" />
                  <span className="text-sm font-semibold text-white">学习目标</span>
                </div>
                <p className="text-sm text-white/60">
                  {Array.isArray(profile.learning_goals)
                    ? profile.learning_goals.join('、')
                    : typeof profile.learning_goals === 'string'
                    ? profile.learning_goals
                    : JSON.stringify(profile.learning_goals)}
                </p>
              </div>

              {/* 薄弱点 */}
              <div className="p-4 bg-red-400/[0.06] rounded-xl border border-white/[0.06]">
                <div className="flex items-center gap-2 mb-2">
                  <Lightbulb className="w-4 h-4 text-red-400" />
                  <span className="text-sm font-semibold text-white">薄弱点</span>
                </div>
                {profile.weak_points && profile.weak_points.length > 0 ? (
                  <ul className="mt-2 space-y-1">
                    {profile.weak_points.map((point, idx) => (
                      <li key={idx} className="text-xs text-red-400/80 flex items-start gap-1">
                        <span className="text-red-400 mt-0.5">!</span>
                        {point}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-white/30">暂无记录</p>
                )}
              </div>

              {/* 兴趣领域 */}
              <div className="p-4 bg-indigo-400/[0.06] rounded-xl border border-white/[0.06]">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                  <span className="text-sm font-semibold text-white">兴趣领域</span>
                </div>
                {profile.interest_areas && profile.interest_areas.length > 0 ? (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {profile.interest_areas.map((area, idx) => (
                      <span key={idx} className="px-3 py-1 bg-indigo-400/[0.1] text-indigo-400 rounded-full text-xs">
                        {area}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-white/30">暂无记录</p>
                )}
              </div>

              {/* 资源偏好 */}
              <div className="p-4 bg-cyan-400/[0.06] rounded-xl border border-white/[0.06]">
                <div className="flex items-center gap-2 mb-2">
                  <Code className="w-4 h-4 text-cyan-400" />
                  <span className="text-sm font-semibold text-white">资源偏好</span>
                </div>
                {profile.preferred_resources && profile.preferred_resources.length > 0 ? (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {profile.preferred_resources.map((res, idx) => (
                      <span key={idx} className="px-3 py-1 bg-cyan-400/[0.1] text-cyan-400 rounded-full text-xs">
                        {res}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-white/30">暂无记录</p>
                )}
              </div>
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
