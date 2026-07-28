'use client';

import { useState } from 'react';
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
        // 错题重练：从错题本直接取题
        const res = await api.getErrorNotes(subject || undefined, 0) as any;
        if (res.success && Array.isArray(res.data) && res.data.length > 0) {
          const shuffled = [...res.data].sort(() => Math.random() - 0.5);
          const selected = shuffled.slice(0, questionCount);
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
        }
        if (questions.length === 0) {
          setError('暂无错题数据，请先完成一些练习');
          return;
        }
      } else {
        // 普通练习 / 薄弱点专练
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
        <input type="text" value={topic} onChange={e => setTopic(e.target.value)}
          placeholder="或输入具体知识点（可选）"
          className="w-full px-4 py-2.5 bg-white/5 border border-white/[0.06] rounded-lg text-sm text-white placeholder-white/20 focus:outline-none focus:border-purple-500/30" />
      </div>

      {/* Question Count */}
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

      {error && <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">{error}</div>}

      <button onClick={handleGenerateAndStart} disabled={generating || loading}
        className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-500 to-violet-500 text-white font-medium text-sm hover:from-purple-600 hover:to-violet-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed">
        {generating ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
            {mode === 'review' ? '加载错题中...' : 'AI 出题中...'}
          </span>
        ) : '开始做题'}
      </button>
    </div>
  );
}
