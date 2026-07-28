'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import type { QuizQuestion, QuizSession, ErrorNote } from './types';
import QuizStartPanel from './quiz/QuizStartPanel';
import QuizQuestionCard from './quiz/QuizQuestionCard';
import QuizResultPanel from './quiz/QuizResultPanel';
import QuizHistoryPanel from './quiz/QuizHistoryPanel';
import QuizStatsPanel from './quiz/QuizStatsPanel';

type QuizView = 'start' | 'playing' | 'result' | 'history' | 'stats';

export default function QuizModule() {
  const [view, setView] = useState<QuizView>('start');
  const [loading, setLoading] = useState(false);
  const [questions, setQuestions] = useState<QuizQuestion[]>([]);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, { userAnswer: string; isCorrect: boolean; correctAnswer: string; explanation?: string }>>({});
  const [sessionResult, setSessionResult] = useState<QuizSession | null>(null);
  const [startTime, setStartTime] = useState(Date.now());
  const [quizMode, setQuizMode] = useState<string>('practice');

  // 实时统计
  const answeredCount = Object.keys(answers).length;
  const correctCount = Object.values(answers).filter(a => a.isCorrect).length;
  const wrongCount = answeredCount - correctCount;
  const liveScore = answeredCount > 0 ? Math.round(correctCount / answeredCount * 100) : 0;

  const searchParams = useSearchParams();
  const autoStartRef = useRef(false);

  const handleStart = useCallback(async (config: {
    subject?: string; topic?: string; mode: string; questions: QuizQuestion[];
  }) => {
    setLoading(true);
    try {
      const res = await api.quizStart({
        subject: config.subject,
        topic: config.topic,
        mode: config.mode,
        questions: config.questions,
      }) as any;
      if (res.success) {
        setQuestions(res.data.questions);
        setSessionId(res.data.session_id);
        setCurrentIndex(0);
        setAnswers({});
        setStartTime(Date.now());
        setQuizMode(config.mode);
        setView('playing');
      }
    } catch (err) {
      console.error('开始答题失败:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // 从 URL 参数自动进入错题巩固模式
  useEffect(() => {
    if (autoStartRef.current) return;
    const mode = searchParams.get('mode');
    if (mode !== 'review') return;
    autoStartRef.current = true;

    const subject = searchParams.get('subject') || undefined;
    const count = parseInt(searchParams.get('count') || '10', 10);

    (async () => {
      setLoading(true);
      setView('start'); // 显示 start 面板以展示加载进度
      try {
        const res = await api.getErrorNotes(subject, 0) as any;
        if (res.success && Array.isArray(res.data) && res.data.length > 0) {
          const shuffled = [...res.data].sort(() => Math.random() - 0.5);
          const selected = shuffled.slice(0, count);
          const qs: QuizQuestion[] = selected.map((note: ErrorNote, i: number) => ({
            id: note.id || i,
            type: 'fill_blank' as const,
            question: note.question,
            options: [],
            answer: note.correct_answer || '',
            explanation: note.error_reason || '',
            difficulty: 'medium' as const,
            knowledge_point: note.chapter || note.subject,
          }));
          if (qs.length > 0) {
            await handleStart({ subject, mode: 'review', questions: qs });
          }
        }
      } catch (err) {
        console.error('错题巩固自动启动失败:', err);
      } finally {
        setLoading(false);
      }
    })();
  }, [searchParams, handleStart]);

  const handleSubmitAnswer = useCallback(async (userAnswer: string) => {
    if (!sessionId || !questions[currentIndex]) return;

    const q = questions[currentIndex];
    const timeSpent = Math.round((Date.now() - startTime) / 1000);

    try {
      const res = await api.quizSubmit({
        session_id: sessionId,
        question_index: currentIndex,
        question_type: q.type,
        question_text: q.question,
        options: q.options,
        correct_answer: q.answer,
        user_answer: userAnswer,
        explanation: q.explanation,
        knowledge_point: q.knowledge_point,
        difficulty: q.difficulty,
        time_spent: timeSpent,
      }) as any;

      if (res.success) {
        setAnswers(prev => ({
          ...prev,
          [currentIndex]: {
            userAnswer,
            isCorrect: res.data.is_correct,
            correctAnswer: res.data.correct_answer,
            explanation: res.data.explanation,
          },
        }));

        // 错题重练模式：提交复习结果，更新间隔重复调度
        if (quizMode === 'review' && q.id) {
          api.submitReviewResult(q.id, res.data.is_correct).catch(() => {});
        }
      }
    } catch (err) {
      console.error('提交答案失败:', err);
    }
  }, [sessionId, questions, currentIndex, startTime]);

  const handleNext = useCallback(() => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(prev => prev + 1);
      setStartTime(Date.now());
    }
  }, [currentIndex, questions.length]);

  const handleFinish = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const res = await api.quizFinish(sessionId) as any;
      if (res.success) {
        setSessionResult(res.data);
        setView('result');
      }
    } catch (err) {
      console.error('结束答题失败:', err);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  const handleBackToStart = useCallback(() => {
    setView('start');
    setQuestions([]);
    setSessionId(null);
    setCurrentIndex(0);
    setAnswers({});
    setSessionResult(null);
    setQuizMode('practice');
  }, []);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.05]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center">
            <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" /></svg>
          </div>
          <h2 className="text-lg font-semibold text-white">在线做题</h2>
        </div>
        <div className="flex items-center gap-2">
          {view !== 'start' && (
            <button onClick={handleBackToStart} className="px-3 py-1.5 text-xs text-white/50 hover:text-white/80 rounded-lg hover:bg-white/5 transition-colors">
              返回
            </button>
          )}
          <button onClick={() => setView('history')} className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${view === 'history' ? 'bg-purple-500/20 text-purple-300' : 'text-white/50 hover:text-white/80 hover:bg-white/5'}`}>
            历史
          </button>
          <button onClick={() => setView('stats')} className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${view === 'stats' ? 'bg-purple-500/20 text-purple-300' : 'text-white/50 hover:text-white/80 hover:bg-white/5'}`}>
            统计
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {view === 'start' && <QuizStartPanel onStart={handleStart} loading={loading} />}
        {view === 'playing' && questions.length > 0 && (
          <QuizQuestionCard
            question={questions[currentIndex]!}
            index={currentIndex}
            total={questions.length}
            answer={answers[currentIndex]}
            onSubmit={handleSubmitAnswer}
            onNext={handleNext}
            onFinish={handleFinish}
            loading={loading}
            answeredCount={answeredCount}
            correctCount={correctCount}
            wrongCount={wrongCount}
            liveScore={liveScore}
          />
        )}
        {view === 'result' && sessionResult && (
          <QuizResultPanel session={sessionResult} answers={answers} onBack={handleBackToStart} />
        )}
        {view === 'history' && <QuizHistoryPanel />}
        {view === 'stats' && <QuizStatsPanel />}
      </div>
    </div>
  );
}
