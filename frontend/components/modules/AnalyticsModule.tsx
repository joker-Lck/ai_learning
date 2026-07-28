'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';

type AnalyticsTab = 'overview' | 'subjects' | 'quiz' | 'knowledge' | 'report';

export default function AnalyticsModule() {
  const [tab, setTab] = useState<AnalyticsTab>('overview');
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<any>(null);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [types, setTypes] = useState<any[]>([]);
  const [studyTrend, setStudyTrend] = useState<any[]>([]);
  const [quizTrend, setQuizTrend] = useState<any[]>([]);
  const [knowledge, setKnowledge] = useState<any[]>([]);
  const [report, setReport] = useState<any>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [ovRes, subRes, typeRes, trendRes, quizRes, knowRes, repRes] = await Promise.all([
        api.analyticsOverview(),
        api.analyticsSubjectBreakdown(),
        api.analyticsResourceTypeBreakdown(),
        api.analyticsStudyTrend(30),
        api.analyticsQuizTrend(30),
        api.analyticsKnowledgeMastery(),
        api.analyticsWeeklyReport(),
      ]);
      if ((ovRes as any).success) setOverview((ovRes as any).data);
      if ((subRes as any).success) setSubjects((subRes as any).data.subjects || []);
      if ((typeRes as any).success) setTypes((typeRes as any).data.types || []);
      if ((trendRes as any).success) setStudyTrend((trendRes as any).data.trend || []);
      if ((quizRes as any).success) setQuizTrend((quizRes as any).data.trend || []);
      if ((knowRes as any).success) setKnowledge((knowRes as any).data.knowledge || []);
      if ((repRes as any).success) setReport((repRes as any).data);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const tabs = [
    { key: 'overview' as AnalyticsTab, label: '总览' },
    { key: 'subjects' as AnalyticsTab, label: '学科分析' },
    { key: 'quiz' as AnalyticsTab, label: '做题分析' },
    { key: 'knowledge' as AnalyticsTab, label: '知识点掌握' },
    { key: 'report' as AnalyticsTab, label: '周报' },
  ];

  const formatSeconds = (s: number) => {
    if (s < 60) return `${s}秒`;
    if (s < 3600) return `${Math.round(s / 60)}分钟`;
    return `${(s / 3600).toFixed(1)}小时`;
  };

  const typeLabel: Record<string, string> = {
    document: '文档', mindmap: '思维导图', quiz: '题目', video: '视频',
    animation: '动画', code_case: '代码', reading: '阅读',
  };
  const typeColors: Record<string, string> = {
    document: '#a78bfa', mindmap: '#60a5fa', quiz: '#fbbf24', video: '#f87171',
    animation: '#34d399', code_case: '#818cf8', reading: '#f472b6',
  };

  if (loading) {
    return (
      <div className="h-full flex flex-col">
        <div className="flex items-center gap-3 px-6 py-4 border-b border-white/[0.05]">
          <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
            <svg className="w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
          </div>
          <h2 className="text-lg font-semibold text-white">学情分析</h2>
        </div>
        <div className="flex-1 flex items-center justify-center"><div className="text-white/30 text-sm">加载中...</div></div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.05]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
            <svg className="w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
          </div>
          <h2 className="text-lg font-semibold text-white">学情分析</h2>
        </div>
        <button onClick={loadData} className="px-3 py-1.5 text-xs text-white/50 hover:text-white/80 rounded-lg hover:bg-white/5 transition-colors">刷新</button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 px-6 pt-3 border-b border-white/[0.05]">
        {tabs.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-xs rounded-t-lg transition-colors ${tab === t.key ? 'bg-purple-500/20 text-purple-300 border-b-2 border-purple-500' : 'text-white/40 hover:text-white/60'}`}>
            {t.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {/* Overview Tab */}
        {tab === 'overview' && overview && (
          <div className="max-w-2xl mx-auto space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { label: '学习时长', value: formatSeconds(overview.total_study_seconds), color: 'text-purple-400' },
                { label: '生成资源', value: overview.resource_count, color: 'text-blue-400' },
                { label: '做题次数', value: overview.quiz_sessions, color: 'text-amber-400' },
                { label: '平均分', value: overview.quiz_avg_score || '-', color: 'text-emerald-400' },
              ].map((card, i) => (
                <div key={i} className="bg-[#1a1a27] rounded-xl border border-white/[0.05] p-4 text-center">
                  <div className={`text-2xl font-bold ${card.color}`}>{card.value}</div>
                  <div className="text-xs text-white/40 mt-1">{card.label}</div>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="bg-[#1a1a27] rounded-xl border border-white/[0.05] p-4 text-center">
                <div className="text-xl font-bold text-white">{overview.login_days}</div>
                <div className="text-xs text-white/40">活跃天数</div>
              </div>
              <div className="bg-[#1a1a27] rounded-xl border border-white/[0.05] p-4 text-center">
                <div className="text-xl font-bold text-white">{overview.quiz_questions}</div>
                <div className="text-xs text-white/40">总做题数</div>
              </div>
            </div>

            {/* Study Trend Mini Chart */}
            {studyTrend.length > 0 && (
              <div className="bg-[#1a1a27] rounded-xl border border-white/[0.05] p-5">
                <h4 className="text-sm font-medium text-white/60 mb-4">近 30 天学习时长</h4>
                <div className="flex items-end gap-1 h-24">
                  {studyTrend.slice(-14).map((d, i) => {
                    const maxS = Math.max(...studyTrend.map(x => x.seconds));
                    const h = maxS > 0 ? Math.max(4, (d.seconds / maxS) * 100) : 4;
                    return (
                      <div key={i} className="flex-1 flex flex-col items-center gap-1">
                        <div className="w-full rounded-t bg-gradient-to-t from-purple-500/60 to-purple-400/30 transition-all" style={{ height: `${h}%` }} />
                        <span className="text-[10px] text-white/20">{d.date?.slice(5)}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Subjects Tab */}
        {tab === 'subjects' && (
          <div className="max-w-2xl mx-auto space-y-6">
            {subjects.length === 0 ? (
              <div className="text-center text-white/30 py-12">暂无学科数据</div>
            ) : (
              <div className="bg-[#1a1a27] rounded-xl border border-white/[0.05] p-5">
                <h4 className="text-sm font-medium text-white/60 mb-4">学科资源分布</h4>
                <div className="space-y-4">
                  {subjects.map((s, i) => {
                    const maxR = Math.max(...subjects.map(x => x.resource_count));
                    const colors = ['#a78bfa', '#60a5fa', '#34d399', '#fbbf24', '#f87171', '#f472b6'];
                    return (
                      <div key={i}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm text-white/80">{s.subject}</span>
                          <div className="flex items-center gap-3 text-xs text-white/40">
                            <span>{s.resource_count} 份资源</span>
                            {s.quiz_sessions > 0 && <span className="text-amber-400">{s.quiz_sessions} 次做题 · 均分 {s.quiz_avg_score}</span>}
                          </div>
                        </div>
                        <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                          <div className="h-full rounded-full transition-all" style={{ width: `${maxR > 0 ? (s.resource_count / maxR) * 100 : 0}%`, backgroundColor: colors[i % colors.length] }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {types.length > 0 && (
              <div className="bg-[#1a1a27] rounded-xl border border-white/[0.05] p-5">
                <h4 className="text-sm font-medium text-white/60 mb-4">资源类型分布</h4>
                <div className="grid grid-cols-2 gap-3">
                  {types.map((t, i) => (
                    <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-white/[0.02]">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: typeColors[t.resource_type] || '#888' }} />
                      <span className="text-sm text-white/70 flex-1">{typeLabel[t.resource_type] || t.resource_type}</span>
                      <span className="text-sm font-medium text-white">{t.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Quiz Analysis Tab */}
        {tab === 'quiz' && (
          <div className="max-w-2xl mx-auto space-y-6">
            {quizTrend.length === 0 ? (
              <div className="text-center text-white/30 py-12">暂无做题数据，完成一些练习后查看</div>
            ) : (
              <div className="bg-[#1a1a27] rounded-xl border border-white/[0.05] p-5">
                <h4 className="text-sm font-medium text-white/60 mb-4">做题趋势（近 30 天）</h4>
                <div className="flex items-end gap-1 h-32">
                  {quizTrend.map((d, i) => {
                    return (
                      <div key={i} className="flex-1 flex flex-col items-center gap-1">
                        <div className="w-full rounded-t transition-all" style={{
                          height: `${Math.max(4, d.avg_score)}%`,
                          backgroundColor: d.avg_score >= 80 ? '#10b981' : d.avg_score >= 60 ? '#f59e0b' : '#ef4444',
                          opacity: 0.7
                        }} />
                        <span className="text-[10px] text-white/20">{d.date?.slice(5)}</span>
                      </div>
                    );
                  })}
                </div>
                <div className="flex items-center gap-4 mt-3 text-xs text-white/30">
                  <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" /> ≥80分</span>
                  <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500" /> 60-79分</span>
                  <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" /> &lt;60分</span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Knowledge Mastery Tab */}
        {tab === 'knowledge' && (
          <div className="max-w-2xl mx-auto space-y-6">
            {knowledge.length === 0 ? (
              <div className="text-center text-white/30 py-12">暂无知识点数据</div>
            ) : (
              <div className="bg-[#1a1a27] rounded-xl border border-white/[0.05] p-5">
                <h4 className="text-sm font-medium text-white/60 mb-4">知识点掌握度</h4>
                <div className="space-y-2">
                  {knowledge.map((k, i) => (
                    <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-white/[0.02]">
                      <div className="flex-1 min-w-0">
                        <div className="text-sm text-white/80 truncate">{k.knowledge_point}</div>
                        <div className="text-xs text-white/30">{k.total} 题</div>
                      </div>
                      <div className="w-24 h-2 bg-white/5 rounded-full overflow-hidden shrink-0">
                        <div className="h-full rounded-full transition-all" style={{
                          width: `${k.accuracy}%`,
                          backgroundColor: k.accuracy >= 80 ? '#10b981' : k.accuracy >= 60 ? '#f59e0b' : '#ef4444',
                        }} />
                      </div>
                      <span className={`text-xs font-medium w-10 text-right ${k.accuracy >= 80 ? 'text-emerald-400' : k.accuracy >= 60 ? 'text-amber-400' : 'text-red-400'}`}>
                        {k.accuracy}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Weekly Report Tab */}
        {tab === 'report' && (
          <div className="max-w-2xl mx-auto space-y-6">
            {!report || (!report.study_seconds && !report.quiz?.quiz_count) ? (
              <div className="text-center text-white/30 py-12">本周暂无学习数据</div>
            ) : (
              <>
                <div className="bg-[#1a1a27] rounded-xl border border-white/[0.05] p-5">
                  <h4 className="text-sm font-medium text-white/60 mb-4">本周学习概览</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div className="text-center p-3 rounded-lg bg-white/[0.02]">
                      <div className="text-xl font-bold text-purple-400">{formatSeconds(report.study_seconds || 0)}</div>
                      <div className="text-xs text-white/40">学习时长</div>
                    </div>
                    <div className="text-center p-3 rounded-lg bg-white/[0.02]">
                      <div className="text-xl font-bold text-amber-400">{report.quiz?.quiz_count || 0}</div>
                      <div className="text-xs text-white/40">做题次数</div>
                    </div>
                    <div className="text-center p-3 rounded-lg bg-white/[0.02]">
                      <div className="text-xl font-bold text-emerald-400">{report.quiz?.avg_score ? Math.round(report.quiz.avg_score) : '-'}</div>
                      <div className="text-xs text-white/40">平均分</div>
                    </div>
                    <div className="text-center p-3 rounded-lg bg-white/[0.02]">
                      <div className="text-xl font-bold text-blue-400">{report.new_resources || 0}</div>
                      <div className="text-xs text-white/40">新资源</div>
                    </div>
                  </div>
                </div>

                {report.weak_topics && report.weak_topics.length > 0 && (
                  <div className="bg-[#1a1a27] rounded-xl border border-white/[0.05] p-5">
                    <h4 className="text-sm font-medium text-white/60 mb-4">本周薄弱知识点</h4>
                    <div className="space-y-2">
                      {report.weak_topics.map((t: any, i: number) => (
                        <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02]">
                          <span className="text-sm text-white/80">{t.knowledge_point}</span>
                          <span className={`text-xs font-medium ${t.accuracy >= 60 ? 'text-amber-400' : 'text-red-400'}`}>{t.accuracy}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
