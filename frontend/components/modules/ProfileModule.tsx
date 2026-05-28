'use client';

import { Send, Target, CheckCircle, Loader2, ChevronLeft, ChevronRight } from 'lucide-react';
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
        <div>
          <h3 className="text-xl font-bold text-white">对话式学生画像构建</h3>
          <p className="text-sm text-white/40">通过6个维度的对话，自动构建个性化学习画像</p>
        </div>
      </div>

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

      {/* 画像预览 */}
      {profileData && (
        <div className="glass-card rounded-xl p-4 border-cyan-400/20">
          <h4 className="font-bold text-cyan-400 mb-3">学生画像</h4>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div><span className="font-semibold text-white">专业:</span> <span className="text-white/60">{profileData.major}</span></div>
            <div><span className="font-semibold text-white">年级:</span> <span className="text-white/60">{profileData.grade_level}</span></div>
            <div className="col-span-2"><span className="font-semibold text-white">知识基础:</span> <span className="text-white/60">{profileData.knowledge_base}</span></div>
            <div className="col-span-2"><span className="font-semibold text-white">认知风格:</span> <span className="text-white/60">{profileData.cognitive_style}</span></div>
            <div className="col-span-2"><span className="font-semibold text-white">学习目标:</span> <span className="text-white/60">{profileData.learning_goals}</span></div>
            {profileData.weak_points?.length > 0 && (
              <div className="col-span-2"><span className="font-semibold text-white">薄弱点:</span> <span className="text-white/60">{profileData.weak_points.join(', ')}</span></div>
            )}
            {profileData.interest_areas?.length > 0 && (
              <div className="col-span-2"><span className="font-semibold text-white">兴趣领域:</span> <span className="text-white/60">{profileData.interest_areas.join(', ')}</span></div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
