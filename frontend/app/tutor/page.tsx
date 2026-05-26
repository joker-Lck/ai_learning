'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { useAuthStore } from '@/stores';
import api from '@/lib/api';
import { tutorAnswer } from '@/lib/kimi-api';
import {
  Lightbulb, Send, MessageSquare, BookOpen,
  Code, Image, Loader2, Sparkles, User
} from 'lucide-react';

interface TutorMessage {
  role: 'user' | 'assistant';
  content: string;
  diagram?: string;
  example?: string;
  timestamp: Date;
}

export default function TutorPage() {
  const { user, isGuest } = useAuthStore();
  const [question, setQuestion] = useState('');
  const [subject, setSubject] = useState('机器学习');
  const [preferredFormat, setPreferredFormat] = useState('all');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<TutorMessage[]>([]);

  const askQuestion = async () => {
    if (!question.trim()) return;

    const userMessage: TutorMessage = {
      role: 'user',
      content: question.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setQuestion('');
    setLoading(true);

    try {
      console.log('🚀 开始AI辅导答疑:', { question: userMessage.content, subject });
      
      // 前端直接调用AI进行辅导
      const answerData = await tutorAnswer(userMessage.content, subject, preferredFormat);
      
      console.log('✅ 辅导回答生成成功');
      
      const assistantMessage: TutorMessage = {
        role: 'assistant',
        content: answerData.text_answer,
        diagram: answerData.diagram || undefined,
        example: answerData.code_example || undefined,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (err: any) {
      console.error('答疑失败:', err);
      alert('答疑失败：' + (err.message || '网络错误'));
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      askQuestion();
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* 页面标题 */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center">
            <Lightbulb className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-800">智能辅导系统</h1>
            <p className="text-sm text-gray-500">
              多模态智能答疑，文字+图解+代码实例
            </p>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* 左侧：问题输入 */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="lg:col-span-1 space-y-4"
        >
          {/* 配置 */}
          <div className="bg-white rounded-2xl shadow-card p-6">
            <h3 className="font-bold text-gray-800 mb-4">问题配置</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  学科
                </label>
                <input
                  type="text"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:border-green-500 text-sm"
                  disabled={isGuest}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  回答格式
                </label>
                <select
                  value={preferredFormat}
                  onChange={(e) => setPreferredFormat(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:border-green-500 text-sm"
                  disabled={isGuest}
                >
                  <option value="all">全部（文字+图解+代码）</option>
                  <option value="text">仅文字</option>
                  <option value="diagram">文字+图解</option>
                  <option value="code">文字+代码</option>
                </select>
              </div>
            </div>
          </div>

          {/* 输入框 */}
          <div className="bg-white rounded-2xl shadow-card p-6">
            <h3 className="font-bold text-gray-800 mb-4">提问</h3>
            
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyPress={handleKeyPress}
              rows={6}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:border-green-500 text-sm resize-none"
              placeholder="输入您的问题..."
              disabled={loading || isGuest}
            />

            <button
              onClick={askQuestion}
              disabled={loading || isGuest || !question.trim()}
              className="w-full mt-3 px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed font-medium flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  思考中...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  发送问题
                </>
              )}
            </button>
          </div>

          {/* 快捷问题 */}
          <div className="bg-white rounded-2xl shadow-card p-6">
            <h3 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-green-500" />
              快捷问题
            </h3>
            <div className="space-y-2">
              {[
                '什么是反向传播算法？',
                '解释梯度下降的原理',
                '什么是过拟合？如何避免？',
                '卷积神经网络的工作原理'
              ].map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => setQuestion(q)}
                  disabled={loading || isGuest}
                  className="w-full text-left px-3 py-2 bg-gray-50 hover:bg-green-50 hover:text-green-700 rounded-lg text-xs transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        </motion.div>

        {/* 右侧：对话区域 */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="lg:col-span-3"
        >
          <div className="bg-white rounded-2xl shadow-card overflow-hidden h-[calc(100vh-200px)] flex flex-col">
            {/* 对话头部 */}
            <div className="p-4 border-b border-gray-100">
              <h3 className="font-bold text-gray-800 flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-green-500" />
                辅导对话
              </h3>
            </div>

            {/* 消息列表 */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {messages.length === 0 && (
                <div className="text-center text-gray-400 py-20">
                  <Lightbulb className="w-16 h-16 mx-auto mb-4 opacity-20" />
                  <p>开始提问，获取多模态智能辅导</p>
                  <p className="text-xs mt-2">支持文字解释、图解说明、代码示例</p>
                </div>
              )}

              {messages.map((msg, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[80%] ${msg.role === 'user' ? 'order-2' : 'order-1'}`}>
                    {/* 头像 */}
                    <div className={`flex items-center gap-2 mb-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        msg.role === 'user'
                          ? 'bg-gradient-to-br from-blue-500 to-cyan-500'
                          : 'bg-gradient-to-br from-green-500 to-emerald-500'
                      }`}>
                        {msg.role === 'user' ? (
                          <User className="w-4 h-4 text-white" />
                        ) : (
                          <Lightbulb className="w-4 h-4 text-white" />
                        )}
                      </div>
                      <span className="text-xs text-gray-500">
                        {msg.role === 'user' ? '您' : 'AI辅导员'}
                      </span>
                    </div>

                    {/* 消息内容 */}
                    <div className={`rounded-2xl p-4 ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white'
                        : 'bg-gray-50 text-gray-800'
                    }`}>
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>

                      {/* 图解 */}
                      {msg.diagram && (
                        <div className="mt-3 p-3 bg-white rounded-lg border border-gray-200">
                          <div className="flex items-center gap-2 mb-2">
                            <Image className="w-4 h-4 text-green-500" />
                            <span className="text-xs font-semibold text-gray-700">图解说明</span>
                          </div>
                          <pre className="text-xs text-gray-600 whitespace-pre-wrap font-mono">
                            {msg.diagram}
                          </pre>
                        </div>
                      )}

                      {/* 代码示例 */}
                      {msg.example && (
                        <div className="mt-3 p-3 bg-gray-900 rounded-lg">
                          <div className="flex items-center gap-2 mb-2">
                            <Code className="w-4 h-4 text-green-400" />
                            <span className="text-xs font-semibold text-gray-300">代码示例</span>
                          </div>
                          <pre className="text-xs text-green-400 whitespace-pre-wrap font-mono">
                            {msg.example}
                          </pre>
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}

              {loading && (
                <div className="flex justify-start">
                  <div className="bg-gray-50 rounded-2xl p-4">
                    <Loader2 className="w-5 h-5 animate-spin text-green-500" />
                  </div>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
