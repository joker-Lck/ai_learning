'use client';

import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/stores';
import api from '@/lib/api';
import { generateMindmap, generateQuiz, generateDocument, tutorAnswer, generateLearningPath } from '@/lib/kimi-api';
import {
  Sparkles, TrendingUp, Users, Send, User, Brain, Target, BookOpen,
  Lightbulb, Code, BarChart3, Clock, Loader2, ArrowRight, Zap,
  Route, FileText, GitBranch, FileCode, Video, CheckCircle, Circle,
  MessageSquare, Image, Award, AlertCircle, GraduationCap, Shield, UserCheck,
  ChevronRight, ChevronLeft, Upload, X
} from 'lucide-react';

// 画像维度定义
const PROFILE_DIMENSIONS = [
  {
    id: 'basic_info',
    title: '基本信息',
    icon: User,
    color: 'from-blue-500 to-cyan-500',
    questions: ['请问您的专业是什么？', '您目前是大几的学生？'],
    placeholder: '例如：计算机科学与技术，大三'
  },
  {
    id: 'knowledge_base',
    title: '知识基础',
    icon: BookOpen,
    color: 'from-purple-500 to-pink-500',
    questions: ['您对当前学科的基础如何？', '您已经学习了哪些相关课程？'],
    placeholder: '例如：已学习Python、数据结构'
  },
  {
    id: 'cognitive_style',
    title: '认知风格',
    icon: Brain,
    color: 'from-green-500 to-emerald-500',
    questions: ['您更喜欢哪种学习方式？', '喜欢独自学习还是小组讨论？'],
    placeholder: '例如：喜欢看图表和视频'
  },
  {
    id: 'learning_goals',
    title: '学习目标',
    icon: Target,
    color: 'from-orange-500 to-red-500',
    questions: ['您学习的主要目标是什么？', '希望多长时间达到什么水平？'],
    placeholder: '例如：3个月内掌握机器学习基础'
  },
  {
    id: 'weak_points',
    title: '薄弱点',
    icon: Lightbulb,
    color: 'from-yellow-500 to-amber-500',
    questions: ['学习中遇到的最大困难是什么？', '哪些知识点让您困惑？'],
    placeholder: '例如：数学推导感到困难'
  },
  {
    id: 'interest_areas',
    title: '兴趣领域',
    icon: Sparkles,
    color: 'from-indigo-500 to-purple-500',
    questions: ['对哪些应用领域感兴趣？', '有没有特别想做的个人项目？'],
    placeholder: '例如：对计算机视觉感兴趣'
  }
];

interface DimensionChat {
  dimensionId: string;
  messages: Array<{ role: 'user' | 'assistant'; content: string }>;
  completed: boolean;
}

// 功能模块类型
type ModuleType = 'profile' | 'resources' | 'path' | 'tutor' | 'assessment' | null;

interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
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
}

interface ResourceItem {
  type: string;
  title: string;
  content_data?: any;  // 修复：使用content_data而不是content
  status: 'generating' | 'complete' | 'error';
}

interface PathStep {
  step_number: number;
  title: string;
  description: string;
  estimated_time: string;
  resources: string[];
  prerequisites: string[];
}

interface LearningPath {
  goal: string;
  total_steps: number;
  estimated_duration: string;
  steps: PathStep[];
}

interface TutorMessage {
  role: 'user' | 'assistant';
  content: string;
  diagram?: string;
  example?: string;
  timestamp: Date;
}

interface AssessmentResult {
  overall_score: number;
  dimensions: Array<{
    name: string;
    score: number;
    max_score: number;
    level: string;
    feedback: string;
  }>;
  strengths: string[];
  improvements: string[];
  recommendations: string[];
}

const stats = [
  { label: '多智能体协同', value: '6个', icon: Brain, color: 'text-purple-400' },
  { label: '资源类型', value: '7种', icon: Users, color: 'text-blue-400' },
  { label: '画像维度', value: '8维', icon: Shield, color: 'text-cyan-400' },
  { label: '防幻觉机制', value: '3层', icon: TrendingUp, color: 'text-emerald-400' },
];

