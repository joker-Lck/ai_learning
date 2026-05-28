'use client';

import { Send, Lightbulb, Loader2 } from 'lucide-react';
import type { TutorMessage } from './types';

interface TutorModuleProps {
  question: string;
  setQuestion: (v: string) => void;
  tutorSubject: string;
  setTutorSubject: (v: string) => void;
  tutorLoading: boolean;
  tutorMessages: TutorMessage[];
  handleAskTutor: () => void;
}

export default function TutorModule({
  question, setQuestion, tutorSubject, setTutorSubject,
  tutorLoading, tutorMessages, handleAskTutor,
}: TutorModuleProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-white">智能辅导系统</h3>

      <div className="glass-card rounded-2xl p-6 min-h-[500px] max-h-[600px] overflow-y-auto">
        {tutorMessages.map((msg, idx) => (
          <div key={idx} className={`mb-4 flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] px-4 py-3 rounded-2xl ${
              msg.role === 'user'
                ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-br-md'
                : 'bg-white/[0.06] text-white/80 border border-white/[0.06] rounded-bl-md'
            }`}>
              <div className="flex items-start gap-2">
                {msg.role === 'assistant' && (
                  <div className="w-6 h-6 rounded-full bg-gradient-to-r from-amber-400 to-orange-400 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Lightbulb className="w-3 h-3 text-white" />
                  </div>
                )}
                <div className="flex-1">
                  <div className="text-xs opacity-70 mb-1">{msg.timestamp.toLocaleTimeString()}</div>
                  <div className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</div>
                  {msg.diagram && (
                    <div className="mt-2 p-2 bg-white/[0.04] rounded-lg text-sm border border-white/[0.06]"> {msg.diagram}</div>
                  )}
                  {msg.example && (
                    <div className="mt-2 p-2 bg-white/[0.04] rounded-lg text-sm border border-white/[0.06]"> 示例: {msg.example}</div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
        {tutorLoading && (
          <div className="flex items-center gap-2 text-white/40">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>AI思考中...</span>
          </div>
        )}
      </div>

      <div className="glass-card rounded-xl p-4 space-y-3">
        <div>
          <label className="block text-sm font-medium text-white/60 mb-1">学科</label>
          <input type="text" value={tutorSubject} onChange={(e) => setTutorSubject(e.target.value)}
            className="w-full px-3 py-2 bg-white/[0.04] border border-white/[0.08] text-white placeholder:text-white/15 rounded-lg focus:border-cyan-400/30 focus:outline-none" />
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleAskTutor()}
            placeholder="输入你的问题..."
            className="flex-1 px-4 py-2 bg-white/[0.04] border border-white/[0.08] text-white placeholder:text-white/15 rounded-lg focus:border-cyan-400/30 focus:outline-none"
            disabled={tutorLoading}
          />
          <button
            onClick={handleAskTutor}
            disabled={tutorLoading || !question.trim()}
            className="px-6 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {tutorLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            提问
          </button>
        </div>
      </div>
    </div>
  );
}
