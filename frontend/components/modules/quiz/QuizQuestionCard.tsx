'use client';

import { useState, useEffect } from 'react';
import type { QuizQuestion } from '../types';

interface Props {
  question: QuizQuestion;
  index: number;
  total: number;
  answer?: { userAnswer: string; isCorrect: boolean; correctAnswer: string; explanation?: string };
  onSubmit: (userAnswer: string) => void;
  onNext: () => void;
  onFinish: () => void;
  loading: boolean;
  answeredCount?: number;
  correctCount?: number;
  wrongCount?: number;
  liveScore?: number;
}

export default function QuizQuestionCard({ question, index, total, answer, onSubmit, onNext, onFinish, loading, answeredCount = 0, correctCount = 0, wrongCount = 0, liveScore = 0 }: Props) {
  const [selected, setSelected] = useState('');
  const [inputValue, setInputValue] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    setSelected('');
    setInputValue('');
    setSubmitted(false);
    setElapsed(0);
  }, [index]);

  useEffect(() => {
    const timer = setInterval(() => setElapsed(prev => prev + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const handleSubmit = () => {
    const userAnswer = question.type === 'fill_blank' ? inputValue : selected;
    if (!userAnswer) return;
    onSubmit(userAnswer);
    setSubmitted(true);
  };

  const formatTime = (s: number) => `${Math.floor(s / 60)}:${(s % 60).toString().padStart(2, '0')}`;

  const diffColor = question.difficulty === 'easy' ? 'text-emerald-400' : question.difficulty === 'hard' ? 'text-red-400' : 'text-amber-400';
  const diffLabel = question.difficulty === 'easy' ? '简单' : question.difficulty === 'hard' ? '困难' : '中等';

  return (
    <div className="p-6 max-w-2xl mx-auto">
      {/* Progress */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <span className="text-sm text-white/50">第 {index + 1}/{total} 题</span>
          <span className={`text-xs px-2 py-0.5 rounded-full bg-white/5 ${diffColor}`}>{diffLabel}</span>
          {question.knowledge_point && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400">{question.knowledge_point}</span>
          )}
        </div>
        <span className="text-sm text-white/30 font-mono">{formatTime(elapsed)}</span>
      </div>

      {/* Progress bar */}
      <div className="w-full h-1 bg-white/5 rounded-full mb-4 overflow-hidden">
        <div className="h-full bg-gradient-to-r from-purple-500 to-violet-500 rounded-full transition-all duration-300"
          style={{ width: `${((index + 1) / total) * 100}%` }} />
      </div>

      {/* 实时计分板 */}
      {answeredCount > 0 && (
        <div className="mb-4 p-3 rounded-xl bg-[#1a1a27] border border-white/[0.05] grid grid-cols-4 gap-3 text-center">
          <div>
            <div className="text-lg font-bold text-white">{answeredCount}/{total}</div>
            <div className="text-[10px] text-white/30">已答</div>
          </div>
          <div>
            <div className="text-lg font-bold text-emerald-400">{correctCount}</div>
            <div className="text-[10px] text-white/30">正确</div>
          </div>
          <div>
            <div className="text-lg font-bold text-red-400">{wrongCount}</div>
            <div className="text-[10px] text-white/30">错误</div>
          </div>
          <div>
            <div className={`text-lg font-bold ${liveScore >= 80 ? 'text-emerald-400' : liveScore >= 60 ? 'text-amber-400' : 'text-red-400'}`}>{liveScore}%</div>
            <div className="text-[10px] text-white/30">正确率</div>
          </div>
        </div>
      )}

      {/* Question */}
      <div className="bg-[#1a1a27] rounded-xl border border-white/[0.05] p-6 mb-6">
        <div className="flex items-start gap-2 mb-4">
          <span className="text-xs px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 shrink-0 mt-0.5">
            {question.type === 'multiple_choice' ? '选择题' : question.type === 'judge' ? '判断题' : '填空题'}
          </span>
          <p className="text-white text-base leading-relaxed">{question.question}</p>
        </div>

        {/* Options */}
        {question.type === 'multiple_choice' && question.options && (
          <div className="space-y-2 mt-4">
            {question.options.map((opt, i) => {
              const optLabel = typeof opt === 'string' && opt.match(/^[A-D][.、.]/) ? opt.charAt(0) : String.fromCharCode(65 + i);
              const optText = typeof opt === 'string' && opt.match(/^[A-D][.、.]/) ? opt.substring(opt.search(/[.、.]/) + 1).trim() : opt;
              const isSelected = selected === optLabel;
              const isCorrect = answer && optLabel === answer.correctAnswer;
              const isWrong = answer && isSelected && !answer.isCorrect;

              return (
                <button key={i} onClick={() => !submitted && setSelected(optLabel)} disabled={submitted}
                  className={`w-full p-3 rounded-lg border text-left transition-all flex items-center gap-3 ${
                    submitted && isCorrect ? 'border-emerald-500/50 bg-emerald-500/10' :
                    submitted && isWrong ? 'border-red-500/50 bg-red-500/10' :
                    isSelected ? 'border-purple-500/50 bg-purple-500/10' :
                    'border-white/[0.05] bg-white/[0.02] hover:border-white/[0.1] hover:bg-white/[0.04]'
                  }`}>
                  <span className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-medium shrink-0 ${
                    submitted && isCorrect ? 'bg-emerald-500/30 text-emerald-300' :
                    submitted && isWrong ? 'bg-red-500/30 text-red-300' :
                    isSelected ? 'bg-purple-500/30 text-purple-300' :
                    'bg-white/5 text-white/40'
                  }`}>{optLabel}</span>
                  <span className={`text-sm ${isSelected ? 'text-white' : 'text-white/70'}`}>{optText}</span>
                </button>
              );
            })}
          </div>
        )}

        {/* Judge */}
        {question.type === 'judge' && (
          <div className="grid grid-cols-2 gap-3 mt-4">
            {[
              { label: '正确', value: 'true', icon: '✓' },
              { label: '错误', value: 'false', icon: '✗' },
            ].map(opt => {
              const isSelected = selected === opt.value;
              const isCorrect = answer && (answer.correctAnswer === opt.value || answer.correctAnswer === 'true');
              const isWrong = answer && isSelected && !answer.isCorrect;

              return (
                <button key={opt.value} onClick={() => !submitted && setSelected(opt.value)} disabled={submitted}
                  className={`p-4 rounded-xl border text-center transition-all ${
                    submitted && isCorrect ? 'border-emerald-500/50 bg-emerald-500/10' :
                    submitted && isWrong ? 'border-red-500/50 bg-red-500/10' :
                    isSelected ? 'border-purple-500/50 bg-purple-500/10' :
                    'border-white/[0.05] bg-white/[0.02] hover:border-white/[0.1]'
                  }`}>
                  <span className={`text-2xl ${isSelected ? 'text-purple-400' : 'text-white/30'}`}>{opt.icon}</span>
                  <div className="text-sm text-white/70 mt-1">{opt.label}</div>
                </button>
              );
            })}
          </div>
        )}

        {/* Fill blank */}
        {question.type === 'fill_blank' && (
          <div className="mt-4">
            <input type="text" value={inputValue} onChange={e => setInputValue(e.target.value)} disabled={submitted}
              placeholder="输入你的答案..."
              className="w-full px-4 py-3 bg-white/5 border border-white/[0.06] rounded-lg text-white placeholder-white/20 focus:outline-none focus:border-purple-500/30 disabled:opacity-50" />
          </div>
        )}
      </div>

      {/* Feedback */}
      {submitted && answer && (
        <div className={`mb-6 p-4 rounded-xl border ${answer.isCorrect ? 'border-emerald-500/20 bg-emerald-500/5' : 'border-red-500/20 bg-red-500/5'}`}>
          <div className="flex items-center gap-2 mb-2">
            <span className={`text-lg ${answer.isCorrect ? 'text-emerald-400' : 'text-red-400'}`}>
              {answer.isCorrect ? '✓ 回答正确！' : '✗ 回答错误'}
            </span>
          </div>
          {!answer.isCorrect && (
            <p className="text-sm text-white/60 mb-2">正确答案：<span className="text-emerald-400 font-medium">{answer.correctAnswer}</span></p>
          )}
          {answer.explanation && (
            <div className="mt-2 pt-2 border-t border-white/[0.05]">
              <p className="text-xs text-white/40 mb-1">解析：</p>
              <p className="text-sm text-white/60 leading-relaxed">{answer.explanation}</p>
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-end gap-3">
        {!submitted ? (
          <button onClick={handleSubmit} disabled={(!selected && !inputValue) || loading}
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-purple-500 to-violet-500 text-white text-sm font-medium hover:from-purple-600 hover:to-violet-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all">
            提交答案
          </button>
        ) : index < total - 1 ? (
          <button onClick={onNext}
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-purple-500 to-violet-500 text-white text-sm font-medium hover:from-purple-600 hover:to-violet-600 transition-all">
            下一题 →
          </button>
        ) : (
          <button onClick={onFinish} disabled={loading}
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 text-white text-sm font-medium hover:from-emerald-600 hover:to-teal-600 disabled:opacity-50 transition-all">
            {loading ? '计算中...' : '查看成绩'}
          </button>
        )}
      </div>
    </div>
  );
}
