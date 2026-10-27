'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  AlertTriangle, Award, BarChart3, BookOpen, CheckCircle2, ChevronDown, ChevronLeft,
  ClipboardCheck, Clock, FileText, GraduationCap, Image as ImageIcon, Loader2,
  Plus, RefreshCw, Save, Sparkles, Target, TrendingUp, Upload, Users, X,
} from 'lucide-react';
import api from '@/lib/api';

/* ═══════════ 类型 ═══════════ */

interface AssignmentRow {
  id: number;
  paper_id: number;
  class_id: number;
  title: string;
  paper_title: string;
  subject: string;
  total_score: number;
  paper_type: string;
  due_at?: string | null;
  status: string;
  submission_count: number;
  graded_count: number;
  created_at: string;
}

interface SubmissionRow {
  id: number;
  assignment_id: number;
  paper_id: number;
  student_id: number;
  student_name: string;
  status: string;
  objective_score?: number | null;
  ai_score?: number | null;
  final_score?: number | null;
  total_score: number;
  answer_count: number;
  graded_count: number;
  submitted_at?: string | null;
}

interface QuestionRow {
  id: number;
  q_index: number;
  question_type: string;
  question_text: string;
  options?: unknown;
  answer?: string | null;
  reference_answer?: string | null;
  scoring_points?: unknown;
  explanation?: string | null;
  knowledge_point?: string | null;
  difficulty?: string | null;
  score: number;
}

interface RagEvidence {
  title?: string;
  content?: string;
  score?: number | string;
  source?: string;
}

interface KnowledgeHits {
  hits?: unknown;
  missing?: unknown;
}

interface AnswerRow {
  id?: number | null;
  question_id: number;
  q_index?: number | null;
  question_type?: string | null;
  question_text?: string | null;
  answer_text?: string | null;
  answer_image_path?: string | null;
  ocr_text?: string | null;
  ocr_confidence?: number | null;
  ocr_engine?: string | null;
  correct_answer?: string | null;
  reference_answer?: string | null;
  max_score?: number | null;
  is_correct?: boolean | null;
  ai_score?: number | null;
  score?: number | null;
  feedback?: string | null;
  rag_evidence?: RagEvidence[] | null;
  knowledge_hits?: KnowledgeHits | null;
  grade_status?: string | null;
  teacher_score?: number | null;
  teacher_feedback?: string | null;
  reviewed_at?: string | null;
}

interface MergedItem {
  key: number;
  question: QuestionRow | null;
  answer: AnswerRow | null;
}

/* ═══════════ 工具函数 ═══════════ */

function toStrArray(v: unknown): string[] {
  if (Array.isArray(v)) return v.map((x) => String(x));
  if (typeof v === 'string' && v.trim()) {
    try {
      const p = JSON.parse(v);
      if (Array.isArray(p)) return p.map((x) => String(x));
    } catch {
      /* 非 JSON 字符串按单条处理 */
    }
    return [v];
  }
  if (v && typeof v === 'object') {
    return Object.entries(v).map(([k, val]) => `${k}. ${String(val)}`);
  }
  return [];
}

function toRagList(v: unknown): RagEvidence[] {
  return Array.isArray(v) ? (v as RagEvidence[]).filter((x) => x && typeof x === 'object') : [];
}

function num(v: unknown, fallback = 0): number {
  const n = typeof v === 'number' ? v : Number(v);
  return Number.isFinite(n) ? n : fallback;
}

function fmtScore(v: unknown): string {
  if (v === null || v === undefined || v === '') return '—';
  const n = Number(v);
  return Number.isFinite(n) ? String(Math.round(n * 100) / 100) : '—';
}

function pct(v: unknown): string {
  const n = Number(v);
  if (!Number.isFinite(n)) return '—';
  return `${Math.round((n <= 1 ? n * 100 : n) * 10) / 10}%`;
}

function confLabel(v: unknown): string {
  const n = Number(v);
  if (!Number.isFinite(n)) return '—';
  return `${Math.round(n <= 1 ? n * 100 : n)}%`;
}

function typeLabel(t?: string | null): string {
  const map: Record<string, string> = {
    single_choice: '单选题', multi_choice: '多选题', true_false: '判断题',
    fill_blank: '填空题', short_answer: '简答题', essay: '论述题',
    subjective: '主观题', objective: '客观题', choice: '选择题', blank: '填空题',
  };
  return (t && (map[t] ?? t)) || '题目';
}

function subStatusChip(status?: string | null) {
  if (status === 'in_progress') return { label: '进行中', cls: 'bg-amber-500/15 text-amber-300 border-amber-400/30' };
  if (status === 'submitted') return { label: '已提交', cls: 'bg-blue-500/15 text-blue-300 border-blue-400/30' };
  if (status === 'graded') return { label: '已批改', cls: 'bg-emerald-500/15 text-emerald-300 border-emerald-400/30' };
  if (status === 'reviewed') return { label: '已复核', cls: 'bg-purple-500/15 text-purple-300 border-purple-400/30' };
  return { label: status || '未知', cls: 'bg-white/[0.06] text-white/50 border-white/[0.08]' };
}

function gradeStatusChip(status?: string | null) {
  if (status === 'teacher_reviewed') return { label: '教师已复核', cls: 'bg-purple-500/15 text-purple-300 border-purple-400/30' };
  if (status === 'ai_graded') return { label: 'AI 已批改', cls: 'bg-blue-500/15 text-blue-300 border-blue-400/30' };
  return { label: '待批改', cls: 'bg-white/[0.06] text-white/50 border-white/[0.08]' };
}

function studentLabel(s: { id: number; username?: string | null; name?: string | null }): string {
  return s.username ?? s.name ?? `学生${s.id}`;
}

function errMsg(e: unknown, fallback: string): string {
  if (e && typeof e === 'object' && 'message' in e) return String((e as { message?: unknown }).message) || fallback;
  return fallback;
}

/* ═══════════ 通用小组件 ═══════════ */

function Loading({ text = '加载中...' }: { text?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 text-white/30 text-sm py-16">
      <Loader2 className="w-4 h-4 animate-spin" />
      {text}
    </div>
  );
}

function EmptyState({ icon: Icon, title, desc }: { icon: any; title: string; desc: string }) {
  return (
    <div className="text-center py-16">
      <Icon className="w-10 h-10 text-white/10 mx-auto mb-3" />
      <p className="text-white/30 text-sm">{title}</p>
      {desc ? <p className="text-white/20 text-xs mt-1">{desc}</p> : null}
    </div>
  );
}

function ErrorText({ msg }: { msg: string | null }) {
  if (!msg) return null;
  return (
    <div className="flex items-start gap-2 rounded-lg border border-red-400/25 bg-red-500/10 px-3 py-2">
      <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
      <p className="text-red-400 text-xs leading-relaxed">{msg}</p>
    </div>
  );
}

