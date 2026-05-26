'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores';
import api from '@/lib/api';
import { generateLearningPath } from '@/lib/kimi-api';
import {
  Route, Target, Clock, CheckCircle, Circle,
  ArrowRight, Loader2, Sparkles, TrendingUp
} from 'lucide-react';

interface PathStep {
  step_number: number;
  title: string;
  description: string;
  estimated_time: string;
  resources: string[];
  prerequisites: string[];
}

interface LearningPath {
  goal: string;
  total_steps: number;
  estimated_duration: string;
  steps: PathStep[];
}

export default function LearningPathPage() {
  const router = useRouter();
  const { user, isGuest } = useAuthStore();
  const [learningGoal, setLearningGoal] = useState('掌握深度学习基础');
  const [loading, setLoading] = useState(false);
  const [path, setPath] = useState<LearningPath | null>(null);

  const generatePath = async () => {
    setLoading(true);

    try {
      console.log('🚀 开始生成学习路径:', { learningGoal });
      
      // 前端直接调用AI生成学习路径
      const pathData = await generateLearningPath(learningGoal);
      
      console.log('✅ 学习路径生成成功:', pathData);
      
      setPath(pathData);
    } catch (err: any) {
      console.error('生成路径失败:', err);
      alert('生成路径失败：' + (err.message || '网络错误'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* 页面标题 */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center">
            <Route className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-800">个性化学习路径规划</h1>
            <p className="text-sm text-gray-500">
              基于学生画像，智能规划科学的学习路径
            </p>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 左侧：配置 */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-white rounded-2xl shadow-card p-6"
        >
          <h2 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Target className="w-5 h-5 text-orange-500" />
            学习目标
          </h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                学习目标
              </label>
              <textarea
                value={learningGoal}
                onChange={(e) => setLearningGoal(e.target.value)}
                rows={4}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-orange-500 text-sm resize-none"
                placeholder="描述您的学习目标..."
                disabled={loading || isGuest}
              />
            </div>

            <button
              onClick={generatePath}
              disabled={loading || isGuest || !learningGoal.trim()}
              className="w-full px-4 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed font-medium flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  规划中...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  生成学习路径
                </>
              )}
            </button>
          </div>

          {/* 提示信息 */}
          <div className="mt-6 p-4 bg-orange-50 rounded-xl">
            <h4 className="text-sm font-semibold text-orange-800 mb-2">💡 提示</h4>
            <ul className="text-xs text-orange-700 space-y-1">
              <li>• 基于您的画像特征定制路径</li>
              <li>• 考虑知识点的前置依赖关系</li>
              <li>• 提供预计学习时间</li>
              <li>• 支持动态调整和进度追踪</li>
            </ul>
          </div>
        </motion.div>

        {/* 右侧：路径展示 */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="lg:col-span-2"
        >
          {!path ? (
            <div className="bg-white rounded-2xl shadow-card p-12 text-center">
              <Route className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <h3 className="text-lg font-semibold text-gray-600 mb-2">
                准备生成学习路径
              </h3>
              <p className="text-sm text-gray-500">
                设置学习目标后，点击"生成学习路径"按钮
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* 路径概览 */}
              <div className="bg-gradient-to-r from-orange-500 to-red-500 rounded-2xl p-6 text-white">
                <h3 className="text-xl font-bold mb-2">{path.goal}</h3>
                <div className="flex items-center gap-6 text-sm">
                  <div className="flex items-center gap-2">
                    <Route className="w-4 h-4" />
                    <span>{path.total_steps} 个学习步骤</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    <span>预计 {path.estimated_duration}</span>
                  </div>
                </div>
              </div>

              {/* 路径步骤 */}
              <div className="bg-white rounded-2xl shadow-card p-6">
                <h3 className="font-bold text-gray-800 mb-6 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-orange-500" />
                  学习路径步骤
                </h3>

                <div className="space-y-4">
                  {path.steps.map((step, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.1 }}
                      className="relative pl-8 pb-6 border-l-2 border-gray-200 last:border-0 last:pb-0"
                    >
                      {/* 步骤编号 */}
                      <div className="absolute left-0 top-0 -translate-x-1/2 w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center text-white text-sm font-bold">
                        {step.step_number}
                      </div>

                      {/* 步骤内容 */}
                      <div className="bg-gray-50 rounded-xl p-4">
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="font-semibold text-gray-800">{step.title}</h4>
                          <span className="text-xs text-orange-600 bg-orange-50 px-2 py-1 rounded-full flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {step.estimated_time}
                          </span>
                        </div>

                        <p className="text-sm text-gray-600 mb-3">{step.description}</p>

                        {/* 关联资源 */}
                        {step.resources && step.resources.length > 0 && (
                          <div className="mb-2">
                            <span className="text-xs font-medium text-gray-700">推荐资源：</span>
                            <div className="flex flex-wrap gap-2 mt-1">
                              {step.resources.map((resource, rIdx) => (
                                <span key={rIdx} className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded">
                                  {resource}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* 前置要求 */}
                        {step.prerequisites && step.prerequisites.length > 0 && (
                          <div>
                            <span className="text-xs font-medium text-gray-700">前置知识：</span>
                            <div className="flex flex-wrap gap-2 mt-1">
                              {step.prerequisites.map((prereq, pIdx) => (
                                <span key={pIdx} className="text-xs bg-purple-50 text-purple-700 px-2 py-1 rounded">
                                  {prereq}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* 操作按钮 */}
              <div className="flex gap-3">
                <button className="flex-1 px-4 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl hover:opacity-90 transition-opacity font-medium flex items-center justify-center gap-2">
                  <CheckCircle className="w-5 h-5" />
                  开始学习
                </button>
                <button className="px-4 py-3 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors font-medium">
                  导出路径
                </button>
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
