'use client';

// 学生端「班级作业」— 查看老师发布的练习/试卷，支持文本作答 + 手写图拍照上传

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ClipboardList, Loader2, FileText, Upload, CheckCircle2,
  ChevronLeft, AlertTriangle, Sparkles,
} from 'lucide-react';
import api from '@/lib/api';

const TYPE_LABELS: Record<string, string> = {
  multiple_choice: '选择题',
  judge: '判断题',
  fill_blank: '填空题',
  short_answer: '简答题',
};

export default function ClassAssignmentsView() {
  const [list, setList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [active, setActive] = useState<any>(null); // 当前作业
  const [questions, setQuestions] = useState<any[]>([]);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [submissionId, setSubmissionId] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState<{ type: 'ok' | 'err'; msg: string } | null>(null);

  const showToast = (type: 'ok' | 'err', msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 3500);
  };

  const loadList = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res: any = await api.myExamAssignments();
      if (res.success) setList(res.data || []);
      else setError(res.message || '加载失败');
    } catch (e: any) {
      setError(e?.message || '加载失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadList(); }, [loadList]);

  const openAssignment = async (a: any) => {
    setBusy(true);
    setError('');
    try {
      const res: any = await api.getExamAssignmentPaper(a.id);
      if (!res.success) {
        showToast('err', res.message || '获取题目失败');
        return;
      }
      setActive({ ...a, ...(res.data || {}) });
      setQuestions((res.data?.paper?.questions) || []);
      setSubmissionId(null);
      setAnswers({});
    } catch (e: any) {
      showToast('err', e?.message || '获取题目失败');
    } finally {
      setBusy(false);
    }
  };

  // 建作答记录（支持上传手写图）
  const ensureSubmission = async (): Promise<number | null> => {
    if (submissionId) return submissionId;
    const res: any = await api.createExamSubmission({ assignment_id: active.id });
    if (!res.success || !res.data?.id) {
      showToast('err', res.message || '创建作答记录失败');
      return null;
    }
    setSubmissionId(res.data.id);
    return res.data.id;
  };

  const uploadImage = async (questionId: number, file: File) => {
    const sid = await ensureSubmission();
    if (!sid) return;
    setBusy(true);
    try {
      const res: any = await api.uploadExamAnswerImage(sid, questionId, file, true);
      if (res.success) {
        const ocrText = res.data?.ocr?.ocr_text;
        if (ocrText) {
          setAnswers(prev => ({ ...prev, [questionId]: ocrText }));
        }
        showToast('ok', res.data?.ocr?.low_confidence
          ? '图片已上传，识别置信度较低，请校对文字'
          : '图片已上传并完成手写识别');
      } else {
        showToast('err', res.message || '上传失败');
      }
    } catch (e: any) {
      showToast('err', e?.message || '上传失败');
    } finally {
      setBusy(false);
    }
  };

  const handleSubmit = async () => {
    if (!active) return;
    setBusy(true);
    try {
      const payload = {
        answers: questions.map((q: any) => ({
          question_id: q.id,
          answer_text: answers[q.id] || '',
        })),
      };
      const res: any = await api.submitExamAssignment(active.id, payload);
      if (res.success) {
        setSubmissionId(res.data?.submission_id ?? null);
        showToast('ok', '已交卷，老师批改后可查看成绩');
        loadList();
      } else {
        showToast('err', res.message || '交卷失败');
      }
    } catch (e: any) {
      showToast('err', e?.message || '交卷失败');
    } finally {
      setBusy(false);
    }
  };

  // ── 列表视图 ──
  if (!active) {
    return (
      <div className="space-y-4">
        {toast && (
          <div className={`px-4 py-2 rounded-lg text-sm ${toast.type === 'ok' ? 'bg-emerald-500/15 text-emerald-300' : 'bg-red-500/15 text-red-300'}`}>
            {toast.msg}
          </div>
        )}
        <div className="flex items-center gap-2">
          <ClipboardList className="w-5 h-5 text-teal-400" />
          <h3 className="text-white font-medium">班级作业</h3>
          {loading && <Loader2 className="w-4 h-4 text-white/40 animate-spin" />}
        </div>
        {error && <p className="text-red-400 text-sm">{error}</p>}
        {!loading && list.length === 0 && (
          <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-10 text-center">
            <FileText className="w-10 h-10 text-white/20 mx-auto mb-3" />
            <p className="text-white/40 text-sm">暂无班级作业</p>
            <p className="text-white/25 text-xs mt-1">老师发布练习或试卷后会显示在这里</p>
          </div>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {list.map((a: any) => (
            <button
              key={a.id}
              onClick={() => openAssignment(a)}
              disabled={busy}
              className="text-left rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 hover:bg-white/[0.05] hover:border-teal-400/30 transition-colors"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-white font-medium">{a.title || '未命名作业'}</p>
                  <p className="text-white/40 text-xs mt-1">
                    {a.subject || '综合'} · {a.paper_type === 'exam' ? '考试' : '练习'} · 满分 {a.total_score}
                    {a.duration_minutes ? ` · ${a.duration_minutes} 分钟` : ''}
                  </p>
                  {a.due_at && (
                    <p className="text-white/30 text-xs mt-1">截止：{String(a.due_at).replace('T', ' ').slice(0, 16)}</p>
                  )}
                </div>
                <StatusBadge status={a.my_status} />
              </div>
            </button>
          ))}
        </div>
      </div>
    );
  }

  // ── 作答视图 ──
  return (
    <div className="space-y-4">
      {toast && (
        <div className={`px-4 py-2 rounded-lg text-sm ${toast.type === 'ok' ? 'bg-emerald-500/15 text-emerald-300' : 'bg-red-500/15 text-red-300'}`}>
          {toast.msg}
        </div>
      )}
      <button
        onClick={() => { setActive(null); setQuestions([]); setSubmissionId(null); loadList(); }}
        className="flex items-center gap-1 text-white/50 hover:text-white text-sm"
      >
        <ChevronLeft className="w-4 h-4" /> 返回作业列表
      </button>

      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
        <h3 className="text-white font-medium">{active.title || '未命名作业'}</h3>
        <p className="text-white/40 text-xs mt-1">
          {active.subject || '综合'} · 共 {questions.length} 题 · 满分 {active.paper?.total_score ?? active.total_score}
        </p>
      </div>

      {questions.map((q: any, idx: number) => (
        <div key={q.id ?? idx} className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 space-y-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="px-2 py-0.5 rounded-md bg-teal-400/15 text-teal-300 text-xs">
              {TYPE_LABELS[q.question_type] || q.question_type}
            </span>
            <span className="text-white/40 text-xs">第 {q.q_index + 1} 题</span>
            {q.score ? <span className="text-white/30 text-xs">{q.score} 分</span> : null}
            {q.knowledge_point ? <span className="text-white/25 text-xs">知识点：{q.knowledge_point}</span> : null}
          </div>
          <p className="text-white/85 text-sm leading-relaxed">{q.question_text}</p>
          {(q.options || []).length > 0 && (
            <div className="space-y-1 pl-2">
              {q.options.map((o: string, i: number) => (
                <p key={i} className="text-white/55 text-sm">{o}</p>
              ))}
            </div>
          )}
          <textarea
            value={answers[q.id] || ''}
            onChange={e => setAnswers(prev => ({ ...prev, [q.id]: e.target.value }))}
            placeholder="在此作答（也可拍照上传手写答案）"
            rows={q.question_type === 'short_answer' ? 5 : 2}
            className="w-full rounded-lg bg-white/[0.04] border border-white/[0.06] text-white text-sm px-3 py-2 focus:outline-none focus:border-teal-400/50"
          />
          <ImageUpload questionId={q.id} onUpload={uploadImage} disabled={busy} />
        </div>
      ))}

      <div className="flex items-center gap-3">
        <button
          onClick={handleSubmit}
          disabled={busy}
          className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-teal-500/80 hover:bg-teal-500 text-white text-sm font-medium disabled:opacity-50"
        >
          {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
          交卷
        </button>
        <p className="text-white/30 text-xs">交卷后老师将批改，主观题支持手写答案识别</p>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status?: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    in_progress: { label: '作答中', cls: 'bg-amber-400/15 text-amber-300' },
    submitted: { label: '已提交', cls: 'bg-blue-400/15 text-blue-300' },
    graded: { label: '已批改', cls: 'bg-emerald-400/15 text-emerald-300' },
    reviewed: { label: '已复核', cls: 'bg-purple-400/15 text-purple-300' },
  };
  const s = map[status || ''] || { label: '未作答', cls: 'bg-white/[0.06] text-white/50' };
  return <span className={`px-2 py-0.5 rounded-md text-xs whitespace-nowrap ${s.cls}`}>{s.label}</span>;
}

function ImageUpload({ questionId, onUpload, disabled }: {
  questionId: number;
  onUpload: (questionId: number, file: File) => Promise<void>;
  disabled?: boolean;
}) {
  const ref = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);

  const pick = async (file: File | undefined) => {
    if (!file) return;
    setUploading(true);
    try {
      await onUpload(questionId, file);
      const url = URL.createObjectURL(file);
      setPreview(prev => { if (prev) URL.revokeObjectURL(prev); return url; });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex items-center gap-3">
      <input
        ref={ref}
        type="file"
        accept="image/jpeg,image/png,image/bmp,image/webp"
        className="hidden"
        onChange={e => { pick(e.target.files?.[0]); e.target.value = ''; }}
      />
      <button
        onClick={() => ref.current?.click()}
        disabled={disabled || uploading}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.05] border border-white/[0.08] text-white/60 hover:text-white hover:border-teal-400/40 text-xs disabled:opacity-50"
      >
        {uploading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
        拍照上传手写答案
      </button>
      {preview && (
        <img src={preview} alt="手写答案" className="w-14 h-14 object-cover rounded-lg border border-white/10" />
      )}
      <span className="text-white/25 text-xs flex items-center gap-1">
        <Sparkles className="w-3 h-3" /> 自动手写识别
      </span>
    </div>
  );
}
