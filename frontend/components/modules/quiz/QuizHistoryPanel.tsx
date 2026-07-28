'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import type { QuizSession } from '../types';

export default function QuizHistoryPanel() {
  const [sessions, setSessions] = useState<QuizSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState<QuizSession | null>(null);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const res = await api.quizHistory(50) as any;
      if (res.success) setSessions(res.data.sessions || []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const loadDetail = async (id: number) => {
    try {
      const res = await api.quizSessionDetail(id) as any;
      if (res.success) setDetail(res.data);
    } catch (err) { console.error(err); }
  };

  const modeLabel = (m: string) => m === 'adaptive' ? '薄弱点专练' : m === 'review' ? '错题重练' : '普通练习';
  const modeColor = (m: string) => m === 'adaptive' ? 'text-amber-400 bg-amber-500/10' : m === 'review' ? 'text-cyan-400 bg-cyan-500/10' : 'text-purple-400 bg-purple-500/10';

  if (detail) {
    return (
      <div className="p-6 max-w-2xl mx-auto">
        <button onClick={() => setDetail(null)} className="mb-4 text-sm text-white/50 hover:text-white/80 flex items-center gap-1">
          ← 返回列表
        </button>
        <div className="bg-[#1a1a27] rounded-xl border border-white/[0.05] p-5 mb-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-white font-medium">{detail.subject || '综合'} · {detail.topic || '练习'}</h3>
            <span className={`text-xs px-2 py-0.5 rounded-full ${modeColor(detail.mode)}`}>{modeLabel(detail.mode)}</span>
          </div>
          <div className="grid grid-cols-4 gap-3 text-center">
            <div><div className="text-xl font-bold text-white">{detail.score}</div><div className="text-xs text-white/40">得分</div></div>
            <div><div className="text-xl font-bold text-emerald-400">{detail.correct_count}</div><div className="text-xs text-white/40">答对</div></div>
            <div><div className="text-xl font-bold text-red-400">{detail.total_questions - detail.correct_count}</div><div className="text-xs text-white/40">答错</div></div>
            <div><div className="text-xl font-bold text-white/60">{detail.total_questions}</div><div className="text-xs text-white/40">总题</div></div>
          </div>
        </div>
        {detail.answers && (
          <div className="space-y-3">
            {detail.answers.map((a, i) => (
              <div key={i} className={`bg-[#1a1a27] rounded-xl border p-4 ${a.is_correct ? 'border-emerald-500/10' : 'border-red-500/10'}`}>
                <div className="flex items-start gap-2 mb-2">
                  <span className={`text-xs px-2 py-0.5 rounded shrink-0 ${a.is_correct ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                    {a.is_correct ? '✓' : '✗'}
                  </span>
                  <p className="text-sm text-white/80">{a.question_text}</p>
                </div>
                {!a.is_correct && (
                  <div className="ml-8 text-xs space-y-1">
                    <p className="text-white/40">你的：<span className="text-red-400">{a.user_answer || '未作答'}</span></p>
                    <p className="text-white/40">正确：<span className="text-emerald-400">{a.correct_answer}</span></p>
                    {a.explanation && <p className="text-white/30 mt-1">{a.explanation}</p>}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="text-white/30 text-sm">加载中...</div></div>;
  }

  if (sessions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center mb-3">
          <svg className="w-6 h-6 text-white/20" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        </div>
        <p className="text-white/40 text-sm">暂无做题记录</p>
        <p className="text-white/20 text-xs mt-1">完成一次练习后这里会显示历史</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h3 className="text-sm font-medium text-white/60 mb-4">做题历史（{sessions.length} 次）</h3>
      <div className="space-y-2">
        {sessions.map(s => (
          <button key={s.id} onClick={() => loadDetail(s.id)}
            className="w-full bg-[#1a1a27] rounded-xl border border-white/[0.05] p-4 hover:border-white/[0.1] transition-all text-left">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold ${s.score >= 80 ? 'bg-emerald-500/20 text-emerald-400' : s.score >= 60 ? 'bg-amber-500/20 text-amber-400' : 'bg-red-500/20 text-red-400'}`}>
                  {Math.round(s.score)}
                </div>
                <div>
                  <div className="text-sm text-white">{s.subject || '综合'} · {s.total_questions} 题</div>
                  <div className="text-xs text-white/30 mt-0.5">{s.created_at?.slice(0, 16)?.replace('T', ' ')}</div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xs px-2 py-0.5 rounded-full ${modeColor(s.mode)}`}>{modeLabel(s.mode)}</span>
                <span className="text-white/20 text-xs">{s.correct_count}/{s.total_questions}</span>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
