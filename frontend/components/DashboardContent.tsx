'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState, useRef, useCallback } from 'react';
import {
  GraduationCap, Brain, Router, Lightbulb, TrendingUp,
  UserCheck, ArrowRight, Database, ChevronDown,
} from 'lucide-react';
import { useDashboard } from './modules/useDashboard';
import { STATS } from './modules/constants';
import type { ModuleType, NavigationContext } from './modules/types';
import { FullBackground } from './shared/BackgroundEffects';
import ProfileModule from './modules/ProfileModule';
import ResourcesModule from './modules/ResourcesModule';
import PathModule from './modules/PathModule';
import TutorModule from './modules/TutorModule';
import AssessmentModule from './modules/AssessmentModule';
import RagKnowledgeModule from './modules/RagKnowledgeModule';
import CollaborationModule from './modules/CollaborationModule';
import WorkSpaceSection from './WorkSpaceSection';

// 页面过渡动画 — 阻尼感
const pageTransition = {
  duration: 0.6,
  ease: [0.22, 1, 0.36, 1],
};

const pageVariants = {
  enter: (direction: number) => ({
    y: direction > 0 ? '100%' : '-100%',
    opacity: 0,
    scale: 0.96,
  }),
  center: { y: 0, opacity: 1, scale: 1 },
  exit: (direction: number) => ({
    y: direction > 0 ? '-100%' : '100%',
    opacity: 0,
    scale: 0.96,
  }),
};

// 模块弹窗动画
const overlayVariants = {
  hidden: { opacity: 0, y: 40, scale: 0.97 },
  visible: { opacity: 1, y: 0, scale: 1 },
  exit: { opacity: 0, y: 20, scale: 0.97 },
};

