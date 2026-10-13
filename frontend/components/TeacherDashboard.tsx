'use client';

import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import {
  Users, BarChart3, BookOpen, Brain, Router, Lightbulb,
  ClipboardCheck, PieChart, Database, GraduationCap,
  LogOut, Settings,
} from 'lucide-react';
import { useAuthStore } from '@/stores';
import { FullBackground } from '@/components/shared/BackgroundEffects';
import StudentMonitorView from '@/components/teacher/StudentMonitorView';
import ClassAnalyticsView from '@/components/teacher/ClassAnalyticsView';
import ClassModule from '@/components/teacher/ClassModule';
import {
  TeachingProfileView,
  TeachingResourcesView,
  TeachingPathView,
  TeachingTutorView,
  TeachingAssessmentView,
  TeachingQuizView,
} from '@/components/teacher/TeacherModuleViews';
import LessonPPTView from '@/components/teacher/LessonPPTView';

type TeacherView =
  | 'overview' | 'classes' | 'students' | 'teachingResources'
  | 'teachingProfile' | 'teachingPath' | 'teachingTutor'
  | 'teachingAssessment' | 'teachingQuiz' | 'teachingAnalytics'
  | 'teachingLesson';

const NAV_ITEMS: Array<{
  view: TeacherView;
  label: string;
  icon: any;
  color: string;
  desc: string;
  group: string;
}> = [
  { view: 'overview', label: '教学概览', icon: GraduationCap, color: 'text-purple-400', desc: '班级人数 / 活跃度', group: '教学管理' },
  { view: 'classes', label: '班级管理', icon: Users, color: 'text-cyan-400', desc: '创建班级 / 邀请码', group: '教学管理' },
  { view: 'students', label: '学生学情', icon: BarChart3, color: 'text-emerald-400', desc: '学生列表 / 详情下钻', group: '教学管理' },
  { view: 'teachingAnalytics', label: '班级学情', icon: PieChart, color: 'text-indigo-400', desc: '全班维度分析', group: '教学管理' },
  { view: 'teachingProfile', label: '学情画像', icon: Brain, color: 'text-emerald-400', desc: '查看学生画像', group: '教学功能' },
  { view: 'teachingResources', label: '教学资源', icon: BookOpen, color: 'text-amber-400', desc: 'AI 生成 / 发布到班级', group: '教学功能' },
  { view: 'teachingPath', label: '教学路径', icon: Router, color: 'text-blue-400', desc: '路径模板 / 一键下发', group: '教学功能' },
  { view: 'teachingTutor', label: '教学辅导', icon: Lightbulb, color: 'text-amber-300', desc: '备课答疑 / 高频提问', group: '教学功能' },
  { view: 'teachingAssessment', label: '班级评估', icon: ClipboardCheck, color: 'text-rose-400', desc: '单生 / 全班对比', group: '教学功能' },
  { view: 'teachingQuiz', label: '题库测验', icon: ClipboardCheck, color: 'text-orange-400', desc: '组卷发布 / 查看作答', group: '教学功能' },
  { view: 'teachingLesson', label: '教案 & PPT', icon: BookOpen, color: 'text-violet-400', desc: 'AI 生成教案课件 / 导出', group: '教学功能' },
];

