import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/stores';
import api from '@/lib/api';
import { PROFILE_DIMENSIONS } from './constants';
import type {
  ModuleType, DimensionChat, ProfileData, ResourceItem,
  LearningPath, TutorMessage, AssessmentResult,
  CourseItem, GradeItem, ErrorNote, StudyPlan, ProfileTab,
} from './types';

export function useDashboard() {
  const { user, isGuest } = useAuthStore();
  const router = useRouter();
  const searchParams = useSearchParams();

  // URL 参数驱动模块切换
  const moduleParam = searchParams.get('module') as ModuleType;
  const [activeModule, setActiveModuleState] = useState<ModuleType>(null);

  useEffect(() => {
    setActiveModuleState(moduleParam || null);
  }, [moduleParam]);

  // 同步更新 URL 和本地状态
  const setActiveModule = useCallback((module: ModuleType) => {
    setActiveModuleState(module);
    if (module) {
      router.push(`/dashboard?module=${module}`, { scroll: false });
    } else {
      router.push('/dashboard', { scroll: false });
    }
  }, [router]);

  // ── 画像构建状态 ──
  const [currentStep, setCurrentStep] = useState(0);
  const [dimensionChats, setDimensionChats] = useState<Record<string, DimensionChat>>({});
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileData, setProfileData] = useState<ProfileData | null>(null);
  const [profileLoaded, setProfileLoaded] = useState(false);

  // 获取当前用户名用于 localStorage key
  const getUsername = () => {
    try {
      const stored = localStorage.getItem('user_info');
      if (stored) return JSON.parse(stored).username || 'default';
    } catch {}
    return user?.username || 'default';
  };

  // 初始化时立即从 localStorage 加载画像
  useEffect(() => {
    if (profileLoaded) return;
    const username = getUsername();
    const localKey = `profile_${username}`;
    const localData = localStorage.getItem(localKey);
    if (localData) {
      try {
        const parsed = JSON.parse(localData);
        if (parsed && (parsed.major || parsed.cognitive_style || parsed.grade_level)) {
          setProfileData(parsed);
        }
      } catch {}
    }
    setProfileLoaded(true);
  }, []);

  // 打开画像模块时尝试从 API 加载最新数据
  useEffect(() => {
    if (isGuest || !profileLoaded) return;
    if (activeModule === 'profile' && !profileLoading) {
      setProfileLoading(true);
      const localKey = `profile_${getUsername()}`;
      
      // 尝试从 API 加载
      api.getProfile().then((res: any) => {
        if (res.success && res.data) {
          const p = res.data;
          if (p.major || p.cognitive_style || (p.knowledge_base && p.knowledge_base !== '{}')) {
            setProfileData(p);
            localStorage.setItem(localKey, JSON.stringify(p));
          }
        }
      }).catch(() => {
        // API 不可用
      }).finally(() => {
        setProfileLoading(false);
      });
    }
  }, [activeModule, profileLoaded]);

  // ── 学生数据管理状态 ──
  const [profileTab, setProfileTab] = useState<ProfileTab>('profile');
  const [currentSemester, setCurrentSemester] = useState('2026-春');
  const [semesters, setSemesters] = useState<string[]>([]);

  // 课程表
  const [courses, setCourses] = useState<CourseItem[]>([]);
  const [courseLoading, setCourseLoading] = useState(false);

  // 成绩
  const [grades, setGrades] = useState<GradeItem[]>([]);
  const [gradeLoading, setGradeLoading] = useState(false);

  // 错题
  const [errorNotes, setErrorNotes] = useState<ErrorNote[]>([]);
  const [errorLoading, setErrorLoading] = useState(false);

  // 学习计划
  const [studyPlans, setStudyPlans] = useState<StudyPlan[]>([]);
  const [planLoading, setPlanLoading] = useState(false);

  // 加载学期列表
  useEffect(() => {
    if (isGuest) return;
    if (activeModule === 'profile') {
      api.listSemesters().then((res: any) => {
        if (res.success && Array.isArray(res.data)) {
          setSemesters(res.data);
        }
      }).catch(() => {});
    }
  }, [activeModule]);

  // 切换学期时加载数据
  const loadSemesterData = (semester: string) => {
    setCurrentSemester(semester);
    const username = getUsername();
    
    // 课程表 - 先从 localStorage 加载
    setCourseLoading(true);
    const localCourses = localStorage.getItem(`courses_${username}_${semester}`);
    if (localCourses) {
      try { setCourses(JSON.parse(localCourses)); } catch {}
    }
    
    api.getCourseSchedule(semester).then((res: any) => {
      if (res.success && res.data?.courses) {
        setCourses(res.data.courses);
        localStorage.setItem(`courses_${username}_${semester}`, JSON.stringify(res.data.courses));
      }
    }).catch(() => {
      // API 不可用，使用 localStorage 数据
    }).finally(() => setCourseLoading(false));
    
    // 成绩 - 先从 localStorage 加载
    setGradeLoading(true);
    const localGrades = localStorage.getItem(`grades_${username}_${semester}`);
    if (localGrades) {
      try { setGrades(JSON.parse(localGrades)); } catch {}
    }
    
    api.getGrades(semester).then((res: any) => {
      if (res.success && Array.isArray(res.data)) {
        setGrades(res.data);
        localStorage.setItem(`grades_${username}_${semester}`, JSON.stringify(res.data));
      }
    }).catch(() => {
      // API 不可用，使用 localStorage 数据
    }).finally(() => setGradeLoading(false));
  };

  useEffect(() => {
    if (isGuest) return;
    if (activeModule === 'profile' && currentSemester) {
      loadSemesterData(currentSemester);
    }
  }, [activeModule, currentSemester]);

  // 保存课程表（乐观更新：先更新 UI 再保存后端）
  const handleSaveCourses = async (semester: string, courseList: CourseItem[]) => {
    setCourses(courseList);
    if (!semesters.includes(semester)) setSemesters(prev => [semester, ...prev]);
    setCourseLoading(true);
    
    // 保存到 localStorage
    const localKey = `courses_${getUsername()}_${semester}`;
    localStorage.setItem(localKey, JSON.stringify(courseList));
    
    try {
      const res: any = await api.saveCourseSchedule(semester, courseList);
      if (!res.success) console.warn('课程表保存失败:', res.message);
    } catch (e) {
      console.error('课程表保存异常:', e);
    } finally { setCourseLoading(false); }
  };

  // 保存成绩（乐观更新）
  const handleSaveGrades = async (semester: string, gradeList: GradeItem[]) => {
    setGrades(gradeList);
    setGradeLoading(true);
    
    // 保存到 localStorage
    const localKey = `grades_${getUsername()}_${semester}`;
    localStorage.setItem(localKey, JSON.stringify(gradeList));
    
    try {
      const res: any = await api.saveGrades(semester, gradeList);
      if (!res.success) console.warn('成绩保存失败:', res.message);
    } catch (e) {
      console.error('成绩保存异常:', e);
    } finally { setGradeLoading(false); }
  };

  // 错题操作
  const loadErrorNotes = async (subject?: string) => {
    setErrorLoading(true);
    try {
      const res: any = await api.getErrorNotes(subject);
      if (res.success && Array.isArray(res.data)) setErrorNotes(res.data);
    } catch {} finally { setErrorLoading(false); }
  };

  useEffect(() => {
    if (isGuest) return;
    if (activeModule === 'profile' && profileTab === 'errors') loadErrorNotes();
  }, [activeModule, profileTab]);

  const handleAddErrorNote = async (note: Omit<ErrorNote, 'id'>) => {
    const newNote = { ...note, id: Date.now(), created_at: new Date().toISOString() };
    setErrorNotes(prev => [newNote, ...prev]);
    
    // 保存到 localStorage
    const localKey = `error_notes_${getUsername()}`;
    const existing = JSON.parse(localStorage.getItem(localKey) || '[]');
    localStorage.setItem(localKey, JSON.stringify([newNote, ...existing]));
    
    try {
      const res: any = await api.saveErrorNote(note);
      if (res.success) loadErrorNotes();
      return res;
    } catch {
      return { success: true, data: newNote };
    }
  };

  const handleToggleMastery = async (noteId: number, currentMastery: number) => {
    await api.updateErrorMastery(noteId, currentMastery ? 0 : 1);
    setErrorNotes(prev => prev.map(n => n.id === noteId ? { ...n, mastery: currentMastery ? 0 : 1 } : n));
  };

  const handleDeleteErrorNote = async (noteId: number) => {
    await api.deleteErrorNote(noteId);
    setErrorNotes(prev => prev.filter(n => n.id !== noteId));
  };

  // 学习计划
  const handleGeneratePlan = async (data: { plan_type: string; custom_goal?: string; exam_date?: string; exam_subjects?: string[] }) => {
    setPlanLoading(true);
    try {
      const res: any = await api.generateStudyPlan({ semester: currentSemester, ...data });
      if (res.success && res.data) {
        setStudyPlans(prev => [{ ...res.data, semester: currentSemester, plan_type: data.plan_type }, ...prev]);

        // 记录活动日志
        try {
          const logs = JSON.parse(localStorage.getItem('activity_logs') || '[]');
          logs.unshift({
            id: `plan-${Date.now()}`,
            type: 'path',
            action: '生成了学习计划',
            detail: data.plan_type === 'weekly' ? '周计划' : data.plan_type === 'exam' ? '备考计划' : '自定义计划',
            time: new Date().toISOString(),
          });
          localStorage.setItem('activity_logs', JSON.stringify(logs.slice(0, 50)));
          window.dispatchEvent(new Event('activity-updated'));
        } catch {}

        return res.data;
      }
    } finally { setPlanLoading(false); }
  };

  const loadStudyPlans = async () => {
    try {
      const res: any = await api.getStudyPlans(currentSemester);
      if (res.success && Array.isArray(res.data)) setStudyPlans(res.data);
    } catch {}
  };

  useEffect(() => {
    if (isGuest) return;
    if (activeModule === 'path') loadStudyPlans();
  }, [activeModule]);

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
  const [subject, setSubject] = useState('');
  const [topic, setTopic] = useState('');
  const [selectedTypes, setSelectedTypes] = useState<string[]>(['document', 'quiz', 'mindmap']);
  const [difficulty, setDifficulty] = useState('intermediate');
  const [resourceLoading, setResourceLoading] = useState(false);
  const [resources, setResources] = useState<ResourceItem[]>([]);

  // 资源生成后同步保存到 localStorage + 记录活动日志
  useEffect(() => {
    if (resources.length === 0) return;
    try {
      const stored = JSON.parse(localStorage.getItem('generated_resources') || '[]');
      const newItems = resources
        .filter(r => r.status === 'complete')
        .map(r => ({
          ...r,
          subject,
          topic,
          created_at: new Date().toISOString(),
        }));
      const merged = [...newItems, ...stored].slice(0, 50);
      localStorage.setItem('generated_resources', JSON.stringify(merged));
      window.dispatchEvent(new Event('resources-updated'));

      // 记录活动日志
      if (newItems.length > 0) {
        const logs = JSON.parse(localStorage.getItem('activity_logs') || '[]');
        logs.unshift({
          id: `res-${Date.now()}`,
          type: 'resource',
          action: `生成了${newItems.length}个${topic}相关资源`,
          detail: subject,
          time: new Date().toISOString(),
        });
        localStorage.setItem('activity_logs', JSON.stringify(logs.slice(0, 50)));
        window.dispatchEvent(new Event('activity-updated'));
      }
    } catch {}
  }, [resources]);

  // ── 学习路径状态 ──
  const [learningGoal, setLearningGoal] = useState('');
  const [pathLoading, setPathLoading] = useState(false);
  const [learningPath, setLearningPath] = useState<LearningPath | null>(null);

  // ── 智能辅导状态 ──
  const [question, setQuestion] = useState('');
  const [tutorSubject, setTutorSubject] = useState('');
  const [tutorLoading, setTutorLoading] = useState(false);
  const [tutorMessages, setTutorMessages] = useState<TutorMessage[]>([]);
  const [streamingContent, setStreamingContent] = useState('');
  const streamingContentRef = useRef('');
  const tutorInitialized = useRef(false);

  // 打开辅导模块时显示欢迎消息
  useEffect(() => {
    if (activeModule === 'tutor' && !tutorInitialized.current && tutorMessages.length === 0) {
      tutorInitialized.current = true;
      setTutorMessages([{
        role: 'assistant',
        content: '你好！我是你的 AI 学习助手 👋\n\n有什么学习上的问题都可以问我，比如：\n- 📚 某个知识点的讲解\n- 💡 习题的解题思路\n- 🔍 概念之间的区别和联系\n\n请在下方输入你的问题吧！',
        timestamp: new Date(),
      }]);
    }
  }, [activeModule]);

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

        // 记录活动日志
        try {
          const logs = JSON.parse(localStorage.getItem('activity_logs') || '[]');
          logs.unshift({
            id: `path-${Date.now()}`,
            type: 'path',
            action: '生成了学习路径',
            detail: learningGoal,
            time: new Date().toISOString(),
          });
          localStorage.setItem('activity_logs', JSON.stringify(logs.slice(0, 50)));
          window.dispatchEvent(new Event('activity-updated'));
        } catch {}
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

        // 记录活动日志
        try {
          const logs = JSON.parse(localStorage.getItem('activity_logs') || '[]');
          logs.unshift({
            id: `tutor-${Date.now()}`,
            type: 'tutor',
            action: '解答了一个学习问题',
            detail: q.length > 30 ? q.slice(0, 30) + '...' : q,
            time: new Date().toISOString(),
          });
          localStorage.setItem('activity_logs', JSON.stringify(logs.slice(0, 50)));
          window.dispatchEvent(new Event('activity-updated'));
        } catch {}
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
      const res: any = await api.assess({ user_id: user?.id, assessment_type: 'comprehensive' });
      if (res.success && res.data?.assessment) {
        setAssessment(res.data.assessment);

        // 记录活动日志
        try {
          const logs = JSON.parse(localStorage.getItem('activity_logs') || '[]');
          logs.unshift({
            id: `assess-${Date.now()}`,
            type: 'assess',
            action: '完成了学习效果评估',
            detail: res.data.assessment.grade || '',
            time: new Date().toISOString(),
          });
          localStorage.setItem('activity_logs', JSON.stringify(logs.slice(0, 50)));
          window.dispatchEvent(new Event('activity-updated'));
        } catch {}
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

  // ── 文件导入处理器（只返回数据，不自动保存）──
  const handleImportCourses = async (file: File) => {
    const res = await api.importCoursesFromFile(file);
    if (res.success && Array.isArray(res.data)) {
      // 标准化字段，确保和手动添加格式一致
      return (res.data as any[]).map((c: any) => ({
        name: String(c.name || '').trim(),
        day: String(c.day || '').trim(),
        start_time: String(c.start_time || '').trim(),
        end_time: String(c.end_time || '').trim(),
        location: String(c.location || '').trim(),
        teacher: String(c.teacher || '').trim(),
      })).filter(c => c.name && c.day && c.start_time && c.end_time) as CourseItem[];
    }
    // 识别失败时提示用户手动添加
    throw new Error(res.message || 'AI识别失败，请使用「手动添加」按钮录入课程');
  };

  const handleImportGrades = async (file: File) => {
    const res = await api.importGradesFromFile(file);
    if (res.success && Array.isArray(res.data)) {
      return (res.data as any[]).map((g: any) => ({
        semester: currentSemester,
        course_name: String(g.course_name || '').trim(),
        score: g.score != null ? Number(g.score) : null,
        credits: g.credits != null ? Number(g.credits) : null,
        grade_type: String(g.grade_type || 'overall').trim(),
        exam_date: g.exam_date ? String(g.exam_date).trim() : undefined,
      })).filter(g => g.course_name && g.score != null) as GradeItem[];
    }
    throw new Error(res.error || res.message || 'AI识别失败');
  };

  const handleImportErrors = async (file: File) => {
    const res = await api.importErrorsFromFile(file);
    if (res.success && Array.isArray(res.data)) {
      return (res.data as any[]).map((e: any) => ({
        subject: String(e.subject || '').trim(),
        chapter: String(e.chapter || '').trim(),
        question: String(e.question || '').trim(),
        my_answer: String(e.my_answer || '').trim(),
        correct_answer: String(e.correct_answer || '').trim(),
        error_reason: String(e.error_reason || '').trim(),
        tags: Array.isArray(e.tags) ? e.tags.map((t: any) => String(t).trim()).filter(Boolean) : [],
        mastery: 0,
      })).filter(e => e.subject && e.question) as Omit<ErrorNote, 'id'>[];
    }
    throw new Error(res.error || res.message || 'AI识别失败');
  };

  // ── 确认导入（用户预览后确认保存）──
  const handleConfirmImportCourses = async (imported: CourseItem[]) => {
    // 去重：按 name+day+start_time 去重，新导入的覆盖旧的
    const existingKeys = new Set(imported.map(c => `${c.name}_${c.day}_${c.start_time}`));
    const filteredOld = courses.filter(c => !existingKeys.has(`${c.name}_${c.day}_${c.start_time}`));
    const merged = [...filteredOld, ...imported];
    await handleSaveCourses(currentSemester, merged);
  };

  const handleConfirmImportGrades = async (imported: GradeItem[]) => {
    // 去重：按 course_name 去重，新导入的覆盖旧的
    const existingKeys = new Set(imported.map(g => g.course_name));
    const filteredOld = grades.filter(g => !existingKeys.has(g.course_name));
    const merged = [...filteredOld, ...imported];
    await handleSaveGrades(currentSemester, merged);
  };

  const handleConfirmImportErrors = async (imported: Omit<ErrorNote, 'id'>[]) => {
    for (const note of imported) {
      await handleAddErrorNote(note);
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

  const handleUpdateProfileField = async (field: string, value: any) => {
    // 确保 profileData 是对象
    const currentProfile = profileData || {
      major: '',
      grade_level: '',
      cognitive_style: '',
      knowledge_base: null,
      learning_goals: [],
      interest_areas: [],
      weak_points: [],
      preferred_resources: [],
      learning_history: [],
    };
    
    // 先更新本地状态
    const updatedProfile = { ...currentProfile, [field]: value };
    setProfileData(updatedProfile);
    
    // 保存到 localStorage
    const localKey = `profile_${getUsername()}`;
    localStorage.setItem(localKey, JSON.stringify(updatedProfile));
    
    // 尝试保存到 API
    try {
      const res: any = await api.updateProfileField(field, value);
      if (res.success && res.data) {
        setProfileData(res.data);
        localStorage.setItem(localKey, JSON.stringify(res.data));
      }
    } catch {
      // API 不可用，数据已保存在 localStorage
    }
    
    return { success: true, data: updatedProfile };
  };

  return {
    user, isGuest, activeModule, setActiveModule,
    // 画像
    currentStep, dimensionChats, profileLoading, profileData,
    currentDimension, currentChat, updateCurrentChat,
    handleSendMessage, buildFinalProfile, goToPreviousStep, goToNextStep,
    handleUpdateProfileField,
    // 学生数据管理
    profileTab, setProfileTab, currentSemester, setCurrentSemester, semesters,
    courses, courseLoading, handleSaveCourses,
    grades, gradeLoading, handleSaveGrades,
    errorNotes, errorLoading, handleAddErrorNote, handleToggleMastery, handleDeleteErrorNote,
    handleImportCourses, handleImportGrades, handleImportErrors,
    handleConfirmImportCourses, handleConfirmImportGrades, handleConfirmImportErrors,
    studyPlans, planLoading, handleGeneratePlan,
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
