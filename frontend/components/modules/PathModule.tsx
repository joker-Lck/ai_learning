'use client';

import { useState } from 'react';
import { Route, Loader2, Clock, Zap, CalendarDays, BookOpen } from 'lucide-react';
import type { LearningPath, StudyPlan } from './types';

interface PathModuleProps {
  learningGoal: string;
  setLearningGoal: (v: string) => void;
  pathLoading: boolean;
  learningPath: LearningPath | null;
  handlePlanPath: () => void;
  // 学习规划
  studyPlans: StudyPlan[];
  planLoading: boolean;
  handleGeneratePlan: (data: { plan_type: string; custom_goal?: string; exam_date?: string; exam_subjects?: string[] }) => Promise<any>;
}

type PathTab = 'path' | 'plan';

export default function PathModule({
  learningGoal, setLearningGoal, pathLoading, learningPath, handlePlanPath,
  studyPlans, planLoading, handleGeneratePlan,
}: PathModuleProps) {
  const [tab, setTab] = useState<PathTab>('path');

  return (
    <div className="space-y-4">
      {/* 标题 */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
          <Route className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-xl font-bold text-white">学习路径与规划</h3>
          <p className="text-sm text-white/40">AI 路径推荐 · 智能学习计划</p>
        </div>
      </div>

      {/* Tab 切换 */}
      <div className="flex gap-1 bg-white/[0.03] rounded-xl p-1">
        <button onClick={() => setTab('path')}
          className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-sm font-medium transition-all ${tab === 'path' ? 'bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-amber-400 border border-amber-400/20' : 'text-white/40 hover:text-white/60 hover:bg-white/[0.03]'}`}>
          <BookOpen className="w-4 h-4" /> 学习路径
        </button>
        <button onClick={() => setTab('plan')}
          className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-sm font-medium transition-all ${tab === 'plan' ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-400 border border-cyan-400/20' : 'text-white/40 hover:text-white/60 hover:bg-white/[0.03]'}`}>
          <CalendarDays className="w-4 h-4" /> 学习规划
        </button>
      </div>

      {/* 内容 */}
      {tab === 'path' && <PathTabContent learningGoal={learningGoal} setLearningGoal={setLearningGoal} pathLoading={pathLoading} learningPath={learningPath} handlePlanPath={handlePlanPath} />}
      {tab === 'plan' && <PlanTabContent plans={studyPlans} loading={planLoading} onGenerate={handleGeneratePlan} />}
    </div>
  );
}

// ==================== 学习路径 Tab ====================

