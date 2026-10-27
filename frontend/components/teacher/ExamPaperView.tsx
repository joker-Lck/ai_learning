'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Sparkles, FileText, Download, Send, Trash2, Pencil, Loader2,
  ClipboardList, CalendarClock, Plus, X, CheckCircle2, AlertCircle,
} from 'lucide-react';
import api from '@/lib/api';

/* ─── 类型 ─── */
interface PaperQuestion {
  id?: number;
  q_index?: number;
  type: string;
  question?: string;
  question_text?: string;
  options?: string[];
  answer?: string;
  reference_answer?: string;
  scoring_points?: string[];
  explanation?: string;
  knowledge_point?: string;
  difficulty?: string;
  score?: number;
}

interface ExamPaper {
  id?: number;
  paper_id?: number;
  title: string;
  subject: string;
  grade: string;
  topic: string;
  paper_type: string;
  total_score: number;
  duration_minutes: number;
  difficulty: string;
  knowledge_points: string[];
  question_source?: string;
  questions: PaperQuestion[];
  status?: string;
  created_at?: string;
  question_count?: number;
}

interface PaperListItem {
  id: number;
  title: string;
  subject: string;
  grade: string;
  topic: string;
  paper_type: string;
  total_score: number;
  duration_minutes: number;
  difficulty: string;
  knowledge_points: string[];
  question_source?: string;
  status: string;
  created_at: string;
  question_count: number;
}

interface AssignmentItem {
  id: number;
  paper_id: number;
  class_id: number;
  title: string;
  paper_title: string;
  subject: string;
  total_score: number;
  paper_type: string;
  due_at: string | null;
  status: string;
  submission_count: number;
  graded_count: number;
  created_at: string;
}

interface ClassItem {
  id: number;
  name: string;
  subject?: string;
}

/* ─── 常量 ─── */
const QUESTION_TYPES = [
  { key: 'multiple_choice', label: '选择题' },
  { key: 'judge', label: '判断题' },
  { key: 'fill_blank', label: '填空题' },
  { key: 'short_answer', label: '简答题' },
] as const;

const DIFFICULTY_OPTIONS = [
  { key: 'mixed', label: '混合难度' },
  { key: 'easy', label: '简单' },
  { key: 'medium', label: '中等' },
  { key: 'hard', label: '困难' },
];

const GRADES = ['小学', '初一', '初二', '初三', '高一', '高二', '高三', '大学'];

const TYPE_BADGE_STYLE: Record<string, string> = {
  multiple_choice: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  judge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
  fill_blank: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  short_answer: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
};

function typeLabel(type: string) {
  return QUESTION_TYPES.find(t => t.key === type)?.label || type || '其他';
}

function difficultyLabel(d?: string) {
  return DIFFICULTY_OPTIONS.find(x => x.key === d)?.label || d || '—';
}

function formatDate(s?: string | null) {
  if (!s) return '—';
  try {
    return new Date(s).toLocaleString('zh-CN', { hour12: false });
  } catch {
    return s;
  }
}

function formatDue(s?: string | null) {
  if (!s) return '未设置';
  try {
    return new Date(s).toLocaleString('zh-CN', { hour12: false });
  } catch {
    return s;
  }
}

/* ─── 小组件 ─── */
function EmptyState({ icon: Icon, title, desc }: { icon: any; title: string; desc: string }) {
  return (
    <div className="text-center py-12">
      <Icon className="w-10 h-10 text-white/10 mx-auto mb-3" />
      <p className="text-white/30 text-sm">{title}</p>
      <p className="text-white/20 text-xs mt-1">{desc}</p>
    </div>
  );
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return <label className="block text-white/40 text-xs mb-1.5">{children}</label>;
}

const inputCls =
  'w-full px-3 py-2.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-white text-sm placeholder:text-white/20 focus:border-purple-500/50 outline-none';

