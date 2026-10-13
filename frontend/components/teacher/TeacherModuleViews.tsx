'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Brain, BookOpen, Router, ClipboardCheck, PieChart, Lightbulb,
  ChevronDown, AlertTriangle,
} from 'lucide-react';
import api from '@/lib/api';

/* ── 学生选择器 ── */
function StudentSelector({
  students, selected, onSelect,
}: {
  students: any[]; selected: any; onSelect: (s: any) => void;
}) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <span className="text-white/30 text-xs">选择学生:</span>
      <div className="relative">
        <select
          value={selected?.id || ''}
          onChange={(e) => {
            const s = students.find(st => st.id === Number(e.target.value));
            if (s) onSelect(s);
          }}
          className="appearance-none pl-3 pr-8 py-2 rounded-lg bg-white/[0.04] border border-white/[0.06] text-white text-sm focus:border-white/[0.15] outline-none cursor-pointer"
        >
          <option value="">-- 全部学生 --</option>
          {students.map((s: any) => (
            <option key={s.id} value={s.id}>{s.username} ({s.class_name || '未入班'})</option>
          ))}
        </select>
        <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20 pointer-events-none" />
      </div>
      {selected && (
        <button
          onClick={() => onSelect(null)}
          className="text-white/30 text-xs hover:text-white/50 transition-colors"
        >
          清除选择
        </button>
      )}
    </div>
  );
}

function useStudents() {
  const [students, setStudents] = useState<any[]>([]);
  useEffect(() => {
    api.teacherListStudents().then((res: any) => {
      if (res.success) setStudents(res.data || []);
    }).catch(() => {});
  }, []);
  return students;
}

function EmptyState({ icon: Icon, title, desc }: { icon: any; title: string; desc: string }) {
  return (
    <div className="text-center py-12">
      <Icon className="w-10 h-10 text-white/10 mx-auto mb-3" />
      <p className="text-white/30 text-sm">{title}</p>
      <p className="text-white/20 text-xs mt-1">{desc}</p>
    </div>
  );
}

function Loading() {
  return <div className="text-white/30 text-sm py-12 text-center">加载中...</div>;
}

/* ═══════════════════════════════════════════
   学情画像 — 查看学生画像
   ═══════════════════════════════════════════ */
export function TeachingProfileView() {
  const students = useStudents();
  const [selected, setSelected] = useState<any>(null);
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const loadProfile = useCallback(async (s: any) => {
    if (!s) { setProfile(null); return; }
    setLoading(true);
    try {
      const res: any = await api.teacherStudentProfile(s.id);
      if (res.success) setProfile(res.data);
    } catch {}
    finally { setLoading(false); }
  }, []);

  return (
    <div>
      <StudentSelector students={students} selected={selected} onSelect={(s) => { setSelected(s); loadProfile(s); }} />
      {!selected ? (
        <EmptyState icon={Brain} title="请先选择学生" desc="选择学生后可查看其 9 维度画像" />
      ) : loading ? <Loading /> : profile?.profile_data ? (
        <ProfileContent data={profile} />
      ) : (
        <EmptyState icon={Brain} title="暂无画像数据" desc={`${selected.username} 尚未构建学习画像`} />
      )}
    </div>
  );
}

function ProfileContent({ data }: { data: any }) {
  const pd = typeof data.profile_data === 'string' ? (() => { try { return JSON.parse(data.profile_data); } catch { return null; } })() : data.profile_data;
  if (!pd) return <EmptyState icon={Brain} title="画像数据格式异常" desc="" />;
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {Object.entries(pd).map(([k, v]) => (
        <div key={k} className="rounded-lg bg-white/[0.03] p-3">
          <p className="text-white/40 text-xs mb-1">{k}</p>
          <p className="text-white/70 text-sm">
            {typeof v === 'object' ? JSON.stringify(v).slice(0, 100) : String(v)}
          </p>
        </div>
      ))}
    </div>
  );
}

/* ═══════════════════════════════════════════
   教学资源 — 查看学生资源
   ═══════════════════════════════════════════ */
