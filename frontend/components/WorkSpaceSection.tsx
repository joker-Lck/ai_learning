'use client';

import { useState, useEffect, useCallback, memo, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain, Router, Lightbulb, TrendingUp,
  UserCheck, Database, Bell,
  FileText, Video, BarChart3,
  ArrowRight, Clock, Zap, Users, ChevronRight,
  Sparkles, Target, X, GitBranch, FileCode, Code, BookOpen,
  Maximize2, Loader2,
} from 'lucide-react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from 'recharts';
import type { ModuleType, NavigationContext } from './modules/types';
import MarkdownRenderer from '@/components/shared/MarkdownRenderer';
import api from '@/lib/api';

interface WorkSpaceSectionProps {
  onNavigateModule: (moduleId: ModuleType, ctx?: NavigationContext) => void;
}

/* ═══════════════════════════════════════════
   类型
   ═══════════════════════════════════════════ */

interface ApiResource {
  id: number;
  title: string;
  resource_type: string;
  subject: string;
  topic: string;
  difficulty_level: string;
  content_data: any;
  created_at: string;
  duration_minutes?: number;
}

interface ProfileData {
  major?: string;
  grade_level?: string;
  weak_points?: string[];
  interest_areas?: string[];
  learning_history?: any[];
  preferred_resources?: string[];
}

interface Recommendation {
  topic: string;
  reason: string;
  resource_type?: string;
  priority?: string;
}

interface ActivityLog {
  id: string;
  type: string;
  action: string;
  detail?: string;
  time: string;
}

interface DashboardStats {
  resource_count: number;
  activity_count: number;
  login_days: number;
  total_study_seconds: number;
}

/* ═══════════════════════════════════════════
   雷达图组件
   ═══════════════════════════════════════════ */

function computeDashboardRadar(profile: ProfileData | null) {
  const d = { value: 3, fullMark: 5 };
  if (!profile) return [
    { dimension: '知识基础', ...d }, { dimension: '学习目标', ...d },
    { dimension: '记忆能力', ...d }, { dimension: '自控力', ...d },
    { dimension: '专注度', ...d }, { dimension: '学习深度', ...d },
  ];

  // 知识基础
  let kb = 3;
  const weak = profile.weak_points;
  if (Array.isArray(weak) && weak.length === 0) kb = 4;
  if (Array.isArray(weak) && weak.length > 3) kb = 2;

  // 学习目标
  let goal = 3;
  if (profile.learning_history && profile.learning_history.length > 5) goal = 4;

  // 记忆能力
  let mem = 3;
  if (profile.learning_history && profile.learning_history.length > 10) mem = 4;

  // 自控力
  let sc = 3;
  const prefs = profile.preferred_resources;
  if (Array.isArray(prefs) && prefs.length >= 3) sc = 4;

  // 专注度
  let focus = 3;
  if (Array.isArray(profile.interest_areas) && profile.interest_areas.length > 0) focus = 3 + Math.min(2, Math.floor(profile.interest_areas.length / 3));

  // 学习深度
  let depth = 3;
  if (Array.isArray(profile.interest_areas) && profile.interest_areas.length > 3) depth = 4;

  return [
    { dimension: '知识基础', value: Math.min(5, kb), fullMark: 5 },
    { dimension: '学习目标', value: Math.min(5, goal), fullMark: 5 },
    { dimension: '记忆能力', value: Math.min(5, mem), fullMark: 5 },
    { dimension: '自控力', value: Math.min(5, sc), fullMark: 5 },
    { dimension: '专注度', value: Math.min(5, focus), fullMark: 5 },
    { dimension: '学习深度', value: Math.min(5, depth), fullMark: 5 },
  ];
}

