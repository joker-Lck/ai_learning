'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState, useRef } from 'react';
import {
  GraduationCap, Brain, Router, Lightbulb, TrendingUp,
  UserCheck, ArrowRight, Database, ChevronDown,
} from 'lucide-react';
import { useDashboard } from './modules/useDashboard';
import { STATS } from './modules/constants';
import type { ModuleType, NavigationContext } from './modules/types';
import { DashboardBackground } from './shared/BackgroundEffects';
import ProfileModule from './modules/ProfileModule';
import ResourcesModule from './modules/ResourcesModule';
import PathModule from './modules/PathModule';
import TutorModule from './modules/TutorModule';
import AssessmentModule from './modules/AssessmentModule';
import RagKnowledgeModule from './modules/RagKnowledgeModule';
import WorkSpaceSection from './WorkSpaceSection';

const TOTAL_SECTIONS = 3; // 0: Hero, 1: Workspace, 2: Module Select

const modules = [
  { id: 'profile', label: '学生画像', desc: '对话式画像构建', icon: UserCheck },
  { id: 'resources', label: '资源生成', desc: '7种多模态资源', icon: Brain },
  { id: 'path', label: '学习路径', desc: 'AI路径推荐', icon: Router },
  { id: 'tutor', label: '智能辅导', desc: '智能问答辅导', icon: Lightbulb },
  { id: 'assessment', label: '效果评估', desc: '多维度评估', icon: TrendingUp },
  { id: 'rag', label: '知识库', desc: '上传文档知识库', icon: Database },
];