function StatCard({ label, value, sub, accent }: { label: string; value: string | number; sub?: string; accent: string }) {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
      <p className="text-white/35 text-xs">{label}</p>
      <p className={`text-xl font-bold mt-1 ${accent}`}>{value}</p>
      {sub ? <p className="text-white/20 text-[10px] mt-1">{sub}</p> : null}
    </div>
  );
}

function BackButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-1.5 text-white/40 hover:text-white text-sm transition-colors"
    >
      <ChevronLeft className="w-4 h-4" />
      {label}
    </button>
  );
}

/* ═══════════════════════════════════════════
   1) 作业列表（入口）
   ═══════════════════════════════════════════ */

function AssignmentListView({
  onSelect, error, onError,
}: {
  onSelect: (a: AssignmentRow) => void;
  error: string | null;
  onError: (m: string) => void;
}) {
  const [rows, setRows] = useState<AssignmentRow[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res: any = await api.listExamAssignments();
      if (res?.success) {
        const d = res.data;
        setRows((Array.isArray(d) ? d : (d?.items ?? d?.list ?? [])) as AssignmentRow[]);
      } else {
        onError(res?.error || res?.message || '加载作业列表失败');
      }
    } catch (e: unknown) {
      onError(errMsg(e, '加载作业列表失败'));
    } finally {
      setLoading(false);
    }
  }, [onError]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-white font-semibold text-lg flex items-center gap-2">
            <ClipboardCheck className="w-5 h-5 text-purple-300" />
            批改主观题
          </h2>
          <p className="text-white/30 text-xs mt-1">选择作业进入提交列表，逐题批改或整卷 AI 批改</p>
        </div>
        <button
          onClick={load}
          className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-white/60 text-xs transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          刷新
        </button>
      </div>

      <ErrorText msg={error} />

      {loading ? (
        <Loading />
      ) : rows.length === 0 ? (
        <EmptyState icon={ClipboardCheck} title="暂无作业" desc="在「考试与作业」中布置试卷后，可在此批改学生作答" />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {rows.map((a, i) => (
            <motion.button
              key={a.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(i * 0.03, 0.3) }}
              onClick={() => onSelect(a)}
              className="text-left rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 hover:border-purple-400/30 hover:bg-white/[0.04] transition-all"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-white text-sm font-medium truncate">{a.title || a.paper_title || `作业 #${a.id}`}</p>
                  <p className="text-white/30 text-xs truncate mt-1">{a.paper_title}</p>
                </div>
                <span className="px-2 py-0.5 rounded-full border text-[10px] flex-shrink-0 bg-white/[0.06] text-white/50 border-white/[0.08]">
                  {a.paper_type || '试卷'}
                </span>
              </div>
              <div className="flex items-center gap-2 flex-wrap mt-3">
                {a.subject ? (
                  <span className="px-2 py-0.5 rounded-md bg-cyan-500/10 text-cyan-300/80 border border-cyan-400/20 text-[10px]">
                    {a.subject}
                  </span>
                ) : null}
                <span className="text-white/25 text-[10px]">总分 {fmtScore(a.total_score)}</span>
                {a.due_at ? (
                  <span className="text-white/25 text-[10px] flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    截止 {String(a.due_at).slice(0, 16).replace('T', ' ')}
                  </span>
                ) : null}
              </div>
              <div className="flex items-center gap-2 mt-3">
                <div className="flex-1 h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-purple-500 to-blue-500"
                    style={{ width: `${a.submission_count > 0 ? Math.min(100, (a.graded_count / a.submission_count) * 100) : 0}%` }}
                  />
                </div>
                <span className="text-white/30 text-[10px] font-mono">
                  已批 {a.graded_count} / 提交 {a.submission_count}
                </span>
              </div>
            </motion.button>
          ))}
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════
   2) 提交列表 + 新建批改（线下批改入口）
   ═══════════════════════════════════════════ */

