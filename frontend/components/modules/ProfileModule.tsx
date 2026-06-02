'use client';

import { Send, Target, CheckCircle, Loader2, ChevronLeft, ChevronRight, RefreshCw, User, BookOpen, Brain, Lightbulb, Sparkles, GraduationCap, Clock, Trophy } from 'lucide-react';
import { PROFILE_DIMENSIONS } from './constants';
import type { DimensionChat, ProfileData } from './types';

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
}

/** 画像维度展示配置 */
const PROFILE_DISPLAY = [
  { key: 'major', label: '专业', icon: GraduationCap, color: 'from-blue-500 to-cyan-400', format: (v: any) => v || '未填写' },
  { key: 'grade_level', label: '年级', icon: User, color: 'from-violet-500 to-purple-400', format: (v: any) => v || '未填写' },
  { key: 'cognitive_style', label: '认知风格', icon: Brain, color: 'from-green-500 to-emerald-400', format: (v: any) => v || '未评估' },
  { key: 'knowledge_base', label: '知识基础', icon: BookOpen, color: 'from-amber-500 to-orange-400', format: (v: any) => {
    if (!v) return '未评估';
    if (typeof v === 'string') return v;
    if (v.level) return `水平: ${v.level}${v.topics?.length ? ' · ' + v.topics.join('、') : ''}`;
    return JSON.stringify(v);
  }},
  { key: 'learning_goals', label: '学习目标', icon: Target, color: 'from-red-500 to-pink-400', format: (v: any) => {
    if (!v) return '未设定';
    if (Array.isArray(v)) return v.join('、');
    if (typeof v === 'string') return v;
    return JSON.stringify(v);
  }},
  { key: 'interest_areas', label: '兴趣领域', icon: Sparkles, color: 'from-indigo-500 to-purple-400', format: (v: any) => Array.isArray(v) && v.length ? v.join('、') : '未填写', isArray: true },
  { key: 'weak_points', label: '薄弱环节', icon: Lightbulb, color: 'from-yellow-500 to-amber-400', format: (v: any) => Array.isArray(v) && v.length ? v.join('、') : '暂无', isArray: true },
  { key: 'preferred_resources', label: '偏好资源', icon: Trophy, color: 'from-teal-500 to-cyan-400', format: (v: any) => Array.isArray(v) && v.length ? v.join('、') : '未设定', isArray: true },
];

