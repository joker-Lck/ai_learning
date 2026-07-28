'use client';

import { Send, Lightbulb, Loader2, Mic, MicOff, MessageCircle, HelpCircle, RefreshCw } from 'lucide-react';
import { memo, useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import type { TutorMessage } from './types';
import MarkdownRenderer from '@/components/shared/MarkdownRenderer';
import { useVoiceInput } from '@/lib/useVoiceInput';

const MermaidDiagram = dynamic(() => import('./MermaidDiagram'), { ssr: false });

/** 将 logic_graph 转换为 Mermaid 图表语法 */
function buildMermaidFromGraph(graph: { nodes: Array<{ id: string; label: string; type: string }>; edges: Array<{ source: string; target: string; relation: string }> }): string {
  let mermaid = 'graph LR\n';
  for (const node of graph.nodes) {
    const safeId = node.id.replace(/[^a-zA-Z0-9_]/g, '_');
    const safeLabel = node.label.replace(/"/g, "'");
    if (node.type === 'document') {
      mermaid += `  ${safeId}["📄 ${safeLabel}"]\n`;
    } else {
      mermaid += `  ${safeId}["${safeLabel}"]\n`;
    }
  }
  for (const edge of graph.edges) {
    const safeSource = edge.source.replace(/[^a-zA-Z0-9_]/g, '_');
    const safeTarget = edge.target.replace(/[^a-zA-Z0-9_]/g, '_');
    const safeRelation = edge.relation.replace(/"/g, "'");
    mermaid += `  ${safeSource} -->|"${safeRelation}"| ${safeTarget}\n`;
  }
  return mermaid;
}

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
  const [voiceError, setVoiceError] = useState('');
  const {
    isListening,
    transcript,
    toggleListening,
    isSupported: voiceSupported,
  } = useVoiceInput({
    lang: 'zh-CN',
    onResult: (text) => {
      setVoiceError('');
      setQuestion(text);
    },
    onError: (err) => {
      console.error('Voice error:', err);
      setVoiceError(err);
      setTimeout(() => setVoiceError(''), 5000);
    },
  });

  // 实时更新输入框（中间识别结果）
  useEffect(() => {
    if (isListening && transcript) {
      setQuestion(transcript);
    }
  }, [transcript, isListening]);
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
                  {/* Multi-Hop 推理链路可视化 */}
                  {msg.evidence_chain && msg.evidence_chain.length > 0 && (
                    <div className="mt-3 p-3 glass rounded-lg text-sm">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="text-cyan-400 font-medium">🔗 推理链路</div>
                        {msg.confidence !== undefined && (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300">
                            置信度: {(msg.confidence * 100).toFixed(0)}%
                          </span>
                        )}
                        {msg.hops_used !== undefined && (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300">
                            {msg.hops_used} 跳
                          </span>
                        )}
                      </div>
                      <div className="space-y-2">
                        {msg.evidence_chain.map((evidence, eIdx) => (
                          <div key={eIdx} className="flex items-start gap-2">
                            <div className="flex flex-col items-center">
                              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                                evidence.hop === 0
                                  ? 'bg-green-500/30 text-green-300'
                                  : evidence.hop === 1
                                  ? 'bg-blue-500/30 text-blue-300'
                                  : 'bg-purple-500/30 text-purple-300'
                              }`}>
                                {evidence.hop}
                              </div>
                              {eIdx < (msg.evidence_chain?.length ?? 0) - 1 && (
                                <div className="w-0.5 h-4 bg-white/10" />
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="text-white/90 font-medium truncate">{evidence.title}</span>
                                <span className="text-xs px-1.5 py-0.5 rounded bg-white/10 text-white/50">
                                  {evidence.relation}
                                </span>
                                <span className="text-xs text-white/40">
                                  {(evidence.score * 100).toFixed(0)}%
                                </span>
                              </div>
                              <p className="text-white/50 text-xs mt-0.5 line-clamp-2">{evidence.content}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {/* 知识关联图谱 (Mermaid) */}
                  {msg.logic_graph && msg.logic_graph.nodes.length > 0 && (
                    <div className="mt-3">
                      <div className="text-amber-400 font-medium text-sm mb-1">🕸️ 知识关联图</div>
                      <MermaidDiagram chart={buildMermaidFromGraph(msg.logic_graph)} />
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
                  {/* AI 追问按钮 */}
                  {msg.role === 'assistant' && idx === tutorMessages.length - 1 && !tutorLoading && (
                    <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-white/[0.06]">
                      {[
                        { label: '能再解释一下吗', icon: HelpCircle },
                        { label: '举个例子说明', icon: MessageCircle },
                        { label: '换个角度讲解', icon: RefreshCw },
                      ].map((btn) => {
                        const Icon = btn.icon;
                        return (
                          <button
                            key={btn.label}
                            onClick={() => setQuestion(btn.label)}
                            className="px-3 py-1.5 rounded-lg text-xs bg-white/[0.04] border border-white/[0.08] text-white/40 hover:text-white/70 hover:border-purple-400/30 hover:bg-purple-500/10 flex items-center gap-1.5 transition-all"
                          >
                            <Icon className="w-3 h-3" />
                            {btn.label}
                          </button>
                        );
                      })}
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
        {/* 语音状态提示 */}
        {isListening && (
          <div className="flex items-center gap-2 text-red-400 text-sm animate-pulse">
            <div className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
            正在聆听，请说话...
          </div>
        )}
        {voiceError && (
          <div className="flex items-center gap-2 text-amber-400 text-sm">
            <span>⚠️ {voiceError}</span>
          </div>
        )}
        <div>
          <label className="block text-base font-medium text-white/60 mb-2">学科</label>
          <input type="text" value={tutorSubject} onChange={(e) => setTutorSubject(e.target.value)}
            className="w-full px-4 py-3 glass-input text-white placeholder:text-white/20 rounded-lg text-base focus:outline-none" />
        </div>
        <div className="flex gap-3">
          {/* 语音输入按钮 */}
          {voiceSupported && (
            <button
              onClick={toggleListening}
              disabled={tutorLoading}
              className={`px-4 py-3 rounded-lg flex items-center gap-2 text-base transition-all ${
                isListening
                  ? 'bg-red-500 text-white animate-pulse'
                  : 'glass text-white/60 hover:text-white hover:bg-white/10'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
              title={isListening ? '停止录音' : '语音输入'}
            >
              {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              {isListening ? '停止' : '语音'}
            </button>
          )}
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleAskTutor()}
            placeholder={isListening ? '正在聆听...' : '输入你的问题...'}
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
