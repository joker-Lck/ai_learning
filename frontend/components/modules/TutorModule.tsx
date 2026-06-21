'use client';

import { Send, Lightbulb, Loader2 } from 'lucide-react';
import { memo } from 'react';
import dynamic from 'next/dynamic';
import type { TutorMessage } from './types';
import MarkdownRenderer from '@/components/shared/MarkdownRenderer';

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

export default memo(function TutorModule({
  question, setQuestion, tutorSubject, setTutorSubject,
  tutorLoading, tutorMessages, handleAskTutor, streamingContent,
}: TutorModuleProps) {
  return (
    <div className="space-y-8">
      <h3 className="text-3xl font-bold text-white">智能辅导系统</h3>

      <div className="min-h-[60vh] max-h-[70vh] overflow-y-auto p-6 space-y-5">
        {tutorMessages.map((msg, idx) => (
            <div key={idx} className={`mb-4 flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] px-5 py-4 rounded-xl ${
                msg.role === 'user'
                  ? 'bg-purple-500 text-white'
                  : 'glass text-white/80'
              }`}>
              <div className="flex items-start gap-3">
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-r from-amber-400 to-orange-400 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Lightbulb className="w-4 h-4 text-white" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <div className="text-sm opacity-70 mb-1.5">{msg.timestamp.toLocaleTimeString()}</div>
                  {/* Markdown 渲染 */}
                  <MarkdownRenderer content={msg.content} className={msg.role === 'user' ? '[&_*]:!text-white/90' : ''} />
                  {/* Mermaid 图表 */}
                  {msg.diagram && typeof msg.diagram === 'object' && 'mermaid' in msg.diagram && (
                    <MermaidDiagram chart={(msg.diagram as any).mermaid} />
                  )}
                  {/* 旧格式 diagram 兼容 */}
                  {msg.diagram && typeof msg.diagram === 'string' && (
                    <div className="mt-2 p-3 glass rounded-lg text-sm">
                      <div className="text-purple-400 font-medium mb-1">📊 图解说明</div>
                      <MarkdownRenderer content={msg.diagram} />
                    </div>
                  )}
                  {msg.example && (
                    <div className="mt-2 p-3 glass rounded-lg text-sm">
                      <div className="text-amber-400 font-medium mb-1">💡 示例</div>
                      {typeof msg.example === 'string' ? (
                        <MarkdownRenderer content={msg.example} />
                      ) : (
                        <MarkdownRenderer content={'```json\n' + JSON.stringify(msg.example, null, 2) + '\n```'} />
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
            <div className="max-w-[85%] px-5 py-4 rounded-xl glass text-white/80">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-amber-400 to-orange-400 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Lightbulb className="w-4 h-4 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <MarkdownRenderer content={streamingContent} />
                  <span className="animate-pulse text-purple-400">▌</span>
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

      <div className="space-y-4 pt-4 border-t border-glass">
        <div>
          <label className="block text-base font-medium text-white/60 mb-2">学科</label>
          <input type="text" value={tutorSubject} onChange={(e) => setTutorSubject(e.target.value)}
            className="w-full px-4 py-3 glass-input text-white placeholder:text-white/20 rounded-lg text-base focus:outline-none" />
        </div>
        <div className="flex gap-3">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleAskTutor()}
            placeholder="输入你的问题..."
            className="flex-1 px-5 py-3 glass-input text-white placeholder:text-white/20 rounded-lg text-base focus:outline-none"
            disabled={tutorLoading}
          />
          <button
            onClick={handleAskTutor}
            disabled={tutorLoading || !question.trim()}
            className="px-8 py-3 bg-purple-500 text-white rounded-lg hover:bg-purple-400 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 text-base transition-colors"
          >
            {tutorLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            提问
          </button>
        </div>
      </div>
    </div>
  );
});
