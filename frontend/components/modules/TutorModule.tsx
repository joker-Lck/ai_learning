'use client';

import { Send, Lightbulb, Loader2 } from 'lucide-react';
import dynamic from 'next/dynamic';
import type { TutorMessage } from './types';

const MermaidDiagram = dynamic(() => import('./MermaidDiagram'), { ssr: false });

interface TutorModuleProps {
  question: string;
  setQuestion: (v: string) => void;
  tutorSubject: string;
  setTutorSubject: (v: string) => void;
  tutorLoading: boolean;
  tutorMessages: TutorMessage[];
  handleAskTutor: () => void;
  streamingContent?: string;
}

export default function TutorModule({
  question, setQuestion, tutorSubject, setTutorSubject,
  tutorLoading, tutorMessages, handleAskTutor, streamingContent,
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
                  {/* Mermaid 图表 */}
                  {msg.diagram && typeof msg.diagram === 'object' && 'mermaid' in msg.diagram && (
                    <MermaidDiagram chart={(msg.diagram as any).mermaid} />
                  )}
                  {/* 旧格式 diagram 兼容 */}
                  {msg.diagram && typeof msg.diagram === 'string' && (
                    <div className="mt-2 p-3 bg-white/[0.04] rounded-lg text-sm border border-white/[0.06]">
                      <div className="text-cyan-400 font-medium mb-1">📊 图解说明</div>
                      <div className="whitespace-pre-wrap">{msg.diagram}</div>
                    </div>
                  )}
                  {msg.example && (
                    <div className="mt-2 p-3 bg-white/[0.04] rounded-lg text-sm border border-white/[0.06]">
                      <div className="text-amber-400 font-medium mb-1">💡 示例</div>
                      {typeof msg.example === 'string' ? (
                        <pre className="whitespace-pre-wrap text-white/70">{msg.example}</pre>
                      ) : (
                        <pre className="whitespace-pre-wrap text-white/70">{JSON.stringify(msg.example, null, 2)}</pre>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
        {/* 流式输出中 */}
        {tutorLoading && streamingContent && (
          <div className="mb-4 flex justify-start">
            <div className="max-w-[85%] px-4 py-3 rounded-2xl bg-white/[0.06] text-white/80 border border-white/[0.06] rounded-bl-md">
              <div className="flex items-start gap-2">
                <div className="w-6 h-6 rounded-full bg-gradient-to-r from-amber-400 to-orange-400 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Lightbulb className="w-3 h-3 text-white" />
                </div>
                <div className="flex-1">
                  <div className="text-sm leading-relaxed whitespace-pre-wrap">{streamingContent}<span className="animate-pulse text-cyan-400">▌</span></div>
                </div>
              </div>
            </div>
          </div>
        )}
        {/* 等待 AI 响应 */}
        {tutorLoading && !streamingContent && (
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