export default function ProfileModule({
  currentStep, currentDimension, currentChat, dimensionChats,
  profileLoading, profileData, handleSendMessage, goToPreviousStep, goToNextStep,
}: ProfileModuleProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
          <Target className="w-5 h-5 text-white" />
        </div>
        <div className="flex-1">
          <h3 className="text-xl font-bold text-white">学生画像</h3>
          <p className="text-sm text-white/40">
            {profileData ? '基于对话构建的个性化学习画像' : '通过 6 个维度的对话，自动构建个性化学习画像'}
          </p>
        </div>
      </div>

      {/* ═══ 已有画像：展示完整画像 ═══ */}
      {profileData ? (
        <div className="space-y-4">
          {/* 综合卡片 */}
          <div className="bg-gradient-to-r from-cyan-500/20 to-blue-500/20 rounded-2xl p-5 border border-cyan-400/20">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
                <User className="w-8 h-8 text-white" />
              </div>
              <div className="flex-1">
                <h4 className="text-lg font-bold text-white">{profileData.major || '学生'}</h4>
                <p className="text-sm text-white/50">{profileData.grade_level || ''}</p>
                {profileData.update_time && (
                  <p className="text-xs text-white/30 mt-1 flex items-center gap-1">
                    <Clock className="w-3 h-3" /> 更新于 {profileData.update_time}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* 多维度详情卡片 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {PROFILE_DISPLAY.map((dim) => {
              const value = (profileData as any)[dim.key];
              const Icon = dim.icon;
              const displayText = dim.format(value);
              const isEmpty = !value || (Array.isArray(value) && value.length === 0) || displayText === '未填写' || displayText === '未评估' || displayText === '未设定' || displayText === '暂无';

              return (
                <div key={dim.key} className={`glass-card rounded-xl p-4 transition-all hover:border-white/10 ${isEmpty ? 'opacity-50' : ''}`}>
                  <div className="flex items-center gap-3 mb-2">
                    <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${dim.color} flex items-center justify-center`}>
                      <Icon className="w-4 h-4 text-white" />
                    </div>
                    <span className="font-semibold text-sm text-white">{dim.label}</span>
                  </div>
                  <p className={`text-sm leading-relaxed ${isEmpty ? 'text-white/25 italic' : 'text-white/70'}`}>
                    {displayText}
                  </p>
                </div>
              );
            })}
          </div>

          {/* 学习历史 */}
          {profileData.learning_history?.length > 0 && (
            <div className="glass-card rounded-xl p-4">
              <h5 className="font-semibold text-white mb-3 text-sm flex items-center gap-2">
                <Clock className="w-4 h-4 text-cyan-400" /> 学习记录
                <span className="text-xs text-white/30 font-normal">({profileData.learning_history.length} 条)</span>
              </h5>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {profileData.learning_history.slice(-10).reverse().map((h: any, i: number) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <div className="w-1.5 h-1.5 rounded-full bg-cyan-400/50" />
                    <span className="text-white/50">{typeof h === 'string' ? h : h.topic || h.action || JSON.stringify(h)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        /* ═══ 无画像：对话构建流程 ═══ */
        <div className="space-y-4">
          {/* 进度指示器 */}
          <div className="glass-card rounded-xl p-3">
            <div className="flex items-center justify-between">
              {PROFILE_DIMENSIONS.map((dim, idx) => {
                const Icon = dim.icon;
                const isCompleted = dimensionChats[dim.id]?.completed;
                const isCurrent = idx === currentStep;
                return (
                  <div key={dim.id} className="flex items-center">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${
                      isCompleted ? 'bg-cyan-500 text-white' :
                      isCurrent ? `bg-gradient-to-r ${dim.color} text-white` :
                      'bg-white/[0.08] text-white/30'
                    }`}>
                      {isCompleted ? <CheckCircle className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
                    </div>
                    {idx < PROFILE_DIMENSIONS.length - 1 && (
                      <div className={`w-4 h-0.5 mx-1 ${isCompleted ? 'bg-cyan-500' : 'bg-white/[0.08]'}`} />
                    )}
                  </div>
                );
              })}
            </div>
            <div className="flex justify-between mt-1 text-xs text-white/30">
              {PROFILE_DIMENSIONS.map((dim, idx) => (
                <span key={dim.id} className={idx === currentStep ? 'font-semibold text-white' : ''}>
                  {dim.title}
                </span>
              ))}
            </div>
          </div>

          {/* 当前维度对话区域 */}
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
                  <div className={`max-w-[80%] rounded-xl px-3 py-2 text-sm ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white'
                      : 'bg-white/[0.06] text-white/80'
                  }`}>
                    {msg.content}
                  </div>
                </div>
              ))}
              {profileLoading && (
                <div className="flex justify-start">
                  <div className="bg-white/[0.06] rounded-xl px-3 py-2">
                    <Loader2 className="w-4 h-4 animate-spin text-white/30 border-white/30 border-t-cyan-400" />
                  </div>
                </div>
              )}
            </div>

            <div className="p-3 border-t border-white/[0.06]">
              <div className="flex gap-2">
                <input
                  id="profile-input"
                  type="text"
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder={currentDimension.placeholder}
                  className="flex-1 px-3 py-2 bg-white/[0.04] border border-white/[0.08] text-white placeholder:text-white/15 rounded-lg focus:border-cyan-400/30 focus:outline-none text-sm"
                  disabled={profileLoading}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={profileLoading}
                  className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                >
                  {profileLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  发送
                </button>
              </div>

              <div className="flex justify-between mt-2">
                <button
                  onClick={goToPreviousStep}
                  disabled={currentStep === 0}
                  className="px-3 py-1 text-sm text-white/40 hover:bg-white/[0.04] rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                >
                  <ChevronLeft className="w-4 h-4" /> 上一步
                </button>
                <button
                  onClick={goToNextStep}
                  disabled={currentStep === PROFILE_DIMENSIONS.length - 1}
                  className="px-3 py-1 text-sm text-white/40 hover:bg-white/[0.04] rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                >
                  下一步 <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
