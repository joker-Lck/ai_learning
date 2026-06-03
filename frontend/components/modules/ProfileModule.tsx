'use client';

import { useState } from 'react';
import {
  Send, Target, CheckCircle, Loader2, ChevronLeft, ChevronRight,
  User, BookOpen, Brain, Lightbulb, Sparkles, GraduationCap, Clock, Trophy,
  CalendarDays, BarChart3, AlertCircle, Route, Plus, Trash2, Check, X,
  ChevronDown, FileText, Zap,
} from 'lucide-react';
import { PROFILE_DIMENSIONS } from './constants';
import type {
  DimensionChat, ProfileData, ProfileTab, CourseItem, GradeItem, ErrorNote, StudyPlan,
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
  // 学生数据管理
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
  studyPlans: StudyPlan[];
  planLoading: boolean;
  handleGeneratePlan: (data: { plan_type: string; custom_goal?: string; exam_date?: string; exam_subjects?: string[] }) => Promise<any>;
}

const TABS: { key: ProfileTab; label: string; icon: any }[] = [
  { key: 'profile', label: '画像', icon: User },
  { key: 'schedule', label: '课程表', icon: CalendarDays },
  { key: 'grades', label: '成绩', icon: BarChart3 },
  { key: 'errors', label: '错题本', icon: AlertCircle },
  { key: 'plan', label: '学习规划', icon: Route },
];

const DAYS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
const GRADE_TYPES = [
  { value: 'overall', label: '总评' },
  { value: 'exam', label: '期末' },
  { value: 'quiz', label: '测验' },
  { value: 'homework', label: '作业' },
];

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

