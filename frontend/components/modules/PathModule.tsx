'use client';

import { useState, memo } from 'react';
import { Router, Loader2, Clock, CalendarDays, BookOpen, Sparkles, Zap } from 'lucide-react';
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
  const [generated, setGenerated] = useState(false);
  const [planResult, setPlanResult] = useState<any>(null);

  const loading = pathLoading || planLoading;

  const handleGenerateAll = async () => {
    if (!learningGoal.trim()) return;
    setGenerated(true);
    setPlanResult(null);

    // 并行触发
    handlePlanPath();
    const planData: any = { plan_type: planType, user_requirements: learningGoal.trim() };
    if (planType === 'exam') {
      planData.exam_date = examDate;
      planData.exam_subjects = examSubjects.split(/[,，、]/).map(s => s.trim()).filter(Boolean);
    }
    const result = await handleGeneratePlan(planData);
    if (result) setPlanResult(result);
  };

  // 从多个来源取计划数据
  const plan = planResult || studyPlans[0]?.plan_data || null;

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

      {/* 输入区 */}
      <div className="border border-white/[0.06] rounded-lg p-5 bg-white/[0.02] space-y-4">
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

        <div className="flex flex-wrap gap-2">
          {presets.map(p => (
            <button key={p.type} onClick={() => { setPlanType(p.type); setLearningGoal(p.label); }}
              className={`px-3 py-1.5 rounded-lg text-xs transition-all ${learningGoal === p.label ? 'bg-purple-500/20 text-purple-400 border border-purple-400/20' : 'bg-white/[0.04] text-white/40 hover:text-white/60'}`}>
              {p.label}
            </button>
          ))}
        </div>

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

      {/* 结果：路径 + 规划合并展示 */}
      {generated && (
        <div className="space-y-6">
          {/* 加载状态 */}
          {loading && (
            <div className="border border-white/[0.06] rounded-lg p-6 bg-white/[0.02]">
              <div className="flex items-center gap-2 mb-3">
                <Loader2 className="w-5 h-5 text-purple-400 animate-spin" />
                <p className="text-sm text-purple-400">AI 正在规划学习路径和计划...</p>
              </div>
              {pathStreamContent && (
                <pre className="text-xs text-white/30 max-h-32 overflow-auto whitespace-pre-wrap font-mono border-t border-white/[0.04] pt-3">{pathStreamContent.slice(-400)}</pre>
              )}
            </div>
          )}

          {/* 路径步骤 + 计划合并卡片 */}
          {(learningPath || plan) && !loading && (
            <div className="border border-white/[0.06] rounded-xl bg-white/[0.02] overflow-hidden">
              {/* 标题区 */}
              <div className="px-6 py-4 bg-gradient-to-r from-amber-500/5 to-purple-500/5 border-b border-white/[0.06]">
                <h4 className="font-bold text-white text-lg">{learningPath?.goal || plan?.title || learningGoal}</h4>
                <div className="flex items-center gap-4 mt-1 text-sm text-white/50">
                  {learningPath && <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> {learningPath.estimated_duration}</span>}
                  {learningPath && <span>{learningPath.total_steps} 个步骤</span>}
                  {plan?.focus_areas?.length > 0 && (
                    <div className="flex gap-1.5 ml-2">
                      {plan.focus_areas.slice(0, 3).map((f: string, i: number) => (
                        <span key={i} className="px-2 py-0.5 bg-purple-400/10 text-purple-400 rounded-full text-xs">{f}</span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* 路径步骤 */}
              {learningPath && learningPath.steps.length > 0 && (
                <div className="px-6 py-4 border-b border-white/[0.04]">
                  <div className="flex items-center gap-2 mb-3">
                    <BookOpen className="w-4 h-4 text-amber-400" />
                    <span className="text-sm font-semibold text-white">学习路径</span>
                  </div>
                  <div className="space-y-2">
                    {learningPath.steps.map((step, idx) => (
                      <div key={idx} className="flex items-start gap-3 px-3 py-2.5 rounded-lg bg-white/[0.02] hover:bg-white/[0.04] transition-colors">
                        <div className="w-6 h-6 rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center font-semibold text-[10px] shrink-0 mt-0.5">
                          {step.step_number}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-white text-sm">{step.title}</div>
                          <div className="text-xs text-white/50 mt-0.5">{step.description}</div>
                          {step.prerequisites.length > 0 && (
                            <div className="text-[11px] text-white/25 mt-1">前置: {step.prerequisites.join(', ')}</div>
                          )}
                        </div>
                        <div className="flex items-center gap-1 text-xs text-white/35 shrink-0">
                          <Clock className="w-3 h-3" /> {step.estimated_time}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 学习计划 */}
              {plan && (
                <div className="px-6 py-4">
                  <div className="flex items-center gap-2 mb-3">
                    <CalendarDays className="w-4 h-4 text-purple-400" />
                    <span className="text-sm font-semibold text-white">学习规划</span>
                    {plan.summary && <span className="text-xs text-white/30 ml-2">{plan.summary}</span>}
                  </div>

                  {/* 有结构化每日计划 */}
                  {plan.daily_plans?.length > 0 && (
                    <div className="space-y-2">
                      {plan.daily_plans.map((dp: any, i: number) => (
                        <div key={i} className="border border-white/[0.04] rounded-lg overflow-hidden">
                          <div className="px-3 py-2 bg-white/[0.02] border-b border-white/[0.04] flex items-center justify-between">
                            <span className="text-xs font-semibold text-white">{dp.day}</span>
                            <span className="text-[10px] text-white/25">{dp.tasks?.length || 0} 项</span>
                          </div>
                          <div className="p-2 space-y-1">
                            {dp.tasks?.map((t: any, j: number) => (
                              <div key={j} className="flex items-center gap-2 px-2 py-1.5 text-xs">
                                <span className="text-purple-400 font-mono shrink-0 w-14">{t.time}</span>
                                <span className="px-1.5 py-0.5 bg-white/[0.04] rounded text-[10px] text-white/30 shrink-0">{t.type}</span>
                                <span className="text-white/80 flex-1">{t.subject}</span>
                                <span className="text-white/40">{t.task}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* 无结构化数据，显示原始文本 */}
                  {plan.raw_text && !plan.daily_plans?.length && (
                    <div className="text-sm text-white/60 whitespace-pre-wrap leading-relaxed bg-white/[0.02] rounded-lg p-4">
                      {plan.raw_text.replace(/```json\s*/g, '').replace(/```\s*/g, '')}
                    </div>
                  )}

                  {/* 学习建议 */}
                  {plan.tips?.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-white/[0.04]">
                      <p className="text-xs font-medium text-white/40 mb-2">学习建议</p>
                      <ul className="space-y-1">
                        {plan.tips.map((tip: string, i: number) => (
                          <li key={i} className="text-xs text-white/45 flex items-start gap-2">
                            <Zap className="w-3 h-3 text-purple-400 mt-0.5 shrink-0" />{tip}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* 生成配套资源按钮 */}
              {onNavigateModule && learningPath && (
                <div className="px-6 pb-4">
                  <button
                    onClick={() => onNavigateModule('resources', { topic: learningPath.goal, autoPlan: true })}
                    className="w-full py-3 bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-400/20 text-purple-400 rounded-lg hover:from-purple-500/30 hover:to-pink-500/30 flex items-center justify-center gap-2 text-sm font-medium transition-all"
                  >
                    <Sparkles className="w-4 h-4" />
                    为这条路径生成配套资源
                  </button>
                </div>
              )}
            </div>
          )}
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
