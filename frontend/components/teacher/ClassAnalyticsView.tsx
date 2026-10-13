'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Users, GraduationCap, BarChart3, BookOpen, ClipboardCheck, TrendingUp } from 'lucide-react';
import api from '@/lib/api';

export default function ClassAnalyticsView() {
  const [classes, setClasses] = useState<any[]>([]);
  const [selectedClass, setSelectedClass] = useState<any>(null);
  const [students, setStudents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [studentBriefs, setStudentBriefs] = useState<Record<number, any>>({});
  const [briefsLoading, setBriefsLoading] = useState(false);

  useEffect(() => {
    api.listClasses().then((res: any) => {
      if (res.success) {
        setClasses(res.data || []);
        if (res.data?.length > 0) setSelectedClass(res.data[0]);
      }
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedClass) return;
    api.listClassStudents(selectedClass.id).then((res: any) => {
      if (res.success) setStudents(res.data || []);
    }).catch(() => {});
  }, [selectedClass]);

  // 批量加载学生摘要
  const loadBriefs = useCallback(async () => {
    if (students.length === 0) return;
    setBriefsLoading(true);
    const briefs: Record<number, any> = {};
    await Promise.all(students.map(async (s: any) => {
      try {
        const res: any = await api.teacherStudentBrief(s.id);
        if (res.success) briefs[s.id] = res.data;
      } catch {}
    }));
    setStudentBriefs(briefs);
    setBriefsLoading(false);
  }, [students]);

  useEffect(() => { loadBriefs(); }, [loadBriefs]);

  // 班级聚合统计
  const briefsList = Object.values(studentBriefs);
  const agg = {
    studentCount: students.length,
    avgQuizScore: briefsList.length
      ? Math.round(briefsList.reduce((s: number, b: any) => s + (b.quiz_avg_score || 0), 0) / briefsList.length * 10) / 10
      : 0,
    totalResources: briefsList.reduce((s: number, b: any) => s + (b.resource_count || 0), 0),
    totalQuizzes: briefsList.reduce((s: number, b: any) => s + (b.quiz_count || 0), 0),
    totalStudyHours: Math.round(briefsList.reduce((s: number, b: any) => s + (b.study_seconds || 0), 0) / 3600 * 10) / 10,
  };

  if (loading) return <div className="text-white/30 text-sm py-16 text-center">加载中...</div>;

  if (classes.length === 0) {
    return (
      <div className="text-center py-16">
        <Users className="w-12 h-12 text-white/10 mx-auto mb-3" />
        <p className="text-white/30 text-sm">暂无班级数据</p>
        <p className="text-white/20 text-xs mt-1">请先在「班级管理」中创建班级</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 班级切换 */}
      <div className="flex items-center gap-3">
        <span className="text-white/30 text-xs">选择班级:</span>
        <div className="flex gap-2">
          {classes.map((cls: any) => (
            <button
              key={cls.id}
              onClick={() => setSelectedClass(cls)}
              className={`px-4 py-2 rounded-lg text-sm transition-all ${
                selectedClass?.id === cls.id
                  ? 'bg-purple-500/20 text-purple-300 border border-purple-400/30'
                  : 'text-white/35 hover:text-white/60 border border-white/[0.06] hover:border-white/[0.12]'
              }`}
            >
              {cls.name}
            </button>
          ))}
        </div>
      </div>

      {/* 聚合统计卡 */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <AggCard label="学生总数" value={agg.studentCount} icon={Users} color="text-cyan-400" bg="bg-cyan-500/10" />
        <AggCard label="平均分" value={agg.avgQuizScore} icon={BarChart3} color="text-emerald-400" bg="bg-emerald-500/10" />
        <AggCard label="资源总数" value={agg.totalResources} icon={BookOpen} color="text-amber-400" bg="bg-amber-500/10" />
        <AggCard label="测验总数" value={agg.totalQuizzes} icon={ClipboardCheck} color="text-purple-400" bg="bg-purple-500/10" />
        <AggCard label="学习时长(h)" value={agg.totalStudyHours} icon={TrendingUp} color="text-rose-400" bg="bg-rose-500/10" />
      </div>

      {/* 学生排行 */}
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
        <h3 className="text-white/70 text-sm font-medium mb-4">学生表现排行</h3>
        {briefsLoading ? (
          <div className="text-white/30 text-sm py-8 text-center">加载学生数据...</div>
        ) : (
          <div className="space-y-2">
            {students
              .map((s: any) => ({ ...s, brief: studentBriefs[s.id] }))
              .sort((a: any, b: any) => (b.brief?.quiz_avg_score || 0) - (a.brief?.quiz_avg_score || 0))
              .map((s: any, i: number) => (
                <div key={s.id} className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-white/[0.03]">
                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                    i === 0 ? 'bg-amber-500/20 text-amber-300' :
                    i === 1 ? 'bg-white/10 text-white/60' :
                    i === 2 ? 'bg-orange-500/20 text-orange-300' :
                    'text-white/30'
                  }`}>
                    {i + 1}
                  </span>
                  <div className="w-8 h-8 rounded-full bg-purple-500/15 flex items-center justify-center">
                    <span className="text-purple-300 text-xs">{s.username.charAt(0).toUpperCase()}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white/70 text-sm truncate">{s.username}</p>
                    <div className="flex items-center gap-3 mt-0.5">
                      <span className="text-white/25 text-[10px]">资源 {s.brief?.resource_count ?? 0}</span>
                      <span className="text-white/25 text-[10px]">测验 {s.brief?.quiz_count ?? 0}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`text-sm font-mono ${
                      (s.brief?.quiz_avg_score || 0) >= 80 ? 'text-emerald-400' :
                      (s.brief?.quiz_avg_score || 0) >= 60 ? 'text-white/60' : 'text-red-400'
                    }`}>
                      {s.brief?.quiz_avg_score ?? '-'}
                    </p>
                    <p className="text-white/25 text-[10px]">均分</p>
                  </div>
                  {/* 评分条 */}
                  <div className="w-20">
                    <div className="w-full bg-white/[0.05] rounded-full h-1.5">
                      <div
                        className="bg-gradient-to-r from-purple-500 to-cyan-400 h-1.5 rounded-full"
                        style={{ width: `${Math.min(s.brief?.quiz_avg_score || 0, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            {students.length === 0 && (
              <p className="text-white/30 text-sm text-center py-8">暂无学生</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function AggCard({ label, value, icon: Icon, color, bg }: {
  label: string; value: number | string; icon: any; color: string; bg: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4"
    >
      <div className="flex items-center gap-3">
        <div className={`w-9 h-9 rounded-lg ${bg} flex items-center justify-center`}>
          <Icon className={`w-4 h-4 ${color}`} />
        </div>
        <div>
          <p className={`text-xl font-bold ${color}`}>{value}</p>
          <p className="text-white/30 text-[10px]">{label}</p>
        </div>
      </div>
    </motion.div>
  );
}