export default function ProfileModule(props: ProfileModuleProps) {
  const {
    profileTab, setProfileTab, currentSemester, setCurrentSemester, semesters,
    profileData, profileLoading,
  } = props;

  return (
    <div className="space-y-4">
      {/* 标题 + 学期选择 */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
          <Target className="w-5 h-5 text-white" />
        </div>
        <div className="flex-1">
          <h3 className="text-xl font-bold text-white">学生画像</h3>
          <p className="text-sm text-white/40">
            {profileData ? '个性化学习画像 · 课程 · 成绩 · 错题 · 规划' : '通过对话构建学习画像，管理你的学习数据'}
          </p>
        </div>
        <SemesterSelector current={currentSemester} semesters={semesters} onChange={setCurrentSemester} />
      </div>

      {/* Tab 导航 */}
      <div className="flex gap-1 bg-white/[0.03] rounded-xl p-1">
        {TABS.map(tab => {
          const Icon = tab.icon;
          const active = profileTab === tab.key;
          return (
            <button key={tab.key} onClick={() => setProfileTab(tab.key)}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-sm font-medium transition-all ${
                active ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-400 border border-cyan-400/20' : 'text-white/40 hover:text-white/60 hover:bg-white/[0.03]'
              }`}>
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab 内容 */}
      {profileTab === 'profile' && <ProfileTabContent {...props} />}
      {profileTab === 'schedule' && <ScheduleTabContent courses={props.courses} loading={props.courseLoading} semester={currentSemester} onSave={props.handleSaveCourses} />}
      {profileTab === 'grades' && <GradesTabContent grades={props.grades} loading={props.gradeLoading} semester={currentSemester} onSave={props.handleSaveGrades} />}
      {profileTab === 'errors' && <ErrorsTabContent notes={props.errorNotes} loading={props.errorLoading} onAdd={props.handleAddErrorNote} onToggleMastery={props.handleToggleMastery} onDelete={props.handleDeleteErrorNote} />}
      {profileTab === 'plan' && <PlanTabContent plans={props.studyPlans} loading={props.planLoading} onGenerate={props.handleGeneratePlan} />}
    </div>
  );
}

// ==================== 学期选择器 ====================

function SemesterSelector({ current, semesters, onChange }: { current: string; semesters: string[]; onChange: (s: string) => void }) {
  const [open, setOpen] = useState(false);
  const [custom, setCustom] = useState('');

  return (
    <div className="relative">
      <button onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-1.5 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white/70 hover:border-cyan-400/30 transition-colors">
        <CalendarDays className="w-4 h-4 text-cyan-400" />
        {current || '选择学期'}
        <ChevronDown className="w-3 h-3" />
      </button>
      {open && (
        <div className="absolute right-0 top-full mt-1 w-48 bg-[#0f1a30] border border-white/[0.1] rounded-xl shadow-2xl z-50 overflow-hidden">
          {semesters.map(s => (
            <button key={s} onClick={() => { onChange(s); setOpen(false); }}
              className={`w-full px-3 py-2 text-left text-sm hover:bg-white/[0.06] ${s === current ? 'text-cyan-400 bg-cyan-400/10' : 'text-white/60'}`}>
              {s}
            </button>
          ))}
          <div className="border-t border-white/[0.06] p-2">
            <div className="flex gap-1">
              <input value={custom} onChange={e => setCustom(e.target.value)} placeholder="如 2026-秋"
                className="flex-1 px-2 py-1 bg-white/[0.04] border border-white/[0.08] rounded text-xs text-white placeholder:text-white/20 focus:outline-none" />
              <button onClick={() => { if (custom.trim()) { onChange(custom.trim()); setCustom(''); setOpen(false); } }}
                className="px-2 py-1 bg-cyan-500/20 text-cyan-400 rounded text-xs hover:bg-cyan-500/30">
                <Plus className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ==================== 画像 Tab ====================

function ProfileTabContent(props: ProfileModuleProps) {
  const { profileData, profileLoading, currentStep, currentDimension, currentChat, dimensionChats, handleSendMessage, goToPreviousStep, goToNextStep } = props;

  if (profileData) {
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
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {PROFILE_DISPLAY.map(dim => {
            const value = (profileData as any)[dim.key];
            const Icon = dim.icon;
            const text = dim.fmt(value);
            const empty = !value || (Array.isArray(value) && value.length === 0) || ['未填写', '未评估', '未设定', '暂无'].includes(text);
            return (
              <div key={dim.key} className={`glass-card rounded-xl p-4 hover:border-white/10 transition-all ${empty ? 'opacity-50' : ''}`}>
                <div className="flex items-center gap-3 mb-2">
                  <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${dim.color} flex items-center justify-center`}><Icon className="w-4 h-4 text-white" /></div>
                  <span className="font-semibold text-sm text-white">{dim.label}</span>
                </div>
                <p className={`text-sm leading-relaxed ${empty ? 'text-white/25 italic' : 'text-white/70'}`}>{text}</p>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // 对话构建流程
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
            <currentDimension.icon className="w-5 h-5" />
            <h4 className="font-bold">{currentDimension.title}</h4>
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

// ==================== 课程表 Tab ====================

function ScheduleTabContent({ courses, loading, semester, onSave }: { courses: CourseItem[]; loading: boolean; semester: string; onSave: (s: string, c: CourseItem[]) => Promise<void> }) {
  const [editCourses, setEditCourses] = useState<CourseItem[]>([]);
  const [editing, setEditing] = useState(false);
  const [newCourse, setNewCourse] = useState<CourseItem>({ name: '', day: '周一', start_time: '08:00', end_time: '09:40', location: '', teacher: '' });

  const startEdit = () => { setEditCourses([...courses]); setEditing(true); };
  const addCourse = () => {
    if (!newCourse.name.trim()) return;
    setEditCourses(prev => [...prev, { ...newCourse }]);
    setNewCourse({ name: '', day: '周一', start_time: '08:00', end_time: '09:40', location: '', teacher: '' });
  };
  const removeCourse = (i: number) => setEditCourses(prev => prev.filter((_, idx) => idx !== i));
  const saveCourses = async () => { await onSave(semester, editCourses); setEditing(false); };

  const displayCourses = editing ? editCourses : courses;

  // 按星期分组
  const grouped: Record<string, CourseItem[]> = {};
  DAYS.forEach(d => grouped[d] = []);
  displayCourses.forEach(c => { if (grouped[c.day]) grouped[c.day]!.push(c); });
  Object.values(grouped).forEach(arr => arr.sort((a, b) => a.start_time.localeCompare(b.start_time)));

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-white/40">{semester} 课程表 · {courses.length} 门课程</p>
        {!editing ? (
          <button onClick={startEdit} className="px-3 py-1.5 bg-cyan-500/20 text-cyan-400 rounded-lg text-sm hover:bg-cyan-500/30 flex items-center gap-1"><Plus className="w-3.5 h-3.5" /> 编辑课程</button>
        ) : (
          <div className="flex gap-2">
            <button onClick={() => setEditing(false)} className="px-3 py-1.5 text-white/40 hover:text-white/60 text-sm"><X className="w-4 h-4" /></button>
            <button onClick={saveCourses} disabled={loading} className="px-3 py-1.5 bg-cyan-500/20 text-cyan-400 rounded-lg text-sm hover:bg-cyan-500/30 flex items-center gap-1">
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />} 保存
            </button>
          </div>
        )}
      </div>

      {/* 添加课程表单 */}
      {editing && (
        <div className="glass-card rounded-xl p-4 space-y-3">
          <p className="text-sm font-medium text-white/60">添加课程</p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            <input value={newCourse.name} onChange={e => setNewCourse(p => ({ ...p, name: e.target.value }))} placeholder="课程名称"
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-400/30" />
            <select value={newCourse.day} onChange={e => setNewCourse(p => ({ ...p, day: e.target.value }))}
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white focus:outline-none [&>option]:bg-[#0f1a30] [&>option]:text-white">
              {DAYS.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
            <input type="time" value={newCourse.start_time} onChange={e => setNewCourse(p => ({ ...p, start_time: e.target.value }))}
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white focus:outline-none" />
            <input type="time" value={newCourse.end_time} onChange={e => setNewCourse(p => ({ ...p, end_time: e.target.value }))}
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white focus:outline-none" />
            <input value={newCourse.location || ''} onChange={e => setNewCourse(p => ({ ...p, location: e.target.value }))} placeholder="教室（选填）"
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none" />
            <input value={newCourse.teacher || ''} onChange={e => setNewCourse(p => ({ ...p, teacher: e.target.value }))} placeholder="教师（选填）"
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none" />
          </div>
          <button onClick={addCourse} className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg text-sm hover:opacity-90 flex items-center gap-1"><Plus className="w-4 h-4" /> 添加</button>
        </div>
      )}

      {/* 课程表网格 */}
      {displayCourses.length === 0 && !editing ? (
        <div className="glass-card rounded-xl p-8 text-center text-white/30">
          <CalendarDays className="w-10 h-10 mx-auto mb-2 opacity-30" />
          <p>暂无课程数据，点击"编辑课程"添加</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {DAYS.map(day => (
            <div key={day} className="glass-card rounded-xl overflow-hidden">
              <div className="px-3 py-2 bg-white/[0.04] border-b border-white/[0.06]">
                <span className="text-sm font-semibold text-white">{day}</span>
                <span className="text-xs text-white/30 ml-2">{(grouped[day] || []).length} 节</span>
              </div>
              <div className="p-2 space-y-1.5 min-h-[60px]">
                {(grouped[day] || []).length === 0 ? (
                  <p className="text-xs text-white/15 text-center py-3">无课</p>
                ) : (grouped[day] || []).map((c, i) => (
                  <div key={i} className="flex items-center gap-2 px-2 py-1.5 bg-white/[0.03] rounded-lg group">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white truncate">{c.name}</p>
                      <p className="text-xs text-white/30">{c.start_time}-{c.end_time}{c.location ? ` · ${c.location}` : ''}</p>
                    </div>
                    {editing && (
                      <button onClick={() => removeCourse(editCourses.findIndex(ec => ec.name === c.name && ec.day === c.day && ec.start_time === c.start_time))} className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300 transition-opacity"><Trash2 className="w-3.5 h-3.5" /></button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ==================== 成绩 Tab ====================

function GradesTabContent({ grades, loading, semester, onSave }: { grades: GradeItem[]; loading: boolean; semester: string; onSave: (s: string, g: GradeItem[]) => Promise<void> }) {
  const [editGrades, setEditGrades] = useState<GradeItem[]>([]);
  const [editing, setEditing] = useState(false);
  const [newGrade, setNewGrade] = useState<GradeItem>({ semester, course_name: '', score: null, credits: null, grade_type: 'overall' });

  const startEdit = () => { setEditGrades(grades.length ? [...grades] : []); setEditing(true); };
  const addGrade = () => {
    if (!newGrade.course_name.trim()) return;
    setEditGrades(prev => [...prev, { ...newGrade }]);
    setNewGrade({ semester, course_name: '', score: null, credits: null, grade_type: 'overall' });
  };
  const removeGrade = (i: number) => setEditGrades(prev => prev.filter((_, idx) => idx !== i));
  const updateGrade = (i: number, field: string, value: any) => setEditGrades(prev => prev.map((g, idx) => idx === i ? { ...g, [field]: value } : g));
  const saveGrades = async () => { await onSave(semester, editGrades); setEditing(false); };

  const display = editing ? editGrades : grades;
  const gradedOnly = grades.filter(g => g.score !== null);
  const avgScore = gradedOnly.length ? (gradedOnly.reduce((s, g) => s + (g.score || 0), 0) / gradedOnly.length).toFixed(1) : '--';

  const getScoreColor = (score: number | null) => {
    if (score === null) return 'text-white/30';
    if (score >= 90) return 'text-green-400';
    if (score >= 80) return 'text-cyan-400';
    if (score >= 70) return 'text-amber-400';
    if (score >= 60) return 'text-orange-400';
    return 'text-red-400';
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <p className="text-sm text-white/40">{semester} 成绩</p>
          {grades.length > 0 && <span className="text-sm text-cyan-400">均分 {avgScore}</span>}
        </div>
        {!editing ? (
          <button onClick={startEdit} className="px-3 py-1.5 bg-cyan-500/20 text-cyan-400 rounded-lg text-sm hover:bg-cyan-500/30 flex items-center gap-1"><Plus className="w-3.5 h-3.5" /> 录入成绩</button>
        ) : (
          <div className="flex gap-2">
            <button onClick={() => setEditing(false)} className="px-3 py-1.5 text-white/40 hover:text-white/60 text-sm"><X className="w-4 h-4" /></button>
            <button onClick={saveGrades} disabled={loading} className="px-3 py-1.5 bg-cyan-500/20 text-cyan-400 rounded-lg text-sm hover:bg-cyan-500/30 flex items-center gap-1">
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />} 保存
            </button>
          </div>
        )}
      </div>

      {/* 添加成绩表单 */}
      {editing && (
        <div className="glass-card rounded-xl p-4 space-y-3">
          <p className="text-sm font-medium text-white/60">添加成绩</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            <input value={newGrade.course_name} onChange={e => setNewGrade(p => ({ ...p, course_name: e.target.value }))} placeholder="课程名称"
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-400/30" />
            <input type="number" min="0" max="100" value={newGrade.score ?? ''} onChange={e => setNewGrade(p => ({ ...p, score: e.target.value ? Number(e.target.value) : null }))} placeholder="成绩"
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none" />
            <input type="number" min="0" step="0.5" value={newGrade.credits ?? ''} onChange={e => setNewGrade(p => ({ ...p, credits: e.target.value ? Number(e.target.value) : null }))} placeholder="学分"
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none" />
            <select value={newGrade.grade_type} onChange={e => setNewGrade(p => ({ ...p, grade_type: e.target.value }))}
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white focus:outline-none [&>option]:bg-[#0f1a30] [&>option]:text-white">
              {GRADE_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
          <button onClick={addGrade} className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg text-sm hover:opacity-90 flex items-center gap-1"><Plus className="w-4 h-4" /> 添加</button>
        </div>
      )}

      {/* 成绩列表 */}
      {display.length === 0 && !editing ? (
        <div className="glass-card rounded-xl p-8 text-center text-white/30">
          <BarChart3 className="w-10 h-10 mx-auto mb-2 opacity-30" />
          <p>暂无成绩数据，点击"录入成绩"添加</p>
        </div>
      ) : (
        <div className="glass-card rounded-xl overflow-hidden">
          <div className="grid grid-cols-[1fr_80px_60px_60px_40px] gap-2 px-4 py-2 bg-white/[0.03] border-b border-white/[0.06] text-xs text-white/40 font-medium">
            <span>课程</span><span>成绩</span><span>学分</span><span>类型</span><span></span>
          </div>
          {display.map((g, i) => (
            <div key={i} className="grid grid-cols-[1fr_80px_60px_60px_40px] gap-2 px-4 py-2.5 border-b border-white/[0.03] items-center hover:bg-white/[0.02]">
              {editing ? (
                <>
                  <input value={g.course_name} onChange={e => updateGrade(i, 'course_name', e.target.value)} className="bg-transparent border-b border-white/[0.1] text-sm text-white focus:outline-none focus:border-cyan-400/30" />
                  <input type="number" min="0" max="100" value={g.score ?? ''} onChange={e => updateGrade(i, 'score', e.target.value ? Number(e.target.value) : null)} className="bg-transparent border-b border-white/[0.1] text-sm text-white focus:outline-none w-16" />
                  <input type="number" min="0" step="0.5" value={g.credits ?? ''} onChange={e => updateGrade(i, 'credits', e.target.value ? Number(e.target.value) : null)} className="bg-transparent border-b border-white/[0.1] text-sm text-white focus:outline-none w-14" />
                  <select value={g.grade_type || 'overall'} onChange={e => updateGrade(i, 'grade_type', e.target.value)} className="bg-transparent text-xs text-white/60 focus:outline-none [&>option]:bg-[#0f1a30]">
                    {GRADE_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                  <button onClick={() => removeGrade(i)} className="text-red-400 hover:text-red-300"><Trash2 className="w-3.5 h-3.5" /></button>
                </>
              ) : (
                <>
                  <span className="text-sm text-white truncate">{g.course_name}</span>
                  <span className={`text-sm font-bold ${getScoreColor(g.score)}`}>{g.score ?? '--'}</span>
                  <span className="text-sm text-white/40">{g.credits ?? '--'}</span>
                  <span className="text-xs text-white/30">{GRADE_TYPES.find(t => t.value === g.grade_type)?.label || '总评'}</span>
                  <span></span>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ==================== 错题本 Tab ====================

function ErrorsTabContent({ notes, loading, onAdd, onToggleMastery, onDelete }: { notes: ErrorNote[]; loading: boolean; onAdd: (n: Omit<ErrorNote, 'id'>) => Promise<any>; onToggleMastery: (id: number, m: number) => Promise<void>; onDelete: (id: number) => Promise<void> }) {
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ subject: '', chapter: '', question: '', my_answer: '', correct_answer: '', error_reason: '', tags: '' });
  const [filterSubject, setFilterSubject] = useState('');

  const handleSubmit = async () => {
    if (!form.subject.trim() || !form.question.trim()) return;
    await onAdd({
      ...form,
      tags: form.tags ? form.tags.split(/[,，、]/).map(t => t.trim()).filter(Boolean) : [],
    });
    setForm({ subject: '', chapter: '', question: '', my_answer: '', correct_answer: '', error_reason: '', tags: '' });
    setShowForm(false);
  };

  const subjects = [...new Set(notes.map(n => n.subject))].filter(Boolean);
  const filtered = filterSubject ? notes.filter(n => n.subject === filterSubject) : notes;
  const unmastered = filtered.filter(n => !n.mastery);
  const mastered = filtered.filter(n => n.mastery);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <p className="text-sm text-white/40">错题 {notes.length} 道</p>
          {subjects.length > 0 && (
            <select value={filterSubject} onChange={e => setFilterSubject(e.target.value)}
              className="px-2 py-1 bg-white/[0.04] border border-white/[0.08] rounded-lg text-xs text-white/60 focus:outline-none [&>option]:bg-[#0f1a30] [&>option]:text-white">
              <option value="">全部学科</option>
              {subjects.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          )}
        </div>
        <button onClick={() => setShowForm(!showForm)} className="px-3 py-1.5 bg-cyan-500/20 text-cyan-400 rounded-lg text-sm hover:bg-cyan-500/30 flex items-center gap-1">
          {showForm ? <X className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />} {showForm ? '收起' : '添加错题'}
        </button>
      </div>

      {/* 添加错题表单 */}
      {showForm && (
        <div className="glass-card rounded-xl p-4 space-y-3">
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
            <input value={form.tags} onChange={e => setForm(p => ({ ...p, tags: e.target.value }))} placeholder="标签（逗号分隔，如：概念混淆,计算错误）"
              className="flex-1 px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none" />
            <button onClick={handleSubmit}
              className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg text-sm hover:opacity-90 flex items-center gap-1"><Plus className="w-4 h-4" /> 添加</button>
          </div>
        </div>
      )}

      {/* 错题列表 */}
      {filtered.length === 0 ? (
        <div className="glass-card rounded-xl p-8 text-center text-white/30">
          <AlertCircle className="w-10 h-10 mx-auto mb-2 opacity-30" />
          <p>{filterSubject ? `${filterSubject} 暂无错题` : '暂无错题记录'}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {unmastered.length > 0 && (
            <div>
              <p className="text-xs text-white/30 mb-2">未掌握 ({unmastered.length})</p>
              {unmastered.map(n => <ErrorNoteCard key={n.id} note={n} onToggleMastery={onToggleMastery} onDelete={onDelete} />)}
            </div>
          )}
          {mastered.length > 0 && (
            <div>
              <p className="text-xs text-white/30 mb-2">已掌握 ({mastered.length})</p>
              {mastered.map(n => <ErrorNoteCard key={n.id} note={n} onToggleMastery={onToggleMastery} onDelete={onDelete} />)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ErrorNoteCard({ note, onToggleMastery, onDelete }: { note: ErrorNote; onToggleMastery: (id: number, m: number) => Promise<void>; onDelete: (id: number) => Promise<void> }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className={`glass-card rounded-xl overflow-hidden transition-all ${note.mastery ? 'opacity-60' : ''}`}>
      <div className="flex items-start gap-3 p-3 cursor-pointer hover:bg-white/[0.02]" onClick={() => setExpanded(!expanded)}>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="px-1.5 py-0.5 bg-white/[0.06] rounded text-xs text-white/50">{note.subject}</span>
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

// ==================== 学习规划 Tab ====================

function PlanTabContent({ plans, loading, onGenerate }: { plans: StudyPlan[]; loading: boolean; onGenerate: (d: any) => Promise<any> }) {
  const [planType, setPlanType] = useState('weekly');
  const [customGoal, setCustomGoal] = useState('');
  const [examDate, setExamDate] = useState('');
  const [examSubjects, setExamSubjects] = useState('');
  const [currentPlan, setCurrentPlan] = useState<StudyPlan | null>(null);

  const handleGen = async () => {
    const data: any = { plan_type: planType };
    if (planType === 'custom') data.custom_goal = customGoal;
    if (planType === 'exam') { data.exam_date = examDate; data.exam_subjects = examSubjects.split(/[,，、]/).map(s => s.trim()).filter(Boolean); }
    const result = await onGenerate(data);
    if (result) setCurrentPlan({ ...result, plan_type: planType, semester: '' });
  };

  const display = currentPlan?.plan_data || plans[0]?.plan_data;
  const typeLabels: Record<string, string> = { weekly: '周计划', exam: '备考计划', custom: '自定义计划' };

  return (
    <div className="space-y-4">
      {/* 生成配置 */}
      <div className="glass-card rounded-xl p-4 space-y-3">
        <p className="text-sm font-medium text-white/60 flex items-center gap-2"><Zap className="w-4 h-4 text-cyan-400" /> AI 学习规划</p>
        <div className="flex gap-2">
          {[{ v: 'weekly', l: '周计划' }, { v: 'exam', l: '备考' }, { v: 'custom', l: '自定义' }].map(t => (
            <button key={t.v} onClick={() => setPlanType(t.v)}
              className={`px-3 py-1.5 rounded-lg text-sm transition-all ${planType === t.v ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-400/20' : 'bg-white/[0.04] text-white/40 hover:text-white/60'}`}>
              {t.l}
            </button>
          ))}
        </div>
        {planType === 'custom' && (
          <input value={customGoal} onChange={e => setCustomGoal(e.target.value)} placeholder="想学什么？如：学习 Rust 编程"
            className="w-full px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-400/30" />
        )}
        {planType === 'exam' && (
          <div className="grid grid-cols-2 gap-2">
            <input type="date" value={examDate} onChange={e => setExamDate(e.target.value)}
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white focus:outline-none" />
            <input value={examSubjects} onChange={e => setExamSubjects(e.target.value)} placeholder="备考科目（逗号分隔）"
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none" />
          </div>
        )}
        <button onClick={handleGen} disabled={loading}
          className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg text-sm hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
          {loading ? '生成中...' : '生成学习计划'}
        </button>
      </div>

      {/* 计划展示 */}
      {!display && !loading && (
        <div className="glass-card rounded-xl p-8 text-center text-white/30">
          <Route className="w-10 h-10 mx-auto mb-2 opacity-30" />
          <p>点击上方按钮生成 AI 学习计划</p>
          <p className="text-xs mt-1">系统将根据你的课程表、成绩和薄弱点智能规划</p>
        </div>
      )}

      {display && (
        <div className="space-y-3">
          <div className="bg-gradient-to-r from-cyan-500/15 to-blue-500/15 rounded-xl p-4 border border-cyan-400/15">
            <h4 className="font-bold text-white mb-1">{display.title}</h4>
            <p className="text-sm text-white/50">{display.summary}</p>
            {display.focus_areas?.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {display.focus_areas.map((f: string, i: number) => <span key={i} className="px-2 py-0.5 bg-cyan-400/10 text-cyan-400 rounded-full text-xs">{f}</span>)}
              </div>
            )}
          </div>

          {/* 原始文本降级 */}
          {display.raw_text && !display.daily_plans?.length && (
            <div className="glass-card rounded-xl p-4">
              <div className="text-sm text-white/70 whitespace-pre-wrap">{display.raw_text}</div>
            </div>
          )}

          {/* 每日计划 */}
          {display.daily_plans?.map((dp: any, i: number) => (
            <div key={i} className="glass-card rounded-xl overflow-hidden">
              <div className="px-4 py-2 bg-white/[0.03] border-b border-white/[0.06] flex items-center justify-between">
                <span className="text-sm font-semibold text-white">{dp.day}</span>
                <span className="text-xs text-white/30">{dp.tasks?.length || 0} 项任务</span>
              </div>
              <div className="p-3 space-y-2">
                {dp.tasks?.map((t: any, j: number) => (
                  <div key={j} className="flex items-center gap-3 px-3 py-2 bg-white/[0.02] rounded-lg">
                    <span className="text-xs text-cyan-400 font-mono shrink-0 w-20">{t.time}</span>
                    <span className="px-1.5 py-0.5 bg-white/[0.06] rounded text-xs text-white/40 shrink-0">{t.type}</span>
                    <div className="flex-1 min-w-0">
                      <span className="text-sm text-white">{t.subject}</span>
                      <span className="text-xs text-white/40 ml-2">{t.task}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* 建议 */}
          {display.tips?.length > 0 && (
            <div className="glass-card rounded-xl p-4">
              <p className="text-sm font-medium text-white/60 mb-2">💡 学习建议</p>
              <ul className="space-y-1">
                {display.tips.map((tip: string, i: number) => <li key={i} className="text-sm text-white/50 flex items-start gap-2"><span className="text-cyan-400 mt-0.5">•</span>{tip}</li>)}
              </ul>
            </div>
          )}

          {/* 历史计划 */}
          {plans.length > 1 && (
            <div className="glass-card rounded-xl p-4">
              <p className="text-sm font-medium text-white/60 mb-2">历史计划</p>
              <div className="space-y-1">
                {plans.slice(1).map((p, i) => (
                  <button key={i} onClick={() => setCurrentPlan(p)}
                    className="w-full text-left px-3 py-2 hover:bg-white/[0.03] rounded-lg flex items-center justify-between">
                    <span className="text-sm text-white/60">{p.plan_data?.title || typeLabels[p.plan_type] || p.plan_type}</span>
                    <span className="text-xs text-white/20">{p.created_at?.slice(0, 10)}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
