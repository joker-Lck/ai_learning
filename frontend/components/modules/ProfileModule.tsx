'use client';

import { useState, useRef } from 'react';
import {
  Send, Target, CheckCircle, Loader2, ChevronLeft, ChevronRight,
  User, BookOpen, Brain, Lightbulb, Sparkles, GraduationCap, Clock, Trophy,
  CalendarDays, BarChart3, AlertCircle, Plus, Trash2, Check, X,
  ChevronDown, Edit3, Save, Upload, Minus, Search, Pencil,
} from 'lucide-react';
import { PROFILE_DIMENSIONS } from './constants';
import type {
  DimensionChat, ProfileData, ProfileTab, CourseItem, GradeItem, ErrorNote,
} from './types';

interface ProfileModuleProps {
  currentStep: number;
  currentDimension: typeof PROFILE_DIMENSIONS[number];
  currentChat: DimensionChat;
  dimensionChats: Record<string, DimensionChat>;
  profileLoading: boolean;
  profileData: ProfileData | null;
  handleSendMessage: () => void;
  goToPreviousStep: () => void;
  goToNextStep: () => void;
  profileTab: ProfileTab;
  setProfileTab: (t: ProfileTab) => void;
  currentSemester: string;
  setCurrentSemester: (s: string) => void;
  semesters: string[];
  courses: CourseItem[];
  courseLoading: boolean;
  handleSaveCourses: (semester: string, courses: CourseItem[]) => Promise<void>;
  grades: GradeItem[];
  gradeLoading: boolean;
  handleSaveGrades: (semester: string, grades: GradeItem[]) => Promise<void>;
  errorNotes: ErrorNote[];
  errorLoading: boolean;
  handleAddErrorNote: (note: Omit<ErrorNote, 'id'>) => Promise<any>;
  handleToggleMastery: (noteId: number, currentMastery: number) => Promise<void>;
  handleDeleteErrorNote: (noteId: number) => Promise<void>;
  handleUpdateProfileField: (field: string, value: any) => Promise<any>;
  handleImportCourses: (file: File) => Promise<CourseItem[]>;
  handleImportGrades: (file: File) => Promise<GradeItem[]>;
  handleImportErrors: (file: File) => Promise<Omit<ErrorNote, 'id'>[]>;
  handleConfirmImportCourses: (data: CourseItem[]) => Promise<void>;
  handleConfirmImportGrades: (data: GradeItem[]) => Promise<void>;
  handleConfirmImportErrors: (data: Omit<ErrorNote, 'id'>[]) => Promise<void>;
}

const TABS: { key: ProfileTab; label: string; icon: any }[] = [
  { key: 'profile', label: '画像', icon: User },
  { key: 'schedule', label: '课程表', icon: CalendarDays },
  { key: 'grades', label: '成绩', icon: BarChart3 },
  { key: 'errors', label: '错题本', icon: AlertCircle },
];

const DAYS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
const GRADE_TYPES = [
  { value: 'overall', label: '总评' },
  { value: 'exam', label: '期末' },
  { value: 'quiz', label: '测验' },
  { value: 'homework', label: '作业' },
];

// 超级课程表时间槽 (每格 40 分钟)
const TIME_SLOTS: { start: string; end: string }[] = [];
for (let h = 8; h < 21; h++) {
  TIME_SLOTS.push({ start: `${String(h).padStart(2, '0')}:00`, end: `${String(h).padStart(2, '0')}:40` });
  TIME_SLOTS.push({ start: `${String(h).padStart(2, '0')}:40`, end: `${String(h + 1).padStart(2, '0')}:20` });
}
const SLOT_HEIGHT = 44;

const COURSE_COLORS = [
  'from-blue-500/25 to-cyan-500/25 border-blue-400/30',
  'from-violet-500/25 to-purple-500/25 border-violet-400/30',
  'from-amber-500/25 to-orange-500/25 border-amber-400/30',
  'from-green-500/25 to-emerald-500/25 border-green-400/30',
  'from-pink-500/25 to-rose-500/25 border-pink-400/30',
  'from-indigo-500/25 to-blue-600/25 border-indigo-400/30',
  'from-teal-500/25 to-cyan-500/25 border-teal-400/30',
  'from-red-500/25 to-pink-500/25 border-red-400/30',
  'from-sky-500/25 to-blue-400/25 border-sky-400/30',
  'from-yellow-500/25 to-amber-500/25 border-yellow-400/30',
];

function getCourseColor(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = ((hash << 5) - hash + name.charCodeAt(i)) | 0;
  return COURSE_COLORS[Math.abs(hash) % COURSE_COLORS.length] ?? 'from-blue-500/25 to-cyan-500/25 border-blue-400/30';
}

function timeToMinutes(t: string): number {
  const parts = t.split(':').map(Number);
  return (parts[0] || 0) * 60 + (parts[1] || 0);
}

function getCourseTop(start: string): number {
  const m = timeToMinutes(start) - 480; // 8:00 = 480min
  return (m / 40) * SLOT_HEIGHT;
}

function getCourseHeight(start: string, end: string): number {
  return Math.max(((timeToMinutes(end) - timeToMinutes(start)) / 40) * SLOT_HEIGHT, SLOT_HEIGHT - 4);
}

const PROFILE_DISPLAY = [
  { key: 'major', label: '专业', icon: GraduationCap, color: 'from-blue-500 to-cyan-400', fmt: (v: any) => v || '未填写' },
  { key: 'grade_level', label: '年级', icon: User, color: 'from-violet-500 to-purple-400', fmt: (v: any) => v || '未填写' },
  { key: 'cognitive_style', label: '认知风格', icon: Brain, color: 'from-green-500 to-emerald-400', fmt: (v: any) => v || '未评估' },
  { key: 'knowledge_base', label: '知识基础', icon: BookOpen, color: 'from-amber-500 to-orange-400', fmt: (v: any) => {
    if (!v) return '未评估'; if (typeof v === 'string') return v;
    if (v.level) return `水平: ${v.level}${v.topics?.length ? ' · ' + v.topics.join('、') : ''}`;
    return JSON.stringify(v);
  }},
  { key: 'learning_goals', label: '学习目标', icon: Target, color: 'from-red-500 to-pink-400', fmt: (v: any) => {
    if (!v) return '未设定'; if (Array.isArray(v)) return v.join('、'); if (typeof v === 'string') return v; return JSON.stringify(v);
  }},
  { key: 'interest_areas', label: '兴趣领域', icon: Sparkles, color: 'from-indigo-500 to-purple-400', fmt: (v: any) => Array.isArray(v) && v.length ? v.join('、') : '未填写' },
  { key: 'weak_points', label: '薄弱环节', icon: Lightbulb, color: 'from-yellow-500 to-amber-400', fmt: (v: any) => Array.isArray(v) && v.length ? v.join('、') : '暂无' },
  { key: 'preferred_resources', label: '偏好资源', icon: Trophy, color: 'from-teal-500 to-cyan-400', fmt: (v: any) => Array.isArray(v) && v.length ? v.join('、') : '未设定' },
];

