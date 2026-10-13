'use client';

import { useCallback, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import {
  FileText, Download, Presentation, Sparkles,
  ChevronLeft, ChevronRight, Loader2, BookOpen,
  Palette, Clock, GraduationCap,
} from 'lucide-react';
import api from '@/lib/api';

/* ── PPT 风格 ── */
const STYLES = [
  { key: 'modern', name: '现代蓝', color: '#3B82F6' },
  { key: 'elegant', name: '典雅紫', color: '#8B5CF6' },
  { key: 'warm', name: '暖阳橙', color: '#F97316' },
  { key: 'tech', name: '科技深色', color: '#0EA5E9' },
  { key: 'nature', name: '清新绿', color: '#22C55E' },
];

interface SlideData {
  type: string;
  title: string;
  subtitle?: string;
  bullets?: string[];
  left_title?: string;
  left_bullets?: string[];
  right_title?: string;
  right_bullets?: string[];
  description?: string;
  steps?: string[];
  time?: string;
  notes?: string;
}

interface LessonPlan {
  lesson_title: string;
  subject: string;
  topic: string;
  grade: string;
  duration: number;
  teaching_objectives: { knowledge: string[]; ability: string[]; emotion: string[] };
  key_points: string[];
  difficult_points: string[];
  teaching_methods: string[];
  teaching_aids: string[];
  teaching_process: Array<{
    phase: string; duration: number;
    teacher_activity: string; student_activity: string; design_intent: string;
  }>;
  board_design: string;
  homework: string;
  teaching_reflection: string;
}

/* ═══════════════ PPT 幻灯片预览 ═══════════════ */
function SlidePreview({ slide, style, index, total }: {
  slide: SlideData; style: string; index: number; total: number;
}) {
  const s = STYLES.find(st => st.key === style) ?? STYLES[0]!;
  const isDark = style === 'tech' || slide.type === 'title' || slide.type === 'section' || slide.type === 'qa';
  const bg = isDark ? '#0F172A' : '#F8FAFC';
  const fg = isDark ? '#F1F5F9' : '#1E293B';
  const accent = s.color;

  return (
    <div
      className="relative rounded-xl overflow-hidden shadow-2xl border border-white/10"
      style={{ aspectRatio: '16/9', background: bg, width: '100%' }}
    >
      {/* 装饰 */}
      <div className="absolute top-0 left-0 right-0 h-1.5" style={{ background: accent }} />
      {slide.type === 'title' && (
        <>
          <div className="absolute inset-0 flex flex-col items-center justify-center px-12">
            <h1 className="text-white text-3xl md:text-5xl font-bold text-center leading-tight">{slide.title}</h1>
            <div className="h-1 w-48 my-6 rounded-full" style={{ background: accent }} />
            <p className="text-lg md:text-2xl text-center" style={{ color: accent }}>{slide.subtitle}</p>
          </div>
          <div className="absolute bottom-4 right-6 text-white/30 text-xs">{index + 1} / {total}</div>
        </>
      )}

      {slide.type === 'section' && (
        <>
          <div className="absolute inset-0 flex flex-col items-center justify-center px-12">
            <div className="px-10 py-5 rounded-2xl" style={{ background: accent }}>
              <h2 className="text-white text-3xl md:text-4xl font-bold text-center">{slide.title}</h2>
            </div>
            <p className="mt-6 text-lg text-white/60">{slide.subtitle}</p>
          </div>
          <div className="absolute bottom-4 right-6 text-white/30 text-xs">{index + 1} / {total}</div>
        </>
      )}

      {slide.type === 'qa' && (
        <>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <h1 className="text-white text-4xl md:text-5xl font-bold">{slide.title}</h1>
            <div className="h-1 w-40 my-6 rounded-full" style={{ background: accent }} />
            <p className="text-2xl" style={{ color: accent }}>{slide.subtitle}</p>
          </div>
          <div className="absolute bottom-4 right-6 text-white/30 text-xs">{index + 1} / {total}</div>
        </>
      )}

      {slide.type === 'objectives' && (
        <div className="p-10 md:p-14">
          <h2 className="text-2xl md:text-3xl font-bold mb-2" style={{ color: isDark ? '#fff' : accent }}>{slide.title}</h2>
          <div className="h-1 w-24 mb-8 rounded-full" style={{ background: accent }} />
          <div className="space-y-5">
            {(slide.bullets || []).map((b, i) => (
              <div key={i} className="flex items-center gap-4">
                <div className="w-9 h-9 rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0"
                     style={{ background: accent }}>{i + 1}</div>
                <p className="text-base md:text-xl" style={{ color: fg }}>{b}</p>
              </div>
            ))}
          </div>
          <div className="absolute bottom-4 right-6 text-white/30 text-xs">{index + 1} / {total}</div>
        </div>
      )}

      {slide.type === 'content' && (
        <div className="p-10 md:p-14">
          <h2 className="text-2xl md:text-3xl font-bold mb-2" style={{ color: isDark ? '#fff' : accent }}>{slide.title}</h2>
          <div className="h-1 w-24 mb-8 rounded-full" style={{ background: accent }} />
          <ul className="space-y-4">
            {(slide.bullets || []).map((b, i) => (
              <li key={i} className="flex items-start gap-3">
                <div className="w-2.5 h-2.5 rounded-full mt-2.5 flex-shrink-0" style={{ background: accent }} />
                <p className="text-base md:text-xl leading-relaxed" style={{ color: fg }}>{b}</p>
              </li>
            ))}
          </ul>
          <div className="absolute bottom-4 right-6 text-white/30 text-xs">{index + 1} / {total}</div>
        </div>
      )}

      {slide.type === 'two_column' && (
        <div className="p-8 md:p-12">
          <h2 className="text-2xl md:text-3xl font-bold mb-2" style={{ color: isDark ? '#fff' : accent }}>{slide.title}</h2>
          <div className="h-1 w-24 mb-8 rounded-full" style={{ background: accent }} />
          <div className="grid grid-cols-2 gap-6">
            <div className="rounded-2xl p-6" style={{ background: isDark ? 'rgba(255,255,255,0.05)' : '#E2E8F0' }}>
              <h3 className="text-lg font-bold mb-4" style={{ color: accent }}>{slide.left_title}</h3>
              <ul className="space-y-2.5">
                {(slide.left_bullets || []).map((b, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm md:text-base" style={{ color: fg }}>
                    <span style={{ color: accent }}>▸</span>{b}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-2xl p-6" style={{ background: isDark ? 'rgba(255,255,255,0.05)' : '#E2E8F0' }}>
              <h3 className="text-lg font-bold mb-4" style={{ color: accent }}>{slide.right_title}</h3>
              <ul className="space-y-2.5">
                {(slide.right_bullets || []).map((b, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm md:text-base" style={{ color: fg }}>
                    <span style={{ color: accent }}>▸</span>{b}
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className="absolute bottom-4 right-6 text-white/30 text-xs">{index + 1} / {total}</div>
        </div>
      )}

      {slide.type === 'activity' && (
        <div className="p-10 md:p-14">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-2xl md:text-3xl font-bold" style={{ color: isDark ? '#fff' : accent }}>{slide.title}</h2>
            {slide.time && (
              <span className="px-4 py-1.5 rounded-full text-white text-sm font-medium" style={{ background: accent }}>
                ⏱ {slide.time}
              </span>
            )}
          </div>
          <div className="h-1 w-24 mb-5 rounded-full" style={{ background: accent }} />
          <p className="text-sm md:text-lg mb-6" style={{ color: fg, opacity: 0.8 }}>{slide.description}</p>
          <div className="space-y-3">
            {(slide.steps || []).map((step, i) => (
              <div key={i} className="flex items-center gap-4 rounded-xl px-5 py-3"
                   style={{ background: isDark ? 'rgba(255,255,255,0.06)' : '#E2E8F0' }}>
                <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0"
                     style={{ background: accent }}>{i + 1}</div>
                <p className="text-sm md:text-lg" style={{ color: fg }}>{step}</p>
              </div>
            ))}
          </div>
          <div className="absolute bottom-4 right-6 text-white/30 text-xs">{index + 1} / {total}</div>
        </div>
      )}

      {slide.type === 'summary' && (
        <div className="p-10 md:p-14">
          <h2 className="text-2xl md:text-3xl font-bold mb-2" style={{ color: isDark ? '#fff' : accent }}>{slide.title}</h2>
          <div className="h-1 w-24 mb-8 rounded-full" style={{ background: accent }} />
          <div className="space-y-4">
            {(slide.bullets || []).map((b, i) => (
              <div key={i} className="flex items-center gap-4 rounded-xl px-5 py-4"
                   style={{ background: isDark ? 'rgba(255,255,255,0.06)' : '#E2E8F0' }}>
                <div className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold flex-shrink-0"
                     style={{ background: accent }}>✓</div>
                <p className="text-base md:text-xl" style={{ color: fg }}>{b}</p>
              </div>
            ))}
          </div>
          <div className="absolute bottom-4 right-6 text-white/30 text-xs">{index + 1} / {total}</div>
        </div>
      )}
    </div>
  );
}

/* ═══════════════ 教案展示面板 ═══════════════ */
function LessonPlanView({ plan }: { plan: LessonPlan }) {
  return (
    <div className="space-y-6 text-white/80">
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-6">
        <h3 className="text-white font-bold text-lg mb-4 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-purple-400" /> 基本信息
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div><span className="text-white/30">学科：</span>{plan.subject}</div>
          <div><span className="text-white/30">主题：</span>{plan.topic}</div>
          <div><span className="text-white/30">年级：</span>{plan.grade}</div>
          <div><span className="text-white/30">课时：</span>{plan.duration} 分钟</div>
        </div>
      </div>

      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-6">
        <h3 className="text-white font-bold text-lg mb-4 flex items-center gap-2">
          <GraduationCap className="w-5 h-5 text-blue-400" /> 教学目标
        </h3>
        <div className="space-y-3 text-sm">
          {(['knowledge', 'ability', 'emotion'] as const).map(key => (
            <div key={key}>
              <p className="text-white/50 font-medium mb-1">
                {key === 'knowledge' ? '知识与技能' : key === 'ability' ? '过程与方法' : '情感态度与价值观'}
              </p>
              <ul className="space-y-1">
                {plan.teaching_objectives[key]?.map((item: string, i: number) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-purple-400 mt-0.5">•</span>{item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-6">
          <h3 className="text-white font-bold text-lg mb-3">教学重点</h3>
          <ul className="space-y-2 text-sm">
            {plan.key_points?.map((p, i) => (
              <li key={i} className="flex items-start gap-2"><span className="text-green-400">✓</span>{p}</li>
            ))}
          </ul>
        </div>
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-6">
          <h3 className="text-white font-bold text-lg mb-3">教学难点</h3>
          <ul className="space-y-2 text-sm">
            {plan.difficult_points?.map((p, i) => (
              <li key={i} className="flex items-start gap-2"><span className="text-amber-400">⚠</span>{p}</li>
            ))}
          </ul>
        </div>
      </div>

      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-6">
        <h3 className="text-white font-bold text-lg mb-4">教学过程</h3>
        <div className="space-y-3">
          {plan.teaching_process?.map((step, i) => (
            <div key={i} className="rounded-lg border border-white/[0.06] p-4">
              <div className="flex items-center gap-3 mb-2">
                <span className="px-3 py-1 rounded-full bg-purple-500/20 text-purple-300 text-xs font-medium">
                  {step.phase}
                </span>
                <span className="text-white/30 text-xs flex items-center gap-1">
                  <Clock className="w-3 h-3" />{step.duration}分钟
                </span>
              </div>
              <div className="grid md:grid-cols-3 gap-3 text-sm">
                <div><span className="text-white/30 block text-xs mb-1">教师活动</span>{step.teacher_activity}</div>
                <div><span className="text-white/30 block text-xs mb-1">学生活动</span>{step.student_activity}</div>
                <div><span className="text-white/30 block text-xs mb-1">设计意图</span>{step.design_intent}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-6">
          <h3 className="text-white font-bold text-lg mb-3">板书设计</h3>
          <p className="text-sm whitespace-pre-wrap">{plan.board_design}</p>
        </div>
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-6">
          <h3 className="text-white font-bold text-lg mb-3">课后作业</h3>
          <p className="text-sm">{plan.homework}</p>
        </div>
      </div>

      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-6">
        <h3 className="text-white font-bold text-lg mb-3">教学反思</h3>
        <p className="text-sm text-white/50">{plan.teaching_reflection}</p>
      </div>
    </div>
  );
}

/* ═══════════════ 主组件 ═══════════════ */
export default function LessonPPTView() {
  const [subject, setSubject] = useState('');
  const [topic, setTopic] = useState('');
  const [grade, setGrade] = useState('大学');
  const [duration, setDuration] = useState(45);
  const [style, setStyle] = useState('modern');
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState<'ppt' | 'plan'>('ppt');
  const [slideIndex, setSlideIndex] = useState(0);
  const [lessonPlan, setLessonPlan] = useState<LessonPlan | null>(null);
  const [slides, setSlides] = useState<SlideData[]>([]);
  const [pptContent, setPptContent] = useState<any>(null);
  const [downloading, setDownloading] = useState<string | null>(null);

  const handleGenerate = useCallback(async () => {
    if (!subject.trim() || !topic.trim()) return;
    setLoading(true);
    setLessonPlan(null);
    setSlides([]);
    try {
      const res: any = await api.generateLessonPPT({
        subject: subject.trim(),
        topic: topic.trim(),
        grade,
        duration,
        style,
      });
      if (res.success && res.data) {
        setLessonPlan(res.data.lesson_plan);
        setPptContent(res.data.ppt_content);
        setSlides(res.data.ppt_content?.slides || []);
        setSlideIndex(0);
        setTab('ppt');
      }
    } catch (e) {
      console.error('生成失败', e);
    }
    setLoading(false);
  }, [subject, topic, grade, duration, style]);

  const handleDownloadPptx = useCallback(async () => {
    if (!pptContent) return;
    setDownloading('pptx');
    try {
      const res: any = await api.exportLessonPPTX({ ppt_content: pptContent, style });
      if (res.success && res.data?.filename) {
        window.open(`/api/lesson/download/${res.data.filename}`, '_blank');
      }
    } catch (e) {
      console.error('PPTX 导出失败', e);
    }
    setDownloading(null);
  }, [pptContent, style]);

  const handleDownloadDocx = useCallback(async () => {
    if (!lessonPlan) return;
    setDownloading('docx');
    try {
      const res: any = await api.exportLessonDocx({ lesson_plan: lessonPlan });
      if (res.success && res.data?.filename) {
        window.open(`/api/lesson/download/${res.data.filename}`, '_blank');
      }
    } catch (e) {
      console.error('DOCX 导出失败', e);
    }
    setDownloading(null);
  }, [lessonPlan]);

  return (
    <div className="space-y-6">
      {/* ── 表单区域 ── */}
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-6">
        <h2 className="text-white font-bold text-xl mb-1 flex items-center gap-2">
          <Presentation className="w-6 h-6 text-purple-400" /> 教案 & PPT 生成
        </h2>
        <p className="text-white/30 text-sm mb-6">AI 一键生成专业教学设计与配套课件，支持多种风格 PPT 导出</p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-white/40 text-xs mb-1.5">学科 *</label>
            <input value={subject} onChange={e => setSubject(e.target.value)}
              placeholder="如：数学、物理"
              className="w-full px-3 py-2.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-white text-sm placeholder:text-white/20 focus:border-purple-500/50 outline-none" />
          </div>
          <div>
            <label className="block text-white/40 text-xs mb-1.5">主题 *</label>
            <input value={topic} onChange={e => setTopic(e.target.value)}
              placeholder="如：函数的概念"
              className="w-full px-3 py-2.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-white text-sm placeholder:text-white/20 focus:border-purple-500/50 outline-none" />
          </div>
          <div>
            <label className="block text-white/40 text-xs mb-1.5">年级</label>
            <select value={grade} onChange={e => setGrade(e.target.value)}
              className="w-full px-3 py-2.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-white text-sm focus:border-purple-500/50 outline-none cursor-pointer">
              {['小学', '初一', '初二', '初三', '高一', '高二', '高三', '大学'].map(g =>
                <option key={g} value={g} className="bg-gray-800">{g}</option>
              )}
            </select>
          </div>
          <div>
            <label className="block text-white/40 text-xs mb-1.5">课时（分钟）</label>
            <input type="number" value={duration} min={20} max={120}
              onChange={e => setDuration(Number(e.target.value) || 45)}
              className="w-full px-3 py-2.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-white text-sm focus:border-purple-500/50 outline-none" />
          </div>
        </div>

        {/* 风格选择 */}
        <div className="mb-5">
          <label className="block text-white/40 text-xs mb-2 flex items-center gap-1.5">
            <Palette className="w-3.5 h-3.5" /> PPT 风格
          </label>
          <div className="flex flex-wrap gap-2">
            {STYLES.map(s => (
              <button key={s.key} onClick={() => setStyle(s.key)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all border ${
                  style === s.key
                    ? 'border-white/30 text-white shadow-lg scale-105'
                    : 'border-white/[0.06] text-white/50 hover:text-white/80 hover:border-white/15'
                }`}
                style={style === s.key ? { background: s.color + '30' } : {}}>
                <span className="inline-block w-3 h-3 rounded-full mr-1.5 align-middle" style={{ background: s.color }} />
                {s.name}
              </button>
            ))}
          </div>
        </div>

        <button onClick={handleGenerate} disabled={loading || !subject.trim() || !topic.trim()}
          className="px-8 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 text-white font-medium text-sm
                     hover:from-purple-500 hover:to-blue-500 transition-all disabled:opacity-40 disabled:cursor-not-allowed
                     flex items-center gap-2 shadow-lg shadow-purple-500/20">
          {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5" />}
          {loading ? '正在生成教案与课件…' : '一键生成教案 & PPT'}
        </button>
      </div>

      {/* ── 结果区域 ── */}
      {(slides.length > 0 || lessonPlan) && (
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
          {/* Tab 切换 + 操作按钮 */}
          <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
            <div className="flex items-center gap-2 bg-white/[0.04] rounded-xl p-1">
              <button onClick={() => setTab('ppt')}
                className={`px-5 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                  tab === 'ppt' ? 'bg-purple-600 text-white shadow-lg' : 'text-white/50 hover:text-white/80'
                }`}>
                <Presentation className="w-4 h-4" /> PPT 预览
              </button>
              <button onClick={() => setTab('plan')}
                className={`px-5 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                  tab === 'plan' ? 'bg-purple-600 text-white shadow-lg' : 'text-white/50 hover:text-white/80'
                }`}>
                <FileText className="w-4 h-4" /> 教案内容
              </button>
            </div>

            <div className="flex items-center gap-2">
              {slides.length > 0 && (
                <button onClick={handleDownloadPptx} disabled={downloading === 'pptx'}
                  className="px-5 py-2.5 rounded-lg bg-gradient-to-r from-blue-600 to-cyan-600 text-white text-sm font-medium
                             hover:from-blue-500 hover:to-cyan-500 transition-all flex items-center gap-2 shadow-lg disabled:opacity-50">
                  {downloading === 'pptx' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                  下载 PPTX
                </button>
              )}
              {lessonPlan && (
                <button onClick={handleDownloadDocx} disabled={downloading === 'docx'}
                  className="px-5 py-2.5 rounded-lg bg-gradient-to-r from-emerald-600 to-green-600 text-white text-sm font-medium
                             hover:from-emerald-500 hover:to-green-500 transition-all flex items-center gap-2 shadow-lg disabled:opacity-50">
                  {downloading === 'docx' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                  下载教案 DOCX
                </button>
              )}
            </div>
          </div>

          {/* PPT 预览 Tab */}
          {tab === 'ppt' && slides.length > 0 && (
            <div>
              {/* 幻灯片展示区 */}
              <div className="relative max-w-5xl mx-auto">
                <SlidePreview slide={slides[slideIndex]!} style={style} index={slideIndex} total={slides.length} />

                {/* 导航按钮 */}
                {slideIndex > 0 && (
                  <button onClick={() => setSlideIndex(slideIndex - 1)}
                    className="absolute left-[-48px] top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/[0.08] hover:bg-white/[0.15] flex items-center justify-center text-white transition-all">
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                )}
                {slideIndex < slides.length - 1 && (
                  <button onClick={() => setSlideIndex(slideIndex + 1)}
                    className="absolute right-[-48px] top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/[0.08] hover:bg-white/[0.15] flex items-center justify-center text-white transition-all">
                    <ChevronRight className="w-5 h-5" />
                  </button>
                )}
              </div>

              {/* 幻灯片缩略图导航 */}
              <div className="mt-5 flex items-center gap-2 overflow-x-auto pb-2">
                {slides.map((s, i) => (
                  <button key={i} onClick={() => setSlideIndex(i)}
                    className={`flex-shrink-0 rounded-lg border transition-all overflow-hidden ${
                      i === slideIndex ? 'border-purple-500 ring-2 ring-purple-500/30 scale-105' : 'border-white/10 opacity-50 hover:opacity-80'
                    }`}
                    style={{ width: 110, height: 62, background: (s.type === 'title' || s.type === 'section' || s.type === 'qa' || style === 'tech') ? '#0F172A' : '#F8FAFC' }}>
                    <div className="w-full h-full flex flex-col items-center justify-center px-2">
                      <span className={`text-[8px] leading-tight text-center line-clamp-2 ${
                        (s.type === 'title' || s.type === 'section' || s.type === 'qa' || style === 'tech') ? 'text-white/80' : 'text-gray-700'
                      }`}>{s.title}</span>
                      <span className={`text-[6px] mt-0.5 ${
                        (s.type === 'title' || s.type === 'section' || s.type === 'qa' || style === 'tech') ? 'text-white/30' : 'text-gray-400'
                      }`}>{i + 1}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* 教案内容 Tab */}
          {tab === 'plan' && lessonPlan && <LessonPlanView plan={lessonPlan} />}
        </motion.div>
      )}
    </div>
  );
}
