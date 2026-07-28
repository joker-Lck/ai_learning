'use client';

import type { QuizSession, QuizAnswer } from '../types';

interface Props {
  session: QuizSession;
  answers: Record<number, { userAnswer: string; isCorrect: boolean; correctAnswer: string; explanation?: string }>;
  onBack: () => void;
}

export default function QuizResultPanel({ session, answers, onBack }: Props) {
  const score = session.score || 0;
  const total = session.total_questions;
  const correct = session.correct_count;
  const wrong = total - correct;
  const accuracy = total > 0 ? Math.round(correct / total * 100) : 0;

  const grade = score >= 90 ? 'A' : score >= 80 ? 'B' : score >= 70 ? 'C' : score >= 60 ? 'D' : 'F';
  const gradeColor = score >= 90 ? 'text-emerald-400' : score >= 70 ? 'text-amber-400' : 'text-red-400';
  const ringColor = score >= 90 ? '#10b981' : score >= 70 ? '#f59e0b' : '#ef4444';

  const circumference = 2 * Math.PI * 54;
  const dashOffset = circumference - (score / 100) * circumference;

  return (
    <div className="p-6 max-w-2xl mx-auto">
      {/* Score Circle */}
      <div className="text-center mb-8">
        <div className="relative w-36 h-36 mx-auto mb-4">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="54" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
            <circle cx="60" cy="60" r="54" fill="none" stroke={ringColor} strokeWidth="8"
              strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={dashOffset}
              className="transition-all duration-1000" />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-3xl font-bold ${gradeColor}`}>{score}</span>
            <span className="text-xs text-white/40">分</span>
          </div>
        </div>
        <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${gradeColor} bg-white/5`}>
          {grade} · {accuracy}% 正确率
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        <div className="bg-[#1a1a27] rounded-xl border border-white/[0.05] p-4 text-center">
          <div className="text-2xl font-bold text-white">{total}</div>
          <div className="text-xs text-white/40">总题数</div>
        </div>
        <div className="bg-[#1a1a27] rounded-xl border border-white/[0.05] p-4 text-center">
          <div className="text-2xl font-bold text-emerald-400">{correct}</div>
          <div className="text-xs text-white/40">答对</div>
        </div>
        <div className="bg-[#1a1a27] rounded-xl border border-white/[0.05] p-4 text-center">
          <div className="text-2xl font-bold text-red-400">{wrong}</div>
          <div className="text-xs text-white/40">答错</div>
        </div>
      </div>

      {/* Wrong Answers Review */}
      {Object.entries(answers).filter(([_, a]) => !a.isCorrect).length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-medium text-white/60 mb-3">错题回顾</h4>
          <div className="space-y-3">
            {session.answers && session.answers.filter(a => !a.is_correct).map((a, i) => (
              <div key={i} className="bg-[#1a1a27] rounded-xl border border-white/[0.05] p-4">
                <div className="flex items-start gap-2 mb-2">
                  <span className="text-xs px-2 py-0.5 rounded bg-red-500/20 text-red-400 shrink-0">错题</span>
                  <p className="text-sm text-white/80">{a.question_text}</p>
                </div>
                <div className="flex items-center gap-4 text-xs">
                  <span className="text-white/40">你的答案：<span className="text-red-400">{a.user_answer || '未作答'}</span></span>
                  <span className="text-white/40">正确答案：<span className="text-emerald-400">{a.correct_answer}</span></span>
                </div>
                {a.explanation && (
                  <p className="mt-2 text-xs text-white/40 leading-relaxed">{a.explanation}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        <button onClick={onBack}
          className="flex-1 py-3 rounded-xl bg-white/5 border border-white/[0.05] text-white/70 text-sm hover:bg-white/[0.08] transition-all">
          再来一轮
        </button>
      </div>
    </div>
  );
}