// ==================== 主组件 ====================

export default function ProfileModule(props: ProfileModuleProps) {
  const { profileTab, setProfileTab, currentSemester, setCurrentSemester, semesters, profileData } = props;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
          <Target className="w-5 h-5 text-white" />
        </div>
        <div className="flex-1">
          <h3 className="text-xl font-bold text-white">学生画像</h3>
          <p className="text-sm text-white/40">
            {profileData ? '个性化学习画像 · 课程 · 成绩 · 错题' : '通过对话构建学习画像，管理你的学习数据'}
          </p>
        </div>
        {profileTab !== 'profile' && (
          <SemesterSelector current={currentSemester} semesters={semesters} onChange={setCurrentSemester} />
        )}
      </div>

      <div className="flex gap-1 bg-white/[0.03] rounded-xl p-1">
        {TABS.map(tab => {
          const Icon = tab.icon;
          const active = profileTab === tab.key;
          return (
            <button key={tab.key} onClick={() => setProfileTab(tab.key)}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-sm font-medium transition-all ${
                active ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-400 border border-cyan-400/20' : 'text-white/40 hover:text-white/60 hover:bg-white/[0.03]'
              }`}>
              <Icon className="w-4 h-4" />{tab.label}
            </button>
          );
        })}
      </div>

      {/* 使用 display:none 而非条件渲染，保持组件挂载以支持后台 AI 识别 */}
      <div style={{ display: profileTab === 'profile' ? 'block' : 'none' }}>
        <ProfileTabContent {...props} />
      </div>
      <div style={{ display: profileTab === 'schedule' ? 'block' : 'none' }}>
        <ScheduleTabContent courses={props.courses} loading={props.courseLoading} semester={currentSemester} onSave={props.handleSaveCourses} onImport={props.handleImportCourses} onConfirmImport={props.handleConfirmImportCourses} />
      </div>
      <div style={{ display: profileTab === 'grades' ? 'block' : 'none' }}>
        <GradesTabContent grades={props.grades} loading={props.gradeLoading} semester={currentSemester} onSave={props.handleSaveGrades} onImport={props.handleImportGrades} onConfirmImport={props.handleConfirmImportGrades} />
      </div>
      <div style={{ display: profileTab === 'errors' ? 'block' : 'none' }}>
        <ErrorsTabContent notes={props.errorNotes} loading={props.errorLoading} onAdd={props.handleAddErrorNote} onToggleMastery={props.handleToggleMastery} onDelete={props.handleDeleteErrorNote} onImport={props.handleImportErrors} onConfirmImport={props.handleConfirmImportErrors} />
      </div>
    </div>
  );
}

// ==================== 文件导入按钮 ====================

function FileImporter({ onImport, onConfirm, label, previewType, onFail }: {
  onImport: (file: File) => Promise<any[]>;
  onConfirm: (data: any[]) => Promise<void>;
  label: string;
  previewType: 'courses' | 'grades' | 'errors';
  onFail?: () => void;
}) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [importing, setImporting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [preview, setPreview] = useState<any[] | null>(null);

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    setResult(null);
    try {
      const data = await onImport(file);
      if (Array.isArray(data) && data.length > 0) {
        setPreview(data);
      } else {
        setResult('⚠️ 未识别到数据');
        setTimeout(() => setResult(null), 4000);
      }
    } catch (err: any) {
      setResult(`❌ ${err.message}`);
      if (onFail) onFail();
      setTimeout(() => setResult(null), 6000);
    } finally {
      setImporting(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  const handleConfirm = async () => {
    if (!preview) return;
    setSaving(true);
    try {
      await onConfirm(preview);
      setResult(`✅ 已导入 ${preview.length} 条`);
      setPreview(null);
      setTimeout(() => setResult(null), 3000);
    } catch (err: any) {
      setResult(`❌ 保存失败: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <input ref={fileRef} type="file" accept=".txt,.md,.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.csv,.jpg,.jpeg,.png,.bmp,.webp" onChange={handleFile} className="hidden" />
      <button onClick={() => fileRef.current?.click()} disabled={importing}
        className="px-3 py-1.5 bg-amber-500/15 border border-amber-400/20 text-amber-400 rounded-lg text-sm hover:border-amber-400/40 flex items-center gap-1.5 disabled:opacity-50 transition-all">
        {importing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
        {result || (importing ? 'AI 识别中...' : label)}
      </button>

      {/* 预览弹窗 */}
      {preview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setPreview(null)}>
          <div className="bg-[#0a1628] border border-white/[0.1] rounded-2xl w-[90vw] max-w-2xl max-h-[80vh] flex flex-col shadow-2xl" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.06]">
              <div>
                <h3 className="text-white font-bold text-base">AI 识别结果预览</h3>
                <p className="text-white/40 text-xs mt-0.5">共识别 {preview.length} 条，请确认后导入</p>
              </div>
              <button onClick={() => setPreview(null)} className="p-1.5 hover:bg-white/[0.06] rounded-lg"><X className="w-4 h-4 text-white/40" /></button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              {previewType === 'courses' && preview.map((c: any, i: number) => (
                <div key={i} className="flex items-center gap-3 px-3 py-2 bg-white/[0.03] border border-white/[0.06] rounded-lg">
                  <div className="w-1 h-8 rounded-full bg-cyan-400/50" />
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm font-medium truncate">{c.name}</p>
                    <p className="text-white/40 text-xs">{c.day} {c.start_time}-{c.end_time}{c.location ? ` · ${c.location}` : ''}{c.teacher ? ` · ${c.teacher}` : ''}</p>
                  </div>
                </div>
              ))}
              {previewType === 'grades' && preview.map((g: any, i: number) => (
                <div key={i} className="flex items-center gap-3 px-3 py-2 bg-white/[0.03] border border-white/[0.06] rounded-lg">
                  <div className="w-1 h-8 rounded-full bg-emerald-400/50" />
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm font-medium truncate">{g.course_name}</p>
                    <p className="text-white/40 text-xs">{g.score}分{g.credits ? ` · ${g.credits}学分` : ''} · {g.grade_type}{g.exam_date ? ` · ${g.exam_date}` : ''}</p>
                  </div>
                </div>
              ))}
              {previewType === 'errors' && preview.map((e: any, i: number) => (
                <div key={i} className="flex items-center gap-3 px-3 py-2 bg-white/[0.03] border border-white/[0.06] rounded-lg">
                  <div className="w-1 h-8 rounded-full bg-rose-400/50" />
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm font-medium truncate">{e.question}</p>
                    <p className="text-white/40 text-xs">{e.subject}{e.chapter ? ` · ${e.chapter}` : ''}{e.error_reason ? ` · ${e.error_reason}` : ''}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-end gap-3 px-5 py-3 border-t border-white/[0.06]">
              <button onClick={() => setPreview(null)} className="px-4 py-2 text-white/50 text-sm hover:text-white/80 transition-colors">取消</button>
              <button onClick={handleConfirm} disabled={saving}
                className="px-5 py-2 bg-cyan-400/20 border border-cyan-400/30 text-cyan-400 rounded-lg text-sm hover:bg-cyan-400/30 flex items-center gap-2 disabled:opacity-50 transition-all">
                {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                {saving ? '导入中...' : `确认导入 ${preview.length} 条`}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// ==================== 学期选择器 ====================

function SemesterSelector({ current, semesters, onChange }: { current: string; semesters: string[]; onChange: (s: string) => void }) {
  const [open, setOpen] = useState(false);
  const [custom, setCustom] = useState('');
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [startDate, setStartDate] = useState('');

  // 根据开学日期生成学期名称
  const getSemesterFromDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    const year = date.getFullYear();
    const month = date.getMonth() + 1; // 1-12
    // 2-7月=春，8-1月(次年)=秋
    const season = (month >= 2 && month <= 7) ? '春' : '秋';
    return `${year}-${season}`;
  };

  const handleDateSelect = () => {
    if (!startDate) return;
    const semester = getSemesterFromDate(startDate);
    onChange(semester);
    setShowDatePicker(false);
    setStartDate('');
    setOpen(false);
  };

  return (
    <div className="relative">
      <button onClick={() => setOpen(!open)} className="flex items-center gap-2 px-3 py-1.5 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white/70 hover:border-cyan-400/30 transition-colors">
        <CalendarDays className="w-4 h-4 text-cyan-400" />{current || '选择学期'}<ChevronDown className="w-3 h-3" />
      </button>
      {open && (
        <div className="absolute right-0 top-full mt-1 w-56 bg-[#0f1a30] border border-white/[0.1] rounded-xl shadow-2xl z-50 overflow-hidden">
          {/* 已有学期 */}
          {semesters.length > 0 && (
            <div className="max-h-40 overflow-y-auto">
              {semesters.map(s => (
                <button key={s} onClick={() => { onChange(s); setOpen(false); }}
                  className={`w-full px-3 py-2 text-left text-sm hover:bg-white/[0.06] ${s === current ? 'text-cyan-400 bg-cyan-400/10' : 'text-white/60'}`}>{s}</button>
              ))}
            </div>
          )}
          {/* 新建学期 */}
          <div className="border-t border-white/[0.06] p-2 space-y-2">
            {/* 手动输入 */}
            <div className="flex gap-1">
              <input value={custom} onChange={e => setCustom(e.target.value)} placeholder="如 2026-秋"
                className="flex-1 px-2 py-1 bg-white/[0.04] border border-white/[0.08] rounded text-xs text-white placeholder:text-white/20 focus:outline-none" />
              <button onClick={() => { if (custom.trim()) { onChange(custom.trim()); setCustom(''); setOpen(false); } }}
                className="px-2 py-1 bg-cyan-500/20 text-cyan-400 rounded text-xs hover:bg-cyan-500/30"><Plus className="w-3 h-3" /></button>
            </div>
            {/* 选择开学日期 */}
            {!showDatePicker ? (
              <button onClick={() => setShowDatePicker(true)}
                className="w-full flex items-center gap-1.5 px-2 py-1.5 text-xs text-cyan-400 hover:bg-cyan-400/10 rounded transition-colors">
                <CalendarDays className="w-3 h-3" />选择开学日期自动识别学期
              </button>
            ) : (
              <div className="space-y-1.5">
                <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)}
                  className="w-full px-2 py-1 bg-white/[0.04] border border-white/[0.08] rounded text-xs text-white focus:outline-none focus:border-cyan-400/30" />
                <div className="flex gap-1">
                  <button onClick={handleDateSelect} disabled={!startDate}
                    className="flex-1 px-2 py-1 bg-cyan-500/20 text-cyan-400 rounded text-xs hover:bg-cyan-500/30 disabled:opacity-30">确认</button>
                  <button onClick={() => { setShowDatePicker(false); setStartDate(''); }}
                    className="px-2 py-1 bg-white/[0.04] text-white/40 rounded text-xs hover:bg-white/[0.08]">取消</button>
                </div>
                {startDate && (
                  <p className="text-[10px] text-white/30">将识别为: <span className="text-cyan-400">{getSemesterFromDate(startDate)}</span></p>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ==================== 画像 Tab ====================

function ProfileTabContent(props: ProfileModuleProps) {
  const { profileData, profileLoading, currentStep, currentDimension, currentChat, handleSendMessage, goToPreviousStep, goToNextStep, dimensionChats } = props;
  if (profileData) return <ProfileEditView profileData={profileData} onUpdate={props.handleUpdateProfileField} />;

  return (
    <div className="space-y-4">
      <div className="glass-card rounded-xl p-3">
        <div className="flex items-center justify-between">
          {PROFILE_DIMENSIONS.map((dim, idx) => {
            const Icon = dim.icon;
            const done = dimensionChats[dim.id]?.completed;
            const cur = idx === currentStep;
            return (
              <div key={dim.id} className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${done ? 'bg-cyan-500 text-white' : cur ? `bg-gradient-to-r ${dim.color} text-white` : 'bg-white/[0.08] text-white/30'}`}>
                  {done ? <CheckCircle className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
                </div>
                {idx < PROFILE_DIMENSIONS.length - 1 && <div className={`w-4 h-0.5 mx-1 ${done ? 'bg-cyan-500' : 'bg-white/[0.08]'}`} />}
              </div>
            );
          })}
        </div>
        <div className="flex justify-between mt-1 text-xs text-white/30">
          {PROFILE_DIMENSIONS.map((dim, idx) => <span key={dim.id} className={idx === currentStep ? 'font-semibold text-white' : ''}>{dim.title}</span>)}
        </div>
      </div>
      <div className="glass-card rounded-xl overflow-hidden">
        <div className={`p-3 border-b border-white/[0.06] bg-gradient-to-r ${currentDimension.color} text-white`}>
          <div className="flex items-center gap-2">
            <currentDimension.icon className="w-5 h-5" /><h4 className="font-bold">{currentDimension.title}</h4>
            <span className="text-xs opacity-80 ml-auto">步骤 {currentStep + 1}/{PROFILE_DIMENSIONS.length}</span>
          </div>
        </div>
        <div className="h-64 overflow-y-auto p-4 space-y-3">
          {currentChat.messages.map((msg: any, idx: number) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-xl px-3 py-2 text-sm ${msg.role === 'user' ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white' : 'bg-white/[0.06] text-white/80'}`}>{msg.content}</div>
            </div>
          ))}
          {profileLoading && <div className="flex justify-start"><div className="bg-white/[0.06] rounded-xl px-3 py-2"><Loader2 className="w-4 h-4 animate-spin text-cyan-400" /></div></div>}
        </div>
        <div className="p-3 border-t border-white/[0.06]">
          <div className="flex gap-2">
            <input id="profile-input" type="text" onKeyPress={e => e.key === 'Enter' && handleSendMessage()} placeholder={currentDimension.placeholder}
              className="flex-1 px-3 py-2 bg-white/[0.04] border border-white/[0.08] text-white placeholder:text-white/15 rounded-lg focus:border-cyan-400/30 focus:outline-none text-sm" disabled={profileLoading} />
            <button onClick={handleSendMessage} disabled={profileLoading}
              className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1">
              {profileLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />} 发送
            </button>
          </div>
          <div className="flex justify-between mt-2">
            <button onClick={goToPreviousStep} disabled={currentStep === 0} className="px-3 py-1 text-sm text-white/40 hover:bg-white/[0.04] rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"><ChevronLeft className="w-4 h-4" /> 上一步</button>
            <button onClick={goToNextStep} disabled={currentStep === PROFILE_DIMENSIONS.length - 1} className="px-3 py-1 text-sm text-white/40 hover:bg-white/[0.04] rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1">下一步 <ChevronRight className="w-4 h-4" /></button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ==================== 画像编辑 ====================

function ProfileEditView({ profileData, onUpdate }: { profileData: ProfileData; onUpdate: (field: string, value: any) => Promise<any> }) {
  const [editing, setEditing] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  const [saving, setSaving] = useState(false);

  const startEdit = (key: string, raw: any) => {
    if (Array.isArray(raw)) setEditValue(raw.join('、'));
    else if (raw && typeof raw === 'object') {
      if (raw.level) setEditValue(raw.topics?.length ? `${raw.level}：${raw.topics.join('、')}` : raw.level);
      else setEditValue(JSON.stringify(raw));
    } else setEditValue(raw ?? '');
    setEditing(key);
  };

  const save = async (key: string) => {
    setSaving(true);
    try {
      let value: any = editValue.trim();
      if (['weak_points', 'interest_areas', 'preferred_resources', 'learning_goals'].includes(key)) {
        value = value ? value.split(/[,，、;；]/).map((s: string) => s.trim()).filter(Boolean) : [];
      } else if (key === 'knowledge_base' && value) {
        const parts = value.split(/[：:]/);
        value = { level: parts[0]?.trim() || value, topics: parts[1] ? parts[1].split(/[,，、]/).map((s: string) => s.trim()).filter(Boolean) : [] };
      }
      await onUpdate(key, value);
      setEditing(null);
    } finally { setSaving(false); }
  };

  return (
    <div className="space-y-4">
      <div className="bg-gradient-to-r from-cyan-500/20 to-blue-500/20 rounded-2xl p-5 border border-cyan-400/20">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <User className="w-8 h-8 text-white" />
          </div>
          <div className="flex-1">
            <h4 className="text-lg font-bold text-white">{profileData.major || '学生'}</h4>
            <p className="text-sm text-white/50">{profileData.grade_level || ''}</p>
            {profileData.update_time && <p className="text-xs text-white/30 mt-1 flex items-center gap-1"><Clock className="w-3 h-3" /> 更新于 {profileData.update_time}</p>}
          </div>
          <p className="text-xs text-white/30">点击卡片右上角编辑</p>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {PROFILE_DISPLAY.map(dim => {
          const raw = (profileData as any)[dim.key];
          const Icon = dim.icon;
          const text = dim.fmt(raw);
          const empty = !raw || (Array.isArray(raw) && raw.length === 0) || ['未填写', '未评估', '未设定', '暂无'].includes(text);
          const isEditing = editing === dim.key;
          return (
            <div key={dim.key} className={`glass-card rounded-xl p-4 transition-all ${empty ? 'opacity-50' : ''} ${isEditing ? 'border-cyan-400/30' : 'hover:border-white/10'}`}>
              <div className="flex items-center gap-3 mb-2">
                <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${dim.color} flex items-center justify-center`}><Icon className="w-4 h-4 text-white" /></div>
                <span className="font-semibold text-sm text-white flex-1">{dim.label}</span>
                {!isEditing && <button onClick={() => startEdit(dim.key, raw)} className="p-1 rounded-lg hover:bg-white/[0.06] text-white/30 hover:text-cyan-400 transition-colors"><Edit3 className="w-3.5 h-3.5" /></button>}
              </div>
              {isEditing ? (
                <div className="space-y-2 mt-1">
                  {['major', 'grade_level', 'cognitive_style'].includes(dim.key) ? (
                    <input value={editValue} onChange={e => setEditValue(e.target.value)} className="w-full px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white focus:outline-none focus:border-cyan-400/30" autoFocus />
                  ) : (
                    <textarea value={editValue} onChange={e => setEditValue(e.target.value)} rows={3} className="w-full px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white focus:outline-none focus:border-cyan-400/30 resize-none" placeholder={dim.key === 'knowledge_base' ? '如：中等：数据结构、算法' : '多个内容用逗号分隔'} autoFocus />
                  )}
                  <div className="flex gap-2 justify-end">
                    <button onClick={() => setEditing(null)} className="px-3 py-1 text-xs text-white/40 hover:text-white/60 rounded-lg hover:bg-white/[0.04]">取消</button>
                    <button onClick={() => save(dim.key)} disabled={saving} className="px-3 py-1 text-xs bg-cyan-500/20 text-cyan-400 rounded-lg hover:bg-cyan-500/30 disabled:opacity-50 flex items-center gap-1">
                      {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />} 保存
                    </button>
                  </div>
                </div>
              ) : (
                <p className={`text-sm leading-relaxed ${empty ? 'text-white/25 italic' : 'text-white/70'}`}>{text}</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ==================== 超级课程表 Tab ====================

function ScheduleTabContent({ courses, loading, semester, onSave, onImport, onConfirmImport }: { courses: CourseItem[]; loading: boolean; semester: string; onSave: (s: string, c: CourseItem[]) => Promise<void>; onImport: (f: File) => Promise<CourseItem[]>; onConfirmImport: (data: CourseItem[]) => Promise<void> }) {
  const [editing, setEditing] = useState(false);
  const [editIdx, setEditIdx] = useState<number | null>(null);
  const [form, setForm] = useState<CourseItem>({ name: '', day: '周一', start_time: '08:00', end_time: '09:40', location: '', teacher: '' });

  const addCourse = async () => {
    if (!form.name.trim()) return;
    if (editIdx !== null) {
      // 编辑模式：更新已有课程
      const updated = [...courses];
      updated[editIdx] = { ...form };
      await onSave(semester, updated);
      setEditIdx(null);
    } else {
      // 新增模式
      await onSave(semester, [...courses, { ...form }]);
    }
    setForm({ name: '', day: '周一', start_time: '08:00', end_time: '09:40', location: '', teacher: '' });
  };
  const removeCourse = async (idx: number) => { await onSave(semester, courses.filter((_, i) => i !== idx)); };
  const startEditCourse = (idx: number) => {
    const c = courses[idx];
    if (!c) return;
    setForm({
      name: c.name,
      day: c.day,
      start_time: c.start_time,
      end_time: c.end_time,
      location: c.location || '',
      teacher: c.teacher || '',
    });
    setEditIdx(idx);
    setEditing(true);
  };

  const byDay: Record<string, { c: CourseItem; i: number }[]> = {};
  DAYS.forEach(d => byDay[d] = []);
  courses.forEach((c, i) => { if (byDay[c.day]) byDay[c.day]!.push({ c, i }); });
  Object.values(byDay).forEach(arr => arr.sort((a, b) => a.c.start_time.localeCompare(b.c.start_time)));

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <p className="text-sm text-white/40">{semester} · {courses.length} 门课程</p>
        <div className="flex items-center gap-2">
          <FileImporter onImport={onImport} onConfirm={onConfirmImport} label="上传课表" previewType="courses" onFail={() => setEditing(true)} />
          <button onClick={() => setEditing(!editing)}
            className={`px-3 py-1.5 rounded-lg text-sm flex items-center gap-1.5 transition-all ${editing ? 'bg-red-500/20 text-red-400 border border-red-400/20' : 'bg-cyan-500/20 text-cyan-400 border border-cyan-400/20'}`}>
            {editing ? <><Minus className="w-3.5 h-3.5" /> 收起</> : <><Plus className="w-3.5 h-3.5" /> 手动添加</>}
          </button>
        </div>
      </div>

      {editing && (
        <div className="glass-card rounded-xl p-4 space-y-3 border border-cyan-400/10">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            <input value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} placeholder="课程名称 *"
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-400/30" />
            <select value={form.day} onChange={e => setForm(p => ({ ...p, day: e.target.value }))}
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white focus:outline-none [&>option]:bg-[#0f1a30] [&>option]:text-white">
              {DAYS.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
            <div className="flex gap-1 items-center">
              <input type="time" value={form.start_time} onChange={e => setForm(p => ({ ...p, start_time: e.target.value }))}
                className="flex-1 px-2 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white focus:outline-none" />
              <span className="text-white/20">-</span>
              <input type="time" value={form.end_time} onChange={e => setForm(p => ({ ...p, end_time: e.target.value }))}
                className="flex-1 px-2 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white focus:outline-none" />
            </div>
            <input value={form.location || ''} onChange={e => setForm(p => ({ ...p, location: e.target.value }))} placeholder="教室"
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none" />
            <input value={form.teacher || ''} onChange={e => setForm(p => ({ ...p, teacher: e.target.value }))} placeholder="教师"
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none" />
            <button onClick={addCourse} disabled={loading || !form.name.trim()}
              className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg text-sm hover:opacity-90 flex items-center justify-center gap-1 disabled:opacity-40">
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : editIdx !== null ? <Check className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />} {editIdx !== null ? '保存修改' : '添加'}
            </button>
          </div>
        </div>
      )}

      {courses.length === 0 ? (
        <div className="glass-card rounded-xl p-8 text-center text-white/30">
          <CalendarDays className="w-10 h-10 mx-auto mb-2 opacity-30" />
          <p>暂无课程，点击"手动添加"或"上传课表"开始</p>
        </div>
      ) : (
        <div className="glass-card rounded-xl overflow-hidden overflow-x-auto">
          <div className="min-w-[700px]">
            {/* 表头 */}
            <div className="grid grid-cols-[60px_repeat(7,1fr)] border-b border-white/[0.06]">
              <div className="p-2 text-xs text-white/30 text-center">时间</div>
              {DAYS.map(d => (
                <div key={d} className="p-2 text-xs text-white/50 text-center border-l border-white/[0.04] font-medium">{d}</div>
              ))}
            </div>
            {/* 时间格 + 课程 */}
            <div className="grid grid-cols-[60px_repeat(7,1fr)]">
              {/* 时间列 */}
              <div>
                {TIME_SLOTS.map((slot, i) => (
                  <div key={i} style={{ height: SLOT_HEIGHT }} className="flex items-center justify-center text-[10px] text-white/20 border-b border-white/[0.03]">
                    {slot.start}
                  </div>
                ))}
              </div>
              {/* 每天列 */}
              {DAYS.map(day => (
                <div key={day} className="relative border-l border-white/[0.04]">
                  {TIME_SLOTS.map((_, i) => (
                    <div key={i} style={{ height: SLOT_HEIGHT }} className="border-b border-white/[0.03]" />
                  ))}
                  {/* 课程块 */}
                  {(byDay[day] || []).map(({ c, i }) => (
                    <div key={i} className="absolute left-0.5 right-0.5 rounded-lg bg-gradient-to-br border p-1.5 overflow-hidden group hover:brightness-125 transition-all"
                      style={{ top: getCourseTop(c.start_time), height: getCourseHeight(c.start_time, c.end_time) }}
                      title={`${c.name}\n${c.start_time}-${c.end_time}${c.location ? '\n' + c.location : ''}${c.teacher ? '\n' + c.teacher : ''}`}
                    >
                      <div className={`absolute inset-0 bg-gradient-to-br ${getCourseColor(c.name)} rounded-lg`} />
                      <div className="relative z-10">
                        <p className="text-[11px] font-bold text-white truncate leading-tight">{c.name}</p>
                        <p className="text-[9px] text-white/50 truncate">{c.start_time}-{c.end_time}</p>
                        {c.location && <p className="text-[9px] text-white/30 truncate">{c.location}</p>}
                      </div>
                      <button onClick={(e) => { e.stopPropagation(); startEditCourse(i); }}
                        className="absolute top-0.5 left-0.5 w-5 h-5 flex items-center justify-center rounded-full bg-cyan-500/80 opacity-0 group-hover:opacity-100 transition-opacity z-20 hover:bg-cyan-500"
                        title="编辑此课程">
                        <Pencil className="w-3 h-3 text-white" />
                      </button>
                      <button onClick={(e) => { e.stopPropagation(); removeCourse(i); }}
                        className="absolute top-0.5 right-0.5 w-5 h-5 flex items-center justify-center rounded-full bg-red-500/80 opacity-0 group-hover:opacity-100 transition-opacity z-20 hover:bg-red-500"
                        title="删除此课程">
                        <X className="w-3 h-3 text-white" />
                      </button>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ==================== 成绩 Tab (按学科分组) ====================

function GradesTabContent({ grades, loading, semester, onSave, onImport, onConfirmImport }: { grades: GradeItem[]; loading: boolean; semester: string; onSave: (s: string, g: GradeItem[]) => Promise<void>; onImport: (f: File) => Promise<GradeItem[]>; onConfirmImport: (data: GradeItem[]) => Promise<void> }) {
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<GradeItem>({ semester, course_name: '', score: null, credits: null, grade_type: 'overall' });
  const [sortBy, setSortBy] = useState<'name' | 'score' | 'date'>('name');
  const [search, setSearch] = useState('');

  const addGrade = async () => {
    if (!form.course_name.trim()) return;
    await onSave(semester, [...grades, { ...form }]);
    setForm({ semester, course_name: '', score: null, credits: null, grade_type: 'overall' });
    setShowForm(false);
  };
  const removeGrade = async (idx: number) => { await onSave(semester, grades.filter((_, i) => i !== idx)); };

  const gradedOnly = grades.filter(g => g.score !== null);
  const avgScore = gradedOnly.length ? (gradedOnly.reduce((s, g) => s + (g.score || 0), 0) / gradedOnly.length).toFixed(1) : '--';

  const getScoreColor = (s: number | null) => {
    if (s === null) return 'text-white/30';
    if (s >= 90) return 'text-green-400';
    if (s >= 80) return 'text-cyan-400';
    if (s >= 70) return 'text-amber-400';
    if (s >= 60) return 'text-orange-400';
    return 'text-red-400';
  };
  const getScoreBg = (s: number | null) => {
    if (s === null) return 'bg-white/[0.03]';
    if (s >= 90) return 'bg-green-500/10';
    if (s >= 80) return 'bg-cyan-500/10';
    if (s >= 70) return 'bg-amber-500/10';
    if (s >= 60) return 'bg-orange-500/10';
    return 'bg-red-500/10';
  };

  // 搜索过滤
  const q = search.trim().toLowerCase();
  const searched = q ? grades.filter(g =>
    g.course_name.toLowerCase().includes(q) ||
    (g.grade_type && GRADE_TYPES.find(t => t.value === g.grade_type)?.label.toLowerCase().includes(q)) ||
    (g.exam_date && g.exam_date.includes(q))
  ) : grades;

  // 按学科分组 + 排序
  const grouped: Record<string, GradeItem[]> = {};
  searched.forEach(g => { (grouped[g.course_name] ||= []).push(g); });
  const sortedGroups = Object.entries(grouped).sort((a, b) => {
    if (sortBy === 'name') return a[0].localeCompare(b[0]);
    if (sortBy === 'score') {
      const avgA = a[1].filter(g => g.score !== null).reduce((s, g) => s + (g.score || 0), 0) / (a[1].filter(g => g.score !== null).length || 1);
      const avgB = b[1].filter(g => g.score !== null).reduce((s, g) => s + (g.score || 0), 0) / (b[1].filter(g => g.score !== null).length || 1);
      return avgB - avgA;
    }
    return (b[1][b[1].length - 1]?.exam_date || '').localeCompare(a[1][a[1].length - 1]?.exam_date || '');
  });

  return (
    <div className="space-y-3">
      {/* 搜索栏 */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="搜索课程名称、考试类型..."
          className="w-full pl-9 pr-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-xl text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-400/30 transition-colors" />
        {search && <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-white/20 hover:text-white/50"><X className="w-3.5 h-3.5" /></button>}
      </div>

      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <p className="text-sm text-white/40">{semester} 成绩</p>
          {gradedOnly.length > 0 && <span className="text-sm font-bold text-cyan-400">均分 {avgScore}</span>}
          {q && <span className="text-xs text-white/30">找到 {searched.length} 条</span>}
        </div>
        <div className="flex items-center gap-2">
          <FileImporter onImport={onImport} onConfirm={onConfirmImport} label="上传成绩" previewType="grades" />
          <select value={sortBy} onChange={e => setSortBy(e.target.value as any)}
            className="px-2 py-1.5 bg-white/[0.04] border border-white/[0.08] rounded-lg text-xs text-white/60 focus:outline-none [&>option]:bg-[#0f1a30] [&>option]:text-white">
            <option value="name">按学科</option>
            <option value="score">按均分</option>
            <option value="date">按时间</option>
          </select>
          <button onClick={() => setShowForm(!showForm)}
            className={`px-3 py-1.5 rounded-lg text-sm flex items-center gap-1.5 ${showForm ? 'bg-red-500/20 text-red-400' : 'bg-cyan-500/20 text-cyan-400'}`}>
            {showForm ? <><Minus className="w-3.5 h-3.5" /> 收起</> : <><Plus className="w-3.5 h-3.5" /> 录入</>}
          </button>
        </div>
      </div>

      {showForm && (
        <div className="glass-card rounded-xl p-4 space-y-3 border border-cyan-400/10">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            <input value={form.course_name} onChange={e => setForm(p => ({ ...p, course_name: e.target.value }))} placeholder="课程名称 *"
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-400/30" />
            <input type="number" min="0" max="100" value={form.score ?? ''} onChange={e => setForm(p => ({ ...p, score: e.target.value ? Number(e.target.value) : null }))} placeholder="成绩"
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none" />
            <input type="number" min="0" step="0.5" value={form.credits ?? ''} onChange={e => setForm(p => ({ ...p, credits: e.target.value ? Number(e.target.value) : null }))} placeholder="学分"
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none" />
            <select value={form.grade_type} onChange={e => setForm(p => ({ ...p, grade_type: e.target.value }))}
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white focus:outline-none [&>option]:bg-[#0f1a30] [&>option]:text-white">
              {GRADE_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
          <button onClick={addGrade} disabled={loading || !form.course_name.trim()}
            className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg text-sm hover:opacity-90 flex items-center gap-1 disabled:opacity-40">
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />} 添加
          </button>
        </div>
      )}

      {grades.length === 0 ? (
        <div className="glass-card rounded-xl p-8 text-center text-white/30">
          <BarChart3 className="w-10 h-10 mx-auto mb-2 opacity-30" /><p>暂无成绩，点击"录入"或"上传成绩"开始</p>
        </div>
      ) : (
        <div className="space-y-3">
          {sortedGroups.map(([courseName, items]) => {
            const groupGraded = items.filter(g => g.score !== null);
            const groupAvg = groupGraded.length ? (groupGraded.reduce((s, g) => s + (g.score || 0), 0) / groupGraded.length).toFixed(1) : '--';
            return (
              <div key={courseName} className="glass-card rounded-xl overflow-hidden">
                <div className="flex items-center justify-between px-4 py-2.5 bg-white/[0.03] border-b border-white/[0.06]">
                  <div className="flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-cyan-400" />
                    <span className="font-semibold text-sm text-white">{courseName}</span>
                    <span className="text-xs text-white/30">{items.length} 条记录</span>
                  </div>
                  <span className={`text-sm font-bold ${getScoreColor(Number(groupAvg))}`}>{groupAvg !== '--' ? `${groupAvg} 分` : ''}</span>
                </div>
                <div className="divide-y divide-white/[0.03]">
                  {items.map((g, gi) => {
                    const globalIdx = grades.indexOf(g);
                    return (
                      <div key={gi} className={`flex items-center gap-3 px-4 py-2.5 hover:bg-white/[0.02] ${getScoreBg(g.score)}`}>
                        <div className="flex-1 flex items-center gap-3">
                          <span className={`px-2 py-0.5 rounded text-xs border ${g.grade_type === 'exam' ? 'bg-amber-500/10 border-amber-400/20 text-amber-400' : g.grade_type === 'quiz' ? 'bg-blue-500/10 border-blue-400/20 text-blue-400' : g.grade_type === 'homework' ? 'bg-green-500/10 border-green-400/20 text-green-400' : 'bg-white/[0.04] border-white/[0.08] text-white/40'}`}>
                            {GRADE_TYPES.find(t => t.value === g.grade_type)?.label || '总评'}
                          </span>
                          {g.exam_date && <span className="text-xs text-white/25">{g.exam_date}</span>}
                        </div>
                        <span className={`text-lg font-bold ${getScoreColor(g.score)} min-w-[48px] text-right`}>{g.score ?? '--'}</span>
                        {g.credits !== null && g.credits !== undefined && <span className="text-xs text-white/30 min-w-[32px]">{g.credits} 学分</span>}
                        <button onClick={() => removeGrade(globalIdx)} className="p-1 text-white/15 hover:text-red-400 transition-colors"><Trash2 className="w-3.5 h-3.5" /></button>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ==================== 错题本 Tab (按学科分组) ====================

function ErrorsTabContent({ notes, loading, onAdd, onToggleMastery, onDelete, onImport, onConfirmImport }: { notes: ErrorNote[]; loading: boolean; onAdd: (n: Omit<ErrorNote, 'id'>) => Promise<any>; onToggleMastery: (id: number, m: number) => Promise<void>; onDelete: (id: number) => Promise<void>; onImport: (f: File) => Promise<Omit<ErrorNote, 'id'>[]>; onConfirmImport: (data: Omit<ErrorNote, 'id'>[]) => Promise<void> }) {
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ subject: '', chapter: '', question: '', my_answer: '', correct_answer: '', error_reason: '', tags: '' });
  const [filterSubject, setFilterSubject] = useState('');
  const [sortBy, setSortBy] = useState<'date' | 'subject'>('date');
  const [showMastered, setShowMastered] = useState(true);
  const [search, setSearch] = useState('');

  const handleSubmit = async () => {
    if (!form.subject.trim() || !form.question.trim()) return;
    await onAdd({ ...form, tags: form.tags ? form.tags.split(/[,，、]/).map(t => t.trim()).filter(Boolean) : [] });
    setForm({ subject: '', chapter: '', question: '', my_answer: '', correct_answer: '', error_reason: '', tags: '' });
    setShowForm(false);
  };

  const subjects = [...new Set(notes.map(n => n.subject))].filter(Boolean);
  const subjectFiltered = filterSubject ? notes.filter(n => n.subject === filterSubject) : notes;

  // 搜索过滤
  const q = search.trim().toLowerCase();
  const filtered = q ? subjectFiltered.filter(n =>
    n.question.toLowerCase().includes(q) ||
    n.subject.toLowerCase().includes(q) ||
    (n.chapter && n.chapter.toLowerCase().includes(q)) ||
    (n.error_reason && n.error_reason.toLowerCase().includes(q)) ||
    (n.tags && n.tags.some(t => t.toLowerCase().includes(q)))
  ) : subjectFiltered;

  // 按学科分组
  const grouped: Record<string, ErrorNote[]> = {};
  filtered.forEach(n => { (grouped[n.subject || '未分类'] ||= []).push(n); });
  Object.values(grouped).forEach(arr => arr.sort((a, b) => (b.created_at || '').localeCompare(a.created_at || '')));
  const sortedGroups = Object.entries(grouped).sort((a, b) => sortBy === 'subject' ? a[0].localeCompare(b[0]) : (b[1][0]?.created_at || '').localeCompare(a[1][0]?.created_at || ''));

  const totalUnmastered = filtered.filter(n => !n.mastery).length;
  const totalMastered = filtered.filter(n => n.mastery).length;

  return (
    <div className="space-y-3">
      {/* 搜索栏 */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="搜索题目、学科、章节、错因、标签..."
          className="w-full pl-9 pr-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-xl text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-400/30 transition-colors" />
        {search && <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-white/20 hover:text-white/50"><X className="w-3.5 h-3.5" /></button>}
      </div>

      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <p className="text-sm text-white/40">错题 {notes.length} 道</p>
          <span className="text-xs text-green-400/60">已掌握 {totalMastered}</span>
          <span className="text-xs text-amber-400/60">待巩固 {totalUnmastered}</span>
          {q && <span className="text-xs text-white/30">找到 {filtered.length} 条</span>}
        </div>
        <div className="flex items-center gap-2">
          <FileImporter onImport={onImport} onConfirm={onConfirmImport} label="上传错题" previewType="errors" />
          {subjects.length > 0 && (
            <select value={filterSubject} onChange={e => setFilterSubject(e.target.value)}
              className="px-2 py-1.5 bg-white/[0.04] border border-white/[0.08] rounded-lg text-xs text-white/60 focus:outline-none [&>option]:bg-[#0f1a30] [&>option]:text-white">
              <option value="">全部学科</option>
              {subjects.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          )}
          <select value={sortBy} onChange={e => setSortBy(e.target.value as any)}
            className="px-2 py-1.5 bg-white/[0.04] border border-white/[0.08] rounded-lg text-xs text-white/60 focus:outline-none [&>option]:bg-[#0f1a30] [&>option]:text-white">
            <option value="date">按时间</option>
            <option value="subject">按学科</option>
          </select>
          <button onClick={() => setShowForm(!showForm)}
            className={`px-3 py-1.5 rounded-lg text-sm flex items-center gap-1.5 ${showForm ? 'bg-red-500/20 text-red-400' : 'bg-cyan-500/20 text-cyan-400'}`}>
            {showForm ? <><Minus className="w-3.5 h-3.5" /> 收起</> : <><Plus className="w-3.5 h-3.5" /> 添加错题</>}
          </button>
        </div>
      </div>

      {showForm && (
        <div className="glass-card rounded-xl p-4 space-y-3 border border-cyan-400/10">
          <div className="grid grid-cols-2 gap-2">
            <input value={form.subject} onChange={e => setForm(p => ({ ...p, subject: e.target.value }))} placeholder="学科 *"
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-400/30" />
            <input value={form.chapter} onChange={e => setForm(p => ({ ...p, chapter: e.target.value }))} placeholder="章节"
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none" />
          </div>
          <textarea value={form.question} onChange={e => setForm(p => ({ ...p, question: e.target.value }))} placeholder="题目内容 *" rows={2}
            className="w-full px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-400/30 resize-none" />
          <div className="grid grid-cols-2 gap-2">
            <textarea value={form.my_answer} onChange={e => setForm(p => ({ ...p, my_answer: e.target.value }))} placeholder="我的答案" rows={2}
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none resize-none" />
            <textarea value={form.correct_answer} onChange={e => setForm(p => ({ ...p, correct_answer: e.target.value }))} placeholder="正确答案" rows={2}
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none resize-none" />
          </div>
          <textarea value={form.error_reason} onChange={e => setForm(p => ({ ...p, error_reason: e.target.value }))} placeholder="错误原因分析" rows={2}
            className="w-full px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none resize-none" />
          <div className="flex gap-2">
            <input value={form.tags} onChange={e => setForm(p => ({ ...p, tags: e.target.value }))} placeholder="标签（逗号分隔）"
              className="flex-1 px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none" />
            <button onClick={handleSubmit} disabled={!form.subject.trim() || !form.question.trim()}
              className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg text-sm hover:opacity-90 flex items-center gap-1 disabled:opacity-40">
              <Plus className="w-4 h-4" /> 添加
            </button>
          </div>
        </div>
      )}

      {filtered.length === 0 ? (
        <div className="glass-card rounded-xl p-8 text-center text-white/30">
          <AlertCircle className="w-10 h-10 mx-auto mb-2 opacity-30" /><p>{filterSubject ? `${filterSubject} 暂无错题` : '暂无错题，点击"添加错题"或"上传错题"开始'}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {sortedGroups.map(([subject, items]) => {
            const unmastered = items.filter(n => !n.mastery);
            const mastered = items.filter(n => n.mastery);
            return (
              <div key={subject} className="space-y-2">
                <div className="flex items-center gap-2 px-1">
                  <div className="w-1 h-4 rounded-full bg-gradient-to-b from-cyan-400 to-blue-500" />
                  <span className="text-sm font-semibold text-white">{subject}</span>
                  <span className="text-xs text-white/30">{items.length} 道</span>
                  {unmastered.length > 0 && <span className="text-xs text-amber-400/50">待巩固 {unmastered.length}</span>}
                </div>
                {unmastered.map(n => <ErrorNoteCard key={n.id} note={n} onToggleMastery={onToggleMastery} onDelete={onDelete} />)}
                {showMastered && mastered.length > 0 && (
                  <>
                    {mastered.length > 0 && unmastered.length > 0 && (
                      <button onClick={() => setShowMastered(false)} className="text-xs text-white/20 hover:text-white/40 ml-3 flex items-center gap-1">
                        <Check className="w-3 h-3" /> 已掌握 {mastered.length} 道（点击隐藏）
                      </button>
                    )}
                    {mastered.map(n => <ErrorNoteCard key={n.id} note={n} onToggleMastery={onToggleMastery} onDelete={onDelete} />)}
                  </>
                )}
                {!showMastered && mastered.length > 0 && unmastered.length > 0 && (
                  <button onClick={() => setShowMastered(true)} className="text-xs text-white/20 hover:text-white/40 ml-3 flex items-center gap-1">
                    <ChevronDown className="w-3 h-3" /> 展开已掌握 {mastered.length} 道
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function ErrorNoteCard({ note, onToggleMastery, onDelete }: { note: ErrorNote; onToggleMastery: (id: number, m: number) => Promise<void>; onDelete: (id: number) => Promise<void> }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className={`glass-card rounded-xl overflow-hidden transition-all ${note.mastery ? 'opacity-50' : ''}`}>
      <div className="flex items-start gap-3 p-3 cursor-pointer hover:bg-white/[0.02]" onClick={() => setExpanded(!expanded)}>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            {note.chapter && <span className="text-xs text-white/30">{note.chapter}</span>}
            {note.tags?.map((t, i) => <span key={i} className="px-1.5 py-0.5 bg-amber-400/10 text-amber-400 rounded text-xs">{t}</span>)}
          </div>
          <p className="text-sm text-white/80 line-clamp-2">{note.question}</p>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <button onClick={e => { e.stopPropagation(); onToggleMastery(note.id!, note.mastery || 0); }}
            className={`p-1.5 rounded-lg transition-colors ${note.mastery ? 'bg-green-500/20 text-green-400' : 'bg-white/[0.04] text-white/30 hover:text-green-400'}`}>
            <Check className="w-3.5 h-3.5" />
          </button>
          <button onClick={e => { e.stopPropagation(); onDelete(note.id!); }} className="p-1.5 text-white/20 hover:text-red-400 rounded-lg transition-colors">
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
      {expanded && (
        <div className="px-3 pb-3 space-y-2 border-t border-white/[0.04] pt-2">
          {note.my_answer && <div><span className="text-xs text-red-400/70">我的答案：</span><p className="text-sm text-white/60">{note.my_answer}</p></div>}
          {note.correct_answer && <div><span className="text-xs text-green-400/70">正确答案：</span><p className="text-sm text-white/60">{note.correct_answer}</p></div>}
          {note.error_reason && <div><span className="text-xs text-amber-400/70">错误原因：</span><p className="text-sm text-white/60">{note.error_reason}</p></div>}
          {note.created_at && <p className="text-xs text-white/20">{note.created_at}</p>}
        </div>
      )}
    </div>
  );
}
