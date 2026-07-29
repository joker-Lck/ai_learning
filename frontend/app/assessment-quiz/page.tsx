'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAuthStore } from '@/stores';
import api from '@/lib/api';
import { GraduationCap, CheckCircle, ArrowRight, Loader2 } from 'lucide-react';

interface Question {
  id: number;
  type: string;
  dimension: string;
  question: string;
  options: string[];
  mapping: Record<string, string>;
}

const dimensionLabels: Record<string, string> = {
  knowledge_base: '知识基础',
  cognitive_style: '认知风格',
  learning_goals: '学习目标',
  interest_areas: '兴趣领域',
  preferred_resources: '资源偏好',
  learning_history: '学习历史',
  weak_points: '学习难点',
  major: '专业方向',
  grade_level: '年级',
};

export default function AssessmentQuizPage() {
  const { token, restoreAuth } = useAuthStore();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [currentStep, setCurrentStep] = useState(0); // 0: quiz, 1: result

  useEffect(() => {
    // 从 localStorage 恢复认证状态
    restoreAuth();
  }, []);

  useEffect(() => {
    if (!token) {
      // 尝试从 localStorage 直接读取
      const stored = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
      if (!stored) {
        window.location.href = '/';
        return;
      }
    }
    // 检查是否已有画像，有则直接跳转
    checkExistingProfile();
  }, [token]);

  const checkExistingProfile = async () => {
    try {
      const res: any = await api.getProfile();
      if (res.success && res.data?.has_profile) {
        // 已有真实画像，直接跳转到 dashboard
        window.location.href = '/dashboard';
        return;
      }
    } catch {}
    // 没有画像，加载评估题目
    loadQuiz();
  };

  const loadQuiz = async () => {
    try {
      const res: any = await api.getProfileAssessmentQuiz();
      if (res.success) {
        setQuestions(res.data.questions || []);
      }
    } catch (err) {
      console.error('加载评估题目失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (questionId: number, answer: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: answer }));
  };

  const allAnswered = questions.length > 0 && questions.every(q => answers[q.id]);

  const handleSubmit = async () => {
    if (!allAnswered) return;
    setSubmitting(true);
    try {
      const res: any = await api.submitProfileAssessment(answers);
      if (res.success) {
        setResult(res.data);
        setCompleted(true);
        setCurrentStep(1);
      }
    } catch (err) {
      console.error('提交评估失败:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleGoDashboard = () => {
    window.location.href = '/dashboard';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-purple-400 animate-spin mx-auto mb-4" />
          <p className="text-white/40 text-sm">加载评估题目...</p>
        </div>
      </div>
    );
  }

  if (completed && result) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center p-4">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-lg bg-[#1a1a27] rounded-2xl border border-white/[0.05] p-8 text-center">
          <div className="w-16 h-16 rounded-2xl bg-emerald-500/20 flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-8 h-8 text-emerald-400" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">画像评估完成！</h2>
          <p className="text-white/40 text-sm mb-6">{result.message || '已根据你的回答生成个性化学习画像'}</p>

          {result.profile && (
            <div className="bg-white/[0.02] rounded-xl p-4 mb-6 text-left space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-white/50">知识水平</span>
                <span className="text-sm text-purple-400 font-medium">
                  {typeof result.profile.knowledge_base === 'object' ? result.profile.knowledge_base.level : result.profile.knowledge_base || '待评估'}
                </span>
              </div>
              {result.profile.interest_areas?.length > 0 && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white/50">兴趣方向</span>
                  <span className="text-sm text-cyan-400">{result.profile.interest_areas.slice(0, 3).join('、')}</span>
                </div>
              )}
              {result.profile.learning_goals?.length > 0 && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white/50">学习目标</span>
                  <span className="text-sm text-amber-400">{result.profile.learning_goals.slice(0, 2).join('、')}</span>
                </div>
              )}
              {result.profile.major && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white/50">专业</span>
                  <span className="text-sm text-white/70">{result.profile.major}</span>
                </div>
              )}
              {result.profile.grade_level && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white/50">年级</span>
                  <span className="text-sm text-white/70">{result.profile.grade_level}</span>
                </div>
              )}
            </div>
          )}

          <button onClick={handleGoDashboard}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-500 to-violet-500 text-white font-medium text-sm hover:from-purple-600 hover:to-violet-600 transition-all flex items-center justify-center gap-2">
            进入学习工作台 <ArrowRight className="w-4 h-4" />
          </button>
        </motion.div>
      </div>
    );
  }

  const answeredCount = Object.keys(answers).length;

  return (
    <div className="min-h-screen bg-[#0a0a0a] py-8 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center mx-auto mb-4">
            <GraduationCap className="w-6 h-6 text-purple-400" />
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">学习能力评估</h1>
          <p className="text-white/40 text-sm">回答以下问题，帮助我们了解你的学习特点，为你生成个性化学习方案</p>
        </div>

        {/* Progress */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-white/40">已完成 {answeredCount}/{questions.length} 题</span>
            <span className="text-xs text-white/40">{Math.round(answeredCount / questions.length * 100)}%</span>
          </div>
          <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-purple-500 to-violet-500 rounded-full transition-all duration-500"
              style={{ width: `${(answeredCount / questions.length) * 100}%` }} />
          </div>
        </div>

        {/* Questions */}
        <div className="space-y-4 mb-8">
          {questions.map((q, i) => {
            const dimLabel = dimensionLabels[q.dimension] || q.dimension;
            const isAnswered = !!answers[q.id];
            return (
              <motion.div key={q.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.03, duration: 0.3 }}
                className={`bg-[#1a1a27] rounded-xl border p-5 transition-all ${isAnswered ? 'border-purple-500/20' : 'border-white/[0.05]'}`}>
                <div className="flex items-start gap-3 mb-4">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400 shrink-0 mt-0.5">{dimLabel}</span>
                  <p className="text-white text-sm leading-relaxed">{i + 1}. {q.question}</p>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {q.options.map((opt, j) => {
                    const optLabel = String.fromCharCode(65 + j);
                    const optText = opt.replace(/^[A-D][.、.]\s*/, '');
                    const isSelected = answers[q.id] === optLabel;
                    return (
                      <button key={j} onClick={() => handleSelect(q.id, optLabel)}
                        className={`p-3 rounded-lg border text-left text-sm transition-all ${isSelected
                          ? 'border-purple-500/50 bg-purple-500/10 text-white'
                          : 'border-white/[0.05] bg-white/[0.02] text-white/60 hover:border-white/[0.1] hover:text-white/80'
                        }`}>
                        <span className={`inline-block w-5 h-5 rounded-md text-xs font-medium mr-2 text-center leading-5 ${isSelected ? 'bg-purple-500/30 text-purple-300' : 'bg-white/5 text-white/30'}`}>
                          {optLabel}
                        </span>
                        {optText}
                      </button>
                    );
                  })}
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Submit */}
        <div className="sticky bottom-4">
          <button onClick={handleSubmit} disabled={!allAnswered || submitting}
            className="w-full py-3.5 rounded-xl bg-gradient-to-r from-purple-500 to-violet-500 text-white font-medium text-sm hover:from-purple-600 hover:to-violet-600 transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2">
            {submitting ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> 提交中...</>
            ) : allAnswered ? (
              <><span>提交评估</span> <ArrowRight className="w-4 h-4" /></>
            ) : (
              `还需回答 ${questions.length - answeredCount} 题`
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