export default function TeacherDashboard() {
  const { user, logout } = useAuthStore();
  const [activeView, setActiveView] = useState<TeacherView>('overview');
  const [currentTime, setCurrentTime] = useState('');

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }));
    }, 30000);
    setCurrentTime(new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }));
    return () => clearInterval(timer);
  }, []);

  const handleLogout = () => {
    logout();
    window.location.href = '/';
  };

  // 按 group 分组
  const groups = NAV_ITEMS.reduce<Record<string, typeof NAV_ITEMS>>((acc, item) => {
    (acc[item.group] = acc[item.group] || []).push(item);
    return acc;
  }, {});

  return (
    <div className="min-h-screen flex" style={{ background: '#0a0a0a' }}>
      <FullBackground />

      {/* ── 侧边导航 ── */}
      <aside className="relative z-10 w-60 flex-shrink-0 border-r border-white/[0.06] flex flex-col">
        {/* Logo */}
        <div className="p-5 border-b border-white/[0.06]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-500/15 flex items-center justify-center">
              <GraduationCap className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-white leading-tight">灵犀 · 教师端</p>
              <p className="text-[10px] text-white/25 tracking-wider">TEACHER CONSOLE</p>
            </div>
          </div>
        </div>

        {/* 导航 */}
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-5">
          {Object.entries(groups).map(([group, items]) => (
            <div key={group}>
              <p className="text-[10px] text-white/20 tracking-widest px-2 mb-2 uppercase">{group}</p>
              <div className="space-y-0.5">
                {items.map((item) => {
                  const Icon = item.icon;
                  const isActive = activeView === item.view;
                  return (
                    <button
                      key={item.view}
                      onClick={() => setActiveView(item.view)}
                      className={`
                        w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-left transition-all
                        ${isActive
                          ? 'bg-white/[0.07] text-white'
                          : 'text-white/40 hover:text-white/70 hover:bg-white/[0.03]'
                        }
                      `}
                    >
                      <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? item.color : ''}`} />
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{item.label}</p>
                        <p className="text-[10px] text-white/25 truncate">{item.desc}</p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* 底部用户 */}
        <div className="p-4 border-t border-white/[0.06]">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center">
              <span className="text-xs text-purple-300 font-medium">
                {(user?.username || 'T').charAt(0).toUpperCase()}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-white/70 truncate">{user?.username || '老师'}</p>
              <p className="text-[10px] text-white/25">教师</p>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 rounded-lg text-white/25 hover:text-red-400 hover:bg-red-400/10 transition-colors"
              title="退出登录"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* ── 主内容区 ── */}
      <main className="relative z-10 flex-1 overflow-y-auto">
        {/* 顶栏 */}
        <header className="sticky top-0 z-20 px-8 py-5 border-b border-white/[0.04] bg-[#0a0a0a]/80 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-white">
                {NAV_ITEMS.find(i => i.view === activeView)?.label || '教学概览'}
              </h1>
              <p className="text-xs text-white/30 mt-1">
                {NAV_ITEMS.find(i => i.view === activeView)?.desc || '欢迎回来，老师'}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-white/50">{currentTime}</p>
              <p className="text-[10px] text-white/25 mt-0.5">教学管理平台</p>
            </div>
          </div>
        </header>

        {/* 视图内容 */}
        <div className="p-8">
          <TeacherViewContent view={activeView} />
        </div>
      </main>
    </div>
  );
}

/* ── 视图分发 ── */
function TeacherViewContent({ view }: { view: TeacherView }) {
  return (
    <motion.div
      key={view}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {view === 'overview' && <OverviewPanel />}
      {view === 'classes' && <ClassModule />}
      {view === 'students' && <StudentMonitorView />}
      {view === 'teachingAnalytics' && <ClassAnalyticsView />}
      {view === 'teachingProfile' && <TeachingProfileView />}
      {view === 'teachingResources' && <TeachingResourcesView />}
      {view === 'teachingPath' && <TeachingPathView />}
      {view === 'teachingTutor' && <TeachingTutorView />}
      {view === 'teachingAssessment' && <TeachingAssessmentView />}
      {view === 'teachingQuiz' && <TeachingQuizView />}
      {view === 'teachingLesson' && <LessonPPTView />}
    </motion.div>
  );
}

/* ── 概览面板 ── */
function OverviewPanel() {
  const [stats, setStats] = useState({ classCount: 0, studentCount: 0 });

  useEffect(() => {
    import('@/lib/api').then(({ api }) => {
      api.listClasses().then((res: any) => {
        if (res.success && Array.isArray(res.data)) {
          setStats({
            classCount: res.data.length,
            studentCount: res.data.reduce((s: number, c: any) => s + (c.student_count || 0), 0),
          });
        }
      }).catch(() => {});
    });
  }, []);

  const cards = [
    { label: '我的班级', value: stats.classCount, icon: Users, color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
    { label: '学生总数', value: stats.studentCount, icon: GraduationCap, color: 'text-purple-400', bg: 'bg-purple-500/10' },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        {cards.map(({ label, value, icon: Icon, color, bg }) => (
          <div key={label} className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-6">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-lg ${bg} flex items-center justify-center`}>
                <Icon className={`w-5 h-5 ${color}`} />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{value}</p>
                <p className="text-xs text-white/30 mt-0.5">{label}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-8">
        <p className="text-white/30 text-sm">
          欢迎使用灵犀教师端。左侧选择功能模块开始教学管理。
        </p>
      </div>
    </div>
  );
}

/* ── 占位视图（保留备用） ── */
function PlaceholderView({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-12 text-center">
      <div className="w-16 h-16 rounded-2xl bg-purple-500/10 flex items-center justify-center mx-auto mb-4">
        <Settings className="w-7 h-7 text-purple-400/50" />
      </div>
      <h3 className="text-white font-medium text-lg mb-2">{title}</h3>
      <p className="text-white/30 text-sm">{desc}</p>
    </div>
  );
}
