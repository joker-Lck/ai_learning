'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuthStore } from '@/stores';
import api from '@/lib/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Brain, Zap, Clock, CheckCircle, AlertCircle,
  Loader2, FileText, GitBranch, FileCode, Video,
  BookOpen, Code2, Eye, Download, ChevronDown, ChevronUp,
  Sparkles, Target, Lightbulb
} from 'lucide-react';

// 资源类型定义
const RESOURCE_TYPES = [
  { value: 'document', label: '课程文档', icon: FileText, color: 'blue', desc: '结构化讲解文档' },
  { value: 'mindmap', label: '思维导图', icon: GitBranch, color: 'purple', desc: '知识点树状结构' },
  { value: 'quiz', label: '练习题目', icon: FileCode, color: 'green', desc: '选择/填空/解答题' },
  { value: 'video', label: '视频脚本', icon: Video, color: 'red', desc: '教学视频分镜脚本' },
  { value: 'animation', label: '动画脚本', icon: Zap, color: 'orange', desc: '动画演示分帧描述' },
  { value: 'code_case', label: '代码案例', icon: Code2, color: 'cyan', desc: '完整可运行代码' },
  { value: 'reading', label: '拓展阅读', icon: BookOpen, color: 'indigo', desc: '前沿知识与案例' },
];

const DIFFICULTY_OPTIONS = [
  { value: 'beginner', label: '入门', emoji: '🌱' },
  { value: 'intermediate', label: '中级', emoji: '🌿' },
  { value: 'advanced', label: '高级', emoji: '🌳' },
];

const COLOR_MAP: Record<string, { bg: string; border: string; text: string; badge: string; dot: string; tag: string }> = {
  blue: { bg: 'bg-cyan-400/[0.06]', border: 'border-cyan-400/20', text: 'text-cyan-400', badge: 'bg-cyan-400/[0.1] text-cyan-400', dot: 'bg-cyan-400', tag: 'bg-cyan-400/[0.1] text-cyan-400' },
  purple: { bg: 'bg-violet-400/[0.06]', border: 'border-violet-400/20', text: 'text-violet-400', badge: 'bg-violet-400/[0.1] text-violet-400', dot: 'bg-violet-400', tag: 'bg-violet-400/[0.1] text-violet-400' },
  green: { bg: 'bg-emerald-400/[0.06]', border: 'border-emerald-400/20', text: 'text-emerald-400', badge: 'bg-emerald-400/[0.1] text-emerald-400', dot: 'bg-emerald-400', tag: 'bg-emerald-400/[0.1] text-emerald-400' },
  red: { bg: 'bg-red-400/[0.06]', border: 'border-red-400/20', text: 'text-red-400', badge: 'bg-red-400/[0.1] text-red-400', dot: 'bg-red-400', tag: 'bg-red-400/[0.1] text-red-400' },
  orange: { bg: 'bg-amber-400/[0.06]', border: 'border-amber-400/20', text: 'text-amber-400', badge: 'bg-amber-400/[0.1] text-amber-400', dot: 'bg-amber-400', tag: 'bg-amber-400/[0.1] text-amber-400' },
  cyan: { bg: 'bg-cyan-400/[0.06]', border: 'border-cyan-400/20', text: 'text-cyan-400', badge: 'bg-cyan-400/[0.1] text-cyan-400', dot: 'bg-cyan-400', tag: 'bg-cyan-400/[0.1] text-cyan-400' },
  indigo: { bg: 'bg-indigo-400/[0.06]', border: 'border-indigo-400/20', text: 'text-indigo-400', badge: 'bg-indigo-400/[0.1] text-indigo-400', dot: 'bg-indigo-400', tag: 'bg-indigo-400/[0.1] text-indigo-400' },
};

interface ResourceItem {
  type: string;
  title: string;
  content_data: any;
  status: 'generating' | 'complete' | 'error';
  duration_minutes?: number;
}

