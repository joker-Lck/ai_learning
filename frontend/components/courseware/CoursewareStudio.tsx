'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useCoursewareStore } from '@/stores';
import api from '@/lib/api';
import PPTPreviewer from './PPTPreviewer';
import {
  FileText, Wand2, Send, Loader2, ChevronRight,
  ChevronLeft, Zap, Palette, Check, RotateCcw,
  Download, Sparkles, MessageSquare
} from 'lucide-react';

const steps = [
  { label: '填写主题', icon: FileText, desc: '输入课件主题和年级' },
  { label: '描述需求', icon: MessageSquare, desc: '告诉 AI 你想要什么' },
  { label: '生成课件', icon: Wand2, desc: 'AI 自动生成' },
  { label: '预览下载', icon: Download, desc: '查看和下载课件' },
];

const templateStyles = [
  { id: 'tech', label: '科技蓝', color: '#0a192f', emoji: '🔮' },
  { id: 'edu', label: '教育紫', color: '#5b2c6f', emoji: '📚' },
  { id: 'nature', label: '自然绿', color: '#27ae60', emoji: '🌿' },
  { id: 'minimal', label: '简约灰', color: '#2c3e50', emoji: '⬜' },
  { id: 'business', label: '商务金', color: '#1a1a2e', emoji: '✨' },
];