const DashboardRadarChart = memo(function DashboardRadarChart({ profile }: { profile: ProfileData | null }) {
  const data = useMemo(() => computeDashboardRadar(profile), [profile]);
  return (
    <div className="p-5 rounded-xl bg-[#1a1a27] border border-white/[0.05] mb-5">
      <div className="flex items-center gap-2 mb-3">
        <BarChart3 className="w-4 h-4 text-purple-400" />
        <h3 className="text-sm font-semibold text-white">学习能力画像</h3>
      </div>
      <div style={{ height: 200 }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
            <PolarGrid stroke="rgba(255,255,255,0.06)" />
            <PolarAngleAxis dataKey="dimension" tick={{ fill: 'rgba(255,255,255,0.45)', fontSize: 11 }} />
            <Radar name="能力值" dataKey="value" stroke="#a78bfa" fill="#a78bfa" fillOpacity={0.15} strokeWidth={1.5} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
      <div className="grid grid-cols-3 gap-1.5 mt-2">
        {data.map(d => (
          <div key={d.dimension} className="flex items-center gap-1.5 px-1.5 py-1 rounded bg-white/[0.03]">
            <div className="w-1 h-1 rounded-full bg-purple-400" />
            <span className="text-[10px] text-white/35 flex-1 truncate">{d.dimension}</span>
            <span className="text-[10px] font-medium text-purple-400">{d.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
});

/* ═══════════════════════════════════════════
   资源类型映射
   ═══════════════════════════════════════════ */

const TYPE_MAP: Record<string, { icon: typeof FileText; color: string; label: string }> = {
  document:  { icon: FileText,   color: 'text-purple-400',  label: '讲解文档' },
  mindmap:   { icon: GitBranch,  color: 'text-emerald-400', label: '思维导图' },
  quiz:      { icon: FileCode,   color: 'text-amber-400',   label: '练习题' },
  video:     { icon: Video,      color: 'text-purple-400',  label: '教学视频' },
  animation: { icon: Sparkles,   color: 'text-pink-400',    label: '动画' },
  code:      { icon: Code,       color: 'text-blue-400',    label: '代码' },
  reading:   { icon: BookOpen,   color: 'text-orange-400',  label: '阅读材料' },
};

/* ═══════════════════════════════════════════
   工具函数
   ═══════════════════════════════════════════ */

function formatTimeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return '刚刚';
  if (mins < 60) return `${mins}分钟前`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}小时前`;
  const days = Math.floor(hours / 24);
  return days < 7 ? `${days}天前` : new Date(dateStr).toLocaleDateString('zh-CN');
}

function contentToMarkdown(data: any, type: string): string {
  if (!data) return '暂无内容';
  if (typeof data === 'string') return data;
  const parts: string[] = [];
  if (data.title) parts.push(`## ${data.title}`);
  if (data.summary) parts.push(data.summary);
  if (data.description) parts.push(data.description);
  if (data.content) parts.push(data.content);
  if (data.introduction) parts.push(data.introduction);

  if (data.sections && Array.isArray(data.sections)) {
    for (const sec of data.sections) {
      if (sec.title) parts.push(`### ${sec.title}`);
      if (sec.content) parts.push(sec.content);
      if (sec.items) parts.push(sec.items.map((i: string) => `- ${i}`).join('\n'));
    }
  }
  if (data.root) {
    parts.push(`### 中心主题: ${data.root}`);
    if (data.branches) {
      for (const b of data.branches) {
        parts.push(`#### ${b.topic || b.name || ''}`);
        if (b.subtopics) parts.push(b.subtopics.map((s: any) => `- ${typeof s === 'string' ? s : s.name || s.topic || JSON.stringify(s)}`).join('\n'));
      }
    }
  }
  if (data.questions) {
    data.questions.forEach((q: any, i: number) => {
      parts.push(`**${i + 1}. ${q.question || q.title || ''}**`);
      if (q.options) q.options.forEach((o: string, j: number) => parts.push(`${String.fromCharCode(65 + j)}. ${o}`));
      if (q.answer) parts.push(`> 答案: ${q.answer}`);
      if (q.explanation) parts.push(`> 解析: ${q.explanation}`);
    });
  }
  if (data.code) parts.push(`\`\`\`${data.language || 'python'}\n${data.code}\n\`\`\``);
  if (data.scenes) {
    if (data.duration_minutes) parts.push(`> 🎬 时长: ${data.duration_minutes} 分钟`);
    for (const s of data.scenes) {
      parts.push(`**${s.scene_id ? `场景 ${s.scene_id}` : s.title || ''}${s.duration_seconds ? ` (${s.duration_seconds}s)` : ''}**`);
      if (s.visual_description || s.description) parts.push(s.visual_description || s.description);
      if (s.narration) parts.push(`> 🎙️ ${s.narration}`);
    }
  }
  if (data.frames) {
    for (const f of data.frames) {
      parts.push(`**${f.frame_id || ''}${f.timestamp ? ` [${f.timestamp}]` : ''}**`);
      if (f.description) parts.push(f.description);
      if (f.action) parts.push(`> 🎬 ${f.action}`);
    }
  }
  if (data.script && !data.scenes && !data.frames) parts.push(data.script);
  if (data.materials) data.materials.forEach((m: any) => { parts.push(`### ${m.title || ''}`); if (m.content) parts.push(m.content); });
  if (parts.length === 0) return '```json\n' + JSON.stringify(data, null, 2) + '\n```';
  return parts.join('\n\n');
}

/* ═══════════════════════════════════════════
   资源预览弹窗
   ═══════════════════════════════════════════ */

function ResourcePreview({ resource, onClose }: { resource: ApiResource | null; onClose: () => void }) {
  if (!resource) return null;
  const typeInfo = TYPE_MAP[resource.resource_type] || { icon: FileText, color: 'text-white/60', label: '资源' };
  const Icon = typeInfo.icon;
  const markdown = contentToMarkdown(resource.content_data, resource.resource_type);
  const mediaUrl = resource.content_data?.media_url as string | undefined;
  const genType = resource.content_data?.generation_type as string | undefined;
  const hasMedia = !!mediaUrl;
  const isVideo = genType === 'video' || genType === 'video_with_images' || mediaUrl?.endsWith('.mp4');
  const isSvg = genType === 'svg_animation' || mediaUrl?.endsWith('.html');

  return (
    <motion.div className="fixed inset-0 z-50 flex items-center justify-center p-6" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }}>
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <motion.div className="relative w-full max-w-3xl max-h-[85vh] glass-dark rounded-2xl overflow-hidden flex flex-col" initial={{ scale: 0.92, opacity: 0, y: 20 }} animate={{ scale: 1, opacity: 1, y: 0 }} exit={{ scale: 0.95, opacity: 0 }} transition={{ duration: 0.25, ease: [0.25, 0.46, 0.45, 0.94] }}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-glass">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-9 h-9 rounded-lg bg-purple-500/10 flex items-center justify-center"><Icon className={`w-4 h-4 ${typeInfo.color}`} /></div>
            <div className="min-w-0">
              <h3 className="text-base font-semibold text-white truncate">{resource.title}</h3>
              <span className="text-xs text-white/30">{typeInfo.label}{resource.subject && ` · ${resource.subject}`}{resource.topic && ` - ${resource.topic}`}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {hasMedia && <button onClick={() => window.open(mediaUrl, '_blank')} className="p-2 rounded-lg glass-button text-white/35 hover:text-white"><Maximize2 className="w-4 h-4" /></button>}
            <button onClick={onClose} className="p-2 rounded-lg glass-button text-white/35 hover:text-white"><X className="w-4 h-4" /></button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto px-6 py-5">
          {hasMedia && isVideo && <video controls autoPlay src={mediaUrl} className="w-full rounded-xl glass mb-4" style={{ maxHeight: 400 }} />}
          {hasMedia && isSvg && <iframe src={mediaUrl} className="w-full rounded-xl glass mb-4 bg-[#0a0f1e]" style={{ height: 400 }} title={resource.title} />}
          <MarkdownRenderer content={markdown} />
        </div>
      </motion.div>
    </motion.div>
  );
}

/* ═══════════════════════════════════════════
   子组件 — 全部动态
   ═══════════════════════════════════════════ */

function Header({ profile, stats }: { profile: ProfileData | null; stats: DashboardStats | null }) {
  const hour = new Date().getHours();
  const greeting = hour < 6 ? '凌晨好' : hour < 12 ? '上午好' : hour < 18 ? '下午好' : '晚上好';
  const [username, setUsername] = useState('同学');

  useEffect(() => {
    try {
      const stored = localStorage.getItem('user_info');
      if (stored) {
        const parsed = JSON.parse(stored);
        setUsername(parsed.username || '同学');
      }
    } catch {}
  }, []);

  const weak = profile?.weak_points?.[0];

  const loginDays = stats?.login_days || 0;
  const totalMinutes = Math.floor((stats?.total_study_seconds || 0) / 60);

  const [sessionMinutes, setSessionMinutes] = useState(0);

  useEffect(() => {
    const stored = localStorage.getItem('session_start');
    const today = new Date().toDateString();
    let start: number;

    if (stored) {
      const storedDate = new Date(Number(stored)).toDateString();
      if (storedDate !== today) {
        start = Date.now();
        localStorage.setItem('session_start', String(start));
      } else {
        start = Number(stored);
      }
    } else {
      start = Date.now();
      localStorage.setItem('session_start', String(start));
    }

    const tick = () => {
      setSessionMinutes(Math.floor((Date.now() - start) / 60000));
    };
    tick();
    const interval = setInterval(tick, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const report = () => {
      const sessionStart = Number(localStorage.getItem('session_start') || Date.now());
      const seconds = Math.floor((Date.now() - sessionStart) / 1000);
      if (seconds > 10) {
        const base = process.env.NEXT_PUBLIC_API_URL || '/api';
        const blob = new Blob([JSON.stringify({ seconds })], { type: 'application/json' });
        navigator.sendBeacon?.(`${base}/agent/activity-logs`, blob);
      }
      localStorage.removeItem('session_start');
    };
    window.addEventListener('beforeunload', report);
    return () => window.removeEventListener('beforeunload', report);
  }, []);

  const fmt = (m: number) => {
    if (m < 1) return '<1min';
    if (m < 60) return `${m}min`;
    const h = Math.floor(m / 60);
    const rem = m % 60;
    return rem > 0 ? `${h}h${rem}m` : `${h}h`;
  };

  return (
    <header className="flex items-start justify-between mb-8">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">{greeting}，{username}</h1>
        <p className="text-white/35 text-sm">{weak ? `上次你在「${weak}」这里停下的，继续吧？` : '准备好开始今天的学习了吗？'}</p>
      </div>
      <div className="flex items-center gap-4">
        <button className="relative w-9 h-9 rounded-lg bg-white/[0.04] border border-white/[0.06] flex items-center justify-center text-white/30 hover:text-white/50 transition-colors">
          <Bell className="w-4 h-4" />
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-purple-500" />
        </button>
        <div className="text-right">
          <div className="text-xs text-white/30">{new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })}</div>
          <div className="text-sm text-white/50 mt-0.5">
            已学习 <span className="text-purple-400 font-semibold">{loginDays}</span> 天
            {' · '}
            今日 <span className="text-purple-400 font-semibold">{fmt(sessionMinutes)}</span>
            {' · '}
            累计 <span className="text-purple-400 font-semibold">{fmt(totalMinutes + sessionMinutes)}</span>
          </div>
        </div>
      </div>
    </header>
  );
}

function StatCards({ profile, resourceCount, onNavigateModule }: { profile: ProfileData | null; resourceCount: number; onNavigateModule: (m: ModuleType, ctx?: NavigationContext) => void }) {
  const historyCount = profile?.learning_history?.length || 0;
  const weakCount = profile?.weak_points?.length || 0;
  const interestCount = profile?.interest_areas?.length || 0;

  const stats = [
    { label: '学习记录', value: String(historyCount), icon: Clock, color: 'text-purple-400', hoverBorder: 'hover:border-purple-500/20', moduleId: 'profile' as ModuleType },
    { label: '兴趣领域', value: String(interestCount), icon: Target, color: 'text-cyan-400', hoverBorder: 'hover:border-cyan-500/20', moduleId: 'profile' as ModuleType },
    { label: '生成资源', value: String(resourceCount), icon: Sparkles, color: 'text-amber-400', hoverBorder: 'hover:border-amber-500/20', moduleId: 'resources' as ModuleType },
    { label: '薄弱待补', value: String(weakCount), icon: Zap, color: 'text-emerald-400', hoverBorder: 'hover:border-emerald-500/20', moduleId: 'assessment' as ModuleType },
  ];

  return (
    <div className="grid grid-cols-4 gap-4 mb-8">
      {stats.map((stat, i) => {
        const Icon = stat.icon;
        return (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06, duration: 0.35 }}
            onClick={stat.moduleId ? () => onNavigateModule(stat.moduleId!) : undefined}
            className={`p-5 rounded-xl bg-[#1a1a27] border border-white/[0.05] hover:border-white/[0.08] transition-colors ${stat.moduleId ? `cursor-pointer ${stat.hoverBorder}` : ''}`}
          >
            <Icon className={`w-5 h-5 ${stat.color} mb-3`} />
            <div className="text-2xl font-bold text-white">{stat.value}</div>
            <div className="text-xs text-white/30 mt-1">{stat.label}</div>
          </motion.div>
        );
      })}
    </div>
  );
}