export default function ResourcesPage() {
  const { isGuest } = useAuthStore();
  const [subject, setSubject] = useState('机器学习');
  const [topic, setTopic] = useState('神经网络');
  const [selectedTypes, setSelectedTypes] = useState<string[]>(['document', 'quiz', 'mindmap', 'video', 'animation']);
  const [difficulty, setDifficulty] = useState('intermediate');
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [resources, setResources] = useState<ResourceItem[]>([]);
  const [expandedCards, setExpandedCards] = useState<Set<number>>(new Set());
  const [previewResource, setPreviewResource] = useState<ResourceItem | null>(null);
  const [downloadingIdx, setDownloadingIdx] = useState<number | null>(null);

  const toggleType = (type: string) => {
    setSelectedTypes(prev =>
      prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type]
    );
  };

  const toggleExpand = (idx: number) => {
    setExpandedCards(prev => {
      const next = new Set(prev);
      next.has(idx) ? next.delete(idx) : next.add(idx);
      return next;
    });
  };

  const startGeneration = async () => {
    if (selectedTypes.length === 0) return;

    setLoading(true);
    setProgress(0);
    setCurrentStep('正在连接多智能体系统...');
    // 不清空已有结果，追加新资源
    setExpandedCards(new Set());

    try {
      const total = selectedTypes.length;
      const results: ResourceItem[] = [...resources]; // 保留已有资源

      for (let i = 0; i < total; i++) {
        const type = selectedTypes[i];
        const typeInfo = RESOURCE_TYPES.find(t => t.value === type);
        setCurrentStep(`🤖 ${typeInfo?.label || type} 生成中...`);
        setProgress(Math.round((i / total) * 80));

        try {
          const response: any = await api.generateResources({
            subject,
            topic,
            resource_types: [type],
            difficulty,
          });

          if (response.success && response.data?.resources?.length > 0) {
            for (const r of response.data.resources) {
              results.push({
                type: r.type || type,
                title: r.title || `${topic} - ${typeInfo?.label}`,
                content_data: r.content_data || r,
                status: 'complete',
                duration_minutes: r.duration_minutes,
              });
            }
          } else {
            results.push({
              type,
              title: `${topic} - ${typeInfo?.label}(生成失败)`,
              content_data: { error: response.message || '生成失败' },
              status: 'error',
            });
          }
        } catch (err: any) {
          results.push({
            type,
            title: `${topic} - ${typeInfo?.label}(请求失败)`,
            content_data: { error: err.message || '网络错误' },
            status: 'error',
          });
        }

        setResources([...results]);
      }

      setProgress(100);
      setCurrentStep('✅ 全部完成');
    } catch (err: any) {
      setCurrentStep('❌ 生成失败: ' + (err.message || '未知错误'));
    } finally {
      setLoading(false);
    }
  };

  /** 导出单个资源文件 */
  const handleExport = async (resource: ResourceItem, idx: number) => {
    setDownloadingIdx(idx);
    try {
      const res: any = await api.exportResource(resource);
      if (res.success && res.data) {
        // 从 file_path 中提取文件名，通过 /exports/ 路径下载
        const filePath: string = res.data.file_path.replace(/\\/g, '/');
        const fileName = filePath.split('/').pop() || filePath;
        const fileUrl = `/exports/${fileName}`;
        const a = document.createElement('a');
        a.href = fileUrl;
        a.download = res.data.filename || fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      } else {
        alert('导出失败：' + (res.message || '未知错误'));
      }
    } catch (err: any) {
      alert('导出失败：' + (err.message || '网络错误'));
    } finally {
      setDownloadingIdx(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* 页面标题 */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ type: 'spring', stiffness: 200, damping: 25 }} className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">智能资源生成中心</h1>
            <p className="text-sm text-white/60">多智能体协同生成 7 种类型的个性化学习资源</p>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ===== 左侧：配置面板 ===== */}
        <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ type: 'spring', stiffness: 200, damping: 25 }} className="lg:col-span-1">
          <div className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-6 sticky top-6">
            <h2 className="font-bold text-white mb-4 flex items-center gap-2">
              <Zap className="w-5 h-5 text-cyan-400" />
              生成配置
            </h2>

            {/* 学科 & 主题 */}
            <div className="space-y-3 mb-5">
              <div>
                <label className="block text-sm font-medium text-white/60 mb-1">学科</label>
                <input
                  type="text" value={subject} onChange={e => setSubject(e.target.value)}
                  className="w-full px-3 py-2 bg-white/[0.04] border border-white/[0.08] text-white text-sm placeholder:text-white/15 focus:border-cyan-400/30 focus:ring-1 focus:ring-cyan-400/20 outline-none rounded-xl transition-all"
                  placeholder="例如：机器学习" disabled={loading || isGuest}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white/60 mb-1">主题</label>
                <input
                  type="text" value={topic} onChange={e => setTopic(e.target.value)}
                  className="w-full px-3 py-2 bg-white/[0.04] border border-white/[0.08] text-white text-sm placeholder:text-white/15 focus:border-cyan-400/30 focus:ring-1 focus:ring-cyan-400/20 outline-none rounded-xl transition-all"
                  placeholder="例如：神经网络" disabled={loading || isGuest}
                />
              </div>
            </div>

            {/* 难度 */}
            <div className="mb-5">
              <label className="block text-sm font-medium text-white/60 mb-2">难度级别</label>
              <div className="grid grid-cols-3 gap-2">
                {DIFFICULTY_OPTIONS.map(opt => (
                  <button key={opt.value} onClick={() => setDifficulty(opt.value)} disabled={loading || isGuest}
                    className={`px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                      difficulty === opt.value
                        ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white'
                        : 'bg-white/[0.04] text-white/40 hover:bg-white/[0.08]'
                    } disabled:opacity-50`}>
                    {opt.emoji} {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* 资源类型 */}
            <div className="mb-5">
              <label className="block text-sm font-medium text-white/60 mb-2">
                资源类型 <span className="text-white/30 font-normal">({selectedTypes.length} 已选)</span>
              </label>
              <div className="space-y-2">
                {RESOURCE_TYPES.map(type => {
                  const Icon = type.icon;
                  const sel = selectedTypes.includes(type.value);
                  const colors = COLOR_MAP[type.color];
                  return (
                    <button key={type.value} onClick={() => toggleType(type.value)} disabled={loading || isGuest}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl border transition-all text-left ${
                        sel ? `${colors.border} ${colors.bg}` : 'border-white/[0.06] hover:border-white/[0.12] bg-white/[0.02]'
                      } disabled:opacity-50`}>
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${sel ? colors.bg : 'bg-white/[0.04]'}`}>
                        <Icon className={`w-4 h-4 ${sel ? colors.text : 'text-white/30'}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <span className={`text-sm font-medium ${sel ? 'text-white' : 'text-white/60'}`}>{type.label}</span>
                        <p className="text-xs text-white/30 truncate">{type.desc}</p>
                      </div>
                      {sel && <CheckCircle className={`w-4 h-4 ${colors.text} shrink-0`} />}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 生成按钮 */}
            <button onClick={startGeneration} disabled={loading || isGuest || selectedTypes.length === 0}
              className="w-full px-4 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50 font-medium flex items-center justify-center gap-2">
              {loading ? (
                <><Loader2 className="w-5 h-5 animate-spin" /> 生成中...</>
              ) : (
                <><Sparkles className="w-5 h-5" /> {resources.length > 0 ? '继续生成' : '开始生成资源'}</>
              )}
            </button>

            {resources.length > 0 && !loading && (
              <button
                onClick={() => { setResources([]); setProgress(0); setCurrentStep(''); }}
                className="w-full mt-2 px-4 py-2.5 border border-white/[0.08] bg-white/[0.02] text-white/40 rounded-xl hover:bg-white/[0.06] transition-colors text-sm font-medium"
              >
                清空结果
              </button>
            )}
          </div>
        </motion.div>

        {/* ===== 右侧：进度 & 结果 ===== */}
        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ type: 'spring', stiffness: 200, damping: 25 }} className="lg:col-span-2 space-y-4">

          {/* 进度条 */}
          {(loading || progress > 0) && (
            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
              className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-white/80 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-cyan-400" /> 生成进度
                </span>
                <span className="text-sm font-bold text-cyan-400">{progress}%</span>
              </div>
              <div className="w-full h-2.5 bg-white/[0.06] rounded-full overflow-hidden">
                <motion.div className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full"
                  initial={{ width: 0 }} animate={{ width: `${progress}%` }} transition={{ duration: 0.3 }} />
              </div>
              <p className="text-xs text-white/30 mt-2 flex items-center gap-1.5">
                {loading ? <Loader2 className="w-3 h-3 animate-spin text-cyan-400" /> : null}
                {currentStep}
              </p>
            </motion.div>
          )}

          {/* 资源卡片列表 */}
          <AnimatePresence>
            {resources.map((resource, idx) => {
              const typeInfo = RESOURCE_TYPES.find(t => t.value === resource.type);
              const colors = COLOR_MAP[typeInfo?.color || 'blue'];
              const Icon = typeInfo?.icon || FileText;
              const expanded = expandedCards.has(idx);

              return (
                <motion.div key={idx}
                  initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }} transition={{ delay: idx * 0.05, type: 'spring', stiffness: 200, damping: 25 }}
                  className={`bg-white/[0.04] backdrop-blur-xl rounded-2xl overflow-hidden border ${resource.status === 'error' ? 'border-red-400/30' : 'border-white/[0.06]'} hover:border-cyan-400/20 transition-colors`}>

                  {/* 卡片头部 */}
                  <div className="p-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${colors.bg}`}>
                        <Icon className={`w-5 h-5 ${colors.text}`} />
                      </div>
                      <div>
                        <h3 className="font-semibold text-white text-sm">{resource.title}</h3>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${colors.badge}`}>
                            {typeInfo?.label}
                          </span>
                          {resource.duration_minutes && (
                            <span className="text-xs text-white/30">⏱ {resource.duration_minutes}分钟</span>
                          )}
                          {resource.status === 'error' && (
                            <span className="text-xs text-red-400 flex items-center gap-1">
                              <AlertCircle className="w-3 h-3" /> 生成失败
                            </span>
                          )}
                          {resource.status === 'complete' && (
                            <span className="text-xs text-emerald-400 flex items-center gap-1">
                              <CheckCircle className="w-3 h-3" /> 完成
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      {resource.status === 'complete' && (
                        <button
                          onClick={() => handleExport(resource, idx)}
                          disabled={downloadingIdx === idx}
                          className="p-2 hover:bg-emerald-400/[0.1] rounded-lg transition-colors disabled:opacity-50"
                          title="导出下载"
                        >
                          {downloadingIdx === idx ? (
                            <Loader2 className="w-4 h-4 text-emerald-400 animate-spin" />
                          ) : (
                            <Download className="w-4 h-4 text-emerald-400" />
                          )}
                        </button>
                      )}
                      <button onClick={() => setPreviewResource(resource)}
                        className="p-2 hover:bg-cyan-400/[0.1] rounded-lg transition-colors" title="全屏预览">
                        <Eye className="w-4 h-4 text-cyan-400" />
                      </button>
                      <button onClick={() => toggleExpand(idx)}
                        className="p-2 hover:bg-white/[0.06] rounded-lg transition-colors">
                        {expanded ? <ChevronUp className="w-4 h-4 text-white/40" /> : <ChevronDown className="w-4 h-4 text-white/40" />}
                      </button>
                    </div>
                  </div>

                  {/* 卡片内容 */}
                  <AnimatePresence>
                    {expanded && resource.status === 'complete' && (
                      <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }}
                        className="border-t border-white/[0.06]">
                        <div className="p-4">
                          <ResourceContent type={resource.type} data={resource.content_data} />
                        </div>
                      </motion.div>
                    )}
                    {expanded && resource.status === 'error' && (
                      <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="border-t border-red-400/20 p-4">
                        <div className="bg-red-400/[0.08] rounded-xl p-4 text-sm text-red-400">
                          <AlertCircle className="w-4 h-4 inline mr-1" />
                          {resource.content_data?.error || '未知错误'}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              );
            })}
          </AnimatePresence>

          {/* 空状态 */}
          {!loading && resources.length === 0 && (
            <div className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-16 text-center">
              <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-cyan-400/[0.1] to-blue-400/[0.1] flex items-center justify-center">
                <Brain className="w-10 h-10 text-cyan-400/40" />
              </div>
              <h3 className="text-lg font-semibold text-white/60 mb-1">准备生成学习资源</h3>
              <p className="text-sm text-white/30">配置左侧参数后，点击「开始生成资源」</p>
              <div className="flex items-center justify-center gap-4 mt-4">
                {RESOURCE_TYPES.slice(0, 4).map(t => {
                  const Icon = t.icon;
                  return (
                    <div key={t.value} className="flex flex-col items-center gap-1 opacity-30">
                      <Icon className="w-5 h-5 text-white/30" />
                      <span className="text-xs text-white/30">{t.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </motion.div>
      </div>

      {/* ===== 全屏预览 Modal ===== */}
      {previewResource && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-6" onClick={() => setPreviewResource(null)}>
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
            className="bg-[#0a192f] border border-white/[0.08] rounded-2xl max-w-4xl w-full max-h-[85vh] overflow-hidden"
            onClick={e => e.stopPropagation()}>
            <div className="p-4 border-b border-white/[0.06] flex items-center justify-between">
              <h2 className="font-bold text-white">{previewResource.title}</h2>
              <button onClick={() => setPreviewResource(null)} className="text-white/40 hover:text-white/60 text-xl">×</button>
            </div>
            <div className="p-6 overflow-y-auto max-h-[70vh]">
              <ResourceContent type={previewResource.type} data={previewResource.content_data} full />
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}

/* ===== 资源内容渲染组件 ===== */
function ResourceContent({ type, data, full }: { type: string; data: any; full?: boolean }) {
  if (!data || data.error) {
    return <p className="text-sm text-red-400">{data?.error || '暂无内容'}</p>;
  }

  // 文档类型 — Markdown 渲染
  if (type === 'document') {
    const sections = data.sections || [];
    const mdContent = sections.map((s: any) => `## ${s.heading}\n\n${s.content}`).join('\n\n');
    const keyPoints = data.key_points || [];

    return (
      <div className="space-y-4">
        {data.title && <h2 className="text-lg font-bold text-white">{data.title}</h2>}
        <div className="prose prose-sm max-w-none prose-invert prose-headings:text-white prose-p:text-white/60 prose-strong:text-white/80 prose-li:text-white/60">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{mdContent}</ReactMarkdown>
        </div>
        {keyPoints.length > 0 && (
          <div className="bg-cyan-400/[0.06] rounded-xl p-4">
            <h4 className="text-sm font-semibold text-cyan-400 mb-2 flex items-center gap-1">
              <Target className="w-4 h-4" /> 关键知识点
            </h4>
            <ul className="space-y-1">
              {keyPoints.map((p: string, i: number) => (
                <li key={i} className="text-sm text-cyan-400/80 flex items-start gap-2">
                  <span className="text-cyan-400/40 mt-0.5">•</span>{p}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  // 思维导图 — 树状结构渲染
  if (type === 'mindmap') {
    return (
      <div className="space-y-4">
        {data.title && <h2 className="text-lg font-bold text-white">{data.title}</h2>}
        <MindmapTree node={data.root} level={0} difficultyMarks={data.difficulty_marks} />
        {data.key_concepts?.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {data.key_concepts.map((c: string, i: number) => (
              <span key={i} className="px-3 py-1 bg-violet-400/[0.1] text-violet-400 rounded-full text-xs font-medium">{c}</span>
            ))}
          </div>
        )}
      </div>
    );
  }

  // 练习题 — 题目卡片
  if (type === 'quiz') {
    const questions = data.questions || [];
    return (
      <div className="space-y-4">
        {data.title && <h2 className="text-lg font-bold text-white">{data.title}</h2>}
        <div className="flex items-center gap-3 text-xs text-white/40">
          <span>共 {questions.length} 题</span>
          {data.estimated_time && <span>⏱ 约 {data.estimated_time} 分钟</span>}
        </div>
        {questions.map((q: any, i: number) => (
          <QuizCard key={i} question={q} index={i} />
        ))}
      </div>
    );
  }

  // 代码案例
  if (type === 'code_case') {
    return (
      <div className="space-y-4">
        {data.title && <h2 className="text-lg font-bold text-white">{data.title}</h2>}
        {data.description && <p className="text-sm text-white/60">{data.description}</p>}
        {data.requirements?.length > 0 && (
          <div className="bg-cyan-400/[0.06] rounded-xl p-3">
            <h4 className="text-xs font-semibold text-cyan-400 mb-1">需求说明</h4>
            <ul className="text-sm text-cyan-400/80 space-y-0.5">
              {data.requirements.map((r: string, i: number) => <li key={i}>• {r}</li>)}
            </ul>
          </div>
        )}
        {data.code?.source_code && (
          <div className="bg-white/[0.04] rounded-xl p-4 overflow-x-auto border border-white/[0.06]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-white/30">{data.code.filename || 'code'}</span>
              <span className="text-xs text-white/40">{data.code.language}</span>
            </div>
            <pre className="text-sm text-emerald-400 font-mono whitespace-pre-wrap">{data.code.source_code}</pre>
          </div>
        )}
        {data.expected_output && (
          <div className="bg-emerald-400/[0.06] rounded-xl p-3">
            <h4 className="text-xs font-semibold text-emerald-400 mb-1">预期输出</h4>
            <pre className="text-sm text-emerald-400/80 font-mono whitespace-pre-wrap">{data.expected_output}</pre>
          </div>
        )}
      </div>
    );
  }

  // 视频/动画脚本 — 分镜展示
  if (type === 'video' || type === 'animation') {
    const scenes = data.scenes || data.frames || [];
    const isVideo = type === 'video';
    return (
      <div className="space-y-4">
        {data.title && <h2 className="text-lg font-bold text-white">{data.title}</h2>}
        <div className="flex items-center gap-3 text-xs text-white/40">
          {data.duration_minutes && <span>⏱ {data.duration_minutes} 分钟</span>}
          {data.visual_style && <span>🎨 {data.visual_style}</span>}
        </div>
        <div className="space-y-3">
          {scenes.map((s: any, i: number) => (
            <div key={i} className="border border-white/[0.06] rounded-xl p-3 hover:border-white/[0.1] transition-colors">
              <div className="flex items-center gap-2 mb-2">
                <span className="w-6 h-6 rounded-full bg-red-400/[0.1] text-red-400 text-xs font-bold flex items-center justify-center">
                  {s.scene_id || s.frame_id || i + 1}
                </span>
                {s.timestamp && <span className="text-xs text-white/30">{s.timestamp}</span>}
                {s.duration_seconds && <span className="text-xs text-white/30">{s.duration_seconds}s</span>}
              </div>
              {isVideo ? (
                <>
                  {s.visual_description && <p className="text-sm text-white/60 mb-1">🎬 {s.visual_description}</p>}
                  {s.narration && <p className="text-sm text-white/80 italic">"{s.narration}"</p>}
                </>
              ) : (
                <>
                  {s.description && <p className="text-sm text-white/60 mb-1">{s.description}</p>}
                  {s.action && <p className="text-sm text-white/80">▶ {s.action}</p>}
                </>
              )}
              {s.animation_effects?.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {s.animation_effects.map((e: string, j: number) => (
                    <span key={j} className="px-2 py-0.5 bg-amber-400/[0.1] text-amber-400 rounded text-xs">{e}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
        {data.narration_script && (
          <div className="bg-white/[0.04] rounded-xl p-4 border border-white/[0.06]">
            <h4 className="text-xs font-semibold text-white/40 mb-2">完整解说词</h4>
            <p className="text-sm text-white/60 whitespace-pre-wrap">{data.narration_script}</p>
          </div>
        )}
      </div>
    );
  }

  // 拓展阅读 — Markdown 渲染
  if (type === 'reading') {
    return (
      <div className="space-y-4">
        {data.title && <h2 className="text-lg font-bold text-white">{data.title}</h2>}
        {data.content && (
          <div className="prose prose-sm max-w-none prose-invert prose-headings:text-white prose-p:text-white/60 prose-strong:text-white/80 prose-li:text-white/60">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{data.content}</ReactMarkdown>
          </div>
        )}
        {data.case_studies?.length > 0 && (
          <div className="bg-indigo-400/[0.06] rounded-xl p-4">
            <h4 className="text-sm font-semibold text-indigo-400 mb-2">📋 案例分析</h4>
            <ul className="space-y-1">
              {data.case_studies.map((c: string, i: number) => (
                <li key={i} className="text-sm text-indigo-400/80">• {c}</li>
              ))}
            </ul>
          </div>
        )}
        {data.further_reading?.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-white/60 mb-2">📚 延伸阅读</h4>
            <ul className="space-y-1">
              {data.further_reading.map((r: any, i: number) => (
                <li key={i} className="text-sm text-cyan-400 hover:underline">
                  {r.url ? <a href={r.url} target="_blank" rel="noreferrer">{r.title}</a> : r.title}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  // 兜底 — JSON 展示
  return (
    <pre className="text-xs text-white/60 bg-white/[0.04] rounded-xl p-4 overflow-x-auto font-mono whitespace-pre-wrap border border-white/[0.06]">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

/* ===== 思维导图树节点 — 卡片式布局 ===== */
function MindmapTree({ node, level, difficultyMarks }: { node: any; level: number; difficultyMarks?: Record<string, string> }) {
  if (!node) return null;

  const branchColors = [
    { bg: 'bg-violet-400/[0.06]', border: 'border-violet-400/20', text: 'text-violet-400', dot: 'bg-violet-400', tag: 'bg-violet-400/[0.1] text-violet-400' },
    { bg: 'bg-cyan-400/[0.06]', border: 'border-cyan-400/20', text: 'text-cyan-400', dot: 'bg-cyan-400', tag: 'bg-cyan-400/[0.1] text-cyan-400' },
    { bg: 'bg-emerald-400/[0.06]', border: 'border-emerald-400/20', text: 'text-emerald-400', dot: 'bg-emerald-400', tag: 'bg-emerald-400/[0.1] text-emerald-400' },
    { bg: 'bg-amber-400/[0.06]', border: 'border-amber-400/20', text: 'text-amber-400', dot: 'bg-amber-400', tag: 'bg-amber-400/[0.1] text-amber-400' },
    { bg: 'bg-pink-400/[0.06]', border: 'border-pink-400/20', text: 'text-pink-400', dot: 'bg-pink-400', tag: 'bg-pink-400/[0.1] text-pink-400' },
  ];

  // 根节点 — 横向排列一级分支卡片
  if (level === 0) {
    return (
      <div className="space-y-4">
        {/* 根节点标题 */}
        <div className="flex items-center gap-3 mb-2">
          <div className="w-3 h-3 rounded-full bg-gradient-to-r from-cyan-400 to-blue-500" />
          <span className="text-base font-bold text-white">{node.name}</span>
        </div>
        {/* 一级分支卡片网格 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {node.children?.map((child: any, i: number) => {
            const c = branchColors[i % branchColors.length];
            return (
              <div key={i} className={`rounded-xl border ${c.border} ${c.bg} p-3`}>
                <div className="flex items-center gap-2 mb-2">
                  <div className={`w-2 h-2 rounded-full ${c.dot}`} />
                  <span className={`text-sm font-semibold ${c.text}`}>{child.name}</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {child.children?.map((leaf: any, j: number) => {
                    const diffBadge = difficultyMarks?.[leaf.name];
                    const isHard = diffBadge === 'hard';
                    return (
                      <span key={j} className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium ${c.tag} ${isHard ? 'ring-1 ring-red-400/40' : ''}`}>
                        {leaf.name}
                        {isHard && <span className="text-red-400 text-[10px]">★</span>}
                      </span>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // 非根节点兜底（如果AI返回了更深层级）
  return (
    <div className="ml-4 pl-3 border-l-2 border-white/[0.08]">
      <div className="flex items-center gap-2 py-1">
        <span className="text-sm font-medium text-white/60">{node.name}</span>
      </div>
      {node.children?.map((child: any, i: number) => (
        <MindmapTree key={i} node={child} level={level + 1} difficultyMarks={difficultyMarks} />
      ))}
    </div>
  );
}

/* ===== 练习题卡片 ===== */
function QuizCard({ question, index }: { question: any; index: number }) {
  const [showAnswer, setShowAnswer] = useState(false);
  const diffColor = question.difficulty === 'hard' ? 'bg-red-400/[0.1] text-red-400' :
    question.difficulty === 'medium' ? 'bg-amber-400/[0.1] text-amber-400' : 'bg-emerald-400/[0.1] text-emerald-400';

  return (
    <div className="border border-white/[0.06] rounded-xl p-4 hover:border-cyan-400/20 transition-colors">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="w-6 h-6 rounded-full bg-emerald-400/[0.1] text-emerald-400 text-xs font-bold flex items-center justify-center">{index + 1}</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-white/[0.06] text-white/40">
            {question.type === 'multiple_choice' ? '选择题' : question.type === 'fill_blank' ? '填空题' : '解答题'}
          </span>
          {question.difficulty && <span className={`text-xs px-2 py-0.5 rounded-full ${diffColor}`}>{question.difficulty}</span>}
        </div>
        {question.knowledge_point && <span className="text-xs text-white/30">📌 {question.knowledge_point}</span>}
      </div>

      <p className="text-sm text-white/80 mb-2">{question.question}</p>

      {question.options?.length > 0 && (
        <div className="space-y-1 mb-2 ml-1">
          {question.options.map((opt: string, i: number) => (
            <p key={i} className="text-sm text-white/60">{opt}</p>
          ))}
        </div>
      )}

      <button onClick={() => setShowAnswer(!showAnswer)}
        className="text-xs text-emerald-400 hover:text-emerald-300 font-medium flex items-center gap-1 mt-1">
        <Lightbulb className="w-3 h-3" />
        {showAnswer ? '隐藏答案' : '查看答案与解析'}
      </button>

      <AnimatePresence>
        {showAnswer && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }} className="mt-2 bg-emerald-400/[0.06] rounded-lg p-3">
            <p className="text-sm font-semibold text-emerald-400 mb-1">答案: {question.answer}</p>
            {question.explanation && (
              <p className="text-sm text-emerald-400/80">{question.explanation}</p>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