export function TeachingResourcesView() {
  const students = useStudents();
  const [selected, setSelected] = useState<any>(null);
  const [resources, setResources] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async (s: any) => {
    if (!s) { setResources([]); return; }
    setLoading(true);
    try {
      const res: any = await api.teacherStudentResources(s.id);
      if (res.success) setResources(res.data || []);
    } catch {}
    finally { setLoading(false); }
  }, []);

  return (
    <div>
      <StudentSelector students={students} selected={selected} onSelect={(s) => { setSelected(s); load(s); }} />
      {!selected ? (
        <EmptyState icon={BookOpen} title="请先选择学生" desc="选择学生后可查看其学习资源列表" />
      ) : loading ? <Loading /> : resources.length === 0 ? (
        <EmptyState icon={BookOpen} title="暂无资源" desc={`${selected.username} 尚未生成学习资源`} />
      ) : (
        <div className="space-y-1.5">
          {resources.map((r: any, i: number) => (
            <div key={i} className="flex items-center justify-between px-3 py-2.5 rounded-lg bg-white/[0.03]">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center">
                  <BookOpen className="w-4 h-4 text-cyan-400" />
                </div>
                <div>
                  <p className="text-white/70 text-sm">{r.title}</p>
                  <p className="text-white/25 text-xs">{r.resource_type} · {r.subject || ''}</p>
                </div>
              </div>
              <span className="text-white/25 text-xs">{r.created_at?.slice(0, 10)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════
   教学路径 — 查看学生学习路径
   ═══════════════════════════════════════════ */
export function TeachingPathView() {
  const students = useStudents();
  const [selected, setSelected] = useState<any>(null);
  const [paths, setPaths] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async (s: any) => {
    if (!s) { setPaths([]); return; }
    setLoading(true);
    try {
      const res: any = await api.teacherStudentLearningPath(s.id);
      if (res.success) setPaths(res.data || []);
    } catch {}
    finally { setLoading(false); }
  }, []);

  return (
    <div>
      <StudentSelector students={students} selected={selected} onSelect={(s) => { setSelected(s); load(s); }} />
      {!selected ? (
        <EmptyState icon={Router} title="请先选择学生" desc="选择学生后可查看其学习路径进度" />
      ) : loading ? <Loading /> : paths.length === 0 ? (
        <EmptyState icon={Router} title="暂无学习路径" desc={`${selected.username} 尚未规划学习路径`} />
      ) : (
        <div className="space-y-3">
          {paths.map((p: any, i: number) => {
            const pct = p.total_steps ? Math.round((p.completed_steps / p.total_steps) * 100) : 0;
            return (
              <div key={i} className="rounded-lg bg-white/[0.03] p-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-white/70 text-sm font-medium">{p.path_name}</p>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full ${
                    p.status === 'completed' ? 'bg-emerald-500/15 text-emerald-300' :
                    p.status === 'active' ? 'bg-cyan-500/15 text-cyan-300' : 'bg-white/10 text-white/40'
                  }`}>{p.status}</span>
                </div>
                {p.description && <p className="text-white/30 text-xs mb-2">{p.description}</p>}
                <div className="w-full bg-white/[0.05] rounded-full h-2">
                  <div className="bg-gradient-to-r from-purple-500 to-cyan-400 h-2 rounded-full transition-all" style={{ width: `${pct}%` }} />
                </div>
                <div className="flex items-center justify-between mt-1.5">
                  <span className="text-white/30 text-xs">{p.completed_steps}/{p.total_steps} 步</span>
                  <span className="text-white/40 text-xs font-mono">{pct}%</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════
   班级评估 — 查看学生评估报告
   ═══════════════════════════════════════════ */
export function TeachingAssessmentView() {
  const students = useStudents();
  const [selected, setSelected] = useState<any>(null);
  const [assessments, setAssessments] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async (s: any) => {
    if (!s) { setAssessments([]); return; }
    setLoading(true);
    try {
      const res: any = await api.teacherStudentAssessment(s.id);
      if (res.success) setAssessments(res.data || []);
    } catch {}
    finally { setLoading(false); }
  }, []);

  return (
    <div>
      <StudentSelector students={students} selected={selected} onSelect={(s) => { setSelected(s); load(s); }} />
      {!selected ? (
        <EmptyState icon={ClipboardCheck} title="请先选择学生" desc="选择学生后可查看其效果评估报告" />
      ) : loading ? <Loading /> : assessments.length === 0 ? (
        <EmptyState icon={ClipboardCheck} title="暂无评估报告" desc={`${selected.username} 尚无评估记录`} />
      ) : (
        <div className="space-y-3">
          {assessments.map((a: any, i: number) => (
            <div key={i} className="rounded-lg bg-white/[0.03] p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-white/50 text-xs px-2 py-0.5 rounded-full bg-white/[0.05]">{a.assessment_type}</span>
                  <span className="text-white/25 text-xs">{a.created_at?.slice(0, 10)}</span>
                </div>
                <div className="text-right">
                  <p className={`text-lg font-bold ${
                    (a.overall_score || 0) >= 80 ? 'text-emerald-400' :
                    (a.overall_score || 0) >= 60 ? 'text-amber-400' : 'text-red-400'
                  }`}>{a.overall_score ?? '-'}</p>
                  <p className="text-white/25 text-[10px]">总评分</p>
                </div>
              </div>
              {a.improvement_suggestions && (
                <p className="text-white/30 text-xs leading-relaxed">{a.improvement_suggestions}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════
   题库测验 — 查看学生做题数据
   ═══════════════════════════════════════════ */
export function TeachingQuizView() {
  const students = useStudents();
  const [selected, setSelected] = useState<any>(null);
  const [quizData, setQuizData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async (s: any) => {
    if (!s) { setQuizData(null); return; }
    setLoading(true);
    try {
      const res: any = await api.teacherStudentQuiz(s.id);
      if (res.success) setQuizData(res.data);
    } catch {}
    finally { setLoading(false); }
  }, []);

  return (
    <div>
      <StudentSelector students={students} selected={selected} onSelect={(s) => { setSelected(s); load(s); }} />
      {!selected ? (
        <EmptyState icon={PieChart} title="请先选择学生" desc="选择学生后可查看其测验记录与薄弱知识点" />
      ) : loading ? <Loading /> : !quizData ? (
        <EmptyState icon={PieChart} title="暂无做题数据" desc="" />
      ) : (
        <div className="space-y-4">
          {/* 统计 */}
          <div className="grid grid-cols-3 gap-3">
            <StatBox label="测验次数" value={quizData.stats?.c ?? 0} color="text-amber-400" />
            <StatBox label="平均分" value={quizData.stats?.avg_score ?? 0} color="text-emerald-400" />
            <StatBox label="薄弱知识点" value={quizData.weak_topics?.length ?? 0} color="text-red-400" />
          </div>

          {/* 薄弱知识点 */}
          {quizData.weak_topics?.length > 0 && (
            <div>
              <p className="text-white/40 text-xs mb-2">薄弱知识点排行</p>
              {quizData.weak_topics.map((t: any, i: number) => (
                <div key={i} className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white/[0.03] mb-1">
                  <AlertTriangle className={`w-4 h-4 ${i < 3 ? 'text-red-400' : 'text-white/20'}`} />
                  <span className="text-white/60 text-sm flex-1">{t.knowledge_point}</span>
                  <div className="w-24 bg-white/[0.05] rounded-full h-1.5">
                    <div className="h-1.5 rounded-full bg-red-400" style={{ width: `${t.accuracy}%` }} />
                  </div>
                  <span className="text-red-400 text-xs font-mono w-12 text-right">{t.accuracy}%</span>
                </div>
              ))}
            </div>
          )}

          {/* 最近测验 */}
          {quizData.sessions?.length > 0 && (
            <div>
              <p className="text-white/40 text-xs mb-2">最近测验</p>
              {quizData.sessions.slice(0, 15).map((s: any, i: number) => (
                <div key={i} className="flex items-center justify-between px-3 py-2 rounded-lg bg-white/[0.03] mb-1">
                  <div>
                    <span className="text-white/60 text-sm">{s.subject || '综合'}</span>
                    <span className="text-white/25 text-xs ml-2">{s.topic || ''}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-white/25 text-xs">{s.created_at?.slice(0, 10)}</span>
                    <span className="text-white/30 text-xs">{s.correct_count}/{s.total_questions}</span>
                    <span className={`text-sm font-mono w-10 text-right ${
                      s.score >= 80 ? 'text-emerald-400' : s.score >= 60 ? 'text-amber-400' : 'text-red-400'
                    }`}>{s.score}%</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════
   教学辅导 — 查看学生活跃度/学习记录
   ═══════════════════════════════════════════ */
export function TeachingTutorView() {
  const students = useStudents();
  const [selected, setSelected] = useState<any>(null);
  const [activities, setActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async (s: any) => {
    if (!s) { setActivities([]); return; }
    setLoading(true);
    try {
      const res: any = await api.teacherStudentActivities(s.id);
      if (res.success) setActivities(res.data || []);
    } catch {}
    finally { setLoading(false); }
  }, []);

  return (
    <div>
      <StudentSelector students={students} selected={selected} onSelect={(s) => { setSelected(s); load(s); }} />
      {!selected ? (
        <EmptyState icon={Lightbulb} title="请先选择学生" desc="选择学生后可查看其学习活动记录" />
      ) : loading ? <Loading /> : activities.length === 0 ? (
        <EmptyState icon={Lightbulb} title="暂无活动记录" desc="" />
      ) : (
        <div className="space-y-1.5">
          <p className="text-white/40 text-xs mb-2">最近学习活动</p>
          {activities.slice(0, 20).map((a: any, i: number) => (
            <div key={i} className="flex items-center justify-between px-3 py-2 rounded-lg bg-white/[0.03]">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-cyan-400/40" />
                <span className="text-white/50 text-xs">{a.activity_type}</span>
              </div>
              <div className="flex items-center gap-3">
                {a.duration_seconds > 0 && (
                  <span className="text-white/25 text-xs">{a.duration_seconds}s</span>
                )}
                <span className="text-white/25 text-xs">{a.created_at}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════
   教学知识库 — 知识点掌握概览
   ═══════════════════════════════════════════ */
export function TeachingRagView() {
  const students = useStudents();
  const [selected, setSelected] = useState<any>(null);
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async (s: any) => {
    if (!s) { setAnalytics(null); return; }
    setLoading(true);
    try {
      const res: any = await api.teacherStudentAnalytics(s.id, 'knowledge-mastery');
      if (res.success) setAnalytics(res.data);
    } catch {}
    finally { setLoading(false); }
  }, []);

  return (
    <div>
      <StudentSelector students={students} selected={selected} onSelect={(s) => { setSelected(s); load(s); }} />
      {!selected ? (
        <EmptyState icon={BookOpen} title="请先选择学生" desc="选择学生后可查看其知识点掌握情况" />
      ) : loading ? <Loading /> : !analytics || (Array.isArray(analytics) && analytics.length === 0) ? (
        <EmptyState icon={BookOpen} title="暂无知识点数据" desc="" />
      ) : Array.isArray(analytics) ? (
        <div className="space-y-1.5">
          {analytics.slice(0, 20).map((k: any, i: number) => (
            <div key={i} className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white/[0.03]">
              <span className="text-white/60 text-sm flex-1">{k.knowledge_point}</span>
              <div className="w-32 bg-white/[0.05] rounded-full h-1.5">
                <div
                  className={`h-1.5 rounded-full ${k.accuracy >= 80 ? 'bg-emerald-400' : k.accuracy >= 50 ? 'bg-amber-400' : 'bg-red-400'}`}
                  style={{ width: `${k.accuracy}%` }}
                />
              </div>
              <span className={`text-xs font-mono w-12 text-right ${
                k.accuracy >= 80 ? 'text-emerald-400' : k.accuracy >= 50 ? 'text-amber-400' : 'text-red-400'
              }`}>{k.accuracy}%</span>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState icon={BookOpen} title="暂无知识点数据" desc="" />
      )}
    </div>
  );
}

function StatBox({ label, value, color }: { label: string; value: number | string; color: string }) {
  return (
    <div className="rounded-lg bg-white/[0.03] p-3 text-center">
      <p className={`text-lg font-bold ${color}`}>{value}</p>
      <p className="text-white/30 text-xs mt-1">{label}</p>
    </div>
  );
}
