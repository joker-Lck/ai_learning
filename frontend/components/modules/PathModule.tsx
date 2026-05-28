'use client';

import { Route, Loader2, Clock } from 'lucide-react';
import type { LearningPath } from './types';

interface PathModuleProps {
  learningGoal: string;
  setLearningGoal: (v: string) => void;
  pathLoading: boolean;
  learningPath: LearningPath | null;
  handlePlanPath: () => void;
}

export default function PathModule({
  learningGoal, setLearningGoal, pathLoading, learningPath, handlePlanPath,
}: PathModuleProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-white">个性化学习路径规划</h3>

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