function NewGradeModal({
  assignment, onClose, onCreated, onError,
}: {
  assignment: AssignmentRow;
  onClose: () => void;
  onCreated: (submissionId: number) => void;
  onError: (m: string) => void;
}) {
  const [students, setStudents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res: any = await api.listClassStudents(assignment.class_id);
        if (!alive) return;
        if (res?.success) {
          const d = res.data;
          setStudents((Array.isArray(d) ? d : (d?.items ?? d?.list ?? [])) as any[]);
        } else {
          onError(res?.error || res?.message || '加载学生列表失败');
        }
      } catch (e: unknown) {
        if (alive) onError(errMsg(e, '加载学生列表失败'));
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [assignment.class_id, onError]);

  const confirm = async () => {
    if (selectedId == null) return;
    setBusy(true);
    try {
      const res: any = await api.createExamSubmission({ assignment_id: assignment.id, student_id: selectedId });
      if (!res?.success) {
        onError(res?.error || res?.message || '创建批改记录失败');
        return;
      }
      const d = res.data || {};
      const subId = d.id ?? d.submission_id ?? null;
      if (subId != null) {
        onCreated(Number(subId));
      } else {
        onError('创建成功，但未返回提交 ID，请刷新列表查看');
        onClose();
      }
    } catch (e: unknown) {
      onError(errMsg(e, '创建批改记录失败'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        onClick={(e) => e.stopPropagation()}
        className="bg-[#1a1a2e] rounded-xl border border-white/[0.08] p-6 max-w-md w-full mx-4"
      >
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-purple-500/15 flex items-center justify-center">
            <Plus className="w-5 h-5 text-purple-300" />
          </div>
          <div className="flex-1">
            <h3 className="text-white font-medium">新建批改（线下批改）</h3>
            <p className="text-white/40 text-xs">选择学生后创建作答记录并进入批改工作台</p>
          </div>
          <button
            onClick={onClose}
            className="text-white/30 hover:text-white/60 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] max-h-64 overflow-y-auto">
          {loading ? (
            <Loading text="加载学生..." />
          ) : students.length === 0 ? (
            <p className="text-white/30 text-xs text-center py-8">该班级暂无学生</p>
          ) : (
            <div className="divide-y divide-white/[0.04]">
              {students.map((s: any) => {
                const sid = Number(s.id);
                const label = studentLabel({ id: sid, username: s.username, name: s.name });
                const active = selectedId === sid;
                return (
                  <button
                    key={sid}
                    onClick={() => setSelectedId(sid)}
                    className={`w-full text-left px-3 py-2.5 flex items-center gap-3 transition-colors ${
                      active ? 'bg-purple-500/15' : 'hover:bg-white/[0.04]'
                    }`}
                  >
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                      active ? 'bg-purple-500/25' : 'bg-white/[0.05]'
                    }`}>
                      <span className={`text-xs font-medium ${active ? 'text-purple-200' : 'text-white/50'}`}>
                        {label.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <span className={`text-sm truncate ${active ? 'text-white' : 'text-white/60'}`}>{label}</span>
                    {active ? <CheckCircle2 className="w-4 h-4 text-purple-300 ml-auto flex-shrink-0" /> : null}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <div className="flex justify-end gap-2 mt-5">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-white/40 text-sm hover:text-white/60 hover:bg-white/[0.05] transition-colors"
          >
            取消
          </button>
          <button
            onClick={confirm}
            disabled={selectedId == null || busy}
            className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-sm transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
          >
            {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
            {busy ? '创建中...' : '创建并进入'}
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

function SubmissionListView({
  assignment, onBack, onOpenWorkspace, onViewReport, error, onError,
}: {
  assignment: AssignmentRow;
  onBack: () => void;
  onOpenWorkspace: (subId: number, row: SubmissionRow | null) => void;
  onViewReport: () => void;
  error: string | null;
  onError: (m: string) => void;
}) {
  const [rows, setRows] = useState<SubmissionRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNew, setShowNew] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res: any = await api.listExamSubmissions(assignment.id);
      if (res?.success) {
        const d = res.data;
        setRows((Array.isArray(d) ? d : (d?.items ?? d?.list ?? [])) as SubmissionRow[]);
      } else {
        onError(res?.error || res?.message || '加载提交列表失败');
      }
    } catch (e: unknown) {
      onError(errMsg(e, '加载提交列表失败'));
    } finally {
      setLoading(false);
    }
  }, [assignment.id, onError]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="space-y-4">
      {/* 返回 + 标题 + 操作 */}
      <div className="flex items-center gap-3 flex-wrap">
        <BackButton label="返回作业列表" onClick={onBack} />
        <div className="flex-1 min-w-0">
          <p className="text-white font-medium truncate">{assignment.title || assignment.paper_title}</p>
          <p className="text-white/30 text-xs">
            {assignment.subject ? `${assignment.subject} · ` : ''}
            {assignment.paper_title}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onViewReport}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-white/70 text-xs transition-colors"
          >
            <BarChart3 className="w-3.5 h-3.5" />
            班级报告
          </button>
          <button
            onClick={() => setShowNew(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-blue-600 text-white text-xs font-medium hover:from-purple-500 hover:to-blue-500 transition-all shadow-lg shadow-purple-500/20"
          >
            <Plus className="w-3.5 h-3.5" />
            新建批改
          </button>
        </div>
      </div>

      <ErrorText msg={error} />

      {loading ? (
        <Loading text="加载提交列表..." />
      ) : rows.length === 0 ? (
        <EmptyState icon={Users} title="暂无提交记录" desc="学生提交作答后将在此显示；也可点击「新建批改」录入线下作答" />
      ) : (
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] divide-y divide-white/[0.04] overflow-hidden">
          {rows.map((r, i) => {
            const st = subStatusChip(r.status);
            const done = r.answer_count > 0 ? Math.min(100, (r.graded_count / r.answer_count) * 100) : 0;
            const name = r.student_name || `学生${r.student_id}`;
            return (
              <motion.button
                key={r.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: Math.min(i * 0.03, 0.3) }}
                onClick={() => onOpenWorkspace(r.id, r)}
                className="w-full text-left px-4 py-3.5 hover:bg-white/[0.04] transition-colors"
              >
                <div className="flex items-center gap-3 flex-wrap">
                  <div className="w-9 h-9 rounded-full bg-purple-500/15 flex items-center justify-center flex-shrink-0">
                    <span className="text-purple-300 font-medium text-sm">{name.charAt(0).toUpperCase()}</span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="text-white text-sm font-medium truncate">{name}</p>
                      <span className={`px-2 py-0.5 rounded-full border text-[10px] flex-shrink-0 ${st.cls}`}>{st.label}</span>
                    </div>
                    <p className="text-white/25 text-[10px] mt-0.5">
                      {r.submitted_at ? `提交于 ${String(r.submitted_at).slice(0, 16).replace('T', ' ')}` : '未记录提交时间'}
                    </p>
                  </div>

                  <div className="flex items-center gap-4 text-xs">
                    <div className="text-right">
                      <p className="text-white/25 text-[10px]">最终得分</p>
                      <p className="text-white font-semibold">
                        {fmtScore(r.final_score)}
                        <span className="text-white/25 font-normal"> / {fmtScore(r.total_score)}</span>
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-white/25 text-[10px]">AI 分 / 客观分</p>
                      <p className="text-white/50 font-mono">
                        {fmtScore(r.ai_score)} / {fmtScore(r.objective_score)}
                      </p>
                    </div>
                    <div className="w-28">
                      <p className="text-white/25 text-[10px] mb-1">批改进度</p>
                      <div className="flex items-center gap-1.5">
                        <div className="flex-1 h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                          <div
                            className="h-full rounded-full bg-gradient-to-r from-purple-500 to-blue-500"
                            style={{ width: `${done}%` }}
                          />
                        </div>
                        <span className="text-white/30 text-[10px] font-mono flex-shrink-0">
                          {r.graded_count}/{r.answer_count}
                        </span>
                      </div>
                    </div>
                    <ChevronLeft className="w-4 h-4 text-white/15 rotate-180" />
                  </div>
                </div>
              </motion.button>
            );
          })}
        </div>
      )}

      <AnimatePresence>
        {showNew ? (
          <NewGradeModal
            assignment={assignment}
            onClose={() => setShowNew(false)}
            onCreated={(subId) => { setShowNew(false); onOpenWorkspace(subId, null); }}
            onError={onError}
          />
        ) : null}
      </AnimatePresence>
    </div>
  );
}

/* ═══════════════════════════════════════════
   3) 批改工作台（核心）
   ═══════════════════════════════════════════ */

function WorkspaceView({
  submissionId, assignmentId, initialRow, onBack, error, onError,
}: {
  submissionId: number;
  assignmentId: number;
  initialRow: SubmissionRow | null;
  onBack: () => void;
  error: string | null;
  onError: (m: string) => void;
}) {
  const [sub, setSub] = useState<SubmissionRow | null>(initialRow);
  const [questions, setQuestions] = useState<QuestionRow[]>([]);
  const [answers, setAnswers] = useState<AnswerRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [gradingAll, setGradingAll] = useState(false);

  /* 手写图 objectURL 管理（卸载时统一 revoke） */
  const imgUrlsRef = useRef<Record<number, string>>({});
  const [, setImgTick] = useState(0);

  const setImageUrl = useCallback((questionId: number, url: string | null) => {
    const prev = imgUrlsRef.current[questionId];
    if (prev && prev !== url) URL.revokeObjectURL(prev);
    if (url) imgUrlsRef.current[questionId] = url;
    else delete imgUrlsRef.current[questionId];
    setImgTick((t) => t + 1);
  }, []);

  useEffect(() => {
    return () => {
      Object.values(imgUrlsRef.current).forEach((u) => URL.revokeObjectURL(u));
      imgUrlsRef.current = {};
    };
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [subRes, asgRes]: any[] = await Promise.all([
        api.getExamSubmission(submissionId),
        api.getExamAssignment(assignmentId),
      ]);

      if (subRes?.success) {
        const d = subRes.data || {};
        setSub((prev) => ({
          id: d.id ?? submissionId,
          assignment_id: d.assignment_id ?? assignmentId,
          paper_id: d.paper_id ?? prev?.paper_id ?? 0,
          student_id: d.student_id ?? prev?.student_id ?? 0,
          student_name: d.student_name ?? prev?.student_name ?? '',
          status: d.status ?? prev?.status ?? 'submitted',
          objective_score: d.objective_score ?? prev?.objective_score ?? null,
          ai_score: d.ai_score ?? prev?.ai_score ?? null,
          final_score: d.final_score ?? prev?.final_score ?? null,
          total_score: d.total_score ?? prev?.total_score ?? 0,
          answer_count: d.answer_count ?? prev?.answer_count ?? 0,
          graded_count: d.graded_count ?? prev?.graded_count ?? 0,
          submitted_at: d.submitted_at ?? prev?.submitted_at ?? null,
        }));
        const list = Array.isArray(d.answers) ? d.answers : (Array.isArray(d.answer_list) ? d.answer_list : []);
        setAnswers(list as AnswerRow[]);
      } else {
        onError(subRes?.error || subRes?.message || '加载提交详情失败');
      }

      if (asgRes?.success) {
        const ad = asgRes.data || {};
        const qs = Array.isArray(ad.paper?.questions)
          ? ad.paper.questions
          : (Array.isArray(ad.questions) ? ad.questions : []);
        setQuestions(qs as QuestionRow[]);
      } else {
        onError(asgRes?.error || asgRes?.message || '加载试卷题目失败');
      }
    } catch (e: unknown) {
      onError(errMsg(e, '加载批改数据失败'));
    } finally {
      setLoading(false);
    }
  }, [submissionId, assignmentId, onError]);

  useEffect(() => { load(); }, [load]);

  /* 按 question_id 合并题目与作答（无作答行 → 未作答占位） */
  const merged = useMemo<MergedItem[]>(() => {
    const byQid = new Map<number, AnswerRow>();
    answers.forEach((a) => {
      if (a && a.question_id != null) byQid.set(Number(a.question_id), a);
    });
    const used = new Set<number>();
    const items: MergedItem[] = [];
    const qs = [...questions].sort((a, b) => num(a.q_index) - num(b.q_index));
    qs.forEach((q) => {
      used.add(q.id);
      items.push({ key: q.id, question: q, answer: byQid.get(q.id) ?? null });
    });
    answers.forEach((a) => {
      if (!a || a.question_id == null) return;
      const qid = Number(a.question_id);
      if (used.has(qid)) return;
      used.add(qid);
      items.push({ key: qid, question: null, answer: a });
    });
    return items;
  }, [questions, answers]);

  /* 懒加载手写图 objectURL */
  useEffect(() => {
    merged.forEach((item) => {
      const a = item.answer;
      if (!a?.id || !a.answer_image_path) return;
      if (imgUrlsRef.current[item.key]) return;
      const qid = item.key;
      api.getExamAnswerImageBlobUrl(a.id)
        .then((url: string | null) => {
          if (url) setImageUrl(qid, url);
        })
        .catch(() => {});
    });
  }, [merged, setImageUrl]);

  const patchAnswer = useCallback((questionId: number, patch: Partial<AnswerRow>) => {
    setAnswers((prev) => {
      const idx = prev.findIndex((a) => a.question_id === questionId);
      if (idx >= 0) {
        const next = [...prev];
        const cur = next[idx];
        next[idx] = { ...(cur ?? {}), ...patch, question_id: questionId } as AnswerRow;
        return next;
      }
      return [...prev, { question_id: questionId, ...patch } as AnswerRow];
    });
  }, []);

  const gradeAll = async () => {
    setGradingAll(true);
    try {
      const res: any = await api.gradeExamSubmission(submissionId);
      if (!res?.success) {
        onError(res?.error || res?.message || '整卷 AI 批改失败');
      }
    } catch (e: unknown) {
      onError(errMsg(e, '整卷 AI 批改失败'));
    } finally {
      setGradingAll(false);
      load();
    }
  };

  const st = subStatusChip(sub?.status);
  const studentName = sub?.student_name || `学生 #${sub?.student_id ?? submissionId}`;

  return (
    <div className="space-y-4">
      {/* 顶部栏：学生名 / 状态 / 总分 / 整卷 AI 批改 */}
      <div className="flex items-center gap-3 flex-wrap">
        <BackButton label="返回提交列表" onClick={onBack} />
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className="w-10 h-10 rounded-full bg-purple-500/15 flex items-center justify-center flex-shrink-0">
            <span className="text-purple-300 font-medium">{studentName.charAt(0).toUpperCase()}</span>
          </div>
          <div className="min-w-0">
            <p className="text-white font-medium truncate">{studentName}</p>
            <div className="flex items-center gap-2 mt-0.5">
              <span className={`px-2 py-0.5 rounded-full border text-[10px] ${st.cls}`}>{st.label}</span>
              <span className="text-white/30 text-xs">
                总分 <span className="text-white/80 font-semibold">{fmtScore(sub?.final_score)}</span>
                {sub?.total_score ? <span className="text-white/25"> / {fmtScore(sub.total_score)}</span> : null}
              </span>
            </div>
          </div>
        </div>
        <button
          onClick={gradeAll}
          disabled={gradingAll || loading}
          className="px-4 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-blue-600 text-white text-sm font-medium
                     hover:from-purple-500 hover:to-blue-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed
                     flex items-center gap-2 shadow-lg shadow-purple-500/20"
        >
          {gradingAll ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          {gradingAll ? 'AI 批改中（最长约 3 分钟）…' : '整卷 AI 批改'}
        </button>
      </div>

      <ErrorText msg={error} />

      {loading ? (
        <Loading text="加载批改数据..." />
      ) : merged.length === 0 ? (
        <EmptyState icon={FileText} title="暂无题目" desc="试卷题目或学生作答为空" />
      ) : (
        <div className="space-y-4">
          {merged.map((item) => (
            <QuestionCard
              key={item.key}
              item={item}
              submissionId={submissionId}
              imgUrl={imgUrlsRef.current[item.key] ?? null}
              onPatch={patchAnswer}
              onSetImage={(url) => setImageUrl(item.key, url)}
              onError={onError}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/* ── 单题卡片（题干 / 手写图 / 识别文本 / AI 批改 / 教师复核） ── */

function QuestionCard({
  item, submissionId, imgUrl, onPatch, onSetImage, onError,
}: {
  item: MergedItem;
  submissionId: number;
  imgUrl: string | null;
  onPatch: (questionId: number, patch: Partial<AnswerRow>) => void;
  onSetImage: (url: string | null) => void;
  onError: (m: string) => void;
}) {
  const { question, answer } = item;
  const qid = item.key;
  const qType = question?.question_type ?? answer?.question_type ?? '';
  const qText = question?.question_text ?? answer?.question_text ?? '（无题干）';
  const qScore = question?.score ?? answer?.max_score ?? 0;
  const kp = question?.knowledge_point ?? '';
  const options = toStrArray(question?.options);
  const answerId = answer?.id ?? null;

  const [text, setText] = useState<string>(answer?.answer_text || answer?.ocr_text || '');
  const [tscore, setTscore] = useState<string>(answer?.teacher_score != null ? String(answer.teacher_score) : '');
  const [tfeedback, setTfeedback] = useState<string>(answer?.teacher_feedback || '');
  const [showRag, setShowRag] = useState(false);
  const [busy, setBusy] = useState<'' | 'upload' | 'save' | 'grade' | 'review'>('');
  const [lowOcr, setLowOcr] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  /* 作答行创建/切换时同步本地编辑态（避免覆盖正在输入的内容） */
  useEffect(() => {
    setText(answer?.answer_text || answer?.ocr_text || '');
    setTscore(answer?.teacher_score != null ? String(answer.teacher_score) : '');
    setTfeedback(answer?.teacher_feedback || '');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [answer?.id]);

  const hits = toStrArray(answer?.knowledge_hits?.hits);
  const missing = toStrArray(answer?.knowledge_hits?.missing);
  const ragList = toRagList(answer?.rag_evidence);
  const gs = gradeStatusChip(answer?.grade_status);

  const handleFile = async (file: File | null | undefined) => {
    if (!file) return;
    setBusy('upload');
    try {
      const res: any = await api.uploadExamAnswerImage(submissionId, qid, file, true);
      if (!res?.success) {
        onError(res?.error || res?.message || '上传图片失败');
        return;
      }
      const d = res.data || {};
      const ocr: any = d.ocr && typeof d.ocr === 'object' ? d.ocr : {};
      const newId = d.answer_id ?? d.id ?? answerId;
      const ocrText: string = String(ocr.ocr_text ?? ocr.text ?? d.ocr_text ?? '');
      onPatch(qid, {
        id: newId ?? null,
        answer_image_path: d.answer_image_path ?? '__uploaded__',
        ocr_text: ocrText || answer?.ocr_text || null,
        ocr_confidence: ocr.confidence ?? ocr.ocr_confidence ?? answer?.ocr_confidence ?? null,
        ocr_engine: ocr.engine ?? ocr.ocr_engine ?? answer?.ocr_engine ?? null,
        answer_text: ocrText || answer?.answer_text || null,
      });
      onSetImage(URL.createObjectURL(file));
      setLowOcr(!!ocr.low_confidence);
      if (ocrText) setText(ocrText);
    } catch (e: unknown) {
      onError(errMsg(e, '上传图片失败'));
    } finally {
      setBusy('');
    }
  };

  const saveText = async () => {
    if (!answerId) return;
    setBusy('save');
    try {
      const res: any = await api.updateExamAnswer(answerId, { answer_text: text });
      if (!res?.success) {
        onError(res?.error || res?.message || '保存识别文本失败');
        return;
      }
      onPatch(qid, { answer_text: text });
    } catch (e: unknown) {
      onError(errMsg(e, '保存识别文本失败'));
    } finally {
      setBusy('');
    }
  };

  const doGrade = async () => {
    if (!answerId) return;
    setBusy('grade');
    try {
      const res: any = await api.gradeExamAnswer(answerId);
      if (!res?.success) {
        onError(res?.error || res?.message || 'AI 批改本题失败');
        return;
      }
      const d = res.data || {};
      onPatch(qid, {
        score: d.score ?? null,
        ai_score: d.ai_score ?? d.score ?? null,
        max_score: d.max_score ?? answer?.max_score ?? null,
        feedback: d.feedback ?? d.comment ?? null,
        knowledge_hits: d.knowledge_hits ?? answer?.knowledge_hits ?? null,
        rag_evidence: d.rag_evidence ?? answer?.rag_evidence ?? null,
        grade_status: d.grade_status ?? 'ai_graded',
        is_correct: d.is_correct ?? answer?.is_correct ?? null,
      });
    } catch (e: unknown) {
      onError(errMsg(e, 'AI 批改本题失败'));
    } finally {
      setBusy('');
    }
  };

  const doReview = async () => {
    if (!answerId) return;
    setBusy('review');
    const scoreVal = tscore.trim() === '' ? null : Number(tscore);
    try {
      const res: any = await api.reviewExamAnswer(answerId, {
        teacher_score: scoreVal,
        teacher_feedback: tfeedback,
      });
      if (!res?.success) {
        onError(res?.error || res?.message || '保存复核失败');
        return;
      }
      const d = res.data || {};
      onPatch(qid, {
        teacher_score: scoreVal,
        teacher_feedback: tfeedback,
        grade_status: d.grade_status ?? 'teacher_reviewed',
        reviewed_at: d.reviewed_at ?? new Date().toISOString(),
      });
    } catch (e: unknown) {
      onError(errMsg(e, '保存复核失败'));
    } finally {
      setBusy('');
    }
  };

  const showScoreCard = !!answer && (answer.score != null || answer.ai_score != null || !!answer.feedback);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden"
    >
      {/* 卡片头：题型 + 序号 + 满分 + 知识点 + 状态 */}
      <div className="flex items-center gap-2 flex-wrap px-4 py-3 border-b border-white/[0.06] bg-white/[0.015]">
        <span className="px-2 py-0.5 rounded-md bg-purple-500/15 text-purple-300 border border-purple-400/25 text-[10px]">
          {typeLabel(qType)}
        </span>
        <span className="text-white/70 text-sm font-medium">
          第 {question?.q_index ?? answer?.q_index ?? '?'} 题
        </span>
        <span className="text-white/30 text-xs">满分 {fmtScore(qScore)} 分</span>
        {kp ? (
          <span className="px-2 py-0.5 rounded-md bg-cyan-500/10 text-cyan-300/80 border border-cyan-400/20 text-[10px]">
            {kp}
          </span>
        ) : null}
        <div className="ml-auto">
          <span className={`px-2 py-0.5 rounded-full border text-[10px] ${gs.cls}`}>{gs.label}</span>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* 题干 + 选项 + 参考答案 */}
        <div>
          <p className="text-white/80 text-sm leading-relaxed whitespace-pre-wrap">{qText}</p>
          {options.length > 0 ? (
            <div className="mt-2 space-y-1">
              {options.map((opt, i) => (
                <p key={i} className="text-white/50 text-xs">
                  <span className="text-white/30 mr-1.5">{String.fromCharCode(65 + i)}.</span>
                  {opt}
                </p>
              ))}
            </div>
          ) : null}
          {(question?.reference_answer || answer?.reference_answer) ? (
            <div className="mt-2 rounded-lg bg-white/[0.03] border border-white/[0.05] px-3 py-2">
              <p className="text-white/30 text-[10px] mb-1">参考答案</p>
              <p className="text-white/50 text-xs whitespace-pre-wrap">
                {question?.reference_answer ?? answer?.reference_answer}
              </p>
            </div>
          ) : null}
          {question?.explanation ? (
            <div className="mt-2 rounded-lg bg-white/[0.03] border border-white/[0.05] px-3 py-2">
              <p className="text-white/30 text-[10px] mb-1">解析</p>
              <p className="text-white/50 text-xs whitespace-pre-wrap">{question.explanation}</p>
            </div>
          ) : null}
        </div>

        {/* 手写答案图片 */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <p className="text-white/35 text-xs flex items-center gap-1.5">
              <ImageIcon className="w-3.5 h-3.5" />
              手写答案图片
            </p>
            {imgUrl ? (
              <button
                onClick={() => fileRef.current?.click()}
                disabled={busy === 'upload'}
                className="text-white/40 hover:text-white/70 text-xs flex items-center gap-1 transition-colors disabled:opacity-40"
              >
                {busy === 'upload' ? <Loader2 className="w-3 h-3 animate-spin" /> : <Upload className="w-3 h-3" />}
                更换图片
              </button>
            ) : null}
          </div>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => {
              handleFile(e.target.files?.[0]);
              e.target.value = '';
            }}
          />

          {imgUrl ? (
            <div>
              {/* 手写图需 Bearer 头，统一走 objectURL */}
              <img
                src={imgUrl}
                alt="手写答案"
                className="max-h-64 rounded-lg border border-white/[0.08] bg-white/[0.03]"
              />
              {(answer?.ocr_confidence != null || answer?.ocr_engine) ? (
                <p className="text-white/25 text-[10px] mt-1.5">
                  {answer?.ocr_confidence != null ? <span>识别置信度 {confLabel(answer.ocr_confidence)}</span> : null}
                  {answer?.ocr_engine ? <span className="ml-2">识别引擎 {String(answer.ocr_engine)}</span> : null}
                </p>
              ) : null}
            </div>
          ) : (
            <div
              onClick={() => fileRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                handleFile(e.dataTransfer.files?.[0]);
              }}
              className="rounded-lg border border-dashed border-white/[0.1] bg-white/[0.02] px-4 py-6 text-center cursor-pointer hover:border-purple-400/30 hover:bg-white/[0.04] transition-all"
            >
              {busy === 'upload' ? (
                <Loader2 className="w-5 h-5 text-white/30 animate-spin mx-auto" />
              ) : (
                <Upload className="w-5 h-5 text-white/20 mx-auto mb-1.5" />
              )}
              <p className="text-white/30 text-xs">
                {busy === 'upload' ? '正在上传并 OCR 识别…' : '点击或拖拽上传手写答案图片'}
              </p>
              <p className="text-white/15 text-[10px] mt-0.5">上传后自动 OCR 识别</p>
            </div>
          )}

          {lowOcr ? (
            <div className="flex items-center gap-1.5 mt-2 rounded-lg border border-amber-400/25 bg-amber-500/10 px-3 py-2">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
              <p className="text-amber-300 text-xs">识别置信度低，请人工校对</p>
            </div>
          ) : null}

          {!answerId ? (
            <p className="text-white/20 text-[10px] mt-2">
              该题暂无作答记录（未作答），上传图片后将自动创建作答
            </p>
          ) : null}
        </div>

        {/* 识别文本区 */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <p className="text-white/35 text-xs">识别 / 作答文本（可编辑校对）</p>
            <button
              onClick={saveText}
              disabled={busy === 'save' || !answerId}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.06] hover:bg-white/[0.1] text-white/70 text-xs transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {busy === 'save' ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />}
              保存修改
            </button>
          </div>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={3}
            placeholder={answerId ? '输入或校对 OCR 识别文本…' : '上传图片后自动创建作答记录并识别文本…'}
            className="w-full rounded-lg bg-white/[0.03] border border-white/[0.06] text-white/80 text-sm px-3 py-2
                       placeholder:text-white/20 focus:border-white/[0.15] outline-none resize-y"
          />
        </div>

        {/* AI 批改本题 */}
        <div>
          <button
            onClick={doGrade}
            disabled={busy === 'grade' || !answerId}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-cyan-600 text-white text-xs font-medium
                       hover:from-blue-500 hover:to-cyan-500 transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-lg"
          >
            {busy === 'grade' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            {busy === 'grade' ? 'AI 评分中…' : 'AI 批改本题'}
          </button>
          {!answerId ? (
            <p className="text-white/20 text-[10px] mt-1.5">上传图片生成作答记录后可进行 AI 批改</p>
          ) : null}

          {/* AI 评分卡 */}
          {showScoreCard ? (
            <div className="mt-3 rounded-lg border border-white/[0.06] bg-white/[0.03] p-3 space-y-2.5">
              <div className="flex items-center gap-3 flex-wrap">
                <div className="flex items-baseline gap-1.5">
                  <span className="text-2xl font-bold text-emerald-300">{fmtScore(answer.score ?? answer.ai_score)}</span>
                  <span className="text-white/30 text-xs">/ {fmtScore(answer.max_score ?? qScore)} 分</span>
                </div>
                {answer.is_correct != null ? (
                  <span
                    className={`px-2 py-0.5 rounded-full border text-[10px] ${
                      answer.is_correct
                        ? 'bg-emerald-500/15 text-emerald-300 border-emerald-400/30'
                        : 'bg-red-500/15 text-red-300 border-red-400/30'
                    }`}
                  >
                    {answer.is_correct ? '判定正确' : '判定错误'}
                  </span>
                ) : null}
              </div>

              {answer.feedback ? (
                <div>
                  <p className="text-white/30 text-[10px] mb-1">AI 评语</p>
                  <p className="text-white/65 text-xs leading-relaxed whitespace-pre-wrap">{answer.feedback}</p>
                </div>
              ) : null}

              {(hits.length > 0 || missing.length > 0) ? (
                <div>
                  <p className="text-white/30 text-[10px] mb-1.5">知识点命中</p>
                  <div className="flex flex-wrap gap-1.5">
                    {hits.map((h, i) => (
                      <span
                        key={`hit-${i}`}
                        className="px-2 py-0.5 rounded-full border bg-emerald-500/15 text-emerald-300 border-emerald-400/30 text-[10px]"
                      >
                        ✓ {h}
                      </span>
                    ))}
                    {missing.map((m, i) => (
                      <span
                        key={`miss-${i}`}
                        className="px-2 py-0.5 rounded-full border bg-red-500/15 text-red-300 border-red-400/30 text-[10px]"
                      >
                        ✕ {m}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}

              {ragList.length > 0 ? (
                <div>
                  <button
                    onClick={() => setShowRag(!showRag)}
                    className="flex items-center gap-1.5 text-white/40 hover:text-white/70 text-xs transition-colors"
                  >
                    <BookOpen className="w-3.5 h-3.5" />
                    AI 判分依据（{ragList.length} 条）
                    <ChevronDown className={`w-3 h-3 transition-transform ${showRag ? 'rotate-180' : ''}`} />
                  </button>
                  {showRag ? (
                    <div className="mt-2 space-y-2">
                      {ragList.map((r, i) => (
                        <div key={i} className="rounded-lg bg-white/[0.03] border border-white/[0.05] px-3 py-2">
                          <div className="flex items-center gap-2 flex-wrap">
                            <p className="text-white/70 text-xs font-medium">{r.title || `依据 ${i + 1}`}</p>
                            {r.source ? (
                              <span className="px-1.5 py-0.5 rounded bg-white/[0.05] text-white/30 text-[10px]">
                                来源: {String(r.source)}
                              </span>
                            ) : null}
                            {r.score != null && r.score !== '' ? (
                              <span className="text-white/25 text-[10px]">相关度 {fmtScore(r.score)}</span>
                            ) : null}
                          </div>
                          <p className="text-white/40 text-xs mt-1 leading-relaxed">
                            {(r.content || '').slice(0, 200)}
                            {(r.content || '').length > 200 ? '…' : ''}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : null}
                </div>
              ) : null}
            </div>
          ) : null}
        </div>

        {/* 教师复核区 */}
        <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
          <div className="flex items-center justify-between mb-2">
            <p className="text-white/35 text-xs flex items-center gap-1.5">
              <GraduationCap className="w-3.5 h-3.5" />
              教师复核
            </p>
            {answer?.grade_status === 'teacher_reviewed' ? (
              <span className="px-2 py-0.5 rounded-full border bg-purple-500/15 text-purple-300 border-purple-400/30 text-[10px]">
                教师已复核{answer.reviewed_at ? ` · ${String(answer.reviewed_at).slice(0, 10)}` : ''}
              </span>
            ) : null}
          </div>

          {answer && (answer.ai_score != null || answer.score != null || answer.teacher_score != null) ? (
            <p className="text-white/40 text-xs mb-2">
              AI 分 <span className="text-blue-300 font-semibold">{fmtScore(answer.ai_score ?? answer.score)}</span>
              <span className="mx-1.5 text-white/20">/</span>
              教师分 <span className="text-purple-300 font-semibold">{fmtScore(answer.teacher_score)}</span>
              {answer.max_score != null ? (
                <span className="text-white/25 ml-1.5">（满分 {fmtScore(answer.max_score)}）</span>
              ) : null}
            </p>
          ) : null}

          <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
            <div>
              <p className="text-white/25 text-[10px] mb-1">教师评分</p>
              <input
                type="number"
                step="0.5"
                min="0"
                value={tscore}
                onChange={(e) => setTscore(e.target.value)}
                placeholder="分数"
                className="w-full rounded-lg bg-white/[0.03] border border-white/[0.06] text-white text-sm px-2.5 py-1.5
                           placeholder:text-white/20 focus:border-white/[0.15] outline-none"
              />
            </div>
            <div className="md:col-span-3">
              <p className="text-white/25 text-[10px] mb-1">教师评语</p>
              <input
                type="text"
                value={tfeedback}
                onChange={(e) => setTfeedback(e.target.value)}
                placeholder="评语（可选）"
                className="w-full rounded-lg bg-white/[0.03] border border-white/[0.06] text-white text-sm px-2.5 py-1.5
                           placeholder:text-white/20 focus:border-white/[0.15] outline-none"
              />
            </div>
          </div>

          <div className="mt-2 flex justify-end">
            <button
              onClick={doReview}
              disabled={busy === 'review' || !answerId}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {busy === 'review' ? <Loader2 className="w-3 h-3 animate-spin" /> : <CheckCircle2 className="w-3 h-3" />}
              保存复核
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

/* ═══════════════════════════════════════════
   4) 班级报告视图
   ═══════════════════════════════════════════ */

function ReportView({
  assignment, onBack, error, onError,
}: {
  assignment: AssignmentRow;
  onBack: () => void;
  error: string | null;
  onError: (m: string) => void;
}) {
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    (async () => {
      setLoading(true);
      try {
        const res: any = await api.getExamClassReport(assignment.id);
        if (!alive) return;
        if (res?.success) setReport(res.data || {});
        else onError(res?.error || res?.message || '加载班级报告失败');
      } catch (e: unknown) {
        if (alive) onError(errMsg(e, '加载班级报告失败'));
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [assignment.id, onError]);

  const dist: Array<[string, unknown]> =
    report?.score_distribution && typeof report.score_distribution === 'object'
      ? Object.entries(report.score_distribution)
      : [];
  const distMax = Math.max(1, ...dist.map(([, v]) => num(v)));
  const qStats: any[] = Array.isArray(report?.question_stats) ? report.question_stats : [];
  const weak: any[] = Array.isArray(report?.weak_points)
    ? [...report.weak_points].sort((a: any, b: any) => num(b?.miss_count) - num(a?.miss_count))
    : [];
  const ranking: any[] = Array.isArray(report?.ranking) ? report.ranking : [];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <BackButton label="返回提交列表" onClick={onBack} />
        <div className="flex-1 min-w-0">
          <p className="text-white font-medium truncate flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-purple-300" />
            班级报告 — {report?.title || assignment.title || assignment.paper_title}
          </p>
          <p className="text-white/30 text-xs">总分 {fmtScore(report?.total_score ?? assignment.total_score)}</p>
        </div>
      </div>

      <ErrorText msg={error} />

      {loading ? (
        <Loading text="加载班级报告..." />
      ) : !report ? (
        <EmptyState icon={BarChart3} title="暂无报告数据" desc="报告生成后将在此展示" />
      ) : (
        <>
          {/* 顶部统计卡 */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            <StatCard label="提交数" value={fmtScore(report.submission_count)} accent="text-white" />
            <StatCard label="已批改" value={fmtScore(report.graded_count)} accent="text-emerald-300" />
            <StatCard label="平均分" value={fmtScore(report.avg_score)} accent="text-blue-300" />
            <StatCard label="平均得分率" value={pct(report.avg_rate)} accent="text-cyan-300" />
            <StatCard label="最高分" value={fmtScore(report.max_score)} accent="text-emerald-300" />
            <StatCard label="最低分" value={fmtScore(report.min_score)} accent="text-red-300" />
          </div>

          {/* 得分分布（横条图） */}
          <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
            <p className="text-white/50 text-sm font-medium mb-3 flex items-center gap-1.5">
              <TrendingUp className="w-4 h-4 text-purple-300" />
              得分分布
            </p>
            {dist.length === 0 ? (
              <p className="text-white/25 text-xs py-4 text-center">暂无分布数据</p>
            ) : (
              <div className="space-y-2.5">
                {dist.map(([k, v]) => (
                  <div key={k} className="flex items-center gap-3">
                    <span className="text-white/40 text-xs w-20 flex-shrink-0">{k}</span>
                    <div className="flex-1 h-5 rounded-md bg-white/[0.04] overflow-hidden">
                      <div
                        className="h-full rounded-md bg-gradient-to-r from-purple-500/80 to-blue-500/80"
                        style={{ width: `${(num(v) / distMax) * 100}%` }}
                      />
                    </div>
                    <span className="text-white/50 text-xs font-mono w-8 text-right">{num(v)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 逐题统计表 */}
          <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden">
            <p className="text-white/50 text-sm font-medium px-4 py-3 flex items-center gap-1.5">
              <FileText className="w-4 h-4 text-purple-300" />
              逐题统计
            </p>
            {qStats.length === 0 ? (
              <p className="text-white/25 text-xs pb-6 text-center">暂无逐题数据</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-white/30 text-left border-y border-white/[0.05] bg-white/[0.015]">
                      <th className="px-4 py-2 font-normal">题号</th>
                      <th className="px-4 py-2 font-normal">题型</th>
                      <th className="px-4 py-2 font-normal">知识点</th>
                      <th className="px-4 py-2 font-normal text-right">均分</th>
                      <th className="px-4 py-2 font-normal text-right">得分率</th>
                      <th className="px-4 py-2 font-normal text-right">已批数</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.04]">
                    {qStats.map((q: any, i: number) => (
                      <tr key={q?.question_id ?? i} className="hover:bg-white/[0.02] transition-colors">
                        <td className="px-4 py-2 text-white/70">第 {q?.q_index ?? i + 1} 题</td>
                        <td className="px-4 py-2 text-white/45">{typeLabel(q?.question_type)}</td>
                        <td className="px-4 py-2 text-white/45">{q?.knowledge_point || '—'}</td>
                        <td className="px-4 py-2 text-white/70 text-right font-mono">{fmtScore(q?.avg_score)}</td>
                        <td className="px-4 py-2 text-cyan-300/80 text-right font-mono">{pct(q?.avg_rate)}</td>
                        <td className="px-4 py-2 text-white/35 text-right font-mono">{fmtScore(q?.graded_count)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* 薄弱知识点 */}
          <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
            <p className="text-white/50 text-sm font-medium mb-3 flex items-center gap-1.5">
              <Target className="w-4 h-4 text-red-300" />
              薄弱知识点（按未命中次数）
            </p>
            {weak.length === 0 ? (
              <p className="text-white/25 text-xs">暂无薄弱知识点数据</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {weak.map((w: any, i: number) => (
                  <span
                    key={i}
                    className="px-2.5 py-1 rounded-full border bg-red-500/10 text-red-300 border-red-400/25 text-xs"
                  >
                    {w?.point ?? '未知知识点'}
                    <span className="ml-1.5 text-red-300/60">未命中 {num(w?.miss_count)} 次</span>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* 成绩排名 */}
          <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden">
            <p className="text-white/50 text-sm font-medium px-4 py-3 flex items-center gap-1.5">
              <Award className="w-4 h-4 text-amber-300" />
              成绩排名（前 20）
            </p>
            {ranking.length === 0 ? (
              <p className="text-white/25 text-xs pb-6 text-center">暂无排名数据</p>
            ) : (
              <div className="divide-y divide-white/[0.04]">
                {ranking.slice(0, 20).map((r: any, i: number) => {
                  const name = r?.student_name || `学生${r?.student_id ?? ''}`;
                  const st = subStatusChip(r?.status);
                  return (
                    <div key={r?.student_id ?? i} className="flex items-center gap-3 px-4 py-2.5">
                      <span
                        className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-semibold flex-shrink-0 ${
                          i === 0
                            ? 'bg-amber-500/20 text-amber-300'
                            : i === 1
                              ? 'bg-white/[0.08] text-white/60'
                              : i === 2
                                ? 'bg-orange-500/15 text-orange-300'
                                : 'bg-white/[0.04] text-white/35'
                        }`}
                      >
                        {i + 1}
                      </span>
                      <div className="w-8 h-8 rounded-full bg-purple-500/15 flex items-center justify-center flex-shrink-0">
                        <span className="text-purple-300 text-xs font-medium">{name.charAt(0).toUpperCase()}</span>
                      </div>
                      <p className="text-white/75 text-sm flex-1 truncate">{name}</p>
                      <span className={`px-2 py-0.5 rounded-full border text-[10px] ${st.cls}`}>{st.label}</span>
                      <p className="text-white font-semibold text-sm w-16 text-right font-mono">
                        {fmtScore(r?.final_score)}
                      </p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════
   主入口 — 作业 → 提交 → 批改工作台 / 班级报告
   ═══════════════════════════════════════════ */

export default function GradingView() {
  const [view, setView] = useState<'assignments' | 'submissions' | 'workspace' | 'report'>('assignments');
  const [assignment, setAssignment] = useState<AssignmentRow | null>(null);
  const [submissionId, setSubmissionId] = useState<number | null>(null);
  const [submissionRow, setSubmissionRow] = useState<SubmissionRow | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleError = useCallback((m: string) => setError(m), []);

  const openAssignment = (a: AssignmentRow) => {
    setError(null);
    setAssignment(a);
    setView('submissions');
  };

  const openWorkspace = (subId: number, row: SubmissionRow | null) => {
    setError(null);
    setSubmissionId(subId);
    setSubmissionRow(row);
    setView('workspace');
  };

  const openReport = () => {
    setError(null);
    setView('report');
  };

  const backToAssignments = () => {
    setError(null);
    setView('assignments');
    setAssignment(null);
    setSubmissionId(null);
    setSubmissionRow(null);
  };

  const backToSubmissions = () => {
    setError(null);
    setView('submissions');
    setSubmissionId(null);
    setSubmissionRow(null);
  };

  return (
    <div className="space-y-4">
      {view === 'assignments' ? (
        <AssignmentListView onSelect={openAssignment} error={error} onError={handleError} />
      ) : null}

      {view === 'submissions' && assignment ? (
        <SubmissionListView
          assignment={assignment}
          onBack={backToAssignments}
          onOpenWorkspace={openWorkspace}
          onViewReport={openReport}
          error={error}
          onError={handleError}
        />
      ) : null}

      {view === 'workspace' && assignment && submissionId != null ? (
        <WorkspaceView
          key={submissionId}
          submissionId={submissionId}
          assignmentId={assignment.id}
          initialRow={submissionRow}
          onBack={backToSubmissions}
          error={error}
          onError={handleError}
        />
      ) : null}

      {view === 'report' && assignment ? (
        <ReportView assignment={assignment} onBack={backToSubmissions} error={error} onError={handleError} />
      ) : null}
    </div>
  );
}