export default function DashboardContent() {
  const d = useDashboard();
  const containerRef = useRef<HTMLDivElement>(null);
  const [currentSection, setCurrentSection] = useState(0);
  const [autoPlan, setAutoPlan] = useState(false);

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

  const sectionRefs = useRef<(HTMLElement | null)[]>([]);

  // IntersectionObserver 追踪当前可见 section
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting && entry.intersectionRatio > 0.5) {
            const idx = sectionRefs.current.indexOf(entry.target as HTMLElement);
            if (idx >= 0) setCurrentSection(idx);
          }
        }
      },
      { threshold: 0.5 }
    );
    sectionRefs.current.forEach(el => { if (el) observer.observe(el); });
    return () => observer.disconnect();
  }, [d.activeModule]);

  // 刷新时根据 URL 模块参数滚动到正确位置
  useEffect(() => {
    if (d.activeModule) {
      setTimeout(() => {
        sectionRefs.current[2]?.scrollIntoView({ behavior: 'instant' as ScrollBehavior });
      }, 100);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const scrollToSection = (index: number) => {
    sectionRefs.current[index]?.scrollIntoView({ behavior: 'smooth' });
  };

  const navigateToModule = (moduleId: ModuleType, ctx?: NavigationContext) => {
    requireLogin(() => {
      // 预填充上下文数据
      if (ctx?.subject) d.setSubject(ctx.subject);
      if (ctx?.topic) d.setTopic(ctx.topic);
      if (ctx?.learningGoal) d.setLearningGoal(ctx.learningGoal);
      if (ctx?.tutorSubject) d.setTutorSubject(ctx.tutorSubject);

      // 设置自动触发标志
      setAutoPlan(!!ctx?.autoPlan);

      // 直接设置模块并滚动到第三页
      d.setActiveModule(moduleId);
      requestAnimationFrame(() => {
        scrollToSection(2);
      });
    });
  };

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
            resourceProgress={d.resourceProgress}
            resourceCurrentType={d.resourceCurrentType}
            resourceTotal={d.resourceTotal}
            resourceDone={d.resourceDone}
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

  return (
    <div ref={containerRef} className="h-screen overflow-y-auto" style={{ background: '#0a0a0a', scrollSnapType: 'y proximity', scrollBehavior: 'smooth' }}>
      <DashboardBackground />

      {/* Section 0: Hero */}
      <section
        ref={el => { sectionRefs.current[0] = el; }}
        className="snap-section relative px-6"
      >
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

            <div className="flex items-center justify-center gap-4">
              <motion.button
                onClick={() => scrollToSection(1)}
                className="px-8 py-4 bg-purple-500 text-white rounded-lg text-lg font-medium hover:bg-purple-400 transition-colors flex items-center gap-2"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <GraduationCap className="w-5 h-5" />
                学习看板
              </motion.button>
              <motion.button
                onClick={() => scrollToSection(2)}
                className="px-8 py-4 glass-button text-white rounded-lg text-lg font-medium flex items-center gap-2"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Brain className="w-5 h-5" />
                功能选择
              </motion.button>
            </div>
          </motion.div>

          {/* 统计 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
            className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-6"
          >
            {STATS.map((stat, i) => {
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

        {/* 滚动指示 */}
        {!d.activeModule && (
          <motion.div
            className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 cursor-pointer"
            onClick={() => scrollToSection(1)}
            animate={{ y: [0, 8, 0] }}
            transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          >
            <span className="text-[10px] text-white/20 tracking-widest uppercase">Scroll</span>
            <ChevronDown className="w-4 h-4 text-white/20" />
          </motion.div>
        )}
      </section>

      {/* Section 1: 工作台 */}
      <section
        ref={el => { sectionRefs.current[1] = el; }}
        className="snap-section"
      >
        <WorkSpaceSection onNavigateModule={navigateToModule} />
      </section>

      {/* Section 2: 模块选择 或 模块内容 */}
      <AnimatePresence>
        {d.activeModule ? (
          <motion.section
            key="module-content"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
            ref={el => { sectionRefs.current[2] = el; }}
            className="snap-section"
          >
            <div className="flex-1 overflow-y-auto h-screen px-8 py-20" data-workspace-scroll>
              <div className="max-w-7xl mx-auto">
                <motion.button
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.15, duration: 0.3 }}
                  onClick={() => d.setActiveModule(null)}
                  className="flex items-center gap-3 text-white/40 hover:text-white/70 mb-10 transition-colors"
                >
                  <ArrowRight className="w-5 h-5 rotate-180" />
                  <span className="text-base">返回</span>
                </motion.button>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1, duration: 0.35 }}
                >
                  {renderModule()}
                </motion.div>
              </div>
            </div>
          </motion.section>
        ) : (
          <motion.section
            key="module-select"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            ref={el => { sectionRefs.current[2] = el; }}
            className="snap-section px-6"
          >
            <div className="max-w-6xl mx-auto px-4">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="text-center mb-16"
              >
                <h2 className="text-4xl md:text-5xl font-bold text-white mb-5">选择功能模块</h2>
                <p className="text-white/35 text-lg">选择一个模块开始你的学习之旅</p>
              </motion.div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {modules.map((mod, index) => {
                  const Icon = mod.icon;
                  return (
                    <motion.button
                      key={mod.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.08, duration: 0.4 }}
                      onClick={() => requireLogin(() => {
                        d.setActiveModule(mod.id as ModuleType);
                      })}
                      className="group p-10 rounded-2xl glass-card glass-card-hover text-left"
                    >
                      <div className="w-16 h-16 rounded-xl bg-purple-500/10 flex items-center justify-center mb-6 group-hover:bg-purple-500/20 transition-colors">
                        <Icon className="w-8 h-8 text-purple-400" />
                      </div>
                      <h3 className="text-xl font-semibold text-white mb-2">{mod.label}</h3>
                      <p className="text-base text-white/35">{mod.desc}</p>
                      <ArrowRight className="w-5 h-5 text-white/15 mt-6 group-hover:text-purple-400 group-hover:translate-x-1 transition-all" />
                    </motion.button>
                  );
                })}
              </div>
            </div>
          </motion.section>
        )}
      </AnimatePresence>

      {/* 页面指示器 */}
      <div className="fixed right-5 top-1/2 -translate-y-1/2 z-40 flex flex-col items-end gap-1">
        {[
          { index: 0, label: '首页' },
          { index: 1, label: '工作台' },
          { index: 2, label: d.activeModule ? (modules.find(m => m.id === d.activeModule)?.label || '功能') : '功能' },
        ].map(({ index, label }) => (
          <button
            key={index}
            onClick={() => {
              if (index === 2 && d.activeModule) return;
              if (index < 2) d.setActiveModule(null);
              scrollToSection(index);
            }}
            className="group flex items-center gap-2 py-1"
          >
            <span className={`text-[10px] tracking-wide transition-all duration-200 ${
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