function PathTabContent({ learningGoal, setLearningGoal, pathLoading, learningPath, handlePlanPath }: Pick<PathModuleProps, 'learningGoal' | 'setLearningGoal' | 'pathLoading' | 'learningPath' | 'handlePlanPath'>) {
  return (
    <div className="space-y-4">
      <div className="glass-card rounded-xl p-4 space-y-4">
        <div>
          <label className="block text-sm font-medium text-white/60 mb-1">学习目标</label>
          <input
            type="text"
            value={learningGoal}
            onChange={(e) => setLearningGoal(e.target.value)}
            placeholder="输入你的学习目标..."
            className="w-full px-3 py-2 bg-white/[0.04] border border-white/[0.08] text-white placeholder:text-white/15 rounded-lg focus:border-cyan-400/30 focus:outline-none"
          />
        </div>
        <button
          onClick={handlePlanPath}
          disabled={pathLoading || !learningGoal.trim()}
          className="w-full py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold"
        >
          {pathLoading ? (
            <><Loader2 className="w-5 h-5 animate-spin" /> 规划中...</>
          ) : (
            <><Route className="w-5 h-5" /> 生成学习路径</>
          )}
        </button>
      </div>

      {learningPath && (
        <div className="glass-card rounded-xl p-4 border-amber-400/20">
          <h4 className="font-bold text-amber-400 mb-3">学习路径: {learningPath.goal}</h4>
          <div className="text-sm text-white/60 mb-3">
            预计时长: {learningPath.estimated_duration} | 步骤数: {learningPath.total_steps}
          </div>
          <div className="space-y-3">
            {learningPath.steps.map((step, idx) => (
              <div key={idx} className="glass-card rounded-lg p-3">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 text-white flex items-center justify-center font-bold text-sm">
                    {step.step_number}
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-white">{step.title}</div>
                    <div className="text-sm text-white/60">{step.description}</div>
                  </div>
                  <div className="flex items-center gap-1 text-sm text-white/40">
                    <Clock className="w-4 h-4" /> {step.estimated_time}
                  </div>
                </div>
                {step.prerequisites.length > 0 && (
                  <div className="text-xs text-white/30 ml-10">前置知识: {step.prerequisites.join(', ')}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ==================== 学习规划 Tab ====================

function PlanTabContent({ plans, loading, onGenerate }: { plans: StudyPlan[]; loading: boolean; onGenerate: (d: any) => Promise<any> }) {
  const [planType, setPlanType] = useState('weekly');
  const [requirements, setRequirements] = useState('');
  const [examDate, setExamDate] = useState('');
  const [examSubjects, setExamSubjects] = useState('');
  const [currentPlan, setCurrentPlan] = useState<StudyPlan | null>(null);

  const handleGen = async () => {
    const data: any = { plan_type: planType, user_requirements: requirements.trim() };
    if (planType === 'exam') { data.exam_date = examDate; data.exam_subjects = examSubjects.split(/[,，、]/).map(s => s.trim()).filter(Boolean); }
    const result = await onGenerate(data);
    if (result) setCurrentPlan({ ...result, plan_type: planType, semester: '' });
  };

  const display = currentPlan?.plan_data || plans[0]?.plan_data;
  const typeLabels: Record<string, string> = { weekly: '周计划', exam: '备考计划', custom: '自定义计划' };

  const presets = [
    { label: '帮我制定一周的学习安排', type: 'weekly' },
    { label: '期末考试快到了，帮我备考', type: 'exam' },
    { label: '我想利用课余学一门新技能', type: 'custom' },
  ];

  return (
    <div className="space-y-4">
      {/* 需求输入 */}
      <div className="glass-card rounded-xl p-4 space-y-3">
        <p className="text-sm font-medium text-white/60 flex items-center gap-2"><Zap className="w-4 h-4 text-cyan-400" /> 描述你的学习需求</p>

        {/* 快捷预设 */}
        <div className="flex flex-wrap gap-2">
          {presets.map(p => (
            <button key={p.type} onClick={() => { setPlanType(p.type); setRequirements(p.label); }}
              className={`px-3 py-1.5 rounded-lg text-xs transition-all ${requirements === p.label ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-400/20' : 'bg-white/[0.04] text-white/40 hover:text-white/60'}`}>
              {p.label}
            </button>
          ))}
        </div>

        {/* 主输入框 */}
        <textarea
          value={requirements}
          onChange={e => setRequirements(e.target.value)}
          rows={3}
          placeholder="描述你的学习需求，越详细越好&#10;例如：下周三有数据结构期中考试，这周每天晚上有 2 小时空闲，请帮我制定复习计划"
          className="w-full px-3 py-2.5 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-400/30 resize-none leading-relaxed"
        />

        {/* 备考补充 */}
        {planType === 'exam' && (
          <div className="grid grid-cols-2 gap-2">
            <input type="date" value={examDate} onChange={e => setExamDate(e.target.value)}
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white focus:outline-none [&>option]:bg-[#0f1a30]" />
            <input value={examSubjects} onChange={e => setExamSubjects(e.target.value)} placeholder="备考科目（逗号分隔）"
              className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none" />
          </div>
        )}

        <button onClick={handleGen} disabled={loading || !requirements.trim()}
          className="w-full py-2.5 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg text-sm hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
          {loading ? 'AI 规划中...' : '生成学习计划'}
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
