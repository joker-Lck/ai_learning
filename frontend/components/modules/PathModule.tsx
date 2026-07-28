'use client';

import { useState, memo } from 'react';
import { Router, Loader2, Clock, Zap, CalendarDays, BookOpen, Sparkles } from 'lucide-react';
import type { LearningPath, StudyPlan } from './types';
import type { ModuleType, NavigationContext } from './types';

interface PathModuleProps {
  learningGoal: string;
  setLearningGoal: (v: string) => void;
  pathLoading: boolean;
  learningPath: LearningPath | null;
  handlePlanPath: () => void;
  pathStreamContent?: string;
  studyPlans: StudyPlan[];
  planLoading: boolean;
  handleGeneratePlan: (data: { plan_type: string; custom_goal?: string; exam_date?: string; exam_subjects?: string[] }) => Promise<any>;
  onNavigateModule?: (m: ModuleType, ctx?: NavigationContext) => void;
}

export default memo(function PathModule({
  learningGoal, setLearningGoal, pathLoading, learningPath, handlePlanPath, pathStreamContent,
  studyPlans, planLoading, handleGeneratePlan, onNavigateModule,
}: PathModuleProps) {
  const [planType, setPlanType] = useState('weekly');
  const [examDate, setExamDate] = useState('');
  const [examSubjects, setExamSubjects] = useState('');
  const [currentPlan, setCurrentPlan] = useState<StudyPlan | null>(null);
  const [generated, setGenerated] = useState(false);

  const loading = pathLoading || planLoading;

  // 同时生成路径和规划
  const handleGenerateAll = async () => {
    if (!learningGoal.trim()) return;
    setGenerated(true);

    // 并行触发
    handlePlanPath();
    const planData: any = { plan_type: planType, user_requirements: learningGoal.trim() };
    if (planType === 'exam') {
      planData.exam_date = examDate;
      planData.exam_subjects = examSubjects.split(/[,，、]/).map(s => s.trim()).filter(Boolean);
    }
    const result = await handleGeneratePlan(planData);
    if (result) setCurrentPlan({ ...result, plan_type: planType, semester: '' });
  };

  const display = currentPlan?.plan_data || studyPlans[0]?.plan_data;
  const typeLabels: Record<string, string> = { weekly: '周计划', exam: '备考计划', custom: '自定义计划' };

  const presets = [
    { label: '帮我制定一周的学习安排', type: 'weekly' },
    { label: '期末考试快到了，帮我备考', type: 'exam' },
    { label: '我想利用课余学一门新技能', type: 'custom' },
  ];

  return (
    <div className="space-y-8">
      {/* 标题 */}
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-lg bg-purple-500/15 flex items-center justify-center">
          <Router className="w-5 h-5 text-purple-400" />
        </div>
        <div>
          <h3 className="text-3xl font-bold text-white">学习路径与规划</h3>
          <p className="text-base text-white/35">输入目标，AI 同时生成路径和计划</p>
        </div>
      </div>

      {/* 统一输入区 */}
      <div className="border border-white/[0.06] rounded-lg p-5 bg-white/[0.02] space-y-4">
        {/* 学习目标 */}
        <div>
          <label className="block text-sm font-medium text-white/60 mb-2">学习目标</label>
          <input
            type="text"
            value={learningGoal}
            onChange={(e) => setLearningGoal(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !loading && handleGenerateAll()}
            placeholder="例如：掌握 Python 数据分析、通过期末高等数学考试..."
            className="w-full px-4 py-3 bg-white/[0.04] border border-white/[0.06] text-white placeholder:text-white/20 rounded-lg text-base focus:border-purple-500/30 focus:outline-none"
          />
        </div>

        {/* 快捷预设 */}
        <div className="flex flex-wrap gap-2">
          {presets.map(p => (
            <button key={p.type} onClick={() => { setPlanType(p.type); setLearningGoal(p.label); }}
              className={`px-3 py-1.5 rounded-lg text-xs transition-all ${learningGoal === p.label ? 'bg-purple-500/20 text-purple-400 border border-purple-400/20' : 'bg-white/[0.04] text-white/40 hover:text-white/60'}`}>
              {p.label}
            </button>
          ))}
        </div>

        {/* 备考补充 */}
        {planType === 'exam' && (
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-white/50 mb-1">考试日期</label>
              <input type="date" value={examDate} onChange={e => setExamDate(e.target.value)}
                className="w-full px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white focus:outline-none" />
            </div>
            <div>
              <label className="block text-xs text-white/50 mb-1">备考科目</label>
              <input value={examSubjects} onChange={e => setExamSubjects(e.target.value)} placeholder="逗号分隔"
                className="w-full px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/20 focus:outline-none" />
            </div>
          </div>
        )}

        {/* 生成按钮 */}
        <button
          onClick={handleGenerateAll}
          disabled={loading || !learningGoal.trim()}
          className="w-full py-3.5 bg-purple-500 text-white rounded-lg hover:bg-purple-400 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold text-base transition-colors"
        >
          {loading ? (
            <><Loader2 className="w-5 h-5 animate-spin" /> AI 生成中...</>
          ) : (
            <><Sparkles className="w-5 h-5" /> 生成路径与规划</>
          )}
        </button>
      </div>

      {/* 结果展示 */}
      {generated && (
        <div className="space-y-8">
          {/* 学习路径结果 */}
          <div className="space-y-4">
            <h4 className="text-lg font-semibold text-white flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-amber-400" />
              学习路径
            </h4>

            {pathLoading && (
              <div className="border border-white/[0.06] rounded-lg p-6 bg-white/[0.02]">
                <div className="flex items-center gap-2 mb-3">
                  <Loader2 className="w-5 h-5 text-amber-400 animate-spin" />
                  <p className="text-sm text-amber-400">正在生成学习路径...</p>
                </div>
                {pathStreamContent && (
                  <pre className="text-xs text-white/30 max-h-40 overflow-auto whitespace-pre-wrap font-mono border-t border-white/[0.04] pt-3">{pathStreamContent.slice(-500)}</pre>
                )}
              </div>
            )}

            {learningPath && (
              <div className="border border-white/[0.06] rounded-lg p-4 bg-white/[0.02] border-amber-400/20">
                <h4 className="font-bold text-amber-400 mb-3">{learningPath.goal}</h4>
                <div className="text-sm text-white/60 mb-3">
                  预计时长: {learningPath.estimated_duration} | 步骤数: {learningPath.total_steps}
                </div>
                <div className="space-y-3">
                  {learningPath.steps.map((step, idx) => (
                    <div key={idx} className="border border-white/[0.06] rounded-lg p-3 bg-white/[0.02]">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-6 h-6 rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center font-semibold text-[10px]">
                          {step.step_number}
                        </div>
                        <div className="flex-1">
                          <div className="font-semibold text-white text-sm">{step.title}</div>
                          <div className="text-xs text-white/50">{step.description}</div>
                        </div>
                        <div className="flex items-center gap-1 text-xs text-white/35">
                          <Clock className="w-3.5 h-3.5" /> {step.estimated_time}
                        </div>
                      </div>
                      {step.prerequisites.length > 0 && (
                        <div className="text-[11px] text-white/25 ml-8">前置知识: {step.prerequisites.join(', ')}</div>
                      )}
                    </div>
                  ))}
                </div>
                {onNavigateModule && (
                  <button
                    onClick={() => onNavigateModule('resources', { topic: learningPath.goal, autoPlan: true })}
                    className="w-full mt-3 py-3 bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-400/20 text-purple-400 rounded-lg hover:from-purple-500/30 hover:to-pink-500/30 flex items-center justify-center gap-2 text-sm font-medium transition-all"
                  >
                    <Sparkles className="w-4 h-4" />
                    为这条路径生成配套资源
                  </button>
                )}
              </div>
            )}
          </div>

          {/* 学习规划结果 */}
          <div className="space-y-4">
            <h4 className="text-lg font-semibold text-white flex items-center gap-2">
              <CalendarDays className="w-5 h-5 text-purple-400" />
              学习规划
            </h4>

            {planLoading && (
              <div className="border border-white/[0.06] rounded-lg p-6 text-center bg-white/[0.02]">
                <Loader2 className="w-6 h-6 text-purple-400 animate-spin mx-auto mb-2" />
                <p className="text-sm text-white/40">正在生成学习计划...</p>
              </div>
            )}

            {display && !planLoading && (
              <div className="space-y-3">
                <div className="bg-purple-500/10 rounded-xl p-4 border border-purple-400/15">
                  <h4 className="font-bold text-white mb-1">{display.title}</h4>
                  <p className="text-sm text-white/50">{display.summary}</p>
                  {display.focus_areas?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {display.focus_areas.map((f: string, i: number) => <span key={i} className="px-2 py-0.5 bg-purple-400/10 text-purple-400 rounded-full text-xs">{f}</span>)}
                    </div>
                  )}
                </div>

                {display.raw_text && !display.daily_plans?.length && (
                  <div className="border border-white/[0.06] rounded-lg p-4 bg-white/[0.02]">
                    <div className="text-sm text-white/70 whitespace-pre-wrap leading-relaxed">
                      {display.raw_text.replace(/```json\s*/g, '').replace(/```\s*/g, '')}
                    </div>
                  </div>
                )}

                {display.daily_plans?.map((dp: any, i: number) => (
                  <div key={i} className="border border-white/[0.06] rounded-lg overflow-hidden bg-white/[0.02]">
                    <div className="px-4 py-2 bg-white/[0.03] border-b border-white/[0.06] flex items-center justify-between">
                      <span className="text-sm font-semibold text-white">{dp.day}</span>
                      <span className="text-xs text-white/30">{dp.tasks?.length || 0} 项任务</span>
                    </div>
                    <div className="p-3 space-y-2">
                      {dp.tasks?.map((t: any, j: number) => (
                        <div key={j} className="flex items-center gap-3 px-3 py-2 bg-white/[0.02] rounded-lg">
                          <span className="text-xs text-purple-400 font-mono shrink-0 w-16">{t.time}</span>
                          <span className="px-1.5 py-0.5 bg-white/[0.04] rounded text-[10px] text-white/35 shrink-0">{t.type}</span>
                          <div className="flex-1 min-w-0">
                            <span className="text-sm text-white">{t.subject}</span>
                            <span className="text-xs text-white/40 ml-2">{t.task}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}

                {display.tips?.length > 0 && (
                  <div className="border border-white/[0.06] rounded-lg p-4 bg-white/[0.02]">
                    <p className="text-sm font-medium text-white/50 mb-2">学习建议</p>
                    <ul className="space-y-1">
                      {display.tips.map((tip: string, i: number) => <li key={i} className="text-xs text-white/45 flex items-start gap-2"><span className="text-purple-400 mt-0.5">•</span>{tip}</li>)}
                    </ul>
                  </div>
                )}

                {studyPlans.length > 1 && (
                  <div className="border border-white/[0.06] rounded-lg p-4 bg-white/[0.02]">
                    <p className="text-sm font-medium text-white/50 mb-2">历史计划</p>
                    <div className="space-y-1">
                      {studyPlans.slice(1).map((p, i) => (
                        <button key={i} onClick={() => setCurrentPlan(p)}
                          className="w-full text-left px-3 py-2 hover:bg-white/[0.03] rounded-lg flex items-center justify-between">
                          <span className="text-xs text-white/50">{p.plan_data?.title || typeLabels[p.plan_type] || p.plan_type}</span>
                          <span className="text-[10px] text-white/20">{p.created_at?.slice(0, 10)}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* 未生成时的提示 */}
      {!generated && (
        <div className="border border-white/[0.06] rounded-lg p-8 text-center text-white/25 bg-white/[0.02]">
          <Sparkles className="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p className="text-sm">输入学习目标，一键生成路径和计划</p>
          <p className="text-xs mt-1">AI 将同时为你规划学习路径和制定详细计划</p>
        </div>
      )}
    </div>
  );
});
