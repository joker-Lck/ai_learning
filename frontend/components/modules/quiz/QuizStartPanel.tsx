'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import type { QuizQuestion, ErrorNote } from '../types';

interface Props {
  onStart: (config: { subject?: string; topic?: string; mode: string; questions: QuizQuestion[] }) => void;
  loading: boolean;
}

const SUBJECTS = ['数学', '英语', 'Python', '数据结构', '机器学习', '深度学习', '计算机网络', '操作系统', '数据库'];

export default function QuizStartPanel({ onStart, loading }: Props) {
  const [subject, setSubject] = useState('');
  const [topic, setTopic] = useState('');
  const [mode, setMode] = useState<'practice' | 'adaptive' | 'review'>('practice');
  const [questionCount, setQuestionCount] = useState(10);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  // 错题重练相关状态
  const [errorNotes, setErrorNotes] = useState<ErrorNote[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [loadingNotes, setLoadingNotes] = useState(false);

  // 切换到错题重练模式时加载错题
  useEffect(() => {
    if (mode !== 'review') {
      setErrorNotes([]);
      setSelectedIds(new Set());
      return;
    }
    const loadNotes = async () => {
      setLoadingNotes(true);
      setError('');
      try {
        const res = await api.getErrorNotes(subject || undefined, 0) as any;
        if (res.success && Array.isArray(res.data)) {
          setErrorNotes(res.data);
          // 默认全选
          setSelectedIds(new Set(res.data.map((n: ErrorNote) => n.id).filter((id: number | undefined): id is number => id != null)));
        } else {
          setErrorNotes([]);
        }
      } catch {
        setErrorNotes([]);
      } finally {
        setLoadingNotes(false);
      }
    };
    loadNotes();
  }, [mode, subject]);

  const toggleSelect = (id: number) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const selectAll = () => setSelectedIds(new Set(errorNotes.map(n => n.id).filter((id: number | undefined): id is number => id != null)));
  const deselectAll = () => setSelectedIds(new Set());

  const selectRandom = (count: number) => {
    const shuffled = [...errorNotes].sort(() => Math.random() - 0.5);
    setSelectedIds(new Set(shuffled.slice(0, count).map(n => n.id).filter((id: number | undefined): id is number => id != null)));
  };

  const handleGenerateAndStart = async () => {
    if (mode !== 'review' && !subject && !topic) {
      setError('请选择学科或输入知识点后再出题');
      return;
    }
    setGenerating(true);
    setError('');

    try {
      let questions: QuizQuestion[] = [];

      if (mode === 'review') {
        const selected = errorNotes.filter(n => n.id && selectedIds.has(n.id));
        if (selected.length === 0) {
          setError('请至少选择一道错题');
          setGenerating(false);
          return;
        }
        questions = selected.map((note: ErrorNote, i: number) => ({
          id: note.id || i,
          type: 'fill_blank' as const,
          question: note.question,
          options: [],
          answer: note.correct_answer || '',
          explanation: note.error_reason || '',
          difficulty: 'medium' as const,
          knowledge_point: note.chapter || note.subject,
        }));
      } else {
        const res = await api.quizAdaptive({ subject: subject || topic || undefined, count: questionCount }) as any;
        if (res.success) {
          questions = res.data.questions;
        } else {
          setError(res.message || '出题失败');
          return;
        }
      }

      if (questions.length > 0) {
        onStart({ subject: subject || undefined, topic: topic || undefined, mode, questions });
      }
    } catch (err: any) {
      setError(err.message || '出题失败，请重试');
    } finally {
      setGenerating(false);
    }
  };

  const selectedCount = selectedIds.size;

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <div className="w-16 h-16 rounded-2xl bg-amber-500/20 flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
        </div>
        <h3 className="text-xl font-bold text-white mb-2">开始做题</h3>
        <p className="text-white/40 text-sm">选择模式和学科，AI 将为你生成针对性练习题</p>
      </div>

      {/* Mode Selection */}
      <div className="mb-6">
        <label className="block text-sm text-white/60 mb-3">练习模式</label>
        <div className="grid grid-cols-3 gap-3">
          {[
            { key: 'practice' as const, label: '普通练习', desc: 'AI 出题', icon: '📝' },
            { key: 'adaptive' as const, label: '薄弱点专练', desc: '针对弱项', icon: '🎯' },
            { key: 'review' as const, label: '错题重练', desc: '巩固记忆', icon: '🔄' },
          ].map(m => (
            <button key={m.key} onClick={() => setMode(m.key)}
              className={`p-4 rounded-xl border text-left transition-all ${mode === m.key ? 'border-purple-500/50 bg-purple-500/10' : 'border-white/[0.05] bg-[#1a1a27] hover:border-white/[0.1]'}`}>
              <div className="text-lg mb-1">{m.icon}</div>
              <div className="text-sm font-medium text-white">{m.label}</div>
              <div className="text-xs text-white/40">{m.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Subject */}
      <div className="mb-6">
        <label className="block text-sm text-white/60 mb-2">学科</label>
        <div className="flex flex-wrap gap-2 mb-2">
          {SUBJECTS.map(s => (
            <button key={s} onClick={() => setSubject(s === subject ? '' : s)}
              className={`px-3 py-1.5 text-xs rounded-lg transition-all ${subject === s ? 'bg-purple-500/30 text-purple-300 border border-purple-500/30' : 'bg-white/5 text-white/50 border border-white/[0.05] hover:text-white/70'}`}>
              {s}
            </button>
          ))}
        </div>
        {mode !== 'review' && (
          <input type="text" value={topic} onChange={e => setTopic(e.target.value)}
            placeholder="或输入具体知识点（可选）"
            className="w-full px-4 py-2.5 bg-white/5 border border-white/[0.06] rounded-lg text-sm text-white placeholder-white/20 focus:outline-none focus:border-purple-500/30" />
        )}
      </div>

      {/* Question Count (非 review 模式) */}
      {mode !== 'review' && (
        <div className="mb-6">
          <label className="block text-sm text-white/60 mb-2">题目数量</label>
          <div className="flex gap-2">
            {[5, 10, 15, 20].map(n => (
              <button key={n} onClick={() => setQuestionCount(n)}
                className={`px-4 py-2 text-sm rounded-lg transition-all ${questionCount === n ? 'bg-purple-500/30 text-purple-300 border border-purple-500/30' : 'bg-white/5 text-white/50 border border-white/[0.05] hover:text-white/70'}`}>
                {n} 题
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 错题选择列表 (review 模式) */}
      {mode === 'review' && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <label className="text-sm text-white/60">
              选择错题 <span className="text-white/30">({selectedCount}/{errorNotes.length})</span>
            </label>
            <div className="flex gap-2">
              <button onClick={selectAll} className="text-[11px] px-2.5 py-1 rounded-lg bg-white/5 text-white/40 hover:text-white/70 border border-white/[0.06] transition-colors">全选</button>
              <button onClick={deselectAll} className="text-[11px] px-2.5 py-1 rounded-lg bg-white/5 text-white/40 hover:text-white/70 border border-white/[0.06] transition-colors">全不选</button>
              <button onClick={() => selectRandom(questionCount)} className="text-[11px] px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 border border-amber-500/20 transition-colors">随机 {questionCount} 题</button>
            </div>
          </div>

          {loadingNotes ? (
            <div className="text-center py-8">
              <svg className="w-5 h-5 animate-spin text-purple-400 mx-auto mb-2" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
              <p className="text-xs text-white/30">加载错题中...</p>
            </div>
          ) : errorNotes.length === 0 ? (
            <div className="text-center py-8 rounded-xl bg-white/[0.02] border border-white/[0.05]">
              <p className="text-sm text-white/25">暂无错题数据，请先完成一些练习</p>
            </div>
          ) : (
            <div className="max-h-[320px] overflow-y-auto space-y-2 pr-1">
              {errorNotes.map((note) => {
                const isSelected = note.id ? selectedIds.has(note.id) : false;
                const subjectColors: Record<string, string> = {
                  '数学': 'text-blue-400', '英语': 'text-emerald-400', '物理': 'text-purple-400',
                  '化学': 'text-amber-400', '生物': 'text-green-400',
                };
                const sColor = subjectColors[note.subject] || 'text-red-400';
                return (
                  <div key={note.id}
                    onClick={() => note.id && toggleSelect(note.id)}
                    className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-all ${
                      isSelected ? 'border-purple-500/40 bg-purple-500/[0.06]' : 'border-white/[0.04] bg-white/[0.01] hover:border-white/[0.08]'
                    }`}>
                    <div className={`mt-0.5 w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 transition-all ${
                      isSelected ? 'border-purple-400 bg-purple-500' : 'border-white/20'
                    }`}>
                      {isSelected && <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-[10px] px-1.5 py-0.5 rounded bg-white/5 ${sColor} font-medium`}>{note.subject || '未知'}</span>
                        {note.chapter && <span className="text-[10px] text-white/20 truncate">{note.chapter}</span>}
                      </div>
                      <p className="text-sm text-white/70 line-clamp-2">{note.question}</p>
                      {note.error_reason && <p className="text-[11px] text-white/20 mt-1 line-clamp-1">错因：{note.error_reason}</p>}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {error && <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">{error}</div>}

      <button onClick={handleGenerateAndStart} disabled={generating || loading || (mode === 'review' && selectedCount === 0)}
        className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-500 to-violet-500 text-white font-medium text-sm hover:from-purple-600 hover:to-violet-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed">
        {generating ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
            {mode === 'review' ? '加载错题中...' : 'AI 出题中...'}
          </span>
        ) : mode === 'review' ? `开始练习 ${selectedCount} 道错题` : '开始做题'}
      </button>
    </div>
  );
}