function ContinueLearningList({ resources, onPreview, onNavigateModule }: { resources: ApiResource[]; onPreview: (r: ApiResource) => void; onNavigateModule: (m: ModuleType, ctx?: NavigationContext) => void }) {
  const items = resources.slice(0, 3);

  if (items.length === 0) {
    return (
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-white mb-4">继续学习</h2>
        <div className="p-6 rounded-xl bg-[#1a1a27] border border-white/[0.05] text-center">
          <BookOpen className="w-8 h-8 text-white/15 mx-auto mb-3" />
          <p className="text-sm text-white/25">还没有学习记录</p>
          <button onClick={() => onNavigateModule('resources')} className="mt-3 px-4 py-2 bg-purple-500/15 text-purple-400 rounded-lg text-xs hover:bg-purple-500/25 transition-colors">去生成资源</button>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">继续学习</h2>
        <button onClick={() => onNavigateModule('resources')} className="text-xs text-white/30 hover:text-white/50 flex items-center gap-1 transition-colors">查看全部 <ChevronRight className="w-3.5 h-3.5" /></button>
      </div>
      <div className="space-y-3">
        {items.map((item, i) => {
          const typeInfo = TYPE_MAP[item.resource_type] || { icon: FileText, color: 'text-white/40', label: '资源' };
          const Icon = typeInfo.icon;
          return (
            <motion.div key={item.id} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 + i * 0.06, duration: 0.3 }} onClick={() => onPreview(item)} className="group flex items-center gap-4 p-4 rounded-xl bg-[#1a1a27] border border-white/[0.05] hover:border-purple-500/20 cursor-pointer transition-all">
              <div className="w-11 h-11 rounded-lg bg-purple-500/10 flex items-center justify-center flex-shrink-0"><Icon className={`w-5 h-5 ${typeInfo.color}`} /></div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-white truncate">{item.title}</div>
                <div className="text-xs text-white/25 mt-0.5">{item.subject}{item.topic ? ` · ${item.topic}` : ''} · {typeInfo.label}</div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-white/25">{formatTimeAgo(item.created_at)}</span>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

function RecentGeneratedList({ resources, onPreview }: { resources: ApiResource[]; onPreview: (r: ApiResource) => void }) {
  if (resources.length === 0) {
    return (
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">最近生成</h2>
        <div className="p-8 rounded-xl bg-[#1a1a27] border border-white/[0.05] text-center">
          <Sparkles className="w-8 h-8 text-white/15 mx-auto mb-3" />
          <p className="text-sm text-white/25">还没有生成过资源</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">最近生成</h2>
        <span className="text-xs text-white/20">{resources.length} 个资源</span>
      </div>
      <div className="grid grid-cols-3 gap-3">
        {resources.map((item, i) => {
          const typeInfo = TYPE_MAP[item.resource_type] || { icon: FileText, color: 'text-white/40', label: '资源' };
          const Icon = typeInfo.icon;
          return (
            <motion.div key={item.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 + i * 0.05, duration: 0.3 }} onClick={() => onPreview(item)} className="group p-4 rounded-xl bg-[#1a1a27] border border-white/[0.05] hover:border-purple-500/20 cursor-pointer transition-all">
              <div className="flex items-center gap-2.5 mb-3">
                <div className="w-9 h-9 rounded-lg bg-white/[0.04] flex items-center justify-center"><Icon className={`w-4 h-4 ${typeInfo.color}`} /></div>
                <span className="text-[11px] text-white/20">{typeInfo.label}</span>
              </div>
              <div className="text-sm text-white font-medium truncate mb-1.5">{item.title}</div>
              <div className="flex items-center justify-between">
                <span className="text-[11px] text-white/20 truncate max-w-[60%]">{item.subject}{item.topic ? ` · ${item.topic}` : ''}</span>
                <span className="text-[11px] text-white/15">{formatTimeAgo(item.created_at)}</span>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

function SuggestionCard({ recommendations, onNavigateModule }: { recommendations: Recommendation[]; onNavigateModule: (m: ModuleType, ctx?: NavigationContext) => void }) {
  return (
    <div className="p-5 rounded-xl bg-[#1a1a27] border border-white/[0.05] mb-5">
      <div className="flex items-center gap-2 mb-4">
        <Sparkles className="w-4 h-4 text-amber-400" />
        <h3 className="text-sm font-semibold text-white">今日建议</h3>
      </div>
      {recommendations.length === 0 ? (
        <p className="text-xs text-white/25 text-center py-4">暂无建议，多使用系统后会自动生成</p>
      ) : (
        <div className="space-y-3">
          {recommendations.slice(0, 3).map((item, i) => (
            <div key={i} onClick={() => onNavigateModule('tutor', { topic: item.topic, autoPlan: false })} className="group flex items-start gap-3 cursor-pointer">
              <div className="w-8 h-8 rounded-lg bg-white/[0.04] flex items-center justify-center flex-shrink-0 mt-0.5">
                <Lightbulb className="w-4 h-4 text-white/35" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm text-white/70 group-hover:text-white transition-colors">{item.topic}</div>
                <div className="text-[11px] text-white/20 mt-0.5">{item.reason}</div>
              </div>
              <ArrowRight className="w-3.5 h-3.5 text-white/15 mt-1 group-hover:text-purple-400 transition-colors" />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function QuickStartCard({ onNavigateModule }: { onNavigateModule: (m: ModuleType, ctx?: NavigationContext) => void }) {
  const quickItems = [
    { label: 'AI 问答', icon: Lightbulb, color: 'bg-amber-500/10 text-amber-400', moduleId: 'tutor' as ModuleType },
    { label: '资源生成', icon: Brain, color: 'bg-cyan-500/10 text-cyan-400', moduleId: 'resources' as ModuleType },
    { label: '学习评估', icon: BarChart3, color: 'bg-emerald-500/10 text-emerald-400', moduleId: 'assessment' as ModuleType },
    { label: '上传文档', icon: Database, color: 'bg-purple-500/10 text-purple-400', moduleId: 'rag' as ModuleType },
  ];
  return (
    <div className="p-5 rounded-xl bg-[#1a1a27] border border-white/[0.05]">
      <div className="flex items-center gap-2 mb-4">
        <Zap className="w-4 h-4 text-purple-400" />
        <h3 className="text-sm font-semibold text-white">快速开始</h3>
      </div>
      <div className="grid grid-cols-2 gap-2.5">
        {quickItems.map(item => {
          const Icon = item.icon;
          return (
            <button key={item.label} onClick={() => onNavigateModule(item.moduleId)} className="flex items-center gap-2.5 p-3 rounded-lg bg-white/[0.02] border border-white/[0.04] hover:border-white/[0.08] hover:bg-white/[0.04] transition-all">
              <div className={`w-8 h-8 rounded-lg ${item.color} flex items-center justify-center`}><Icon className="w-4 h-4" /></div>
              <span className="text-xs text-white/50">{item.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function CollaborationFeed({ logs, onNavigateModule }: { logs: ActivityLog[]; onNavigateModule: (m: ModuleType, ctx?: NavigationContext) => void }) {
  const typeConfig: Record<string, { icon: typeof UserCheck; color: string; label: string; moduleId: ModuleType }> = {
    resource:          { icon: Brain, color: 'bg-cyan-500/15 text-cyan-400', label: '资源生成', moduleId: 'resources' },
    resource_generate: { icon: Brain, color: 'bg-cyan-500/15 text-cyan-400', label: '资源生成', moduleId: 'resources' },
    path:              { icon: Router, color: 'bg-emerald-500/15 text-emerald-400', label: '学习路径', moduleId: 'path' },
    assess:            { icon: TrendingUp, color: 'bg-amber-500/15 text-amber-400', label: '效果评估', moduleId: 'assessment' },
    assessment:        { icon: TrendingUp, color: 'bg-amber-500/15 text-amber-400', label: '效果评估', moduleId: 'assessment' },
    tutor:             { icon: Lightbulb, color: 'bg-pink-500/15 text-pink-400', label: '智能辅导', moduleId: 'tutor' },
    tutor_query:       { icon: Lightbulb, color: 'bg-pink-500/15 text-pink-400', label: '智能辅导', moduleId: 'tutor' },
    profile:           { icon: UserCheck, color: 'bg-purple-500/15 text-purple-400', label: '学习画像', moduleId: 'profile' },
    session:           { icon: Clock, color: 'bg-white/10 text-white/40', label: '页面浏览', moduleId: 'profile' },
  };

  if (logs.length === 0) {
    return (
      <div className="mb-5">
        <div className="flex items-center gap-2 mb-3">
          <Users className="w-4 h-4 text-purple-400" />
          <h3 className="text-sm font-semibold text-white">协同动态</h3>
        </div>
        <div className="p-4 rounded-xl bg-[#1a1a27] border border-white/[0.05] text-center">
          <Users className="w-6 h-6 text-white/15 mx-auto mb-2" />
          <p className="text-xs text-white/25">暂无活动记录</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-5">
      <div className="flex items-center gap-2 mb-3">
        <Users className="w-4 h-4 text-purple-400" />
        <h3 className="text-sm font-semibold text-white">协同动态</h3>
      </div>
      <div className="space-y-2 max-h-[200px] overflow-y-auto">
        {logs.slice(0, 5).map((log, i) => {
          const config = typeConfig[log.type] || typeConfig.profile!;
          const Icon = config.icon;
          return (
            <motion.div key={log.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05, duration: 0.2 }} onClick={() => onNavigateModule(config.moduleId)} className="flex items-center gap-2.5 p-2.5 rounded-lg bg-[#1a1a27] border border-white/[0.04] hover:border-white/[0.08] cursor-pointer transition-colors">
              <div className={`w-7 h-7 rounded-md ${config.color} flex items-center justify-center flex-shrink-0`}><Icon className="w-3.5 h-3.5" /></div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-white/50 truncate">{log.action}</p>
                <p className="text-[10px] text-white/20">{formatTimeAgo(log.time)}</p>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   主组件
   ═══════════════════════════════════════════ */

export default memo(function WorkSpaceSection({ onNavigateModule }: WorkSpaceSectionProps) {
  const [previewResource, setPreviewResource] = useState<ApiResource | null>(null);
  const [resources, setResources] = useState<ApiResource[]>([]);
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [activityLogs, setActivityLogs] = useState<ActivityLog[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  const loadActivityLogs = useCallback(() => {
    if (localStorage.getItem('is_guest') === 'true') return;
    api.getActivityLogs(8).then((r: any) => {
      if (r?.success) {
        const actionMap: Record<string, string> = {
          login: '用户登录系统',
          resource_generate: '生成了学习资源',
          tutor_query: '解答了学习问题',
          assessment: '完成了学习评估',
          session: '页面浏览',
        };
        const logs = (r.data.logs || []).map((l: any) => {
          const meta = l.metadata || {};
          let action = meta.question || meta.topic || meta.grade || meta.title || actionMap[l.activity_type] || l.activity_type;
          if (meta.subject && meta.topic) action = `生成了「${meta.topic}」相关资源`;
          return {
            id: String(l.id),
            type: l.activity_type,
            action,
            detail: meta.subject || '',
            time: l.created_at,
          };
        }).filter((l: any) => l.type !== 'session');
        setActivityLogs(logs);
      }
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (localStorage.getItem('is_guest') === 'true') {
      setLoading(false);
      return;
    }
    const loadAll = async () => {
      setLoading(true);
      try {
        const [resRes, recRes, profileRes, statsRes] = await Promise.allSettled([
          api.getResources({ limit: 12 }),
          api.getLearningRecommendations(),
          api.getProfile(),
          api.getDashboardStats(),
        ]);

        if (resRes.status === 'fulfilled' && (resRes.value as any)?.success) {
          setResources((resRes.value as any).data.resources || []);
        }
        if (recRes.status === 'fulfilled' && (recRes.value as any)?.success) {
          const raw = (recRes.value as any).data.recommendations || [];
          setRecommendations(raw.map((r: any) => ({
            topic: r.topic || r.name || '',
            reason: r.reason || '',
            resource_type: r.resource_type || r.type || '',
            priority: r.priority,
          })));
        }
        if (profileRes.status === 'fulfilled' && (profileRes.value as any)?.success) {
          setProfile((profileRes.value as any).data || null);
        }
        if (statsRes.status === 'fulfilled' && (statsRes.value as any)?.success) {
          setStats((statsRes.value as any).data || null);
        }
      } catch {}

      loadActivityLogs();
      setLoading(false);
    };

    loadAll();

    const onResUpdate = () => {
      if (localStorage.getItem('is_guest') === 'true') return;
      api.getResources({ limit: 12 }).then((r: any) => {
        if (r?.success) setResources(r.data.resources || []);
      }).catch(() => {});
      api.getDashboardStats().then((r: any) => {
        if (r?.success) setStats(r.data || null);
      }).catch(() => {});
    };
    window.addEventListener('resources-updated', onResUpdate);
    return () => window.removeEventListener('resources-updated', onResUpdate);
  }, [loadActivityLogs]);

  if (loading) {
    return (
      <div className="flex min-h-screen bg-[#0a0a0a] items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
          <span className="text-sm text-white/30">加载工作台数据...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-[#0a0a0a] overflow-hidden">
      <main className="flex-1 overflow-y-auto h-screen" data-workspace-scroll>
        <div className="px-8 pt-7 pb-8 max-w-[1200px] mx-auto">
          <Header profile={profile} stats={stats} />
          <StatCards profile={profile} resourceCount={resources.length} onNavigateModule={onNavigateModule} />

          <div className="flex gap-6">
            <div className="flex-[7] min-w-0">
              <ContinueLearningList resources={resources} onPreview={setPreviewResource} onNavigateModule={onNavigateModule} />
              <RecentGeneratedList resources={resources} onPreview={setPreviewResource} />
            </div>
            <div className="flex-[3] min-w-0 space-y-5">
              <DashboardRadarChart profile={profile} />
              <SuggestionCard recommendations={recommendations} onNavigateModule={onNavigateModule} />
              <div className="flex gap-4">
                <div className="flex-1 min-w-0">
                  <CollaborationFeed logs={activityLogs} onNavigateModule={onNavigateModule} />
                </div>
                <div className="flex-1 min-w-0">
                  <QuickStartCard onNavigateModule={onNavigateModule} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <AnimatePresence>
        {previewResource && <ResourcePreview resource={previewResource} onClose={() => setPreviewResource(null)} />}
      </AnimatePresence>
    </div>
  );
});
