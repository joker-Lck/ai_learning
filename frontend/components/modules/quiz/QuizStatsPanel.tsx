'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import type { QuizStats, WeakTopic } from '../types';

export default function QuizStatsPanel() {
  const [stats, setStats] = useState<QuizStats | null>(null);
  const [weakTopics, setWeakTopics] = useState<WeakTopic[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statsRes, weakRes] = await Promise.all([
        api.quizStats(),
        api.quizWeakTopics(10),
      ]);
      if ((statsRes as any).success) setStats((statsRes as any).data);
      if ((weakRes as any).success) setWeakTopics((weakRes as any).data.weak_topics || []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="text-white/30 text-sm">加载中...</div></div>;
  }

  if (!stats || stats.total_sessions === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center mb-3">
          <svg className="w-6 h-6 text-white/20" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
        </div>
        <p className="text-white/40 text-sm">暂无做题数据</p>
      </div>
    );
  }

  const subjectColors = ['#a78bfa', '#60a5fa', '#34d399', '#fbbf24', '#f87171', '#f472b6', '#818cf8'];

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      {/* Overview */}
      <div className="grid grid-cols-4 gap-3">
        <div className="bg-[#1a1a27] rounded-xl border border-white/[0.05] p-4 text-center">
          <div className="text-2xl font-bold text-white">{stats.total_sessions}</div>
          <div className="text-xs text-white/40">做题次数</div>
        </div>
        <div className="bg-[#1a1a27] rounded-xl border border-white/[0.05] p-4 text-center">
          <div className="text-2xl font-bold text-purple-400">{stats.total_questions}</div>
          <div className="text-xs text-white/40">总题数</div>
        </div>
        <div className="bg-[#1a1a27] rounded-xl border border-white/[0.05] p-4 text-center">
          <div className="text-2xl font-bold text-emerald-400">{stats.total_correct}</div>
          <div className="text-xs text-white/40">答对总数</div>
        </div>
        <div className="bg-[#1a1a27] rounded-xl border border-white/[0.05] p-4 text-center">
          <div className="text-2xl font-bold text-amber-400">{stats.avg_score}</div>
          <div className="text-xs text-white/40">平均分</div>
        </div>
      </div>

      {/* By Subject */}
      {stats.by_subject && stats.by_subject.length > 0 && (
        <div className="bg-[#1a1a27] rounded-xl border border-white/[0.05] p-5">
          <h4 className="text-sm font-medium text-white/60 mb-4">学科分布</h4>
          <div className="space-y-3">
            {stats.by_subject.map((s, i) => {
              const maxQ = Math.max(...stats.by_subject.map(x => x.questions));
              return (
                <div key={i}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-white/70">{s.subject}</span>
                    <span className="text-xs text-white/40">{s.sessions}次 · 平均{s.avg_score}分</span>
                  </div>
                  <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all" style={{ width: `${maxQ > 0 ? (s.questions / maxQ) * 100 : 0}%`, backgroundColor: subjectColors[i % subjectColors.length] }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* By Difficulty */}
      {stats.by_difficulty && stats.by_difficulty.length > 0 && (
        <div className="bg-[#1a1a27] rounded-xl border border-white/[0.05] p-5">
          <h4 className="text-sm font-medium text-white/60 mb-4">难度分布</h4>
          <div className="grid grid-cols-3 gap-3">
            {stats.by_difficulty.map((d, i) => {
              const accuracy = d.total > 0 ? Math.round(d.correct / d.total * 100) : 0;
              const diffLabel = d.difficulty === 'easy' ? '简单' : d.difficulty === 'hard' ? '困难' : '中等';
              const diffColor = d.difficulty === 'easy' ? 'text-emerald-400' : d.difficulty === 'hard' ? 'text-red-400' : 'text-amber-400';
              return (
                <div key={i} className="text-center p-3 rounded-lg bg-white/[0.02]">
                  <div className={`text-xl font-bold ${diffColor}`}>{accuracy}%</div>
                  <div className="text-xs text-white/40">{diffLabel} ({d.total}题)</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Weak Topics */}
      {weakTopics.length > 0 && (
        <div className="bg-[#1a1a27] rounded-xl border border-white/[0.05] p-5">
          <h4 className="text-sm font-medium text-white/60 mb-4">薄弱知识点</h4>
          <div className="space-y-2">
            {weakTopics.map((t, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02]">
                <div>
                  <span className="text-sm text-white/80">{t.knowledge_point}</span>
                  <span className="text-xs text-white/30 ml-2">({t.total}题)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-20 h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${t.accuracy}%`, backgroundColor: t.accuracy >= 80 ? '#10b981' : t.accuracy >= 60 ? '#f59e0b' : '#ef4444' }} />
                  </div>
                  <span className={`text-xs font-medium ${t.accuracy >= 80 ? 'text-emerald-400' : t.accuracy >= 60 ? 'text-amber-400' : 'text-red-400'}`}>{t.accuracy}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