export default function DashboardContent() {
  const { user, isGuest } = useAuthStore();
  const searchParams = useSearchParams();

  // 从 URL 参数读取模块类型
  const moduleParam = searchParams.get('module') as ModuleType;
  const [activeModule, setActiveModule] = useState<ModuleType>(null);

  // 当 URL 参数变化时，自动切换模块
  useEffect(() => {
    if (moduleParam) {
      setActiveModule(moduleParam);
    } else {
      // 没有module参数时，清除activeModule，显示工作台
      setActiveModule(null);
    }
  }, [moduleParam]);

  // 画像构建状态 - 6维度多轮对话
  const [currentStep, setCurrentStep] = useState(0);
  const [dimensionChats, setDimensionChats] = useState<Record<string, DimensionChat>>({});
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileData, setProfileData] = useState<ProfileData | null>(null);

  // 获取当前维度对话
  const currentDimension = PROFILE_DIMENSIONS[currentStep];
  const currentChat = dimensionChats[currentDimension?.id] || {
    dimensionId: currentDimension?.id,
    messages: [{
      role: 'assistant' as const,
      content: currentDimension?.questions[0] || ''
    }],
    completed: false
  };

  // 更新当前维度对话
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

  // 资源生成状态
  const [subject, setSubject] = useState('机器学习');
  const [topic, setTopic] = useState('神经网络');
  const [selectedTypes, setSelectedTypes] = useState<string[]>(['document', 'quiz', 'mindmap']);
  const [difficulty, setDifficulty] = useState('intermediate');
  const [resourceLoading, setResourceLoading] = useState(false);
  const [resources, setResources] = useState<ResourceItem[]>([]);

  // 学习路径状态
  const [learningGoal, setLearningGoal] = useState('掌握深度学习基础');
  const [pathLoading, setPathLoading] = useState(false);
  const [learningPath, setLearningPath] = useState<LearningPath | null>(null);

  // 智能辅导状态
  const [question, setQuestion] = useState('');
  const [tutorSubject, setTutorSubject] = useState('机器学习');
  const [tutorLoading, setTutorLoading] = useState(false);
  const [tutorMessages, setTutorMessages] = useState<TutorMessage[]>([]);

  // 学习评估状态
  const [assessLoading, setAssessLoading] = useState(false);
  const [assessment, setAssessment] = useState<AssessmentResult | null>(null);
  const [assessTab, setAssessTab] = useState<'assess' | 'analyze'>('assess');

  // 资料分析状态
  const [analysisFiles, setAnalysisFiles] = useState<File[]>([]);
  const [analysisDragOver, setAnalysisDragOver] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const analysisFileInputRef = useRef<HTMLInputElement>(null);
  const [analysisSubject, setAnalysisSubject] = useState('');
  const [analysisTopic, setAnalysisTopic] = useState('');
  const [analysisDifficulty, setAnalysisDifficulty] = useState('intermediate');

  // 处理画像构建 - 6维度多轮对话
  const handleSendMessage = async () => {
    const inputValue = (document.getElementById('profile-input') as HTMLInputElement)?.value;
    if (!inputValue?.trim()) return;

    const userMessage = { role: 'user' as const, content: inputValue.trim() };
    const newMessages = [...currentChat.messages, userMessage];

    // 清空输入框
    (document.getElementById('profile-input') as HTMLInputElement).value = '';

    setProfileLoading(true);

    setTimeout(() => {
      let aiResponse = '';
      const currentQuestionIndex = currentChat.messages.filter(m => m.role === 'assistant').length - 1;

      if (currentQuestionIndex < currentDimension.questions.length - 1) {
        // 还有问题要问
        aiResponse = currentDimension.questions[currentQuestionIndex + 1];
        updateCurrentChat([...newMessages, { role: 'assistant', content: aiResponse }]);
      } else {
        // 当前维度完成
        aiResponse = `✅ 好的，我已经记录了您的${currentDimension.title}信息。`;
        updateCurrentChat([...newMessages, { role: 'assistant', content: aiResponse }], true);

        // 自动进入下一个维度
        setTimeout(() => {
          if (currentStep < PROFILE_DIMENSIONS.length - 1) {
            setCurrentStep(prev => prev + 1);
          } else {
            // 所有维度完成，构建画像
            buildFinalProfile();
          }
        }, 1000);
      }

      setProfileLoading(false);
    }, 800);
  };

  // 构建最终画像 — 通过后端画像智能体
  const buildFinalProfile = async () => {
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
        setProfileData(profileData);
      } else {
        console.warn('画像构建返回异常:', response?.message);
        alert(response?.message || '画像构建失败，请重试');
      }
    } catch (error: any) {
      console.error('构建画像失败:', error);
      alert('构建画像失败：' + (error.message || '网络错误'));
    } finally {
      setProfileLoading(false);
    }
  };

  // 上一步
  const goToPreviousStep = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  };

  // 下一步
  const goToNextStep = () => {
    if (currentStep < PROFILE_DIMENSIONS.length - 1) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleGenerateResources = async () => {
    if (selectedTypes.length === 0) {
      alert('请至少选择一种资源类型');
      return;
    }

    setResourceLoading(true);
    setResources([]);

    try {
      // 前端直接调用AI生成资源
      console.log('🚀 开始前端AI资源生成:', { subject, topic, selectedTypes, difficulty });

      const generatedResources: ResourceItem[] = [];

      // 并行生成所有选中的资源类型
      const generationPromises = selectedTypes.map(async (type): Promise<ResourceItem | null> => {
        try {
          let contentData: any = {};

          switch (type) {
            case 'mindmap':
              contentData = await generateMindmap(subject, topic, difficulty);
              break;

            case 'quiz':
              contentData = await generateQuiz(subject, topic, difficulty);
              break;

            case 'document':
              contentData = await generateDocument(subject, topic, difficulty);
              break;

            default:
              console.warn(`未知的资源类型: ${type}`);
              return null;
          }

          console.log(`✅ ${type} 生成成功:`, contentData.title || type);

          return {
            type,
            title: contentData.title || `${topic}${getTypeName(type)}`,
            content_data: contentData,
            status: 'complete' as const
          };
        } catch (error: any) {
          console.error(`❌ ${type} 生成失败:`, error);
          return {
            type,
            title: `${topic}${getTypeName(type)}(生成失败)`,
            content_data: { error: error.message },
            status: 'error' as const
          };
        }
      });

      const results = await Promise.all(generationPromises);
      const validResults = results.filter((r): r is ResourceItem => r !== null && r !== undefined);

      console.log('✅ 所有资源生成完成:', validResults.length);
      setResources(validResults);

    } catch (error: any) {
      console.error('资源生成失败:', error);
      alert(`资源生成失败: ${error.message}`);
    } finally {
      setResourceLoading(false);
    }
  };

  // 获取资源类型中文名
  const getTypeName = (type: string) => {
    const names: Record<string, string> = {
      mindmap: '思维导图',
      quiz: '练习题',
      document: '讲解文档'
    };
    return names[type] || type;
  };

  const handlePlanPath = async () => {
    setPathLoading(true);

    try {
      console.log('🚀 开始生成学习路径:', { learningGoal });

      // 前端直接调用AI生成学习路径
      const pathData = await generateLearningPath(learningGoal, profileData);

      console.log('✅ 学习路径生成成功:', pathData);

      if (pathData) {
        setLearningPath(pathData);
      }
    } catch (error: any) {
      console.error('规划路径失败:', error);
    } finally {
      setPathLoading(false);
    }
  };

  const handleAskTutor = async () => {
    if (!question.trim()) return;

    const userMessage: TutorMessage = {
      role: 'user',
      content: question.trim(),
      timestamp: new Date()
    };
    setTutorMessages(prev => [...prev, userMessage]);
    setQuestion('');
    setTutorLoading(true);

    try {
      console.log('🚀 开始AI辅导答疑:', { question: question.trim(), subject: tutorSubject });

      // 前端直接调用AI进行辅导
      const answerData = await tutorAnswer(question.trim(), tutorSubject, 'all');

      console.log('✅ 辅导回答生成成功');

      const assistantMessage: TutorMessage = {
        role: 'assistant',
        content: answerData.text_answer,
        diagram: answerData.diagram || undefined,
        example: answerData.code_example || undefined,
        timestamp: new Date()
      };
      setTutorMessages(prev => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error('❌ 提问失败:', error);
      setTutorMessages(prev => [...prev, {
        role: 'assistant',
        content: `️ 回答失败: ${error.message}`,
        timestamp: new Date()
      }]);
    } finally {
      setTutorLoading(false);
    }
  };

  const handleAssess = async () => {
    setAssessLoading(true);

    try {
      const res: any = await api.assess({
        user_id: 1,
        assessment_type: 'comprehensive'
      });

      if (res.success) {
        setAssessment(res.data.assessment);
      }
    } catch (error: any) {
      console.error('评估失败:', error);
    } finally {
      setAssessLoading(false);
    }
  };

  // 资料分析相关函数
  const addAnalysisFiles = (fileList: FileList) => {
    const newFiles = Array.from(fileList).filter(f => f.size <= 10 * 1024 * 1024);
    setAnalysisFiles(prev => {
      const combined = [...prev, ...newFiles];
      return combined.slice(0, 10);
    });
  };

  const removeAnalysisFile = (idx: number) => {
    setAnalysisFiles(prev => prev.filter((_, i) => i !== idx));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getFileIcon = (name: string) => {
    const ext = name.split('.').pop()?.toLowerCase();
    if (['jpg', 'jpeg', 'png', 'gif'].includes(ext || '')) return '🖼️';
    if (['pdf'].includes(ext || '')) return '📕';
    if (['doc', 'docx'].includes(ext || '')) return '📘';
    if (['ppt', 'pptx'].includes(ext || '')) return '📙';
    if (['md'].includes(ext || '')) return '📗';
    return '📄';
  };

  const handleAnalyze = async () => {
    if (analysisFiles.length === 0) return;
    setAnalyzing(true);
    setAnalysisResult(null);

    try {
      const res: any = await api.uploadAndAnalyze(analysisFiles, {
        subject: analysisSubject || undefined,
        topic: analysisTopic || undefined,
        difficulty: analysisDifficulty,
      });

      if (res.success) {
        setAnalysisResult(res.data.analysis);
      }
    } catch (err: any) {
      console.error('分析失败:', err);
    } finally {
      setAnalyzing(false);
    }
  };

  // 渲染各个模块
  const renderModule = () => {
    switch (activeModule) {
      case 'profile':
        return (
          <div className="space-y-4">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
                <Target className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">对话式学生画像构建</h3>
                <p className="text-sm text-white/40">通过6个维度的对话，自动构建个性化学习画像</p>
              </div>
            </div>

            {/* 进度指示器 */}
            <div className="glass-card rounded-xl p-3">
              <div className="flex items-center justify-between">
                {PROFILE_DIMENSIONS.map((dim, idx) => {
                  const Icon = dim.icon;
                  const isCompleted = dimensionChats[dim.id]?.completed;
                  const isCurrent = idx === currentStep;

                  return (
                    <div key={dim.id} className="flex items-center">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${
                        isCompleted ? 'bg-cyan-500 text-white' :
                        isCurrent ? `bg-gradient-to-r ${dim.color} text-white` :
                        'bg-white/[0.08] text-white/30'
                      }`}>
                        {isCompleted ? <CheckCircle className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
                      </div>
                      {idx < PROFILE_DIMENSIONS.length - 1 && (
                        <div className={`w-4 h-0.5 mx-1 ${
                          isCompleted ? 'bg-cyan-500' : 'bg-white/[0.08]'
                        }`} />
                      )}
                    </div>
                  );
                })}
              </div>
              <div className="flex justify-between mt-1 text-xs text-white/30">
                {PROFILE_DIMENSIONS.map((dim, idx) => (
                  <span key={dim.id} className={idx === currentStep ? 'font-semibold text-white' : ''}>
                    {dim.title}
                  </span>
                ))}
              </div>
            </div>

            {/* 当前维度对话区域 */}
            <div className="glass-card rounded-xl overflow-hidden">
              <div className={`p-3 border-b border-white/[0.06] bg-gradient-to-r ${currentDimension.color} text-white`}>
                <div className="flex items-center gap-2">
                  <currentDimension.icon className="w-5 h-5" />
                  <h4 className="font-bold">{currentDimension.title}</h4>
                  <span className="text-xs opacity-80 ml-auto">
                    步骤 {currentStep + 1}/{PROFILE_DIMENSIONS.length}
                  </span>
                </div>
              </div>

              {/* 对话消息列表 */}
              <div className="h-64 overflow-y-auto p-4 space-y-3">
                {currentChat.messages.map((msg: any, idx: number) => (
                  <div
                    key={idx}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`max-w-[80%] rounded-xl px-3 py-2 text-sm ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white'
                        : 'bg-white/[0.06] text-white/80'
                    }`}>
                      {msg.content}
                    </div>
                  </div>
                ))}

                {profileLoading && (
                  <div className="flex justify-start">
                    <div className="bg-white/[0.06] rounded-xl px-3 py-2">
                      <Loader2 className="w-4 h-4 animate-spin text-white/30 border-white/30 border-t-cyan-400" />
                    </div>
                  </div>
                )}
              </div>

              {/* 输入区域 */}
              <div className="p-3 border-t border-white/[0.06]">
                <div className="flex gap-2">
                  <input
                    id="profile-input"
                    type="text"
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder={currentDimension.placeholder}
                    className="flex-1 px-3 py-2 bg-white/[0.04] border border-white/[0.08] text-white placeholder:text-white/15 rounded-lg focus:border-cyan-400/30 focus:outline-none text-sm"
                    disabled={profileLoading}
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={profileLoading}
                    className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                  >
                    {profileLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                    发送
                  </button>
                </div>

                {/* 导航按钮 */}
                <div className="flex justify-between mt-2">
                  <button
                    onClick={goToPreviousStep}
                    disabled={currentStep === 0}
                    className="px-3 py-1 text-sm text-white/40 hover:bg-white/[0.04] rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                  >
                    <ChevronLeft className="w-4 h-4" />
                    上一步
                  </button>
                  <button
                    onClick={goToNextStep}
                    disabled={currentStep === PROFILE_DIMENSIONS.length - 1}
                    className="px-3 py-1 text-sm text-white/40 hover:bg-white/[0.04] rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                  >
                    下一步
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* 画像预览 */}
            {profileData && (
              <div className="glass-card rounded-xl p-4 border-cyan-400/20">
                <h4 className="font-bold text-cyan-400 mb-3">学生画像</h4>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div><span className="font-semibold text-white">专业:</span> <span className="text-white/60">{profileData.major}</span></div>
                  <div><span className="font-semibold text-white">年级:</span> <span className="text-white/60">{profileData.grade_level}</span></div>
                  <div className="col-span-2"><span className="font-semibold text-white">知识基础:</span> <span className="text-white/60">{profileData.knowledge_base}</span></div>
                  <div className="col-span-2"><span className="font-semibold text-white">认知风格:</span> <span className="text-white/60">{profileData.cognitive_style}</span></div>
                  <div className="col-span-2"><span className="font-semibold text-white">学习目标:</span> <span className="text-white/60">{profileData.learning_goals}</span></div>
                  {profileData.weak_points?.length > 0 && (
                    <div className="col-span-2"><span className="font-semibold text-white">薄弱点:</span> <span className="text-white/60">{profileData.weak_points.join(', ')}</span></div>
                  )}
                  {profileData.interest_areas?.length > 0 && (
                    <div className="col-span-2"><span className="font-semibold text-white">兴趣领域:</span> <span className="text-white/60">{profileData.interest_areas.join(', ')}</span></div>
                  )}
                </div>
              </div>
            )}
          </div>
        );

      case 'resources':
        return (
          <div className="space-y-4">
            <h3 className="text-xl font-bold text-white">多智能体资源生成</h3>

            <div className="glass-card rounded-xl p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-white/60 mb-1">学科</label>
                  <input
                    type="text"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    className="w-full px-3 py-2 bg-white/[0.04] border border-white/[0.08] text-white placeholder:text-white/15 rounded-lg focus:border-cyan-400/30 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-white/60 mb-1">主题</label>
                  <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    className="w-full px-3 py-2 bg-white/[0.04] border border-white/[0.08] text-white placeholder:text-white/15 rounded-lg focus:border-cyan-400/30 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-white/60 mb-2">资源类型</label>
                <div className="flex flex-wrap gap-2">
                  {[
                    { id: 'document', label: ' 文档', icon: FileText },
                    { id: 'mindmap', label: ' 思维导图', icon: GitBranch },
                    { id: 'quiz', label: ' 题库', icon: FileCode },
                    { id: 'video', label: '🎥 视频', icon: Video },
                    { id: 'animation', label: '✨ 动画', icon: Sparkles },
                    { id: 'code', label: '💻 代码', icon: Code },
                    { id: 'reading', label: '📖 阅读', icon: BookOpen }
                  ].map(type => (
                    <button
                      key={type.id}
                      onClick={() => {
                        setSelectedTypes(prev =>
                          prev.includes(type.id)
                            ? prev.filter(t => t !== type.id)
                            : [...prev, type.id]
                        );
                      }}
                      className={`px-3 py-2 rounded-lg border transition-all text-sm ${
                        selectedTypes.includes(type.id)
                          ? 'border-cyan-400/30 bg-cyan-400/10 text-cyan-400'
                          : 'border-white/[0.08] bg-white/[0.02] text-white/40 hover:border-white/[0.15] hover:text-white/60'
                      }`}
                    >
                      {type.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-white/60 mb-1">难度级别</label>
                <select
                  value={difficulty}
                  onChange={(e) => setDifficulty(e.target.value)}
                  className="w-full px-3 py-2 bg-white/[0.04] border border-white/[0.08] text-white rounded-lg focus:border-cyan-400/30 focus:outline-none"
                >
                  <option value="beginner">初级</option>
                  <option value="intermediate">中级</option>
                  <option value="advanced">高级</option>
                </select>
              </div>

              <button
                onClick={handleGenerateResources}
                disabled={resourceLoading || selectedTypes.length === 0}
                className="w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold"
              >
                {resourceLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    生成中...
                  </>
                ) : (
                  <>
                    <Brain className="w-5 h-5" />
                    开始生成资源
                  </>
                )}
              </button>
            </div>

            {resources.length > 0 && (
              <div className="space-y-3">
                <h4 className="font-bold text-white">生成的资源 ({resources.length})</h4>
                {resources.map((resource, idx) => (
                  <div key={idx} className="glass-card rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {resource.type === 'document' && <FileText className="w-5 h-5 text-cyan-400" />}
                        {resource.type === 'mindmap' && <GitBranch className="w-5 h-5 text-emerald-400" />}
                        {resource.type === 'quiz' && <FileCode className="w-5 h-5 text-amber-400" />}
                        <span className="font-semibold text-white">{resource.title}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => {
                            // 预览功能：在新窗口打开内容
                            const previewWindow = window.open('', '_blank');
                            if (previewWindow) {
                              // 修复：使用content_data而不是content
                              const content = resource.content_data
                                ? JSON.stringify(resource.content_data, null, 2)
                                : '暂无内容数据';
                              previewWindow.document.write(`
                                <html>
                                  <head>
                                    <title>${resource.title} - 预览</title>
                                    <style>
                                      body { font-family: Arial, sans-serif; padding: 40px; line-height: 1.6; max-width: 900px; margin: 0 auto; }
                                      h1 { color: #2563eb; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }
                                      h2 { color: #059669; margin-top: 20px; }
                                      pre { background: #f3f4f6; padding: 16px; border-radius: 8px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; font-size: 14px; }
                                      code { background: #f3f4f6; padding: 2px 6px; border-radius: 4px; }
                                    </style>
                                  </head>
                                  <body>
                                    <h1>${resource.title}</h1>
                                    <pre>${content.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>
                                  </body>
                                </html>
                              `);
                              previewWindow.document.close();
                            }
                          }}
                          className="px-3 py-1 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:opacity-90 transition-colors text-sm flex items-center gap-1"
                        >
                          👁️ 预览
                        </button>
                        <button
                          onClick={async () => {
                            try {
                              console.log('📤 开始导出资源:', resource);

                              // 调用后端API导出文件
                              const res: any = await api.exportResource(resource);

                              if (res.success && res.data) {
                                console.log('✅ 导出成功:', res.data);

                                // 从后端获取文件并下载（通过 Next.js 代理）
                                const filePath: string = res.data.file_path.replace(/\\/g, '/');
                                const fileName = filePath.split('/').pop() || filePath;
                                const fileUrl = `/exports/${fileName}`;
                                console.log('📥 下载URL:', fileUrl);

                                const a = document.createElement('a');
                                a.href = fileUrl;
                                a.download = res.data.filename || fileName;
                                document.body.appendChild(a);
                                a.click();
                                document.body.removeChild(a);

                                alert(`✅ 导出成功！\n文件名: ${res.data.filename}\n文件类型: ${res.data.file_type}`);
                              } else {
                                alert(`❌ 导出失败: ${res.message || '未知错误'}`);
                              }
                            } catch (error: any) {
                              console.error('❌ 导出失败:', error);
                              alert(`❌ 导出失败: ${error.message || '网络错误'}`);
                            }
                          }}
                          className="px-3 py-1 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-lg hover:opacity-90 transition-colors text-sm flex items-center gap-1"
                        >
                          📥 导出
                        </button>
                        <CheckCircle className="w-5 h-5 text-emerald-400" />
                      </div>
                    </div>
                    <div className="text-sm text-white/60 whitespace-pre-wrap">
                      {resource.content_data
                        ? JSON.stringify(resource.content_data, null, 2)
                        : '暂无内容'}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        );

      case 'path':
        return (
          <div className="space-y-4">
            <h3 className="text-xl font-bold text-white">个性化学习路径规划</h3>

            <div className="glass-card rounded-xl p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-white/60 mb-1">学习目标</label>
                <input
                  type="text"
                  value={learningGoal}
                  onChange={(e) => setLearningGoal(e.target.value)}
                  placeholder="输入你的学习目标..."
                  className="w-full px-3 py-2 bg-white/[0.04] border border-white/[0.08] text-white placeholder:text-white/15 rounded-lg focus:border-cyan-400/30 focus:outline-none"
                />
              </div>

              <button
                onClick={handlePlanPath}
                disabled={pathLoading || !learningGoal.trim()}
                className="w-full py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold"
              >
                {pathLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    规划中...
                  </>
                ) : (
                  <>
                    <Route className="w-5 h-5" />
                    生成学习路径
                  </>
                )}
              </button>
            </div>

            {learningPath && (
              <div className="glass-card rounded-xl p-4 border-amber-400/20">
                <h4 className="font-bold text-amber-400 mb-3">学习路径: {learningPath.goal}</h4>
                <div className="text-sm text-white/60 mb-3">
                  预计时长: {learningPath.estimated_duration} | 步骤数: {learningPath.total_steps}
                </div>
                <div className="space-y-3">
                  {learningPath.steps.map((step, idx) => (
                    <div key={idx} className="glass-card rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 text-white flex items-center justify-center font-bold text-sm">
                          {step.step_number}
                        </div>
                        <div className="flex-1">
                          <div className="font-semibold text-white">{step.title}</div>
                          <div className="text-sm text-white/60">{step.description}</div>
                        </div>
                        <div className="flex items-center gap-1 text-sm text-white/40">
                          <Clock className="w-4 h-4" />
                          {step.estimated_time}
                        </div>
                      </div>
                      {step.prerequisites.length > 0 && (
                        <div className="text-xs text-white/30 ml-10">
                          前置知识: {step.prerequisites.join(', ')}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );

      case 'tutor':
        return (
          <div className="space-y-4">
            <h3 className="text-xl font-bold text-white">智能辅导系统</h3>

            <div className="glass-card rounded-2xl p-6 min-h-[500px] max-h-[600px] overflow-y-auto">
              {tutorMessages.map((msg, idx) => (
                <div key={idx} className={`mb-4 flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] px-4 py-3 rounded-2xl ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-br-md'
                      : 'bg-white/[0.06] text-white/80 border border-white/[0.06] rounded-bl-md'
                  }`}>
                    <div className="flex items-start gap-2">
                      {msg.role === 'assistant' && (
                        <div className="w-6 h-6 rounded-full bg-gradient-to-r from-amber-400 to-orange-400 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <Lightbulb className="w-3 h-3 text-white" />
                        </div>
                      )}
                      <div className="flex-1">
                        <div className="text-xs opacity-70 mb-1">
                          {msg.timestamp.toLocaleTimeString()}
                        </div>
                        <div className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</div>
                        {msg.diagram && (
                          <div className="mt-2 p-2 bg-white/[0.04] rounded-lg text-sm border border-white/[0.06]">
                            📊 {msg.diagram}
                          </div>
                        )}
                        {msg.example && (
                          <div className="mt-2 p-2 bg-white/[0.04] rounded-lg text-sm border border-white/[0.06]">
                             示例: {msg.example}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              {tutorLoading && (
                <div className="flex items-center gap-2 text-white/40">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>AI思考中...</span>
                </div>
              )}
            </div>

            <div className="glass-card rounded-xl p-4 space-y-3">
              <div>
                <label className="block text-sm font-medium text-white/60 mb-1">学科</label>
                <input
                  type="text"
                  value={tutorSubject}
                  onChange={(e) => setTutorSubject(e.target.value)}
                  className="w-full px-3 py-2 bg-white/[0.04] border border-white/[0.08] text-white placeholder:text-white/15 rounded-lg focus:border-cyan-400/30 focus:outline-none"
                />
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAskTutor()}
                  placeholder="输入你的问题..."
                  className="flex-1 px-4 py-2 bg-white/[0.04] border border-white/[0.08] text-white placeholder:text-white/15 rounded-lg focus:border-cyan-400/30 focus:outline-none"
                  disabled={tutorLoading}
                />
                <button
                  onClick={handleAskTutor}
                  disabled={tutorLoading || !question.trim()}
                  className="px-6 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {tutorLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  提问
                </button>
              </div>
            </div>
          </div>
        );

      case 'assessment':
        return (
          <div className="space-y-5">
            <h3 className="text-xl font-bold text-white">学习效果评估</h3>

            {/* Tab 切换 */}
            <div className="flex gap-2 bg-white/[0.04] rounded-xl p-1 border border-white/[0.06]">
              <button
                onClick={() => setAssessTab('assess')}
                className={`flex-1 px-4 py-2.5 rounded-lg font-medium text-sm transition-all ${
                  assessTab === 'assess'
                    ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white'
                    : 'text-white/40 hover:text-white/60'
                }`}
              >
                <span className="flex items-center justify-center gap-2">
                  <BarChart3 className="w-4 h-4" />
                  AI 综合评估
                </span>
              </button>
              <button
                onClick={() => setAssessTab('analyze')}
                className={`flex-1 px-4 py-2.5 rounded-lg font-medium text-sm transition-all ${
                  assessTab === 'analyze'
                    ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white'
                    : 'text-white/40 hover:text-white/60'
                }`}
              >
                <span className="flex items-center justify-center gap-2">
                  <FileText className="w-4 h-4" />
                  资料分析
                </span>
              </button>
            </div>

            {/* ======== Tab 1: AI 综合评估 ======== */}
            {assessTab === 'assess' && (
              <div className="space-y-4">
                {!assessment ? (
                  <div className="text-center py-12">
                    <BarChart3 className="w-16 h-16 mx-auto mb-4 text-white/20" />
                    <h4 className="text-lg font-semibold text-white/60 mb-2">开始学习效果评估</h4>
                    <p className="text-sm text-white/40 mb-5">基于您的学习行为和画像特征，进行多维度综合评估</p>
                    <button
                      onClick={handleAssess}
                      disabled={assessLoading}
                      className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-xl hover:opacity-90 disabled:opacity-50 font-medium flex items-center gap-2 mx-auto"
                    >
                      {assessLoading ? (
                        <><Loader2 className="w-5 h-5 animate-spin" /> 评估中...</>
                      ) : (
                        <><Award className="w-5 h-5" /> 开始评估</>
                      )}
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="bg-gradient-to-r from-cyan-500 to-blue-500 rounded-2xl p-6 text-white text-center">
                      <h4 className="text-lg font-semibold mb-3">综合评分</h4>
                      <div className="text-5xl font-bold mb-1">{assessment.overall_score}</div>
                      <p className="text-white/80 text-sm">满分 100 分</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {assessment.dimensions.map((dim, idx) => (
                        <div key={idx} className="glass-card rounded-xl p-4">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-semibold text-sm text-white">{dim.name}</span>
                            <span className="text-xs text-white/40">{dim.score}/{dim.max_score} · {dim.level}</span>
                          </div>
                          <div className="w-full bg-white/[0.06] rounded-full h-2 mb-2">
                            <div className="bg-gradient-to-r from-cyan-500 to-blue-500 h-2 rounded-full" style={{ width: `${(dim.score / dim.max_score) * 100}%` }} />
                          </div>
                          <p className="text-xs text-white/40">{dim.feedback}</p>
                        </div>
                      ))}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div className="glass-card rounded-xl p-4 border-emerald-400/20">
                        <h5 className="font-semibold text-emerald-400 mb-2 flex items-center gap-2 text-sm">
                          <CheckCircle className="w-4 h-4" /> 优势
                        </h5>
                        <ul className="text-sm text-white/60 space-y-1">
                          {assessment.strengths.map((s, idx) => <li key={idx}>• {s}</li>)}
                        </ul>
                      </div>
                      <div className="glass-card rounded-xl p-4 border-amber-400/20">
                        <h5 className="font-semibold text-amber-400 mb-2 flex items-center gap-2 text-sm">
                          <AlertCircle className="w-4 h-4" /> 改进建议
                        </h5>
                        <ul className="text-sm text-white/60 space-y-1">
                          {assessment.improvements.map((imp, idx) => <li key={idx}>• {imp}</li>)}
                        </ul>
                      </div>
                    </div>

                    <div className="glass-card rounded-xl p-4 border-cyan-400/20">
                      <h5 className="font-semibold text-cyan-400 mb-2 flex items-center gap-2 text-sm">
                        <Lightbulb className="w-4 h-4" /> 学习建议
                      </h5>
                      <ul className="text-sm text-white/60 space-y-1">
                        {assessment.recommendations.map((rec, idx) => <li key={idx}>• {rec}</li>)}
                      </ul>
                    </div>

                    <button
                      onClick={handleAssess}
                      disabled={assessLoading}
                      className="w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-xl hover:opacity-90 disabled:opacity-50 font-medium flex items-center justify-center gap-2"
                    >
                      {assessLoading ? <><Loader2 className="w-5 h-5 animate-spin" /> 重新评估中...</> : <><TrendingUp className="w-5 h-5" /> 重新评估</>}
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* ======== Tab 2: 资料分析 ======== */}
            {assessTab === 'analyze' && (
              <div className="space-y-4">
                {/* 上传区域 */}
                <div
                  onDrop={(e) => { e.preventDefault(); setAnalysisDragOver(false); addAnalysisFiles(e.dataTransfer.files); }}
                  onDragOver={(e) => { e.preventDefault(); setAnalysisDragOver(true); }}
                  onDragLeave={() => setAnalysisDragOver(false)}
                  onClick={() => analysisFileInputRef.current?.click()}
                  className={`rounded-2xl border-2 border-dashed p-8 text-center cursor-pointer transition-colors ${
                    analysisDragOver ? 'border-cyan-400/50 bg-cyan-400/5' : 'border-white/[0.08] bg-white/[0.02] hover:border-cyan-400/30'
                  }`}
                >
                  <input
                    ref={analysisFileInputRef}
                    type="file"
                    multiple
                    accept=".txt,.md,.pdf,.doc,.docx,.ppt,.pptx,.jpg,.jpeg,.png"
                    className="hidden"
                    onChange={(e) => { if (e.target.files) addAnalysisFiles(e.target.files); e.target.value = ''; }}
                  />
                  <Upload className={`w-10 h-10 mx-auto mb-3 ${analysisDragOver ? 'text-cyan-400' : 'text-white/30'}`} />
                  <p className="text-sm font-medium text-white/60 mb-1">
                    拖拽文件到此处，或 <span className="text-cyan-400 underline">点击选择</span>
                  </p>
                  <p className="text-xs text-white/30">支持 PDF、Word、PPT、TXT、Markdown、图片 · 单文件 10MB · 最多 10 个</p>
                </div>

                {/* 文件列表 */}
                {analysisFiles.length > 0 && (
                  <div className="glass-card rounded-2xl p-4">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm font-semibold text-white/60">
                        已选 {analysisFiles.length} 个文件 ({formatFileSize(analysisFiles.reduce((s, f) => s + f.size, 0))})
                      </span>
                      <button onClick={() => setAnalysisFiles([])} className="text-xs text-red-400/80 hover:text-red-400">清空</button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {analysisFiles.map((f, i) => (
                        <div key={i} className="flex items-center gap-2 bg-white/[0.06] rounded-lg px-3 py-2 text-sm group">
                          <span>{getFileIcon(f.name)}</span>
                          <span className="text-white/60 max-w-[140px] truncate">{f.name}</span>
                          <span className="text-xs text-white/30">{formatFileSize(f.size)}</span>
                          <button onClick={(e) => { e.stopPropagation(); removeAnalysisFile(i); }} className="opacity-0 group-hover:opacity-100 text-white/30 hover:text-red-400/80">
                            <X className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 可选参数 */}
                <div className="glass-card rounded-2xl p-4">
                  <p className="text-xs text-white/30 mb-3">以下为可选参数，帮助 AI 更精准分析</p>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <input
                      value={analysisSubject}
                      onChange={(e) => setAnalysisSubject(e.target.value)}
                      placeholder="学科（如：机器学习）"
                      className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] text-white placeholder:text-white/15 rounded-lg text-sm focus:border-cyan-400/30 focus:outline-none"
                    />
                    <input
                      value={analysisTopic}
                      onChange={(e) => setAnalysisTopic(e.target.value)}
                      placeholder="主题（如：神经网络）"
                      className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] text-white placeholder:text-white/15 rounded-lg text-sm focus:border-cyan-400/30 focus:outline-none"
                    />
                    <select
                      value={analysisDifficulty}
                      onChange={(e) => setAnalysisDifficulty(e.target.value)}
                      className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] text-white rounded-lg text-sm focus:border-cyan-400/30 focus:outline-none"
                    >
                      <option value="beginner">初级</option>
                      <option value="intermediate">中级</option>
                      <option value="advanced">高级</option>
                    </select>
                  </div>
                </div>

                {/* 分析按钮 */}
                <button
                  onClick={handleAnalyze}
                  disabled={analyzing || analysisFiles.length === 0}
                  className="w-full py-3 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-xl hover:opacity-90 disabled:opacity-50 font-medium flex items-center justify-center gap-2"
                >
                  {analyzing ? (
                    <><Loader2 className="w-5 h-5 animate-spin" /> AI 分析中...</>
                  ) : (
                    <><Sparkles className="w-5 h-5" /> 开始分析</>
                  )}
                </button>

                {/* 分析结果 */}
                {analysisResult && (
                  <div className="space-y-4">
                    {/* 总分 */}
                    <div className="bg-gradient-to-r from-emerald-500 to-teal-500 rounded-2xl p-6 text-white text-center">
                      <h4 className="text-lg font-semibold mb-3">学习效果评分</h4>
                      <div className="text-5xl font-bold mb-1">{analysisResult.overall_score || '--'}</div>
                      <p className="text-white/80 text-sm">满分 100</p>
                    </div>

                    {/* 知识总览 */}
                    {analysisResult.knowledge_overview && (
                      <div className="glass-card rounded-xl p-4">
                        <h5 className="font-semibold text-white mb-2 text-sm">📚 知识总览</h5>
                        <p className="text-sm text-white/60 leading-relaxed">{analysisResult.knowledge_overview}</p>
                      </div>
                    )}

                    {/* 知识点 */}
                    {analysisResult.knowledge_points?.length > 0 && (
                      <div className="glass-card rounded-xl p-4">
                        <h5 className="font-semibold text-white mb-3 text-sm">🎯 知识点分析</h5>
                        <div className="space-y-2">
                          {analysisResult.knowledge_points.map((kp: any, i: number) => (
                            <div key={i} className="bg-white/[0.04] rounded-lg p-3">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-medium text-sm text-white">{kp.point}</span>
                                {kp.importance && (
                                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                                    kp.importance === 'high' ? 'bg-red-400/15 text-red-400/80' :
                                    kp.importance === 'medium' ? 'bg-amber-400/15 text-amber-400' :
                                    'bg-emerald-400/15 text-emerald-400'
                                  }`}>
                                    {kp.importance === 'high' ? '重要' : kp.importance === 'medium' ? '中等' : '了解'}
                                  </span>
                                )}
                                {kp.mastery_level && (
                                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                                    kp.mastery_level === 'good' ? 'bg-emerald-400/15 text-emerald-400' :
                                    kp.mastery_level === 'moderate' ? 'bg-amber-400/15 text-amber-400' :
                                    'bg-red-400/15 text-red-400/80'
                                  }`}>
                                    {kp.mastery_level === 'good' ? '已掌握' : kp.mastery_level === 'moderate' ? '部分掌握' : '需加强'}
                                  </span>
                                )}
                              </div>
                              {kp.description && <p className="text-xs text-white/40">{kp.description}</p>}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 优势与不足 */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {analysisResult.strengths?.length > 0 && (
                        <div className="glass-card rounded-xl p-4 border-emerald-400/20">
                          <h5 className="font-semibold text-emerald-400 mb-2 text-sm">✅ 学习优势</h5>
                          <ul className="text-sm text-white/60 space-y-1">
                            {analysisResult.strengths.map((s: string, i: number) => <li key={i}>• {s}</li>)}
                          </ul>
                        </div>
                      )}
                      {analysisResult.weaknesses?.length > 0 && (
                        <div className="glass-card rounded-xl p-4 border-red-400/20">
                          <h5 className="font-semibold text-red-400/80 mb-2 text-sm">⚠️ 薄弱环节</h5>
                          <ul className="text-sm text-white/60 space-y-1">
                            {analysisResult.weaknesses.map((w: string, i: number) => <li key={i}>• {w}</li>)}
                          </ul>
                        </div>
                      )}
                    </div>

                    {/* 学习缺口 */}
                    {analysisResult.learning_gaps?.length > 0 && (
                      <div className="glass-card rounded-xl p-4 border-amber-400/20">
                        <h5 className="font-semibold text-amber-400 mb-2 text-sm">🔍 学习缺口</h5>
                        <ul className="text-sm text-white/60 space-y-1">
                          {analysisResult.learning_gaps.map((g: string, i: number) => <li key={i}>• {g}</li>)}
                        </ul>
                      </div>
                    )}

                    {/* 难度评估 */}
                    {analysisResult.difficulty_assessment && (
                      <div className="glass-card rounded-xl p-4 border-purple-400/20">
                        <h5 className="font-semibold text-purple-400 mb-2 text-sm">📊 难度评估</h5>
                        <p className="text-sm text-white/60">{analysisResult.difficulty_assessment}</p>
                      </div>
                    )}

                    {/* 学习建议 */}
                    {analysisResult.study_recommendations?.length > 0 && (
                      <div className="glass-card rounded-xl p-4 border-cyan-400/20">
                        <h5 className="font-semibold text-cyan-400 mb-2 text-sm">💡 学习建议</h5>
                        <div className="space-y-2">
                          {analysisResult.study_recommendations.map((rec: any, i: number) => (
                            <div key={i} className="flex items-start gap-2">
                              <div className="w-5 h-5 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0 mt-0.5">
                                {i + 1}
                              </div>
                              <p className="text-sm text-white/60">{typeof rec === 'string' ? rec : rec.recommendation || rec.title || JSON.stringify(rec)}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* AI 总结 */}
                    {analysisResult.summary && (
                      <div className="glass-card rounded-xl p-4 border-emerald-400/20">
                        <h5 className="font-semibold text-emerald-400 mb-2 text-sm">🤖 AI 总结</h5>
                        <p className="text-sm text-white/60 leading-relaxed">{analysisResult.summary}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* 欢迎区域 - 仅在未选择模块时显示 */}
      {!activeModule && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: 'spring', stiffness: 200, damping: 25 }}
          className="mb-8"
        >
          <div className="bg-gradient-to-r from-cyan-500 to-blue-500 rounded-2xl p-6 text-white mb-6">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center">
                <GraduationCap className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold mb-1">
                  基于多智能体的个性化学习资源生成系统
                </h1>
                <p className="text-white/80 text-sm">
                  v7.2 多数据库架构版 · 对话式画像构建 · 多智能体协同 · 防幻觉机制 · 流式输出
                </p>
              </div>
            </div>
          </div>

          {/* 统计卡片 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {stats.map((stat, index) => {
              const Icon = stat.icon;
              return (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1, type: 'spring', stiffness: 200, damping: 25 }}
                  className="glass-card rounded-xl p-4"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-lg bg-white/[0.06] flex items-center justify-center ${stat.color}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-white">{stat.value}</div>
                      <div className="text-xs text-white/40">{stat.label}</div>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>
      )}

      {/* 功能模块选择 - 仅在未选择模块时显示 */}
      {!activeModule && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, type: 'spring', stiffness: 200, damping: 25 }}
          className="mb-6"
        >
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-cyan-400" />
            功能模块
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[
            { id: 'profile', label: '学生画像', icon: UserCheck, color: 'cyan', emoji: '' },
            { id: 'resources', label: '资源生成', icon: Brain, color: 'purple', emoji: '🤖' },
            { id: 'path', label: '学习路径', icon: Route, color: 'amber', emoji: '🗺️' },
            { id: 'tutor', label: '智能辅导', icon: Lightbulb, color: 'green', emoji: '💡' },
            { id: 'assessment', label: '效果评估', icon: TrendingUp, color: 'blue', emoji: '' }
          ].map((module) => {
            const Icon = module.icon;
            const isActive = activeModule === module.id;
            const colorMap: any = {
              cyan: 'from-cyan-500 to-blue-500',
              purple: 'from-purple-500 to-pink-500',
              amber: 'from-amber-500 to-orange-500',
              green: 'from-emerald-500 to-teal-500',
              blue: 'from-blue-500 to-indigo-500'
            };

            return (
              <button
                key={module.id}
                onClick={() => setActiveModule(module.id as ModuleType)}
                className={`p-4 rounded-xl transition-all ${
                  isActive
                    ? `bg-gradient-to-r ${colorMap[module.color]} text-white scale-105`
                    : 'glass-card hover:bg-white/[0.06] text-white/60 hover:text-white'
                }`}
              >
                <div className="text-2xl mb-2">{module.emoji}</div>
                <div className="text-sm font-semibold">{module.label}</div>
              </button>
            );
          })}
        </div>
      </motion.div>
      )}

      {/* 功能模块内容 */}
      {activeModule && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: 'spring', stiffness: 200, damping: 25 }}
          className="glass-card rounded-2xl p-6"
        >
          {renderModule()}
        </motion.div>
      )}

      {/* 快捷操作 */}
      {!activeModule && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, type: 'spring', stiffness: 200, damping: 25 }}
          className="glass-card rounded-2xl p-6"
        >
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-cyan-400" />
            快速开始
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => setActiveModule('profile')}
              disabled={isGuest}
              className="flex items-center gap-3 p-4 rounded-xl border border-white/[0.08] bg-white/[0.02] hover:border-cyan-400/30 hover:bg-cyan-400/5 transition-all group disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="w-10 h-10 rounded-lg bg-cyan-400/10 flex items-center justify-center group-hover:bg-cyan-400/20 transition-colors">
                <UserCheck className="w-5 h-5 text-cyan-400" />
              </div>
              <div className="text-left">
                <div className="font-semibold text-white">构建画像</div>
                <div className="text-xs text-white/40">对话式8维度画像</div>
              </div>
              <ArrowRight className="w-4 h-4 text-white/30 ml-auto group-hover:text-cyan-400" />
            </button>

            <button
              onClick={() => setActiveModule('resources')}
              disabled={isGuest}
              className="flex items-center gap-3 p-4 rounded-xl border border-white/[0.08] bg-white/[0.02] hover:border-purple-400/30 hover:bg-purple-400/5 transition-all group disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="w-10 h-10 rounded-lg bg-purple-400/10 flex items-center justify-center group-hover:bg-purple-400/20 transition-colors">
                <Brain className="w-5 h-5 text-purple-400" />
              </div>
              <div className="text-left">
                <div className="font-semibold text-white">生成资源</div>
                <div className="text-xs text-white/40">7种多模态资源</div>
              </div>
              <ArrowRight className="w-4 h-4 text-white/30 ml-auto group-hover:text-purple-400" />
            </button>

            <button
              onClick={() => setActiveModule('assessment')}
              disabled={isGuest}
              className="flex items-center gap-3 p-4 rounded-xl border border-white/[0.08] bg-white/[0.02] hover:border-indigo-400/30 hover:bg-indigo-400/5 transition-all group disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="w-10 h-10 rounded-lg bg-indigo-400/10 flex items-center justify-center group-hover:bg-indigo-400/20 transition-colors">
                <Award className="w-5 h-5 text-indigo-400" />
              </div>
              <div className="text-left">
                <div className="font-semibold text-white">效果评估</div>
                <div className="text-xs text-white/40">多维度评估反馈</div>
              </div>
              <ArrowRight className="w-4 h-4 text-white/30 ml-auto group-hover:text-indigo-400" />
            </button>
          </div>
        </motion.div>
      )}
    </div>
  );
}