/* ─── 题目卡片 ─── */
function QuestionCard({
  q, index, onScoreChange, onTextChange, onDelete,
}: {
  q: PaperQuestion;
  index: number;
  onScoreChange: (score: number) => void;
  onTextChange: (text: string) => void;
  onDelete: () => void;
}) {
  const isSubjective = q.type === 'short_answer';
  const text = q.question ?? q.question_text ?? '';
  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="w-7 h-7 rounded-full bg-white/[0.08] flex items-center justify-center text-white/70 text-xs font-bold flex-shrink-0">
            {index}
          </span>
          <span className={`px-2 py-0.5 rounded-full text-[11px] border ${TYPE_BADGE_STYLE[q.type] || 'bg-white/10 text-white/50 border-white/10'}`}>
            {typeLabel(q.type)}
          </span>
          {q.difficulty && (
            <span className="px-2 py-0.5 rounded-full text-[11px] bg-white/[0.06] text-white/40 border border-white/[0.06]">
              {difficultyLabel(q.difficulty)}
            </span>
          )}
          {q.knowledge_point && (
            <span className="text-[11px] text-white/30">知识点：{q.knowledge_point}</span>
          )}
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <div className="flex items-center gap-1">
            <span className="text-white/30 text-xs">分值</span>
            <input
              type="number"
              min={0}
              value={q.score ?? 0}
              onChange={e => onScoreChange(Number(e.target.value) || 0)}
              className="w-16 px-2 py-1 rounded-md bg-white/[0.06] border border-white/[0.08] text-white text-xs text-center focus:border-purple-500/50 outline-none"
            />
          </div>
          <button
            onClick={onDelete}
            className="p-1.5 rounded-lg text-red-400/60 hover:text-red-400 hover:bg-red-500/10 transition-colors"
            title="删除该题"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      <textarea
        value={text}
        onChange={e => onTextChange(e.target.value)}
        rows={Math.min(4, Math.max(2, Math.ceil(text.length / 40)))}
        className="w-full px-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.06] text-white/90 text-sm leading-relaxed focus:border-purple-500/50 outline-none resize-y"
      />

      {q.type === 'multiple_choice' && q.options && q.options.length > 0 && (
        <div className="mt-3 space-y-1.5">
          {q.options.map((opt, oi) => (
            <div key={oi} className="flex items-start gap-2 text-sm">
              <span className="text-white/30 w-5 flex-shrink-0 mt-0.5">{String.fromCharCode(65 + oi)}.</span>
              <span className="text-white/70">{opt}</span>
            </div>
          ))}
        </div>
      )}

      {q.type === 'judge' && q.options && q.options.length > 0 && (
        <div className="mt-3 flex items-center gap-2 text-sm">
          <span className="text-white/30">选项：</span>
          {q.options.map((opt, oi) => (
            <span key={oi} className="px-2 py-0.5 rounded bg-white/[0.06] text-white/60 text-xs">{opt}</span>
          ))}
        </div>
      )}

      <div className="mt-3 space-y-1.5 text-sm">
        <div className="flex items-start gap-2">
          <span className="text-emerald-400/70 text-xs flex-shrink-0 mt-0.5 w-12">答案</span>
          <span className="text-white/75">{q.answer || '—'}</span>
        </div>
        {isSubjective && q.reference_answer && (
          <div className="flex items-start gap-2">
            <span className="text-blue-400/70 text-xs flex-shrink-0 mt-0.5 w-12">参考答</span>
            <span className="text-white/70">{q.reference_answer}</span>
          </div>
        )}
        {isSubjective && q.scoring_points && q.scoring_points.length > 0 && (
          <div className="flex items-start gap-2">
            <span className="text-purple-400/70 text-xs flex-shrink-0 mt-0.5 w-12">评分点</span>
            <ul className="space-y-0.5">
              {q.scoring_points.map((p, pi) => (
                <li key={pi} className="text-white/60 text-xs">· {p}</li>
              ))}
            </ul>
          </div>
        )}
        {q.explanation && (
          <div className="flex items-start gap-2">
            <span className="text-white/30 text-xs flex-shrink-0 mt-0.5 w-12">解析</span>
            <span className="text-white/55 text-xs leading-relaxed">{q.explanation}</span>
          </div>
        )}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   教师端 — AI 出题 / 组卷
   ═══════════════════════════════════════════ */
export default function ExamPaperView() {
  /* ── 顶层 Tab ── */
  const [tab, setTab] = useState<'generate' | 'papers' | 'assignments'>('generate');

  /* ── 消息 ── */
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const flash = useCallback((msg: string) => {
    setMessage(msg);
    setError(null);
    window.setTimeout(() => setMessage(null), 4000);
  }, []);

  /* ── 生成表单 ── */
  const [subject, setSubject] = useState('');
  const [grade, setGrade] = useState('初一');
  const [topic, setTopic] = useState('');
  const [kpText, setKpText] = useState('');
  const [difficulty, setDifficulty] = useState('mixed');
  const [paperType, setPaperType] = useState('practice');
  const [totalScore, setTotalScore] = useState(100);
  const [durationMinutes, setDurationMinutes] = useState(60);
  const [qMultiple, setQMultiple] = useState(5);
  const [qJudge, setQJudge] = useState(3);
  const [qFill, setQFill] = useState(3);
  const [qShort, setQShort] = useState(2);
  const [useBank, setUseBank] = useState(true);
  const [generating, setGenerating] = useState(false);

  /* ── 试卷预览 / 编辑 ── */
  const [paper, setPaper] = useState<ExamPaper | null>(null);
  const [paperId, setPaperId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState(false);

  /* ── 我的试卷 ── */
  const [papers, setPapers] = useState<PaperListItem[]>([]);
  const [papersLoading, setPapersLoading] = useState(false);

  /* ── 发布管理 ── */
  const [assignments, setAssignments] = useState<AssignmentItem[]>([]);
  const [assignLoading, setAssignLoading] = useState(false);

  /* ── 发布弹窗 ── */
  const [publishOpen, setPublishOpen] = useState(false);
  const [publishPaperId, setPublishPaperId] = useState<number | null>(null);
  const [classes, setClasses] = useState<ClassItem[]>([]);
  const [classId, setClassId] = useState('');
  const [dueAt, setDueAt] = useState('');
  const [publishing, setPublishing] = useState(false);

  /* ─────────── 数据加载 ─────────── */
  const loadPapers = useCallback(async () => {
    setPapersLoading(true);
    try {
      const res: any = await api.listExamPapers();
      if (res.success) setPapers(res.data || []);
      else setError(res.message || res.error || '加载试卷列表失败');
    } catch (e: any) {
      setError(e?.message || '加载试卷列表失败');
    }
    setPapersLoading(false);
  }, []);

  const loadAssignments = useCallback(async () => {
    setAssignLoading(true);
    try {
      const res: any = await api.listExamAssignments();
      if (res.success) setAssignments(res.data || []);
      else setError(res.message || res.error || '加载发布列表失败');
    } catch (e: any) {
      setError(e?.message || '加载发布列表失败');
    }
    setAssignLoading(false);
  }, []);

  useEffect(() => {
    if (tab === 'papers') loadPapers();
    if (tab === 'assignments') loadAssignments();
  }, [tab, loadPapers, loadAssignments]);

  /* ─────────── 生成试卷 ─────────── */
  const handleGenerate = useCallback(async () => {
    if (!subject.trim() || !topic.trim()) {
      setError('请填写学科和主题');
      return;
    }
    setGenerating(true);
    setError(null);
    setMessage(null);
    try {
      const knowledge_points = kpText
        .split(/[,，]/)
        .map(s => s.trim())
        .filter(Boolean);
      const res: any = await api.generateExamPaper({
        subject: subject.trim(),
        grade,
        topic: topic.trim(),
        knowledge_points,
        difficulty,
        paper_type: paperType,
        total_score: Number(totalScore) || 100,
        duration_minutes: Number(durationMinutes) || 60,
        question_spec: {
          multiple_choice: Number(qMultiple) || 0,
          judge: Number(qJudge) || 0,
          fill_blank: Number(qFill) || 0,
          short_answer: Number(qShort) || 0,
        },
        use_bank: useBank,
      });
      if (res.success && res.data) {
        const data = res.data as ExamPaper;
        setPaper({ ...data, questions: data.questions || [] });
        setPaperId(null);
        flash(res.message || '试卷生成成功，请预览并编辑');
      } else {
        setError(res.message || res.error || '生成试卷失败');
      }
    } catch (e: any) {
      setError(e?.message || '生成试卷失败，请稍后重试');
    }
    setGenerating(false);
  }, [subject, grade, topic, kpText, difficulty, paperType, totalScore, durationMinutes, qMultiple, qJudge, qFill, qShort, useBank, flash]);

  /* ─────────── 题目编辑 ─────────── */
  const updateQuestion = useCallback((idx: number, patch: Partial<PaperQuestion>) => {
    setPaper(prev => {
      if (!prev) return prev;
      const questions = prev.questions.map((q, i) => {
        if (i !== idx) return q;
        const next = { ...q, ...patch };
        // 同步两种题干字段，兼容生成 / 已存试卷
        if (patch.question_text !== undefined) next.question = patch.question_text;
        if (patch.question !== undefined) next.question_text = patch.question;
        return next;
      });
      return { ...prev, questions };
    });
  }, []);

  const deleteQuestion = useCallback((idx: number) => {
    setPaper(prev => {
      if (!prev) return prev;
      return { ...prev, questions: prev.questions.filter((_, i) => i !== idx) };
    });
  }, []);

  const computedScore = useMemo(
    () => (paper?.questions || []).reduce((s, q) => s + (Number(q.score) || 0), 0),
    [paper]
  );

  const groupedQuestions = useMemo(() => {
    if (!paper) return [];
    return QUESTION_TYPES.map(t => ({
      key: t.key,
      label: t.label,
      items: paper.questions
        .map((q, index) => ({ q, index }))
        .filter(x => (x.q.type || '') === t.key),
    })).filter(g => g.items.length > 0);
  }, [paper]);

  /* ─────────── 保存 / 更新 ─────────── */
  const handleSave = useCallback(async () => {
    if (!paper) return;
    if (!paper.title?.trim()) {
      setError('请填写试卷标题');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const knowledge_points = (paper.knowledge_points || []).filter(Boolean);
      if (paperId != null) {
        // 更新已有试卷：保留 id / q_index，仅提交可变字段
        const questions = paper.questions.map(q => ({
          id: q.id,
          q_index: q.q_index,
          question_text: q.question ?? q.question_text ?? '',
          options: q.options || [],
          answer: q.answer ?? '',
          reference_answer: q.reference_answer ?? '',
          scoring_points: q.scoring_points || [],
          explanation: q.explanation ?? '',
          knowledge_point: q.knowledge_point ?? '',
          difficulty: q.difficulty ?? 'medium',
          score: Number(q.score) || 0,
        }));
        const res: any = await api.updateExamPaper(paperId, {
          title: paper.title,
          subject: paper.subject,
          grade: paper.grade,
          topic: paper.topic,
          paper_type: paper.paper_type,
          total_score: computedScore,
          duration_minutes: paper.duration_minutes,
          difficulty: paper.difficulty,
          knowledge_points,
          questions,
        });
        if (res.success) {
          flash(res.message || '试卷已保存');
          loadPapers();
        } else {
          setError(res.message || res.error || '保存失败');
        }
      } else {
        // 新建试卷
        const payload = {
          ...paper,
          total_score: computedScore,
          knowledge_points,
          questions: paper.questions.map(q => ({
            ...q,
            question: q.question ?? q.question_text ?? '',
            question_text: q.question ?? q.question_text ?? '',
            score: Number(q.score) || 0,
          })),
        };
        const res: any = await api.saveExamPaper(payload);
        if (res.success && res.data?.paper_id) {
          setPaperId(res.data.paper_id);
          flash(res.message || `试卷已保存（ID: ${res.data.paper_id}）`);
          loadPapers();
        } else if (res.success) {
          flash(res.message || '试卷已保存');
          loadPapers();
        } else {
          setError(res.message || res.error || '保存失败');
        }
      }
    } catch (e: any) {
      setError(e?.message || '保存失败');
    }
    setSaving(false);
  }, [paper, paperId, computedScore, flash, loadPapers]);

  /* ─────────── 导出 DOCX ─────────── */
  const handleExport = useCallback(async (id: number) => {
    setExporting(true);
    setError(null);
    try {
      const res: any = await api.exportExamPaper(id);
      if (res.success && res.data?.filename) {
        const ok = await api.downloadExamFile(res.data.filename);
        flash(ok ? (res.message || '导出成功') : '导出成功但下载失败，请重试');
      } else {
        setError(res.message || res.error || '导出失败');
      }
    } catch (e: any) {
      setError(e?.message || '导出失败');
    }
    setExporting(false);
  }, [flash]);

  /* ─────────── 发布 ─────────── */
  const openPublish = useCallback(async (id: number) => {
    setPublishPaperId(id);
    setPublishOpen(true);
    setClassId('');
    setDueAt('');
    setError(null);
    try {
      const res: any = await api.listClasses();
      if (res.success) setClasses(res.data || []);
    } catch {
      setClasses([]);
    }
  }, []);

  const handlePublish = useCallback(async () => {
    if (publishPaperId == null) return;
    if (!classId) {
      setError('请选择班级');
      return;
    }
    setPublishing(true);
    setError(null);
    try {
      const res: any = await api.assignExamPaper(publishPaperId, {
        class_id: Number(classId),
        due_at: dueAt || undefined,
        allow_late: true,
      });
      if (res.success) {
        flash(res.message || '已发布到班级');
        setPublishOpen(false);
        setTab('assignments');
        loadAssignments();
      } else {
        setError(res.message || res.error || '发布失败');
      }
    } catch (e: any) {
      setError(e?.message || '发布失败');
    }
    setPublishing(false);
  }, [publishPaperId, classId, dueAt, flash, loadAssignments]);

  /* ─────────── 我的试卷操作 ─────────── */
  const handleEdit = useCallback(async (id: number) => {
    setError(null);
    try {
      const res: any = await api.getExamPaper(id);
      if (res.success && res.data) {
        const data = res.data as ExamPaper;
        setPaper({ ...data, questions: data.questions || [] });
        setPaperId(data.id ?? id);
        setTab('generate');
        flash('已加载试卷，可编辑后保存');
      } else {
        setError(res.message || res.error || '加载试卷失败');
      }
    } catch (e: any) {
      setError(e?.message || '加载试卷失败');
    }
  }, [flash]);

  const handleDeletePaper = useCallback(async (id: number, title: string) => {
    if (!window.confirm(`确定删除试卷「${title}」？此操作不可恢复。`)) return;
    setError(null);
    try {
      const res: any = await api.deleteExamPaper(id);
      if (res.success) {
        flash(res.message || '试卷已删除');
        loadPapers();
      } else {
        setError(res.message || res.error || '删除失败');
      }
    } catch (e: any) {
      setError(e?.message || '删除失败');
    }
  }, [flash, loadPapers]);

  /* ─────────── 发布管理：截止 ─────────── */
  const handleCloseAssignment = useCallback(async (id: number) => {
    if (!window.confirm('确定截止该次考试发布？')) return;
    setError(null);
    try {
      const res: any = await api.closeExamAssignment(id);
      if (res.success) {
        flash(res.message || '已截止');
        loadAssignments();
      } else {
        setError(res.message || res.error || '操作失败');
      }
    } catch (e: any) {
      setError(e?.message || '操作失败');
    }
  }, [flash, loadAssignments]);

  /* ═══════════ 渲染 ═══════════ */
  return (
    <div className="space-y-6">
      {/* 消息条 */}
      {error && (
        <div className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-red-500/10 border border-red-500/20">
          <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
          <p className="text-red-400 text-xs">{error}</p>
        </div>
      )}
      {message && (
        <div className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <p className="text-emerald-300 text-xs">{message}</p>
        </div>
      )}

      {/* ─── Tab 导航 ─── */}
      <div className="flex items-center gap-2 bg-white/[0.04] rounded-xl p-1 w-fit">
        <button
          onClick={() => setTab('generate')}
          className={`px-5 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
            tab === 'generate' ? 'bg-purple-600 text-white shadow-lg' : 'text-white/50 hover:text-white/80'
          }`}
        >
          <Sparkles className="w-4 h-4" /> 生成试卷
        </button>
        <button
          onClick={() => setTab('papers')}
          className={`px-5 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
            tab === 'papers' ? 'bg-purple-600 text-white shadow-lg' : 'text-white/50 hover:text-white/80'
          }`}
        >
          <FileText className="w-4 h-4" /> 我的试卷
        </button>
        <button
          onClick={() => setTab('assignments')}
          className={`px-5 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
            tab === 'assignments' ? 'bg-purple-600 text-white shadow-lg' : 'text-white/50 hover:text-white/80'
          }`}
        >
          <CalendarClock className="w-4 h-4" /> 发布管理
        </button>
      </div>

      {/* ═══════════ Tab1 生成试卷 ═══════════ */}
      {tab === 'generate' && (
        <>
          <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-6">
            <h2 className="text-white font-bold text-xl mb-1 flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-purple-400" /> AI 出题 / 组卷
            </h2>
            <p className="text-white/30 text-sm mb-6">按学科、知识点与题型配置一键生成试卷，支持题库复用与 DOCX 导出</p>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
              <div>
                <FieldLabel>学科 *</FieldLabel>
                <input value={subject} onChange={e => setSubject(e.target.value)} placeholder="如：数学"
                  className={inputCls} />
              </div>
              <div>
                <FieldLabel>年级</FieldLabel>
                <select value={grade} onChange={e => setGrade(e.target.value)}
                  className={`${inputCls} cursor-pointer`}>
                  {GRADES.map(g => <option key={g} value={g} className="bg-gray-800">{g}</option>)}
                </select>
              </div>
              <div>
                <FieldLabel>主题 *</FieldLabel>
                <input value={topic} onChange={e => setTopic(e.target.value)} placeholder="如：一元二次方程"
                  className={inputCls} />
              </div>
              <div>
                <FieldLabel>难度</FieldLabel>
                <select value={difficulty} onChange={e => setDifficulty(e.target.value)}
                  className={`${inputCls} cursor-pointer`}>
                  {DIFFICULTY_OPTIONS.map(d => <option key={d.key} value={d.key} className="bg-gray-800">{d.label}</option>)}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
              <div>
                <FieldLabel>试卷类型</FieldLabel>
                <select value={paperType} onChange={e => setPaperType(e.target.value)}
                  className={`${inputCls} cursor-pointer`}>
                  <option value="practice" className="bg-gray-800">练习卷</option>
                  <option value="exam" className="bg-gray-800">考试卷</option>
                </select>
              </div>
              <div>
                <FieldLabel>总分</FieldLabel>
                <input type="number" min={10} value={totalScore}
                  onChange={e => setTotalScore(Number(e.target.value) || 100)}
                  className={inputCls} />
              </div>
              <div>
                <FieldLabel>时长（分钟）</FieldLabel>
                <input type="number" min={10} value={durationMinutes}
                  onChange={e => setDurationMinutes(Number(e.target.value) || 60)}
                  className={inputCls} />
              </div>
              <div>
                <FieldLabel>知识点（逗号分隔）</FieldLabel>
                <input value={kpText} onChange={e => setKpText(e.target.value)} placeholder="如：因式分解,韦达定理"
                  className={inputCls} />
              </div>
            </div>

            {/* 题型数量 */}
            <div className="mb-4">
              <FieldLabel>题型数量</FieldLabel>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.06]">
                  <span className="text-white/50 text-xs flex-1">选择题</span>
                  <input type="number" min={0} value={qMultiple}
                    onChange={e => setQMultiple(Number(e.target.value) || 0)}
                    className="w-16 px-2 py-1 rounded-md bg-white/[0.06] border border-white/[0.08] text-white text-sm text-center focus:border-purple-500/50 outline-none" />
                </div>
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.06]">
                  <span className="text-white/50 text-xs flex-1">判断题</span>
                  <input type="number" min={0} value={qJudge}
                    onChange={e => setQJudge(Number(e.target.value) || 0)}
                    className="w-16 px-2 py-1 rounded-md bg-white/[0.06] border border-white/[0.08] text-white text-sm text-center focus:border-purple-500/50 outline-none" />
                </div>
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.06]">
                  <span className="text-white/50 text-xs flex-1">填空题</span>
                  <input type="number" min={0} value={qFill}
                    onChange={e => setQFill(Number(e.target.value) || 0)}
                    className="w-16 px-2 py-1 rounded-md bg-white/[0.06] border border-white/[0.08] text-white text-sm text-center focus:border-purple-500/50 outline-none" />
                </div>
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.06]">
                  <span className="text-white/50 text-xs flex-1">简答题</span>
                  <input type="number" min={0} value={qShort}
                    onChange={e => setQShort(Number(e.target.value) || 0)}
                    className="w-16 px-2 py-1 rounded-md bg-white/[0.06] border border-white/[0.08] text-white text-sm text-center focus:border-purple-500/50 outline-none" />
                </div>
              </div>
            </div>

            {/* use_bank */}
            <label className="flex items-center gap-2 mb-5 cursor-pointer select-none w-fit">
              <input
                type="checkbox"
                checked={useBank}
                onChange={e => setUseBank(e.target.checked)}
                className="w-4 h-4 rounded border-white/20 bg-white/10 text-purple-500 focus:ring-purple-500/40 cursor-pointer"
              />
              <span className="text-white/60 text-sm">优先复用题库</span>
            </label>

            <button
              onClick={handleGenerate}
              disabled={generating || !subject.trim() || !topic.trim()}
              className="px-8 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 text-white font-medium text-sm
                         hover:from-purple-500 hover:to-blue-500 transition-all disabled:opacity-40 disabled:cursor-not-allowed
                         flex items-center gap-2 shadow-lg shadow-purple-500/20"
            >
              {generating ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5" />}
              {generating ? '正在生成试卷…' : 'AI 生成试卷'}
            </button>
          </div>

          {/* ─── 预览编辑区 ─── */}
          {paper && (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-6"
            >
              <div className="flex items-start justify-between gap-4 mb-5 flex-wrap">
                <div className="flex-1 min-w-[240px]">
                  <FieldLabel>试卷标题</FieldLabel>
                  <input
                    value={paper.title || ''}
                    onChange={e => setPaper(p => (p ? { ...p, title: e.target.value } : p))}
                    className={`${inputCls} text-base font-medium`}
                  />
                  <div className="flex items-center gap-3 mt-2 text-xs text-white/35 flex-wrap">
                    <span>{paper.subject}</span>
                    <span>·</span>
                    <span>{paper.grade}</span>
                    <span>·</span>
                    <span>{paper.topic}</span>
                    <span>·</span>
                    <span>{paper.paper_type === 'exam' ? '考试卷' : '练习卷'}</span>
                    <span>·</span>
                    <span>{difficultyLabel(paper.difficulty)}</span>
                    <span>·</span>
                    <span>{paper.duration_minutes} 分钟</span>
                    {paper.question_source && (
                      <>
                        <span>·</span>
                        <span>来源：{paper.question_source}</span>
                      </>
                    )}
                  </div>
                  {(paper.knowledge_points || []).length > 0 && (
                    <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                      {paper.knowledge_points.map((kp, i) => (
                        <span key={i} className="px-2 py-0.5 rounded-full bg-white/[0.06] text-white/40 text-[11px]">
                          {kp}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="px-5 py-2.5 rounded-lg bg-gradient-to-r from-purple-600 to-blue-600 text-white text-sm font-medium
                               hover:from-purple-500 hover:to-blue-500 transition-all flex items-center gap-2 shadow-lg disabled:opacity-50"
                  >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                    保存试卷
                  </button>
                  <button
                    onClick={() => {
                      if (paperId == null) {
                        setError('请先保存试卷，再导出 DOCX');
                        return;
                      }
                      handleExport(paperId);
                    }}
                    disabled={exporting || paperId == null}
                    className="px-5 py-2.5 rounded-lg bg-gradient-to-r from-blue-600 to-cyan-600 text-white text-sm font-medium
                               hover:from-blue-500 hover:to-cyan-500 transition-all flex items-center gap-2 shadow-lg disabled:opacity-50"
                    title={paperId == null ? '保存后可导出' : '导出 DOCX'}
                  >
                    {exporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                    导出 DOCX
                  </button>
                  <button
                    onClick={() => {
                      if (paperId == null) {
                        setError('请先保存试卷，再发布到班级');
                        return;
                      }
                      openPublish(paperId);
                    }}
                    disabled={paperId == null}
                    className="px-5 py-2.5 rounded-lg bg-gradient-to-r from-emerald-600 to-green-600 text-white text-sm font-medium
                               hover:from-emerald-500 hover:to-green-500 transition-all flex items-center gap-2 shadow-lg disabled:opacity-50"
                    title={paperId == null ? '保存后可发布' : '发布到班级'}
                  >
                    <Send className="w-4 h-4" /> 发布到班级
                  </button>
                </div>
              </div>

              {/* 题目分组 */}
              {groupedQuestions.length === 0 ? (
                <EmptyState icon={ClipboardList} title="暂无题目" desc="生成试卷后题目将显示在这里" />
              ) : (
                <div className="space-y-6">
                  {groupedQuestions.map(group => (
                    <div key={group.key}>
                      <h3 className="text-white/70 font-medium text-sm mb-3 flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded-full text-[11px] border ${TYPE_BADGE_STYLE[group.key] || ''}`}>
                          {group.label}
                        </span>
                        <span className="text-white/30 text-xs">{group.items.length} 题</span>
                      </h3>
                      <div className="space-y-3">
                        {group.items.map(({ q, index }) => (
                          <QuestionCard
                            key={q.id ?? `q-${index}`}
                            q={q}
                            index={index + 1}
                            onScoreChange={score => updateQuestion(index, { score })}
                            onTextChange={text => updateQuestion(index, { question_text: text })}
                            onDelete={() => deleteQuestion(index)}
                          />
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* 底部统计 */}
              <div className="mt-5 pt-4 border-t border-white/[0.06] flex items-center justify-between">
                <p className="text-white/40 text-sm">
                  已选 <span className="text-white font-medium">{paper.questions.length}</span> 题
                  <span className="mx-2 text-white/20">/</span>
                  合计 <span className="text-purple-300 font-medium">{computedScore}</span> 分
                </p>
                {paper.status && (
                  <span className={`px-2.5 py-1 rounded-full text-xs ${
                    paper.status === 'published'
                      ? 'bg-emerald-500/15 text-emerald-300'
                      : 'bg-white/[0.06] text-white/40'
                  }`}>
                    {paper.status === 'published' ? '已发布' : paper.status === 'draft' ? '草稿' : paper.status}
                  </span>
                )}
              </div>
            </motion.div>
          )}
        </>
      )}

      {/* ═══════════ Tab2 我的试卷 ═══════════ */}
      {tab === 'papers' && (
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-6">
          <h2 className="text-white font-bold text-xl mb-1 flex items-center gap-2">
            <FileText className="w-6 h-6 text-purple-400" /> 我的试卷
          </h2>
          <p className="text-white/30 text-sm mb-6">管理已保存的试卷，支持编辑、导出、发布与删除</p>

          {papersLoading ? (
            <div className="text-white/30 text-sm py-12 text-center">加载中...</div>
          ) : papers.length === 0 ? (
            <EmptyState icon={FileText} title="暂无试卷" desc="去「生成试卷」创建第一份试卷吧" />
          ) : (
            <div className="space-y-3">
              {papers.map(p => (
                <div
                  key={p.id}
                  className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-4 flex items-center gap-4 flex-wrap"
                >
                  <div className="flex-1 min-w-[200px]">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-white font-medium text-sm">{p.title}</p>
                      <span className={`px-2 py-0.5 rounded-full text-[11px] ${
                        p.status === 'published'
                          ? 'bg-emerald-500/15 text-emerald-300'
                          : 'bg-white/[0.06] text-white/40'
                      }`}>
                        {p.status === 'published' ? '已发布' : '草稿'}
                      </span>
                      <span className="px-2 py-0.5 rounded-full text-[11px] bg-purple-500/15 text-purple-300">
                        {p.paper_type === 'exam' ? '考试卷' : '练习卷'}
                      </span>
                    </div>
                    <div className="flex items-center gap-2.5 mt-1.5 text-xs text-white/30 flex-wrap">
                      <span>{p.subject}</span>
                      <span>·</span>
                      <span>{p.grade}</span>
                      {p.topic && (<><span>·</span><span>{p.topic}</span></>)}
                      <span>·</span>
                      <span>{p.question_count} 题</span>
                      <span>·</span>
                      <span>{p.total_score} 分</span>
                      <span>·</span>
                      <span>{p.duration_minutes} 分钟</span>
                      <span>·</span>
                      <span>{formatDate(p.created_at)}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleEdit(p.id)}
                      className="px-3 py-1.5 rounded-lg bg-white/[0.06] border border-white/[0.08] text-white/70 text-xs hover:text-white hover:border-white/20 transition-all flex items-center gap-1"
                    >
                      <Pencil className="w-3.5 h-3.5" /> 编辑
                    </button>
                    <button
                      onClick={() => handleExport(p.id)}
                      disabled={exporting}
                      className="px-3 py-1.5 rounded-lg bg-blue-500/15 border border-blue-500/20 text-blue-300 text-xs hover:bg-blue-500/25 transition-all flex items-center gap-1 disabled:opacity-50"
                    >
                      {exporting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                      导出
                    </button>
                    <button
                      onClick={() => openPublish(p.id)}
                      className="px-3 py-1.5 rounded-lg bg-emerald-500/15 border border-emerald-500/20 text-emerald-300 text-xs hover:bg-emerald-500/25 transition-all flex items-center gap-1"
                    >
                      <Send className="w-3.5 h-3.5" /> 发布
                    </button>
                    <button
                      onClick={() => handleDeletePaper(p.id, p.title)}
                      className="px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/15 text-red-400/80 text-xs hover:text-red-400 hover:bg-red-500/20 transition-all flex items-center gap-1"
                    >
                      <Trash2 className="w-3.5 h-3.5" /> 删除
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ═══════════ Tab3 发布管理 ═══════════ */}
      {tab === 'assignments' && (
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-6">
          <h2 className="text-white font-bold text-xl mb-1 flex items-center gap-2">
            <CalendarClock className="w-6 h-6 text-purple-400" /> 发布管理
          </h2>
          <p className="text-white/30 text-sm mb-6">查看已发布试卷的提交与批改进度，可手动截止</p>

          {assignLoading ? (
            <div className="text-white/30 text-sm py-12 text-center">加载中...</div>
          ) : assignments.length === 0 ? (
            <EmptyState
              icon={CalendarClock}
              title="暂无发布记录"
              desc="在「生成试卷」或「我的试卷」中将试卷发布到班级后，记录会显示在这里"
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-white/30 text-xs border-b border-white/[0.06]">
                    <th className="text-left py-2.5 pr-3 font-medium">试卷标题</th>
                    <th className="text-left py-2.5 pr-3 font-medium">学科</th>
                    <th className="text-left py-2.5 pr-3 font-medium">提交数</th>
                    <th className="text-left py-2.5 pr-3 font-medium">已批改</th>
                    <th className="text-left py-2.5 pr-3 font-medium">截止时间</th>
                    <th className="text-left py-2.5 pr-3 font-medium">状态</th>
                    <th className="text-right py-2.5 font-medium">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {assignments.map(a => (
                    <tr key={a.id} className="border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors">
                      <td className="py-3 pr-3">
                        <p className="text-white/85 font-medium">{a.paper_title || a.title}</p>
                        <p className="text-white/25 text-xs mt-0.5">
                          {a.paper_type === 'exam' ? '考试卷' : '练习卷'} · {a.total_score} 分
                        </p>
                      </td>
                      <td className="py-3 pr-3 text-white/50">{a.subject}</td>
                      <td className="py-3 pr-3 text-white/70">{a.submission_count}</td>
                      <td className="py-3 pr-3 text-white/70">{a.graded_count}</td>
                      <td className="py-3 pr-3 text-white/50 text-xs">{formatDue(a.due_at)}</td>
                      <td className="py-3 pr-3">
                        <span className={`px-2 py-0.5 rounded-full text-[11px] ${
                          a.status === 'active'
                            ? 'bg-emerald-500/15 text-emerald-300'
                            : 'bg-white/[0.06] text-white/40'
                        }`}>
                          {a.status === 'active' ? '进行中' : a.status === 'closed' ? '已截止' : a.status}
                        </span>
                      </td>
                      <td className="py-3 text-right">
                        {a.status === 'active' ? (
                          <button
                            onClick={() => handleCloseAssignment(a.id)}
                            className="px-3 py-1.5 rounded-lg bg-white/[0.06] border border-white/[0.08] text-white/60 text-xs hover:text-white hover:border-white/20 transition-all"
                          >
                            截止
                          </button>
                        ) : (
                          <span className="text-white/20 text-xs">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ═══════════ 发布到班级 Modal ═══════════ */}
      {publishOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.2 }}
            className="w-full max-w-md rounded-xl border border-white/[0.08] bg-[#111827] p-6 shadow-2xl"
          >
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-white font-bold text-lg flex items-center gap-2">
                <Send className="w-5 h-5 text-emerald-400" /> 发布到班级
              </h3>
              <button
                onClick={() => setPublishOpen(false)}
                className="p-1.5 rounded-lg text-white/30 hover:text-white/60 hover:bg-white/[0.06] transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <FieldLabel>选择班级 *</FieldLabel>
                <select
                  value={classId}
                  onChange={e => setClassId(e.target.value)}
                  className={`${inputCls} cursor-pointer`}
                >
                  <option value="" className="bg-gray-800">-- 请选择班级 --</option>
                  {classes.map(c => (
                    <option key={c.id} value={c.id} className="bg-gray-800">
                      {c.name}{c.subject ? `（${c.subject}）` : ''}
                    </option>
                  ))}
                </select>
                {classes.length === 0 && (
                  <p className="text-white/25 text-xs mt-1.5">暂无可用班级，请先创建班级</p>
                )}
              </div>
              <div>
                <FieldLabel>截止时间</FieldLabel>
                <input
                  type="datetime-local"
                  value={dueAt}
                  onChange={e => setDueAt(e.target.value)}
                  className={`${inputCls} [color-scheme:dark]`}
                />
                <p className="text-white/25 text-xs mt-1.5">不填则长期有效，学生可在截止前提交</p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 mt-6">
              <button
                onClick={() => setPublishOpen(false)}
                className="px-4 py-2 rounded-lg text-white/50 text-sm hover:text-white/80 hover:bg-white/[0.06] transition-all"
              >
                取消
              </button>
              <button
                onClick={handlePublish}
                disabled={publishing || !classId}
                className="px-5 py-2 rounded-lg bg-gradient-to-r from-emerald-600 to-green-600 text-white text-sm font-medium
                           hover:from-emerald-500 hover:to-green-500 transition-all flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {publishing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                确认发布
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