export default function DashboardContent() {
  const d = useDashboard();
  const [currentSection, setCurrentSection] = useState(0);
  const [direction, setDirection] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const wheelTimeout = useRef<NodeJS.Timeout | null>(null);

  const requireLogin = (callback: () => void) => {
    const hasToken = !!localStorage.getItem('auth_token');
    const isGuest = localStorage.getItem('is_guest') === 'true';
    if (!hasToken || isGuest) {
      sessionStorage.setItem('guest_prompt', '1');
      window.location.href = '/';
      return;
    }
    callback();
  };

  // 带阻尼的页面切换（只有 0 和 1 两页）
  const goToSection = useCallback((index: number) => {
    if (isAnimating) return;
    if (index < 0 || index > 1) return;
    if (index === currentSection) return;

    setIsAnimating(true);
    setDirection(index > currentSection ? 1 : -1);
    setCurrentSection(index);
    setTimeout(() => setIsAnimating(false), 700);
  }, [currentSection, isAnimating]);

  // 鼠标滚轮切换（带防抖阻尼）
  useEffect(() => {
    const handleWheel = (e: WheelEvent) => {
      // 如果有模块打开，不拦截滚轮（让模块内容滚动）
      if (d.activeModule) return;
      e.preventDefault();
      if (isAnimating) return;
      if (wheelTimeout.current) return;

      wheelTimeout.current = setTimeout(() => {
        wheelTimeout.current = null;
      }, 800);

      const delta = e.deltaY;
      if (Math.abs(delta) < 30) return;

      if (delta > 0 && currentSection < 1) {
        goToSection(currentSection + 1);
      } else if (delta < 0 && currentSection > 0) {
        goToSection(currentSection - 1);
      }
    };

    const container = document.querySelector('[data-dashboard-container]');
    if (container) {
      container.addEventListener('wheel', handleWheel as unknown as EventListener, { passive: false });
      return () => container.removeEventListener('wheel', handleWheel as unknown as EventListener);
    }
  }, [currentSection, isAnimating, goToSection, d.activeModule]);

  // 触摸滑动切换
  useEffect(() => {
    let touchStartY = 0;
    let touchStartTime = 0;

    const handleTouchStart = (e: TouchEvent) => {
      touchStartY = e.touches[0]?.clientY ?? 0;
      touchStartTime = Date.now();
    };

    const handleTouchEnd = (e: TouchEvent) => {
      if (d.activeModule) return;
      if (isAnimating) return;
      const touchEndY = e.changedTouches[0]?.clientY ?? 0;
      const deltaY = touchStartY - touchEndY;
      const deltaTime = Date.now() - touchStartTime;

      if (Math.abs(deltaY) < 50 || deltaTime > 500) return;

      if (deltaY > 0 && currentSection < 1) {
        goToSection(currentSection + 1);
      } else if (deltaY < 0 && currentSection > 0) {
        goToSection(currentSection - 1);
      }
    };

    const container = document.querySelector('[data-dashboard-container]');
    if (container) {
      container.addEventListener('touchstart', handleTouchStart as unknown as EventListener, { passive: true });
      container.addEventListener('touchend', handleTouchEnd as unknown as EventListener, { passive: true });
      return () => {
        container.removeEventListener('touchstart', handleTouchStart as unknown as EventListener);
        container.removeEventListener('touchend', handleTouchEnd as unknown as EventListener);
      };
    }
  }, [currentSection, isAnimating, goToSection, d.activeModule]);

  // 键盘切换
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (d.activeModule) return;
      if (e.key === 'ArrowDown' || e.key === 'PageDown') {
        e.preventDefault();
        if (currentSection < 1) goToSection(currentSection + 1);
      } else if (e.key === 'ArrowUp' || e.key === 'PageUp') {
        e.preventDefault();
        if (currentSection > 0) goToSection(currentSection - 1);
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [currentSection, goToSection, d.activeModule]);

  // ESC 关闭模块
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && d.activeModule) {
        d.setActiveModule(null);
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [d.activeModule]);

  const navigateToModule = (moduleId: ModuleType, ctx?: NavigationContext) => {
    requireLogin(() => {
      if (ctx?.subject) d.setSubject(ctx.subject);
      if (ctx?.topic) d.setTopic(ctx.topic);
      if (ctx?.learningGoal) d.setLearningGoal(ctx.learningGoal);
      if (ctx?.tutorSubject) d.setTutorSubject(ctx.tutorSubject);
      d.setActiveModule(moduleId);
      // 切换到工作台页
      if (currentSection !== 1) goToSection(1);
    });
  };

  const renderModule = () => {
    switch (d.activeModule) {
      case 'profile':
        return (
          <ProfileModule
            currentStep={d.currentStep} currentDimension={d.currentDimension}
            currentChat={d.currentChat} dimensionChats={d.dimensionChats}
            profileLoading={d.profileLoading} profileData={d.profileData}
            handleSendMessage={d.handleSendMessage} goToPreviousStep={d.goToPreviousStep}
            goToNextStep={d.goToNextStep} profileTab={d.profileTab} setProfileTab={d.setProfileTab}
            currentSemester={d.currentSemester} setCurrentSemester={d.setCurrentSemester}
            semesters={d.semesters} courses={d.courses} courseLoading={d.courseLoading}
            handleSaveCourses={d.handleSaveCourses} grades={d.grades} gradeLoading={d.gradeLoading}
            handleSaveGrades={d.handleSaveGrades} errorNotes={d.errorNotes}
            errorLoading={d.errorLoading} handleAddErrorNote={d.handleAddErrorNote}
            handleToggleMastery={d.handleToggleMastery} handleDeleteErrorNote={d.handleDeleteErrorNote}
            handleUpdateProfileField={d.handleUpdateProfileField}
            handleImportCourses={d.handleImportCourses} handleImportGrades={d.handleImportGrades}
            handleImportErrors={d.handleImportErrors}
            handleConfirmImportCourses={d.handleConfirmImportCourses}
            handleConfirmImportGrades={d.handleConfirmImportGrades}
            handleConfirmImportErrors={d.handleConfirmImportErrors}
          />
        );
      case 'resources':
        return (
          <ResourcesModule
            subject={d.subject} setSubject={d.setSubject} topic={d.topic} setTopic={d.setTopic}
            selectedTypes={d.selectedTypes} setSelectedTypes={d.setSelectedTypes}
            difficulty={d.difficulty} setDifficulty={d.setDifficulty}
            resourceLoading={d.resourceLoading} resources={d.resources}
            handleGenerateResources={d.handleGenerateResources} getTypeName={d.getTypeName}
            resourceProgress={d.resourceProgress} resourceCurrentType={d.resourceCurrentType}
            resourceTotal={d.resourceTotal} resourceDone={d.resourceDone}
          />
        );
      case 'path':
        return (
          <PathModule
            learningGoal={d.learningGoal} setLearningGoal={d.setLearningGoal}
            learningPath={d.learningPath} pathLoading={d.pathLoading}
            handlePlanPath={d.handlePlanPath} studyPlans={d.studyPlans}
            planLoading={d.planLoading} handleGeneratePlan={d.handleGeneratePlan}
            onNavigateModule={navigateToModule}
          />
        );
      case 'tutor':
        return (
          <TutorModule
            question={d.question} setQuestion={d.setQuestion}
            tutorSubject={d.tutorSubject} setTutorSubject={d.setTutorSubject}
            tutorMessages={d.tutorMessages} tutorLoading={d.tutorLoading}
            handleAskTutor={d.handleAskTutor} streamingContent={d.streamingContent}
          />
        );
      case 'assessment':
        return (
          <AssessmentModule
            assessLoading={d.assessLoading} assessment={d.assessment}
            assessTab={d.assessTab} setAssessTab={d.setAssessTab} handleAssess={d.handleAssess}
            analysisFiles={d.analysisFiles} setAnalysisFiles={d.setAnalysisFiles}
            analysisDragOver={d.analysisDragOver} setAnalysisDragOver={d.setAnalysisDragOver}
            analyzing={d.analyzing} analysisResult={d.analysisResult}
            analysisFileInputRef={d.analysisFileInputRef}
            analysisSubject={d.analysisSubject} setAnalysisSubject={d.setAnalysisSubject}
            analysisTopic={d.analysisTopic} setAnalysisTopic={d.setAnalysisTopic}
            analysisDifficulty={d.analysisDifficulty} setAnalysisDifficulty={d.setAnalysisDifficulty}
            addAnalysisFiles={d.addAnalysisFiles} removeAnalysisFile={d.removeAnalysisFile}
            formatFileSize={d.formatFileSize} getFileIcon={d.getFileIcon} handleAnalyze={d.handleAnalyze}
          />
        );
      case 'rag':
        return <RagKnowledgeModule />;
      case 'collaboration':
        return <CollaborationModule />;
      default:
        return null;
    }
  };

  return (
    <div className="relative h-screen overflow-hidden bg-[#0a0a0a]" data-dashboard-container>

      <AnimatePresence initial={false} custom={direction} mode="wait">
        {/* Page 0: Hero — 装饰背景 */}
        {currentSection === 0 && (
          <motion.section
            key="hero"
            custom={direction}
            variants={pageVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={pageTransition}
            className="absolute inset-0 flex items-center justify-center px-6"
          >
            <FullBackground />
            <div className="max-w-3xl mx-auto text-center">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
              >
                <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-purple-500/20 bg-purple-500/5 mb-8">
                  <GraduationCap className="w-3.5 h-3.5 text-purple-400" />
                  <span className="text-xs text-purple-300">多智能体协同 · 个性化学习</span>
                </div>

                <h1 className="text-6xl md:text-7xl lg:text-8xl font-bold text-white mb-10 leading-none">
                  多模态 AI
                  <br />
                  <span className="text-purple-400">教学智能体</span>
                </h1>

                <p className="text-white/40 text-xl md:text-2xl mb-14 max-w-2xl mx-auto leading-relaxed">
                  6 大智能体协同工作，7 种资源类型一键生成，构建专属你的沉浸式学习体验
                </p>

                <motion.button
                  onClick={() => goToSection(1)}
                  className="px-8 py-4 bg-purple-500 text-white rounded-lg text-lg font-medium hover:bg-purple-400 transition-colors flex items-center gap-2 mx-auto"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <GraduationCap className="w-5 h-5" />
                  进入学习看板
                </motion.button>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3, duration: 0.6 }}
                className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-6"
              >
                {STATS.map((stat) => {
                  const Icon = stat.icon;
                  return (
                    <div key={stat.label} className="text-center">
                      <Icon className={`w-7 h-7 mx-auto mb-3 ${stat.color}`} />
                      <div className="text-4xl font-bold text-white">{stat.value}</div>
                      <div className="text-base text-white/30 mt-1.5">{stat.label}</div>
                    </div>
                  );
                })}
              </motion.div>
            </div>

            <motion.div
              className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 cursor-pointer"
              onClick={() => goToSection(1)}
              animate={{ y: [0, 8, 0] }}
              transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
            >
              <span className="text-[10px] text-white/20 tracking-widest uppercase">Scroll</span>
              <ChevronDown className="w-4 h-4 text-white/20" />
            </motion.div>
          </motion.section>
        )}

        {/* Page 1: 工作台（唯一的工作页面） */}
        {currentSection === 1 && (
          <motion.section
            key="workspace"
            custom={direction}
            variants={pageVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={pageTransition}
            className="absolute inset-0"
          >
            <WorkSpaceSection onNavigateModule={navigateToModule} />
          </motion.section>
        )}
      </AnimatePresence>

      {/* 模块内容覆盖层（从工作台内部打开） */}
      <AnimatePresence>
        {d.activeModule && currentSection === 1 && (
          <motion.div
            key="module-overlay"
            variants={overlayVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
            className="absolute inset-0 z-30 bg-[#0a0a0a]/95 backdrop-blur-sm overflow-y-auto"
          >
            <div className="px-8 py-8 max-w-7xl mx-auto">
              <motion.button
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.15, duration: 0.3 }}
                onClick={() => d.setActiveModule(null)}
                className="flex items-center gap-3 text-white/40 hover:text-white/70 mb-8 transition-colors"
              >
                <ArrowRight className="w-5 h-5 rotate-180" />
                <span className="text-base">返回工作台</span>
              </motion.button>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1, duration: 0.35 }}
              >
                {renderModule()}
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 页面指示器（只有 2 个点） */}
      <div className="fixed right-5 top-1/2 -translate-y-1/2 z-40 flex flex-col items-end gap-1">
        {[
          { index: 0, label: '首页' },
          { index: 1, label: '工作台' },
        ].map(({ index, label }) => (
          <button
            key={index}
            onClick={() => goToSection(index)}
            className="group flex items-center gap-2 py-1"
          >
            <span className={`text-[10px] tracking-wide transition-all duration-300 ${
              currentSection === index ? 'text-white/50 translate-x-0 opacity-100' : 'text-white/0 translate-x-2 opacity-0 group-hover:text-white/30 group-hover:translate-x-0 group-hover:opacity-100'
            }`}>{label}</span>
            <span className={`block rounded-full transition-all duration-300 ${
              currentSection === index
                ? 'w-2 h-6 bg-purple-400'
                : 'w-1.5 h-1.5 bg-white/20 group-hover:bg-white/40 group-hover:scale-110'
            }`} />
          </button>
        ))}
      </div>
    </div>
  );
}
