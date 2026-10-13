'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Users, Search, ChevronLeft, BarChart3, BookOpen, Brain, Router,
  ClipboardCheck, PieChart, Activity, AlertTriangle, FileText,
  GraduationCap, Eye,
} from 'lucide-react';
import api from '@/lib/api';

interface StudentRow {
  id: number;
  username: string;
  email?: string;
  joined_at?: string;
  status?: string;
  class_id?: number;
  class_name?: string;
}

export default function StudentMonitorView() {
  const [students, setStudents] = useState<StudentRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedStudent, setSelectedStudent] = useState<StudentRow | null>(null);
  const [studentDetail, setStudentDetail] = useState<any>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailTab, setDetailTab] = useState<string>('brief');

  const loadStudents = useCallback(async () => {
    setLoading(true);
    try {
      const res: any = await api.teacherListStudents();
      if (res.success) setStudents(res.data || []);
    } catch {}
    finally { setLoading(false); }
  }, []);

  useEffect(() => { loadStudents(); }, [loadStudents]);

  const filtered = students.filter(s =>
    s.username.toLowerCase().includes(search.toLowerCase()) ||
    (s.class_name || '').includes(search)
  );

  const openDetail = async (student: StudentRow) => {
    setSelectedStudent(student);
    setDetailTab('brief');
    setDetailLoading(true);
    try {
      const res: any = await api.teacherStudentBrief(student.id);
      if (res.success) setStudentDetail(res.data);
    } catch {}
    finally { setDetailLoading(false); }
  };

  const loadDetailTab = async (tab: string) => {
    if (!selectedStudent) return;
    setDetailTab(tab);
    setDetailLoading(true);
    try {
      let res: any;
      const sid = selectedStudent.id;
      switch (tab) {
        case 'profile': res = await api.teacherStudentProfile(sid); break;
        case 'resources': res = await api.teacherStudentResources(sid); break;
        case 'path': res = await api.teacherStudentLearningPath(sid); break;
        case 'quiz': res = await api.teacherStudentQuiz(sid); break;
        case 'assessment': res = await api.teacherStudentAssessment(sid); break;
        case 'analytics': res = await api.teacherStudentAnalytics(sid, 'overview'); break;
        case 'activities': res = await api.teacherStudentActivities(sid); break;
        case 'errors': res = await api.teacherStudentErrors(sid); break;
        case 'grades': res = await api.teacherStudentGrades(sid); break;
        case 'schedule': res = await api.teacherStudentCourseSchedule(sid); break;
      }
      if (res?.success) setStudentDetail(res.data);
    } catch {}
    finally { setDetailLoading(false); }
  };

  // ── 列表视图 ──
  if (!selectedStudent) {
    return (
      <div className="space-y-4">
        {/* 搜索栏 */}
        <div className="flex items-center gap-3">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="搜索学生姓名 / 班级..."
              className="w-full pl-10 pr-4 py-2 rounded-lg bg-white/[0.04] border border-white/[0.06] text-white text-sm placeholder:text-white/20 focus:border-white/[0.15] outline-none"
            />
          </div>
          <div className="flex items-center gap-2 text-xs text-white/30">
            <Users className="w-4 h-4" />
            <span>{filtered.length} 名学生</span>
          </div>
        </div>

        {/* 学生卡片列表 */}
        {loading ? (
          <div className="text-white/30 text-sm py-16 text-center">加载中...</div>
        ) : filtered.length === 0 ? (
          <div className="text-white/30 text-sm py-16 text-center">
            暂无学生数据。学生通过邀请码加入班级后可在此查看。
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {filtered.map((s, i) => (
              <motion.button
                key={s.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.03 }}
                onClick={() => openDetail(s)}
                className="text-left rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 hover:border-purple-400/30 hover:bg-white/[0.04] transition-all"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-purple-500/15 flex items-center justify-center">
                    <span className="text-purple-300 font-medium text-sm">
                      {s.username.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-white text-sm font-medium truncate">{s.username}</p>
                    <p className="text-white/30 text-xs truncate">{s.class_name || '未入班'}</p>
                  </div>
                  <ChevronLeft className="w-4 h-4 text-white/15 rotate-180" />
                </div>
                {s.joined_at && (
                  <p className="text-white/20 text-[10px] mt-2">加入于 {s.joined_at}</p>
                )}
              </motion.button>
            ))}
          </div>
        )}
      </div>
    );
  }

  // ── 学生详情视图 ──
  return (
    <div className="space-y-4">
      {/* 返回 + 学生头信息 */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => setSelectedStudent(null)}
          className="flex items-center gap-1.5 text-white/40 hover:text-white text-sm transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          返回列表
        </button>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-purple-500/15 flex items-center justify-center">
            <span className="text-purple-300 font-medium">{selectedStudent.username.charAt(0).toUpperCase()}</span>
          </div>
          <div>
            <p className="text-white font-medium">{selectedStudent.username}</p>
            <p className="text-white/30 text-xs">{selectedStudent.class_name || '未入班'}</p>
          </div>
        </div>
      </div>

      {/* 详情 Tab 导航 */}
      <div className="flex flex-wrap gap-1.5">
        {[
          { key: 'brief', label: '概要', icon: BarChart3 },
          { key: 'profile', label: '画像', icon: Brain },
          { key: 'schedule', label: '课程表', icon: GraduationCap },
          { key: 'resources', label: '资源', icon: BookOpen },
          { key: 'path', label: '路径', icon: Router },
          { key: 'quiz', label: '做题', icon: ClipboardCheck },
          { key: 'assessment', label: '评估', icon: PieChart },
          { key: 'analytics', label: '学情', icon: Activity },
          { key: 'activities', label: '活跃度', icon: Activity },
          { key: 'errors', label: '错题', icon: AlertTriangle },
          { key: 'grades', label: '成绩', icon: FileText },
        ].map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => loadDetailTab(key)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              detailTab === key
                ? 'bg-purple-500/20 text-purple-300 border border-purple-400/30'
                : 'text-white/35 hover:text-white/60 border border-transparent hover:border-white/[0.06]'
            }`}
          >
            <Icon className="w-3.5 h-3.5" />
            {label}
          </button>
        ))}
      </div>

      {/* 详情内容 */}
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-6 min-h-[300px]">
        {detailLoading ? (
          <div className="text-white/30 text-sm py-12 text-center">加载中...</div>
        ) : (
          <DetailContent tab={detailTab} data={studentDetail} studentId={selectedStudent.id} />
        )}
      </div>
    </div>
  );
}

/* ── 详情内容分发 ── */
function DetailContent({ tab, data, studentId }: { tab: string; data: any; studentId: number }) {
  if (!data || (typeof data === 'object' && Object.keys(data).length === 0 && !Array.isArray(data))) {
    return <p className="text-white/30 text-sm text-center py-8">暂无数据</p>;
  }

  if (tab === 'brief') {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatBox label="资源数" value={data.resource_count ?? 0} color="text-cyan-400" />
        <StatBox label="做题数" value={data.quiz_count ?? 0} color="text-amber-400" />
        <StatBox label="均分" value={data.quiz_avg_score ?? 0} color="text-emerald-400" />
        <StatBox label="学习时长(秒)" value={data.study_seconds ?? 0} color="text-purple-400" />
        {data.profile_scores && (
          <div className="col-span-full mt-4">
            <p className="text-white/40 text-xs mb-3">画像评分</p>
            <div className="grid grid-cols-3 gap-2">
              {Object.entries(data.profile_scores).map(([k, v]) => (
                <div key={k} className="flex items-center justify-between px-3 py-2 rounded-lg bg-white/[0.03]">
                  <span className="text-white/40 text-xs">{k}</span>
                  <span className="text-white/70 text-xs font-mono">{String(v)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  if (tab === 'profile' && data.profile_data) {
    const pd = typeof data.profile_data === 'string' ? JSON.parse(data.profile_data) : data.profile_data;
    return (
      <div className="space-y-3">
        {Object.entries(pd).map(([k, v]) => (
          <div key={k} className="flex items-start gap-3 px-3 py-2.5 rounded-lg bg-white/[0.03]">
            <span className="text-white/40 text-xs w-20 flex-shrink-0 mt-0.5">{k}</span>
            <span className="text-white/70 text-sm">{typeof v === 'object' ? JSON.stringify(v) : String(v)}</span>
          </div>
        ))}
      </div>
    );
  }

  if (tab === 'quiz' && data) {
    return (
      <div className="space-y-4">
        {data.stats && (
          <div className="grid grid-cols-3 gap-3">
            <StatBox label="测验次数" value={data.stats.c ?? 0} color="text-amber-400" />
            <StatBox label="均分" value={data.stats.avg_score ?? 0} color="text-emerald-400" />
            <StatBox label="薄弱点数" value={data.weak_topics?.length ?? 0} color="text-red-400" />
          </div>
        )}
        {data.weak_topics?.length > 0 && (
          <div>
            <p className="text-white/40 text-xs mb-2">薄弱知识点</p>
            {data.weak_topics.map((t: any, i: number) => (
              <div key={i} className="flex items-center justify-between px-3 py-2 rounded-lg bg-white/[0.03] mb-1">
                <span className="text-white/60 text-xs">{t.knowledge_point}</span>
                <span className="text-red-400 text-xs font-mono">{t.accuracy}%</span>
              </div>
            ))}
          </div>
        )}
        {data.sessions?.length > 0 && (
          <div>
            <p className="text-white/40 text-xs mb-2">最近测验</p>
            {data.sessions.slice(0, 10).map((s: any, i: number) => (
              <div key={i} className="flex items-center justify-between px-3 py-2 rounded-lg bg-white/[0.03] mb-1">
                <div>
                  <span className="text-white/60 text-xs">{s.subject || '综合'} · {s.topic || ''}</span>
                  <span className="text-white/25 text-[10px] ml-2">{s.created_at}</span>
                </div>
                <span className={`text-xs font-mono ${s.score >= 80 ? 'text-emerald-400' : s.score >= 60 ? 'text-amber-400' : 'text-red-400'}`}>
                  {s.score}分
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  if (tab === 'errors' && Array.isArray(data)) {
    return (
      <div className="space-y-2">
        {data.length === 0 ? (
          <p className="text-white/30 text-sm text-center py-8">暂无错题</p>
        ) : data.map((e: any, i: number) => (
          <div key={i} className="rounded-lg bg-white/[0.03] p-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-white/60 text-xs">{e.subject}</span>
              <span className={`text-[10px] px-2 py-0.5 rounded-full ${e.mastery ? 'bg-emerald-500/15 text-emerald-300' : 'bg-red-500/15 text-red-300'}`}>
                {e.mastery ? '已掌握' : '待复习'}
              </span>
            </div>
            <p className="text-white/70 text-sm">{e.question}</p>
            {e.error_reason && <p className="text-white/30 text-xs mt-1">{e.error_reason}</p>}
          </div>
        ))}
      </div>
    );
  }

  if (tab === 'grades' && Array.isArray(data)) {
    return (
      <div className="space-y-1.5">
        {data.length === 0 ? (
          <p className="text-white/30 text-sm text-center py-8">暂无成绩</p>
        ) : data.map((g: any, i: number) => (
          <div key={i} className="flex items-center justify-between px-3 py-2 rounded-lg bg-white/[0.03]">
            <div>
              <span className="text-white/60 text-sm">{g.course_name}</span>
              <span className="text-white/25 text-xs ml-2">{g.semester}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-white/30 text-xs">{g.credits || ''}学分</span>
              <span className={`text-sm font-mono ${g.score >= 90 ? 'text-emerald-400' : g.score >= 60 ? 'text-white/70' : 'text-red-400'}`}>
                {g.score ?? '-'}
              </span>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (tab === 'activities' && Array.isArray(data)) {
    return (
      <div className="space-y-1.5">
        {data.length === 0 ? (
          <p className="text-white/30 text-sm text-center py-8">暂无活跃记录</p>
        ) : data.slice(0, 20).map((a: any, i: number) => (
          <div key={i} className="flex items-center justify-between px-3 py-2 rounded-lg bg-white/[0.03]">
            <div>
              <span className="text-white/50 text-xs">{a.activity_type}</span>
              {a.metadata && <span className="text-white/25 text-[10px] ml-2">{String(a.metadata).slice(0, 50)}</span>}
            </div>
            <span className="text-white/25 text-[10px]">{a.created_at}</span>
          </div>
        ))}
      </div>
    );
  }

  if (tab === 'path' && Array.isArray(data)) {
    return (
      <div className="space-y-2">
        {data.length === 0 ? (
          <p className="text-white/30 text-sm text-center py-8">暂无学习路径</p>
        ) : data.map((p: any, i: number) => (
          <div key={i} className="rounded-lg bg-white/[0.03] p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-white/70 text-sm">{p.path_name}</span>
              <span className={`text-[10px] px-2 py-0.5 rounded-full ${p.status === 'completed' ? 'bg-emerald-500/15 text-emerald-300' : p.status === 'active' ? 'bg-cyan-500/15 text-cyan-300' : 'bg-white/10 text-white/40'}`}>
                {p.status}
              </span>
            </div>
            <div className="w-full bg-white/[0.05] rounded-full h-1.5">
              <div
                className="bg-purple-500 h-1.5 rounded-full"
                style={{ width: `${p.total_steps ? Math.round((p.completed_steps / p.total_steps) * 100) : 0}%` }}
              />
            </div>
            <p className="text-white/25 text-xs mt-1">
              {p.completed_steps}/{p.total_steps} 步
            </p>
          </div>
        ))}
      </div>
    );
  }

  if (tab === 'resources' && Array.isArray(data)) {
    return (
      <div className="space-y-1.5">
        {data.length === 0 ? (
          <p className="text-white/30 text-sm text-center py-8">暂无资源</p>
        ) : data.map((r: any, i: number) => (
          <div key={i} className="flex items-center justify-between px-3 py-2 rounded-lg bg-white/[0.03]">
            <div>
              <span className="text-white/60 text-sm">{r.title}</span>
              <span className="text-white/25 text-xs ml-2">{r.resource_type}</span>
            </div>
            <span className="text-white/25 text-[10px]">{r.created_at}</span>
          </div>
        ))}
      </div>
    );
  }

  if (tab === 'assessment' && Array.isArray(data)) {
    return (
      <div className="space-y-2">
        {data.length === 0 ? (
          <p className="text-white/30 text-sm text-center py-8">暂无评估报告</p>
        ) : data.map((a: any, i: number) => (
          <div key={i} className="rounded-lg bg-white/[0.03] p-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-white/60 text-sm">{a.assessment_type}</span>
              <span className="text-purple-400 text-sm font-mono">{a.overall_score}</span>
            </div>
            <p className="text-white/30 text-xs">{a.improvement_suggestions?.slice(0, 100)}</p>
          </div>
        ))}
      </div>
    );
  }

  if (tab === 'analytics' && data) {
    return (
      <div className="grid grid-cols-3 gap-3">
        <StatBox label="测验次数" value={data.c ?? 0} color="text-amber-400" />
        <StatBox label="均分" value={data.avg_score ?? 0} color="text-emerald-400" />
        <StatBox label="总用时(秒)" value={data.total_seconds ?? 0} color="text-purple-400" />
      </div>
    );
  }

  if (tab === 'schedule' && Array.isArray(data)) {
    return (
      <div className="space-y-2">
        {data.length === 0 ? (
          <p className="text-white/30 text-sm text-center py-8">暂无课程表</p>
        ) : data.map((s: any, i: number) => (
          <div key={i} className="rounded-lg bg-white/[0.03] p-3">
            <p className="text-white/60 text-sm mb-2">{s.semester}</p>
            {Array.isArray(s.courses) ? s.courses.map((c: any, j: number) => (
              <div key={j} className="flex items-center justify-between px-2 py-1">
                <span className="text-white/50 text-xs">{c.name} · {c.day}</span>
                <span className="text-white/25 text-[10px]">{c.start_time}-{c.end_time}</span>
              </div>
            )) : <p className="text-white/25 text-xs">课程数据不可用</p>}
          </div>
        ))}
      </div>
    );
  }

  return <p className="text-white/30 text-sm text-center py-8">暂无数据</p>;
}

function StatBox({ label, value, color }: { label: string; value: number | string; color: string }) {
  return (
    <div className="rounded-lg bg-white/[0.03] p-3 text-center">
      <p className={`text-lg font-bold ${color}`}>{value}</p>
      <p className="text-white/30 text-xs mt-1">{label}</p>
    </div>
  );
}