export default function CoursewareStudio() {
  const store = useCoursewareStore();
  const [currentStep, setCurrentStep] = useState(0);
  const [requirement, setRequirement] = useState('');
  const [requirements, setRequirements] = useState<string[]>([]);
  const [error, setError] = useState('');

  const handleAddRequirement = () => {
    if (requirement.trim()) {
      setRequirements([...requirements, requirement.trim()]);
      setRequirement('');
    }
  };

  const handleGenerate = async () => {
    if (!store.topic.trim()) {
      setError('请输入课件主题');
      return;
    }

    setCurrentStep(2);
    store.setGenerating(true);
    setError('');

    const reqText = requirements.length > 0 ? requirements.join('\n') : '无特殊要求';

    try {
      await api.generateCoursewareStream(
        store.topic,
        reqText,
        store.fastMode,
        (chunk) => {
          // 进度更新通过 onDone 处理
        },
        (data) => {
          store.setCoursewareResult(data);
          setCurrentStep(3);
        },
        (err) => {
          setError(err);
          store.setGenerating(false);
          setCurrentStep(1);
        },
      );
    } catch (err: any) {
      setError(err.message || '生成失败');
      store.setGenerating(false);
      setCurrentStep(1);
    }
  };

  const handleReset = () => {
    store.reset();
    setRequirements([]);
    setCurrentStep(0);
    setError('');
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* 头部 */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-800">AI 课件生成</h1>
              <p className="text-sm text-gray-500">四步生成专业 PPT 课件 · 支持 5 种模板风格</p>
            </div>
          </div>
          <button
            onClick={handleReset}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm text-gray-500 hover:text-red-500 hover:bg-red-50 transition-all"
          >
            <RotateCcw className="w-4 h-4" />
            重新开始
          </button>
        </div>
      </motion.div>

      {/* 步骤指示器 */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between max-w-2xl mx-auto">
          {steps.map((step, i) => {
            const Icon = step.icon;
            const isActive = i === currentStep;
            const isCompleted = i < currentStep;

            return (
              <div key={i} className="flex items-center">
                <div className="flex flex-col items-center">
                  <motion.div
                    className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all ${
                      isCompleted
                        ? 'bg-green-500 text-white'
                        : isActive
                        ? 'bg-gradient-to-br from-purple-500 to-pink-500 text-white shadow-lg shadow-purple-500/30'
                        : 'bg-gray-100 text-gray-400'
                    }`}
                    animate={isActive ? { scale: [1, 1.1, 1] } : {}}
                    transition={{ duration: 1.5, repeat: isActive ? Infinity : 0 }}
                  >
                    {isCompleted ? <Check className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
                  </motion.div>
                  <p className={`text-xs mt-2 font-medium ${isActive ? 'text-purple-600' : 'text-gray-400'}`}>
                    {step.label}
                  </p>
                </div>
                {i < steps.length - 1 && (
                  <div className={`w-16 h-0.5 mx-2 mt-[-20px] ${i < currentStep ? 'bg-green-500' : 'bg-gray-200'}`} />
                )}
              </div>
            );
          })}
        </div>
      </motion.div>

      {/* 步骤内容 */}
      <AnimatePresence mode="wait">
        {/* 步骤 1: 填写主题 */}
        {currentStep === 0 && (
          <motion.div
            key="step-0"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="max-w-2xl mx-auto"
          >
            <div className="bg-white rounded-2xl p-8 shadow-card">
              <h2 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2">
                <FileText className="w-5 h-5 text-purple-500" />
                填写课件信息
              </h2>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">课件主题 *</label>
                  <input
                    type="text"
                    value={store.topic}
                    onChange={(e) => store.setTopic(e.target.value)}
                    placeholder="例如：函数的单调性、牛顿第二定律、光合作用..."
                    className="w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-purple-400 focus:ring-2 focus:ring-purple-400/20 outline-none transition-all"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">生成模式</label>
                  <div className="flex gap-4">
                    <button
                      onClick={() => store.setFastMode(true)}
                      className={`flex-1 p-4 rounded-xl border-2 transition-all ${
                        store.fastMode
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <Zap className="w-4 h-4 text-orange-500" />
                        <span className="font-medium">快速模式</span>
                      </div>
                      <p className="text-xs text-gray-500">8-10 页 · 15-25 秒 · 无配图</p>
                    </button>
                    <button
                      onClick={() => store.setFastMode(false)}
                      className={`flex-1 p-4 rounded-xl border-2 transition-all ${
                        !store.fastMode
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <Palette className="w-4 h-4 text-purple-500" />
                        <span className="font-medium">标准模式</span>
                      </div>
                      <p className="text-xs text-gray-500">10-15 页 · 45-90 秒 · 含配图</p>
                    </button>
                  </div>
                </div>

                {error && <p className="text-red-500 text-sm">❌ {error}</p>}

                <button
                  onClick={() => {
                    if (store.topic.trim()) {
                      setCurrentStep(1);
                      setError('');
                    } else {
                      setError('请输入课件主题');
                    }
                  }}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-medium hover:shadow-lg transition-all flex items-center justify-center gap-2"
                >
                  下一步 <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </motion.div>
        )}

        {/* 步骤 2: 描述需求 */}
        {currentStep === 1 && (
          <motion.div
            key="step-1"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="max-w-2xl mx-auto"
          >
            <div className="bg-white rounded-2xl p-8 shadow-card">
              <h2 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-purple-500" />
                描述具体需求
              </h2>

              <div className="space-y-4">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={requirement}
                    onChange={(e) => setRequirement(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleAddRequirement()}
                    placeholder="输入一个需求后点击添加..."
                    className="flex-1 px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-purple-400 focus:ring-2 focus:ring-purple-400/20 outline-none transition-all"
                  />
                  <button
                    onClick={handleAddRequirement}
                    className="px-4 py-3 rounded-xl bg-gray-100 text-gray-600 hover:bg-gray-200 transition-all"
                  >
                    添加
                  </button>
                </div>

                {requirements.length > 0 && (
                  <div className="space-y-2">
                    {requirements.map((r, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, y: -5 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-50 rounded-lg"
                      >
                        <Check className="w-4 h-4 text-purple-500" />
                        <span className="text-sm text-gray-700 flex-1">{r}</span>
                        <button
                          onClick={() => setRequirements(requirements.filter((_, j) => j !== i))}
                          className="text-gray-400 hover:text-red-500"
                        >
                          ×
                        </button>
                      </motion.div>
                    ))}
                  </div>
                )}

                {requirements.length === 0 && (
                  <p className="text-sm text-gray-400 text-center py-4">
                    暂无特殊需求，可以直接生成，也可以添加具体要求让 AI 更精准
                  </p>
                )}

                <div className="flex gap-3">
                  <button
                    onClick={() => setCurrentStep(0)}
                    className="px-6 py-3 rounded-xl border-2 border-gray-200 text-gray-600 hover:bg-gray-50 transition-all flex items-center gap-2"
                  >
                    <ChevronLeft className="w-4 h-4" /> 上一步
                  </button>
                  <button
                    onClick={handleGenerate}
                    className="flex-1 py-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-medium hover:shadow-lg transition-all flex items-center justify-center gap-2"
                  >
                    <Wand2 className="w-4 h-4" /> 开始生成课件
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* 步骤 3: 生成中 */}
        {currentStep === 2 && (
          <motion.div
            key="step-2"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            className="max-w-lg mx-auto text-center"
          >
            <div className="bg-white rounded-2xl p-12 shadow-card">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                className="w-20 h-20 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center mx-auto mb-6"
              >
                <Wand2 className="w-10 h-10 text-white" />
              </motion.div>
              <h2 className="text-xl font-bold text-gray-800 mb-2">AI 正在生成课件</h2>
              <p className="text-gray-500 mb-6">
                {store.fastMode ? '快速模式 · 预计 15-25 秒' : '标准模式 · 预计 45-90 秒'}
              </p>

              {/* 进度条 */}
              <div className="w-full bg-gray-100 rounded-full h-2 mb-4 overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
                  initial={{ width: '0%' }}
                  animate={{ width: '80%' }}
                  transition={{ duration: 10, ease: 'easeOut' }}
                />
              </div>

              <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
                <Loader2 className="w-4 h-4 animate-spin" />
                识别学科 → 生成大纲 → 构建幻灯片...
              </div>

              {error && (
                <p className="text-red-500 text-sm mt-4">❌ {error}</p>
              )}
            </div>
          </motion.div>
        )}

        {/* 步骤 4: 预览下载 */}
        {currentStep === 3 && store.slides.length > 0 && (
          <motion.div
            key="step-3"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <PPTPreviewer
              slides={store.slides}
              theme={store.theme}
              topic={store.topic}
              subject={store.subject}
              coursewareId={store.coursewareId}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
