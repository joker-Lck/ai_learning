import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/stores';
import api from '@/lib/api';
import { PROFILE_DIMENSIONS } from './constants';
import type {
  ModuleType, DimensionChat, ProfileData, ResourceItem,
  LearningPath, TutorMessage, AssessmentResult,
} from './types';

export function useDashboard() {
  const { user, isGuest } = useAuthStore();
  const searchParams = useSearchParams();

  // URL 参数驱动模块切换
  const moduleParam = searchParams.get('module') as ModuleType;
  const [activeModule, setActiveModule] = useState<ModuleType>(null);

  useEffect(() => {
    setActiveModule(moduleParam || null);
  }, [moduleParam]);

  // ── 画像构建状态 ──
  const [currentStep, setCurrentStep] = useState(0);
  const [dimensionChats, setDimensionChats] = useState<Record<string, DimensionChat>>({});
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileData, setProfileData] = useState<ProfileData | null>(null);

  const currentDimension = PROFILE_DIMENSIONS[currentStep]!;
  const currentChat = dimensionChats[currentDimension.id] || {
    dimensionId: currentDimension.id,
    messages: [{ role: 'assistant' as const, content: currentDimension.questions[0] || '' }],
    completed: false,
  };

  const updateCurrentChat = (messages: Array<{ role: 'user' | 'assistant'; content: string }>, completed = false) => {
    setDimensionChats(prev => ({
      ...prev,
      [currentDimension.id]: { dimensionId: currentDimension.id, messages, completed },
    }));
  };

  // ── 资源生成状态 ──
  const [subject, setSubject] = useState('机器学习');
  const [topic, setTopic] = useState('神经网络');
  const [selectedTypes, setSelectedTypes] = useState<string[]>(['document', 'quiz', 'mindmap']);
  const [difficulty, setDifficulty] = useState('intermediate');
  const [resourceLoading, setResourceLoading] = useState(false);
  const [resources, setResources] = useState<ResourceItem[]>([]);

  // ── 学习路径状态 ──
  const [learningGoal, setLearningGoal] = useState('掌握深度学习基础');
  const [pathLoading, setPathLoading] = useState(false);
  const [learningPath, setLearningPath] = useState<LearningPath | null>(null);

  // ── 智能辅导状态 ──
  const [question, setQuestion] = useState('');
  const [tutorSubject, setTutorSubject] = useState('机器学习');
  const [tutorLoading, setTutorLoading] = useState(false);
  const [tutorMessages, setTutorMessages] = useState<TutorMessage[]>([]);
  const [streamingContent, setStreamingContent] = useState('');
  const streamingContentRef = useRef('');

  // ── 学习评估状态 ──
  const [assessLoading, setAssessLoading] = useState(false);
  const [assessment, setAssessment] = useState<AssessmentResult | null>(null);
  const [assessTab, setAssessTab] = useState<'assess' | 'analyze'>('assess');

  // ── 资料分析状态 ──
  const [analysisFiles, setAnalysisFiles] = useState<File[]>([]);
  const [analysisDragOver, setAnalysisDragOver] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const analysisFileInputRef = useRef<HTMLInputElement>(null);
  const [analysisSubject, setAnalysisSubject] = useState('');
  const [analysisTopic, setAnalysisTopic] = useState('');
  const [analysisDifficulty, setAnalysisDifficulty] = useState('intermediate');

  // ── 画像构建处理 ──
  const handleSendMessage = async () => {
    const inputValue = (document.getElementById('profile-input') as HTMLInputElement)?.value;
    if (!inputValue?.trim()) return;

    const userMessage = { role: 'user' as const, content: inputValue.trim() };
    const newMessages = [...currentChat.messages, userMessage];
    (document.getElementById('profile-input') as HTMLInputElement).value = '';
    setProfileLoading(true);

    setTimeout(() => {
      let aiResponse = '';
      const currentQuestionIndex = currentChat.messages.filter((m: any) => m.role === 'assistant').length - 1;

      if (currentQuestionIndex < currentDimension.questions.length - 1) {
        aiResponse = currentDimension.questions[currentQuestionIndex + 1] ?? '';
        updateCurrentChat([...newMessages, { role: 'assistant', content: aiResponse }]);
      } else {
        aiResponse = `✅ 好的，我已经记录了您的${currentDimension.title}信息。`;
        updateCurrentChat([...newMessages, { role: 'assistant', content: aiResponse }], true);

        setTimeout(() => {
          if (currentStep < PROFILE_DIMENSIONS.length - 1) {
            setCurrentStep(prev => prev + 1);
          } else {
            buildFinalProfile();
          }
        }, 1000);
      }
      setProfileLoading(false);
    }, 800);
  };

  const buildFinalProfile = async () => {
    setProfileLoading(true);
    try {
      const conversationLog = Object.values(dimensionChats).flatMap(chat => chat.messages);
      const response: any = await api.buildProfile(conversationLog);
      if (response?.success && response?.data?.profile) {
        setProfileData(response.data.profile);
      } else {
        alert(response?.message || '画像构建失败，请重试');
      }
    } catch (error: any) {
      alert('构建画像失败：' + (error.message || '网络错误'));
    } finally {
      setProfileLoading(false);
    }
  };

  const goToPreviousStep = () => { if (currentStep > 0) setCurrentStep(prev => prev - 1); };
  const goToNextStep = () => { if (currentStep < PROFILE_DIMENSIONS.length - 1) setCurrentStep(prev => prev + 1); };

  // ── 资源生成处理 ──
  const getTypeName = (type: string) => {
    const names: Record<string, string> = { mindmap: '思维导图', quiz: '练习题', document: '讲解文档' };
    return names[type] || type;
  };

  const handleGenerateResources = async () => {
    if (selectedTypes.length === 0) { alert('请至少选择一种资源类型'); return; }
    setResourceLoading(true);
    setResources([]);
    try {
      const response: any = await api.generateResources({ subject, topic, resource_types: selectedTypes, difficulty });
      if (response?.success && response?.data?.resources) {
        const generatedResources: ResourceItem[] = response.data.resources.map((r: any) => ({
          type: r.type || r.resource_type,
          title: r.title || `${topic}资源`,
          content_data: r.content_data || r,
          status: 'complete' as const,
        }));
        setResources(generatedResources);
      } else {
        alert(response?.message || '资源生成失败，请重试');
      }
    } catch (error: any) {
      alert('资源生成失败：' + (error.message || '网络错误'));
    } finally {
      setResourceLoading(false);
    }
  };

  // ── 学习路径处理 ──
  const handlePlanPath = async () => {
    setPathLoading(true);
    try {
      const response: any = await api.planPath({ learning_goal: learningGoal });
      if (response?.success && response?.data) {
        setLearningPath(response.data.path || response.data);
      } else {
        alert(response?.message || '路径生成失败，请重试');
      }
    } catch (error: any) {
      alert('路径生成失败：' + (error.message || '网络错误'));
    } finally {
      setPathLoading(false);
    }
  };

  // ── 智能辅导处理（SSE 真流式）──
  const handleAskTutor = () => {
    if (!question.trim()) return;
    const q = question.trim();
    const userMessage: TutorMessage = { role: 'user', content: q, timestamp: new Date() };
    setTutorMessages(prev => [...prev, userMessage]);
    setQuestion('');
    setTutorLoading(true);
    setStreamingContent('');
    streamingContentRef.current = '';

    api.askQuestionStream(
      q,
      tutorSubject,
      // onChunk — 逐字追加
      (chunk) => {
        streamingContentRef.current += chunk;
        setStreamingContent(prev => prev + chunk);
      },
      // onDone — 流结束，把累积文本存入消息
      (extra) => {
        const finalText = streamingContentRef.current || '暂无回答';
        setStreamingContent('');
        streamingContentRef.current = '';
        setTutorMessages(prev => [...prev, {
          role: 'assistant',
          content: finalText,
          diagram: extra.diagram,
          example: extra.example,
          timestamp: new Date(),
        }]);
        setTutorLoading(false);
      },
      // onError
      (errMsg) => {
        setStreamingContent('');
        streamingContentRef.current = '';
        setTutorMessages(prev => [...prev, { role: 'assistant', content: `❌ ${errMsg}`, timestamp: new Date() }]);
        setTutorLoading(false);
      },
    );
  };

  // ── 学习评估处理 ──
  const handleAssess = async () => {
    setAssessLoading(true);
    try {
      const res: any = await api.assess({ user_id: 1, assessment_type: 'comprehensive' });
      if (res.success && res.data?.assessment) {
        setAssessment(res.data.assessment);
      } else {
        console.error('评估返回异常:', res);
        alert(res.message || '评估失败，请稍后重试');
      }
    } catch (error: any) {
      console.error('评估请求失败:', error);
      alert(error.message || '评估请求失败，请检查网络连接');
    } finally {
      setAssessLoading(false);
    }
  };

  // ── 资料分析处理 ──
  const addAnalysisFiles = (fileList: FileList) => {
    const newFiles = Array.from(fileList).filter(f => f.size <= 10 * 1024 * 1024);
    setAnalysisFiles(prev => [...prev, ...newFiles].slice(0, 10));
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
      if (res.success) setAnalysisResult(res.data.analysis);
    } catch (err: any) {
      // 分析失败静默处理
    } finally {
      setAnalyzing(false);
    }
  };

  return {
    user, isGuest, activeModule, setActiveModule,
    // 画像
    currentStep, dimensionChats, profileLoading, profileData,
    currentDimension, currentChat, updateCurrentChat,
    handleSendMessage, buildFinalProfile, goToPreviousStep, goToNextStep,
    // 资源
    subject, setSubject, topic, setTopic, selectedTypes, setSelectedTypes,
    difficulty, setDifficulty, resourceLoading, resources, handleGenerateResources, getTypeName,
    // 路径
    learningGoal, setLearningGoal, pathLoading, learningPath, handlePlanPath,
    // 辅导
    question, setQuestion, tutorSubject, setTutorSubject, tutorLoading, tutorMessages, handleAskTutor, streamingContent,
    // 评估
    assessLoading, assessment, assessTab, setAssessTab, handleAssess,
    // 分析
    analysisFiles, setAnalysisFiles, analysisDragOver, setAnalysisDragOver,
    analyzing, analysisResult, analysisFileInputRef,
    analysisSubject, setAnalysisSubject, analysisTopic, setAnalysisTopic,
    analysisDifficulty, setAnalysisDifficulty,
    addAnalysisFiles, removeAnalysisFile, formatFileSize, getFileIcon, handleAnalyze,
  };
}
