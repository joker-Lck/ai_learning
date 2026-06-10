'use client';

import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  GraduationCap, Zap, Brain, Route, Lightbulb, TrendingUp,
  UserCheck, ArrowRight, Award, Database, Clock,
} from 'lucide-react';
import { useDashboard } from './modules/useDashboard';
import { STATS } from './modules/constants';
import type { ModuleType } from './modules/types';
import { DashboardBackground } from './shared/BackgroundEffects';
import ProfileModule from './modules/ProfileModule';
import ResourcesModule from './modules/ResourcesModule';
import PathModule from './modules/PathModule';
import TutorModule from './modules/TutorModule';
import AssessmentModule from './modules/AssessmentModule';
import RagKnowledgeModule from './modules/RagKnowledgeModule';

export default function DashboardContent() {
  const d = useDashboard();

  const renderModule = () => {
    switch (d.activeModule) {
      case 'profile':
        return (
          <ProfileModule
            currentStep={d.currentStep}
            currentDimension={d.currentDimension}
            currentChat={d.currentChat}
            dimensionChats={d.dimensionChats}
            profileLoading={d.profileLoading}
            profileData={d.profileData}
            handleSendMessage={d.handleSendMessage}
            goToPreviousStep={d.goToPreviousStep}
            goToNextStep={d.goToNextStep}
            profileTab={d.profileTab}
            setProfileTab={d.setProfileTab}
            currentSemester={d.currentSemester}
            setCurrentSemester={d.setCurrentSemester}
            semesters={d.semesters}
            courses={d.courses}
            courseLoading={d.courseLoading}
            handleSaveCourses={d.handleSaveCourses}
            grades={d.grades}
            gradeLoading={d.gradeLoading}
            handleSaveGrades={d.handleSaveGrades}
            errorNotes={d.errorNotes}
            errorLoading={d.errorLoading}
            handleAddErrorNote={d.handleAddErrorNote}
            handleToggleMastery={d.handleToggleMastery}
            handleDeleteErrorNote={d.handleDeleteErrorNote}
            handleUpdateProfileField={d.handleUpdateProfileField}
            handleImportCourses={d.handleImportCourses}
            handleImportGrades={d.handleImportGrades}
            handleImportErrors={d.handleImportErrors}
            handleConfirmImportCourses={d.handleConfirmImportCourses}
            handleConfirmImportGrades={d.handleConfirmImportGrades}
            handleConfirmImportErrors={d.handleConfirmImportErrors}
          />
        );
      case 'resources':
        return (
          <ResourcesModule
            subject={d.subject}
            setSubject={d.setSubject}
            topic={d.topic}
            setTopic={d.setTopic}
            selectedTypes={d.selectedTypes}
            setSelectedTypes={d.setSelectedTypes}
            difficulty={d.difficulty}
            setDifficulty={d.setDifficulty}
            resourceLoading={d.resourceLoading}
            resources={d.resources}
            handleGenerateResources={d.handleGenerateResources}
            getTypeName={d.getTypeName}
          />
        );
      case 'path':
        return (
          <PathModule
            learningGoal={d.learningGoal}
            setLearningGoal={d.setLearningGoal}
            pathLoading={d.pathLoading}
            learningPath={d.learningPath}
            handlePlanPath={d.handlePlanPath}
            studyPlans={d.studyPlans}
            planLoading={d.planLoading}
            handleGeneratePlan={d.handleGeneratePlan}
          />
        );
      case 'tutor':
        return (
          <TutorModule
            question={d.question}
            setQuestion={d.setQuestion}
            tutorSubject={d.tutorSubject}
            setTutorSubject={d.setTutorSubject}
            tutorLoading={d.tutorLoading}
            tutorMessages={d.tutorMessages}
            handleAskTutor={d.handleAskTutor}
            streamingContent={d.streamingContent}
          />
        );
      case 'assessment':
        return (
          <AssessmentModule
            assessLoading={d.assessLoading}
            assessment={d.assessment}
            assessTab={d.assessTab}
            setAssessTab={d.setAssessTab}
            handleAssess={d.handleAssess}
            analysisFiles={d.analysisFiles}
            setAnalysisFiles={d.setAnalysisFiles}
            analysisDragOver={d.analysisDragOver}
            setAnalysisDragOver={d.setAnalysisDragOver}
            analyzing={d.analyzing}
            analysisResult={d.analysisResult}
            analysisFileInputRef={d.analysisFileInputRef}
            analysisSubject={d.analysisSubject}
            setAnalysisSubject={d.setAnalysisSubject}
            analysisTopic={d.analysisTopic}
            setAnalysisTopic={d.setAnalysisTopic}
            analysisDifficulty={d.analysisDifficulty}
            setAnalysisDifficulty={d.setAnalysisDifficulty}
            addAnalysisFiles={d.addAnalysisFiles}
            removeAnalysisFile={d.removeAnalysisFile}
            formatFileSize={d.formatFileSize}
            getFileIcon={d.getFileIcon}
            handleAnalyze={d.handleAnalyze}
          />
        );
      case 'rag':
        return <RagKnowledgeModule />;
      default:
        return null;
    }
  };

  // 游客模式：5 分钟后自动跳转回登录页
  const router = useRouter();
  const GUEST_TIMEOUT = 5 * 60 * 1000; // 5 分钟
  const [guestCountdown, setGuestCountdown] = useState(GUEST_TIMEOUT / 1000);

  useEffect(() => {
    if (!d.isGuest) return;

    const interval = setInterval(() => {
      setGuestCountdown(prev => {
        if (prev <= 1) {
          clearInterval(interval);
          window.location.href = '/';
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [d.isGuest]);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="max-w-7xl mx-auto relative">
      <DashboardBackground />

      {/* 游客模式提示横幅 */}
      {d.isGuest && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 px-5 py-3.5 rounded-2xl border border-amber-400/20 bg-amber-400/5 backdrop-blur-sm flex items-center gap-3"
        >
          <span className="text-lg">👁️</span>
          <div className="flex-1">
            <p className="text-sm font-medium text-amber-400">游客模式 — 仅可浏览界面</p>
            <p className="text-xs text-amber-300/40 mt-0.5">所有功能按钮已禁用，请登录后体验完整功能</p>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-400/10 border border-amber-400/20">
            <Clock className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-sm font-mono font-medium text-amber-400">{formatTime(guestCountdown)}</span>
          </div>
        </motion.div>
      )}

      {/* 欢迎区域 - 仅在未选择模块时显示 */}
      {!d.activeModule && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: 'spring', stiffness: 200, damping: 25 }}
          className="mb-8"
        >
          <div className="bg-gradient-to-r from-cyan-500 to-blue-500 rounded-2xl p-6 text-white mb-6">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center">
                <GraduationCap className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold mb-1">基于多智能体的个性化学习资源生成系统</h1>
                <p className="text-white/80 text-sm">
                  对话式画像构建 · 多智能体协同 · 防幻觉机制 · 流式输出
                </p>
              </div>
            </div>
          </div>

          {/* 统计卡片 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {STATS.map((stat, index) => {
              const Icon = stat.icon;
              return (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1, type: 'spring', stiffness: 200, damping: 25 }}
                  className="glass-card rounded-xl p-4"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-lg bg-white/[0.06] flex items-center justify-center ${stat.color}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-white">{stat.value}</div>
                      <div className="text-xs text-white/40">{stat.label}</div>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>
      )}

      {/* 功能模块选择 - 仅在未选择模块时显示 */}
      {!d.activeModule && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, type: 'spring', stiffness: 200, damping: 25 }}
          className="mb-6"
        >
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-cyan-400" />
            功能模块
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {[
              { id: 'profile', label: '学生画像', icon: UserCheck, color: 'cyan', emoji: '' },
              { id: 'resources', label: '资源生成', icon: Brain, color: 'purple', emoji: '🤖' },
              { id: 'path', label: '学习路径', icon: Route, color: 'amber', emoji: '🗺️' },
              { id: 'tutor', label: '智能辅导', icon: Lightbulb, color: 'green', emoji: '💡' },
              { id: 'assessment', label: '效果评估', icon: TrendingUp, color: 'blue', emoji: '' },
              { id: 'rag', label: '知识库', icon: Database, color: 'emerald', emoji: '📚' },
            ].map((module) => {
              const Icon = module.icon;
              const isActive = d.activeModule === module.id;
              const colorMap: Record<string, string> = {
                cyan: 'from-cyan-500 to-blue-500',
                purple: 'from-purple-500 to-pink-500',
                amber: 'from-amber-500 to-orange-500',
                green: 'from-emerald-500 to-teal-500',
                blue: 'from-blue-500 to-indigo-500',
                emerald: 'from-emerald-500 to-green-500',
              };
              return (
                <button
                  key={module.id}
                  onClick={() => d.setActiveModule(module.id as ModuleType)}
                  className={`p-4 rounded-xl transition-all ${
                    isActive
                      ? `bg-gradient-to-r ${colorMap[module.color]} text-white scale-105`
                      : 'glass-card hover:bg-white/[0.06] text-white/60 hover:text-white'
                  }`}
                >
                  <div className="text-2xl mb-2">{module.emoji}</div>
                  <div className="text-sm font-semibold">{module.label}</div>
                </button>
              );
            })}
          </div>
        </motion.div>
      )}

      {/* 功能模块内容 */}
      {d.activeModule && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: 'spring', stiffness: 200, damping: 25 }}
          className="glass-card rounded-2xl p-6 relative"
        >
          {renderModule()}
          {/* 游客模式遮罩 */}
          {d.isGuest && (
            <div className="absolute inset-0 rounded-2xl bg-[#060d1f]/80 backdrop-blur-sm flex flex-col items-center justify-center z-10">
              <span className="text-4xl mb-3">🔒</span>
              <p className="text-white font-medium mb-1">游客模式无法使用此功能</p>
              <p className="text-white/40 text-sm mb-4">请登录后体验完整功能</p>
              <button
                onClick={() => { localStorage.removeItem('is_guest'); window.location.href = '/'; }}
                className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 text-white text-sm font-medium hover:opacity-90 transition-opacity"
              >
                立即登录
              </button>
            </div>
          )}
        </motion.div>
      )}

      {/* 快捷操作 */}
      {!d.activeModule && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, type: 'spring', stiffness: 200, damping: 25 }}
          className="glass-card rounded-2xl p-6"
        >
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-cyan-400" />
            快速开始
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => d.setActiveModule('profile')}
              className="flex items-center gap-3 p-4 rounded-xl border border-white/[0.08] bg-white/[0.02] hover:border-cyan-400/30 hover:bg-cyan-400/5 transition-all group"
            >
              <div className="w-10 h-10 rounded-lg bg-cyan-400/10 flex items-center justify-center group-hover:bg-cyan-400/20 transition-colors">
                <UserCheck className="w-5 h-5 text-cyan-400" />
              </div>
              <div className="text-left">
                <div className="font-semibold text-white">构建画像</div>
                <div className="text-xs text-white/40">对话式8维度画像</div>
              </div>
              <ArrowRight className="w-4 h-4 text-white/30 ml-auto group-hover:text-cyan-400" />
            </button>

            <button
              onClick={() => d.setActiveModule('resources')}
              className="flex items-center gap-3 p-4 rounded-xl border border-white/[0.08] bg-white/[0.02] hover:border-purple-400/30 hover:bg-purple-400/5 transition-all group"
            >
              <div className="w-10 h-10 rounded-lg bg-purple-400/10 flex items-center justify-center group-hover:bg-purple-400/20 transition-colors">
                <Brain className="w-5 h-5 text-purple-400" />
              </div>
              <div className="text-left">
                <div className="font-semibold text-white">生成资源</div>
                <div className="text-xs text-white/40">7种多模态资源</div>
              </div>
              <ArrowRight className="w-4 h-4 text-white/30 ml-auto group-hover:text-purple-400" />
            </button>

            <button
              onClick={() => d.setActiveModule('assessment')}
              className="flex items-center gap-3 p-4 rounded-xl border border-white/[0.08] bg-white/[0.02] hover:border-indigo-400/30 hover:bg-indigo-400/5 transition-all group"
            >
              <div className="w-10 h-10 rounded-lg bg-indigo-400/10 flex items-center justify-center group-hover:bg-indigo-400/20 transition-colors">
                <Award className="w-5 h-5 text-indigo-400" />
              </div>
              <div className="text-left">
                <div className="font-semibold text-white">效果评估</div>
                <div className="text-xs text-white/40">多维度评估反馈</div>
              </div>
              <ArrowRight className="w-4 h-4 text-white/30 ml-auto group-hover:text-indigo-400" />
            </button>
          </div>
        </motion.div>
      )}
    </div>
  );
}
