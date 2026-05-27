'use client';

import { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuthStore } from '@/stores';
import api from '@/lib/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  TrendingUp, BarChart3, Target, Award,
  Loader2, CheckCircle, AlertCircle, Sparkles,
  Upload, FileText, X, BookOpen, Brain,
  ChevronDown, ChevronUp, File, Image, FileSpreadsheet,
  Download
} from 'lucide-react';

/* ===================== 类型定义 ===================== */

interface AssessmentResult {
  overall_score: number;
  dimensions: Array<{
    name: string;
    score: number;
    max_score: number;
    level: string;
    feedback: string;
  }>;
  strengths: string[];
  improvements: string[];
  recommendations: string[];
}

interface DocAnalysisResult {
  files: Array<{
    filename: string;
    status: string;
    char_count: number;
    error?: string;
  }>;
  analysis: {
    knowledge_overview: {
      total_knowledge_points: number;
      main_topics: string[];
      coverage_summary: string;
    };
    knowledge_points: Array<{
      name: string;
      importance: string;
      mastery_hint: string;
      description: string;
    }>;
    strengths: string[];
    weaknesses: string[];
    learning_gaps: Array<{
      gap: string;
      related_topics: string[];
      suggestion: string;
    }>;
    difficulty_assessment: {
      overall_level: string;
      reasoning: string;
    };
    study_recommendations: Array<{
      priority: string;
      action: string;
      resources: string;
    }>;
    overall_score: number;
    summary: string;
  };
  analyzed_at: string;
}

/* ===================== 文件图标 ===================== */

function getFileIcon(filename: string) {
  const ext = filename.split('.').pop()?.toLowerCase() || '';
  if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext))
    return <Image className="w-5 h-5 text-pink-400" />;
  if (['pdf'].includes(ext))
    return <FileText className="w-5 h-5 text-red-400" />;
  if (['doc', 'docx'].includes(ext))
    return <FileText className="w-5 h-5 text-cyan-400" />;
  if (['ppt', 'pptx'].includes(ext))
    return <FileSpreadsheet className="w-5 h-5 text-amber-400" />;
  return <File className="w-5 h-5 text-white/40" />;
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

/* ===================== 资料分析结果组件 ===================== */

function AnalysisReport({ result }: { result: DocAnalysisResult }) {
  const { analysis } = result;
  const [expanded, setExpanded] = useState<Record<string, boolean>>({
    overview: true,
    knowledge: true,
    gaps: true,
    recommendations: true,
  });

  const toggle = (key: string) => setExpanded((p) => ({ ...p, [key]: !p[key] }));

  /** 导出分析报告为 Markdown 文件 */
  const handleExportReport = () => {
    const lines: string[] = [];
    lines.push(`# 学习资料分析报告`);
    lines.push('');
    lines.push(`> 分析时间: ${result.analyzed_at}`);
    lines.push(`> 文件数量: ${result.files.length}`);
    lines.push('');

    // 文件列表
    lines.push('## 文件列表');
    result.files.forEach((f) => {
      const icon = f.status === 'success' ? '✅' : f.status === 'warning' ? '⚠️' : '❌';
      lines.push(`- ${icon} ${f.filename} (${f.char_count.toLocaleString()} 字)`);
    });
    lines.push('');

    // 综合评分
    lines.push(`## 综合评分: ${analysis.overall_score} / 100`);
    lines.push('');

    // 知识覆盖概览
    lines.push('## 知识覆盖概览');
    lines.push(analysis.knowledge_overview.coverage_summary);
    lines.push(`- 涉及知识点: ${analysis.knowledge_overview.total_knowledge_points} 个`);
    lines.push(`- 主要主题: ${analysis.knowledge_overview.main_topics.join(', ')}`);
    if (analysis.difficulty_assessment) {
      lines.push(`- 难度评估: ${analysis.difficulty_assessment.overall_level} — ${analysis.difficulty_assessment.reasoning}`);
    }
    lines.push('');

    // 知识点
    if (analysis.knowledge_points?.length) {
      lines.push('## 知识点分析');
      analysis.knowledge_points.forEach((kp) => {
        lines.push(`### ${kp.name}`);
        lines.push(`- 重要性: ${kp.importance} | 掌握度: ${kp.mastery_hint}`);
        lines.push(kp.description);
        lines.push('');
      });
    }

    // 优势 & 薄弱
    if (analysis.strengths?.length) {
      lines.push('## 已掌握领域');
      analysis.strengths.forEach((s) => lines.push(`- ✅ ${s}`));
      lines.push('');
    }
    if (analysis.weaknesses?.length) {
      lines.push('## 薄弱环节');
      analysis.weaknesses.forEach((w) => lines.push(`- ⚠️ ${w}`));
      lines.push('');
    }

    // 知识缺口
    if (analysis.learning_gaps?.length) {
      lines.push('## 知识缺口');
      analysis.learning_gaps.forEach((g) => {
        lines.push(`### ${g.gap}`);
        lines.push(`- 相关主题: ${g.related_topics.join(', ')}`);
        lines.push(`- 建议: ${g.suggestion}`);
        lines.push('');
      });
    }

    // 学习建议
    if (analysis.study_recommendations?.length) {
      lines.push('## 学习建议');
      analysis.study_recommendations.forEach((rec, i) => {
        lines.push(`${i + 1}. **[${rec.priority}]** ${rec.action} (推荐资源: ${rec.resources})`);
      });
      lines.push('');
    }

    // 综合报告
    if (analysis.summary) {
      lines.push('## AI 综合分析报告');
      lines.push(analysis.summary);
    }

    const md = lines.join('\n');
    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `学习资料分析报告_${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getImportanceColor = (imp: string) => {
    if (imp === '核心') return 'bg-red-400/[0.1] text-red-400 border-red-400/20';
    if (imp === '重要') return 'bg-amber-400/[0.1] text-amber-400 border-amber-400/20';
    return 'bg-white/[0.06] text-white/40 border-white/[0.08]';
  };

  const getMasteryColor = (m: string) => {
    if (m === '已掌握') return 'text-emerald-400';
    if (m === '需巩固') return 'text-amber-400';
    return 'text-red-400';
  };

  const getPriorityColor = (p: string) => {
    if (p === '高') return 'bg-red-500';
    if (p === '中') return 'bg-amber-500';
    return 'bg-cyan-500';
  };

  return (
    <div className="space-y-5">
      {/* 文件解析状态 */}
      <div className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-5">
        <h3 className="font-bold text-white mb-3 flex items-center gap-2">
          <FileText className="w-5 h-5 text-indigo-400" />
          文件解析结果
        </h3>
        <div className="flex flex-wrap gap-2">
          {result.files.map((f, i) => (
            <div
              key={i}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm border ${
                f.status === 'success'
                  ? 'bg-emerald-400/[0.06] border-emerald-400/20 text-emerald-400'
                  : f.status === 'warning'
                  ? 'bg-amber-400/[0.06] border-amber-400/20 text-amber-400'
                  : 'bg-red-400/[0.06] border-red-400/20 text-red-400'
              }`}
            >
              {getFileIcon(f.filename)}
              <span className="font-medium">{f.filename}</span>
              {f.char_count > 0 && (
                <span className="text-xs opacity-70">{f.char_count.toLocaleString()} 字</span>
              )}
              {f.error && <span className="text-xs">{f.error}</span>}
            </div>
          ))}
        </div>
      </div>

      {/* 综合评分 + 覆盖概览 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-indigo-500 to-purple-500 rounded-2xl p-6 text-white text-center flex flex-col items-center justify-center">
          <p className="text-white/80 text-sm mb-2">资料质量评分</p>
          <p className="text-5xl font-bold">{analysis.overall_score}</p>
          <p className="text-white/60 text-xs mt-1">满分 100</p>
          <button
            onClick={handleExportReport}
            className="mt-4 px-4 py-1.5 bg-white/20 hover:bg-white/30 rounded-lg text-white text-xs font-medium flex items-center gap-1.5 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            导出报告
          </button>
        </div>
        <div className="md:col-span-2 bg-white/[0.04] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-5">
          <button
            onClick={() => toggle('overview')}
            className="w-full flex items-center justify-between"
          >
            <h3 className="font-bold text-white flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-indigo-400" />
              知识覆盖概览
            </h3>
            {expanded.overview ? <ChevronUp className="w-4 h-4 text-white/40" /> : <ChevronDown className="w-4 h-4 text-white/40" />}
          </button>
          <AnimatePresence>
            {expanded.overview && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="mt-4 space-y-3">
                  <p className="text-sm text-white/60 leading-relaxed">{analysis.knowledge_overview.coverage_summary}</p>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-white/40">涉及知识点:</span>
                    <span className="text-sm font-semibold text-indigo-400">{analysis.knowledge_overview.total_knowledge_points} 个</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {analysis.knowledge_overview.main_topics.map((t, i) => (
                      <span key={i} className="px-3 py-1 bg-indigo-400/[0.1] text-indigo-400 rounded-full text-xs font-medium">
                        {t}
                      </span>
                    ))}
                  </div>
                  {analysis.difficulty_assessment && (
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-xs text-white/40">难度评估:</span>
                      <span className="px-2 py-0.5 bg-violet-400/[0.1] text-violet-400 rounded text-xs font-medium">
                        {analysis.difficulty_assessment.overall_level}
                      </span>
                      <span className="text-xs text-white/30">{analysis.difficulty_assessment.reasoning}</span>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* 知识点列表 */}
      {analysis.knowledge_points?.length > 0 && (
        <div className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-5">
          <button
            onClick={() => toggle('knowledge')}
            className="w-full flex items-center justify-between"
          >
            <h3 className="font-bold text-white flex items-center gap-2">
              <Brain className="w-5 h-5 text-violet-400" />
              知识点分析 ({analysis.knowledge_points.length})
            </h3>
            {expanded.knowledge ? <ChevronUp className="w-4 h-4 text-white/40" /> : <ChevronDown className="w-4 h-4 text-white/40" />}
          </button>
          <AnimatePresence>
            {expanded.knowledge && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
                  {analysis.knowledge_points.map((kp, i) => (
                    <div key={i} className="border border-white/[0.06] rounded-xl p-4 hover:border-indigo-400/20 transition-colors">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-semibold text-white text-sm">{kp.name}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded border ${getImportanceColor(kp.importance)}`}>
                          {kp.importance}
                        </span>
                        <span className={`text-[10px] font-medium ${getMasteryColor(kp.mastery_hint)}`}>
                          {kp.mastery_hint}
                        </span>
                      </div>
                      <p className="text-xs text-white/60 leading-relaxed">{kp.description}</p>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* 优势 & 薄弱 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-5">
          <h3 className="font-bold text-white mb-3 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-emerald-400" />
            已掌握领域
          </h3>
          <ul className="space-y-2">
            {(analysis.strengths || []).map((s, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-white/60">
                <span className="text-emerald-400 mt-0.5 flex-shrink-0">✓</span>
                {s}
              </li>
            ))}
            {(!analysis.strengths || analysis.strengths.length === 0) && (
              <li className="text-sm text-white/30">暂无数据</li>
            )}
          </ul>
        </div>
        <div className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-5">
          <h3 className="font-bold text-white mb-3 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-amber-400" />
            薄弱环节
          </h3>
          <ul className="space-y-2">
            {(analysis.weaknesses || []).map((w, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-white/60">
                <span className="text-amber-400 mt-0.5 flex-shrink-0">!</span>
                {w}
              </li>
            ))}
            {(!analysis.weaknesses || analysis.weaknesses.length === 0) && (
              <li className="text-sm text-white/30">暂无数据</li>
            )}
          </ul>
        </div>
      </div>

      {/* 知识缺口 */}
      {analysis.learning_gaps?.length > 0 && (
        <div className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-5">
          <button
            onClick={() => toggle('gaps')}
            className="w-full flex items-center justify-between"
          >
            <h3 className="font-bold text-white flex items-center gap-2">
              <Target className="w-5 h-5 text-red-400" />
              知识缺口 ({analysis.learning_gaps.length})
            </h3>
            {expanded.gaps ? <ChevronUp className="w-4 h-4 text-white/40" /> : <ChevronDown className="w-4 h-4 text-white/40" />}
          </button>
          <AnimatePresence>
            {expanded.gaps && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="mt-4 space-y-3">
                  {analysis.learning_gaps.map((g, i) => (
                    <div key={i} className="border-l-4 border-red-400/50 bg-red-400/[0.06] rounded-r-xl p-4">
                      <p className="font-semibold text-sm text-white mb-1">{g.gap}</p>
                      <div className="flex flex-wrap gap-1 mb-2">
                        {g.related_topics.map((t, j) => (
                          <span key={j} className="text-[10px] px-1.5 py-0.5 bg-red-400/[0.1] text-red-400 rounded">{t}</span>
                        ))}
                      </div>
                      <p className="text-xs text-white/60">💡 {g.suggestion}</p>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* 学习建议 */}
      {analysis.study_recommendations?.length > 0 && (
        <div className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-5">
          <button
            onClick={() => toggle('recommendations')}
            className="w-full flex items-center justify-between"
          >
            <h3 className="font-bold text-white flex items-center gap-2">
              <Award className="w-5 h-5 text-violet-400" />
              学习建议 ({analysis.study_recommendations.length})
            </h3>
            {expanded.recommendations ? <ChevronUp className="w-4 h-4 text-white/40" /> : <ChevronDown className="w-4 h-4 text-white/40" />}
          </button>
          <AnimatePresence>
            {expanded.recommendations && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="mt-4 space-y-3">
                  {analysis.study_recommendations.map((rec, i) => (
                    <div key={i} className="flex items-start gap-3 p-4 bg-gradient-to-br from-violet-400/[0.06] to-indigo-400/[0.06] rounded-xl border border-white/[0.06]">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0 ${getPriorityColor(rec.priority)}`}>
                        {rec.priority}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-white font-medium">{rec.action}</p>
                        <p className="text-xs text-white/40 mt-1">推荐资源类型: {rec.resources}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* AI 综合分析报告 */}
      {analysis.summary && (
        <div className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-5">
          <h3 className="font-bold text-white mb-3 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-amber-400" />
            AI 综合分析报告
          </h3>
          <div className="prose prose-sm max-w-none prose-invert prose-headings:text-white prose-p:text-white/60 prose-strong:text-white/80 prose-li:text-white/60 bg-amber-400/[0.04] rounded-xl p-4 border border-amber-400/10">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{analysis.summary}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}

/* ===================== 主页面 ===================== */

export default function AssessmentPage() {
  const { user, isGuest } = useAuthStore();

  // Tab 切换
  const [activeTab, setActiveTab] = useState<'assess' | 'analyze'>('assess');

  // --- 评估相关 ---
  const [loading, setLoading] = useState(false);
  const [assessment, setAssessment] = useState<AssessmentResult | null>(null);

  // --- 资料分析相关 ---
  const [files, setFiles] = useState<File[]>([]);
  const [subject, setSubject] = useState('');
  const [topic, setTopic] = useState('');
  const [difficulty, setDifficulty] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<DocAnalysisResult | null>(null);
  const [analysisError, setAnalysisError] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  /* ---- 评估 ---- */
  const runAssessment = async () => {
    setLoading(true);
    try {
      const res: any = await api.assess({
        user_id: user?.id || 1,
        assessment_type: 'comprehensive',
      });
      if (res.success) {
        setAssessment(res.data);
      } else {
        alert('评估失败：' + (res.message || '未知错误'));
      }
    } catch (err: any) {
      alert('评估失败：' + (err.message || '网络错误'));
    } finally {
      setLoading(false);
    }
  };

  /* ---- 文件操作 ---- */
  const addFiles = (newFiles: FileList | File[]) => {
    const arr = Array.from(newFiles);
    const allowed = ['txt', 'md', 'pdf', 'doc', 'docx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png'];
    const valid = arr.filter((f) => {
      const ext = f.name.split('.').pop()?.toLowerCase() || '';
      return allowed.includes(ext);
    });
    if (valid.length < arr.length) {
      alert(`已过滤不支持的文件格式。支持: ${allowed.join(', ')}`);
    }
    setFiles((prev) => {
      const merged = [...prev, ...valid];
      return merged.slice(0, 10); // 最多10个
    });
  };

  const removeFile = (idx: number) => setFiles((prev) => prev.filter((_, i) => i !== idx));

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length > 0) addFiles(e.dataTransfer.files);
  }, []);

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const onDragLeave = useCallback(() => setDragOver(false), []);

  /* ---- 分析 ---- */
  const runAnalysis = async () => {
    if (files.length === 0) {
      alert('请先上传学习资料');
      return;
    }
    setAnalyzing(true);
    setAnalysisError('');
    setAnalysisResult(null);
    try {
      const res: any = await api.uploadAndAnalyze(files, { subject, topic, difficulty });
      if (res.success) {
        setAnalysisResult(res.data);
      } else {
        setAnalysisError(res.message || '分析失败');
      }
    } catch (err: any) {
      setAnalysisError(err.message || '网络错误');
    } finally {
      setAnalyzing(false);
    }
  };

  /* ---- 样式 ---- */
  const getScoreColor = (score: number, maxScore: number) => {
    const pct = score / maxScore;
    if (pct >= 0.8) return 'text-emerald-400';
    if (pct >= 0.6) return 'text-cyan-400';
    if (pct >= 0.4) return 'text-amber-400';
    return 'text-red-400';
  };

  const getLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case '优秀':
      case 'excellent':
        return 'bg-emerald-400/[0.1] text-emerald-400';
      case '良好':
      case 'good':
        return 'bg-cyan-400/[0.1] text-cyan-400';
      case '一般':
      case 'average':
        return 'bg-amber-400/[0.1] text-amber-400';
      default:
        return 'bg-red-400/[0.1] text-red-400';
    }
  };

  /* ===================== 渲染 ===================== */
  return (
    <div className="max-w-7xl mx-auto">
      {/* 页面标题 */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: 'spring', stiffness: 200, damping: 25 }}
        className="mb-6"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
            <TrendingUp className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">学习效果评估</h1>
            <p className="text-sm text-white/60">
              多维度精准评估 · 上传资料AI分析 · 动态反馈学习策略
            </p>
          </div>
        </div>
      </motion.div>

      {/* Tab 切换 */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('assess')}
          className={`px-5 py-2.5 rounded-xl font-medium text-sm transition-all ${
            activeTab === 'assess'
              ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white'
              : 'bg-white/[0.04] text-white/40 hover:bg-white/[0.08] border border-white/[0.06]'
          }`}
        >
          <span className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            AI 综合评估
          </span>
        </button>
        <button
          onClick={() => setActiveTab('analyze')}
          className={`px-5 py-2.5 rounded-xl font-medium text-sm transition-all ${
            activeTab === 'analyze'
              ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white'
              : 'bg-white/[0.04] text-white/40 hover:bg-white/[0.08] border border-white/[0.06]'
          }`}
        >
          <span className="flex items-center gap-2">
            <Upload className="w-4 h-4" />
            资料分析
          </span>
        </button>
      </div>

      {/* ======== Tab 1: AI 综合评估 ======== */}
      {activeTab === 'assess' && (
        <>
          {!assessment ? (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-20">
              <BarChart3 className="w-24 h-24 mx-auto mb-6 text-white/10" />
              <h3 className="text-xl font-semibold text-white/60 mb-3">开始学习效果评估</h3>
              <p className="text-sm text-white/40 mb-6 max-w-md mx-auto">
                基于您的学习行为和画像特征，进行多维度综合评估，提供个性化改进建议
              </p>
              <button
                onClick={runAssessment}
                disabled={loading || isGuest}
                className="px-8 py-3 bg-gradient-to-r from-indigo-500 to-purple-500 text-white rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed font-medium flex items-center gap-2 mx-auto"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" /> 评估中...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" /> 开始评估
                  </>
                )}
              </button>
            </motion.div>
          ) : (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
              {/* 总分 */}
              <div className="bg-gradient-to-r from-indigo-500 to-purple-500 rounded-2xl p-8 text-white text-center">
                <h3 className="text-lg font-semibold mb-4">综合评分</h3>
                <div className="text-6xl font-bold mb-2">{assessment.overall_score}</div>
                <p className="text-white/80">满分 100 分</p>
                <button
                  onClick={() => {
                    const lines: string[] = ['# AI 学习效果评估报告', ''];
                    lines.push(`## 综合评分: ${assessment.overall_score} / 100`, '');
                    if (assessment.dimensions?.length) {
                      lines.push('## 多维度评估');
                      assessment.dimensions.forEach((d) => {
                        lines.push(`- **${d.name}**: ${d.score}/${d.max_score} (${d.level}) — ${d.feedback}`);
                      });
                      lines.push('');
                    }
                    if (assessment.strengths?.length) {
                      lines.push('## 学习优势');
                      assessment.strengths.forEach((s) => lines.push(`- ✅ ${s}`));
                      lines.push('');
                    }
                    if (assessment.improvements?.length) {
                      lines.push('## 改进建议');
                      assessment.improvements.forEach((s) => lines.push(`- ⚠️ ${s}`));
                      lines.push('');
                    }
                    if (assessment.recommendations?.length) {
                      lines.push('## 个性化学习建议');
                      assessment.recommendations.forEach((r, i) => lines.push(`${i + 1}. ${r}`));
                    }
                    const blob = new Blob([lines.join('\n')], { type: 'text/markdown;charset=utf-8' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `AI评估报告_${new Date().toISOString().slice(0, 10)}.md`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                  }}
                  className="mt-4 px-4 py-1.5 bg-white/20 hover:bg-white/30 rounded-lg text-white text-xs font-medium flex items-center gap-1.5 mx-auto transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  导出报告
                </button>
              </div>

              {/* 各维度 */}
              <div className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-6">
                <h3 className="font-bold text-white mb-6 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-indigo-400" /> 多维度评估
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {assessment.dimensions.map((dim, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.1, type: 'spring', stiffness: 200, damping: 25 }}
                      className="border border-white/[0.06] rounded-xl p-4 hover:border-indigo-400/20 transition-colors"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="font-semibold text-white">{dim.name}</h4>
                          <span className={`text-xs px-2 py-1 rounded-full ${getLevelColor(dim.level)}`}>
                            {dim.level}
                          </span>
                        </div>
                        <div className="text-right">
                          <div className={`text-2xl font-bold ${getScoreColor(dim.score, dim.max_score)}`}>
                            {dim.score}
                          </div>
                          <div className="text-xs text-white/40">/ {dim.max_score}</div>
                        </div>
                      </div>
                      <div className="w-full h-2 bg-white/[0.06] rounded-full overflow-hidden mb-2">
                        <motion.div
                          className={`h-full rounded-full ${
                            dim.score / dim.max_score >= 0.8
                              ? 'bg-emerald-500'
                              : dim.score / dim.max_score >= 0.6
                              ? 'bg-cyan-500'
                              : dim.score / dim.max_score >= 0.4
                              ? 'bg-amber-500'
                              : 'bg-red-500'
                          }`}
                          initial={{ width: 0 }}
                          animate={{ width: `${(dim.score / dim.max_score) * 100}%` }}
                          transition={{ duration: 0.5, delay: idx * 0.1 }}
                        />
                      </div>
                      <p className="text-xs text-white/60">{dim.feedback}</p>
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* 优势 & 改进 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-6">
                  <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-emerald-400" /> 学习优势
                  </h3>
                  <ul className="space-y-3">
                    {assessment.strengths.map((s, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-white/60">
                        <span className="text-emerald-400 mt-0.5">✓</span> {s}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-6">
                  <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-amber-400" /> 改进建议
                  </h3>
                  <ul className="space-y-3">
                    {assessment.improvements.map((s, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-white/60">
                        <span className="text-amber-400 mt-0.5">!</span> {s}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* 个性化建议 */}
              <div className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-6">
                <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                  <Award className="w-5 h-5 text-violet-400" /> 个性化学习建议
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {assessment.recommendations.map((rec, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.1, type: 'spring', stiffness: 200, damping: 25 }}
                      className="flex items-start gap-3 p-4 bg-gradient-to-br from-violet-400/[0.06] to-indigo-400/[0.06] rounded-xl border border-white/[0.06]"
                    >
                      <div className="w-6 h-6 rounded-full bg-gradient-to-br from-violet-500 to-indigo-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                        {idx + 1}
                      </div>
                      <p className="text-sm text-white/60">{rec}</p>
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* 操作按钮 */}
              <div className="flex gap-3">
                <button
                  onClick={runAssessment}
                  disabled={loading || isGuest}
                  className="flex-1 px-4 py-3 bg-gradient-to-r from-indigo-500 to-purple-500 text-white rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed font-medium flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" /> 重新评估中...
                    </>
                  ) : (
                    <>
                      <TrendingUp className="w-5 h-5" /> 重新评估
                    </>
                  )}
                </button>
              </div>
            </motion.div>
          )}
        </>
      )}

      {/* ======== Tab 2: 资料分析 ======== */}
      {activeTab === 'analyze' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-5">
          {/* 上传区域 */}
          <div
            onDrop={onDrop}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            className={`relative rounded-2xl border-2 border-dashed p-8 text-center transition-colors cursor-pointer ${
              dragOver
                ? 'border-cyan-400/40 bg-cyan-400/[0.06]'
                : 'border-white/[0.1] bg-white/[0.02] hover:border-cyan-400/30 hover:bg-white/[0.04]'
            }`}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".txt,.md,.pdf,.doc,.docx,.ppt,.pptx,.jpg,.jpeg,.png"
              className="hidden"
              onChange={(e) => {
                if (e.target.files) addFiles(e.target.files);
                e.target.value = '';
              }}
            />
            <Upload className={`w-12 h-12 mx-auto mb-3 ${dragOver ? 'text-cyan-400' : 'text-white/30'}`} />
            <p className="text-sm font-medium text-white/60 mb-1">
              拖拽文件到此处，或 <span className="text-cyan-400 underline">点击选择文件</span>
            </p>
            <p className="text-xs text-white/30">
              支持 PDF、Word、PPT、TXT、Markdown、图片 · 单文件最大 10MB · 最多 10 个文件
            </p>
          </div>

          {/* 已选文件列表 */}
          {files.length > 0 && (
            <div className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-white text-sm">
                  已选择 {files.length} 个文件 ({formatFileSize(files.reduce((s, f) => s + f.size, 0))})
                </h3>
                <button
                  onClick={() => setFiles([])}
                  className="text-xs text-red-400 hover:text-red-300"
                >
                  清空全部
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {files.map((f, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-2 bg-white/[0.04] border border-white/[0.06] rounded-lg px-3 py-2 text-sm group"
                  >
                    {getFileIcon(f.name)}
                    <span className="text-white/60 max-w-[160px] truncate">{f.name}</span>
                    <span className="text-xs text-white/30">{formatFileSize(f.size)}</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        removeFile(i);
                      }}
                      className="opacity-0 group-hover:opacity-100 transition-opacity text-white/30 hover:text-red-400"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 可选上下文 */}
          <div className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-5">
            <h3 className="font-semibold text-white text-sm mb-3">
              分析上下文 <span className="text-white/30 font-normal">(可选，帮助AI更精准分析)</span>
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <input
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="学科 (如: 高等数学)"
                className="px-4 py-2.5 rounded-xl bg-white/[0.04] border border-white/[0.08] text-white text-sm placeholder:text-white/15 focus:border-cyan-400/30 focus:ring-1 focus:ring-cyan-400/20 outline-none"
              />
              <input
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="主题 (如: 微积分)"
                className="px-4 py-2.5 rounded-xl bg-white/[0.04] border border-white/[0.08] text-white text-sm placeholder:text-white/15 focus:border-cyan-400/30 focus:ring-1 focus:ring-cyan-400/20 outline-none"
              />
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="px-4 py-2.5 rounded-xl bg-white/[0.04] border border-white/[0.08] text-white text-sm placeholder:text-white/15 focus:border-cyan-400/30 focus:ring-1 focus:ring-cyan-400/20 outline-none"
              >
                <option value="" className="bg-[#0a192f]">难度 (可选)</option>
                <option value="入门" className="bg-[#0a192f]">入门</option>
                <option value="中级" className="bg-[#0a192f]">中级</option>
                <option value="高级" className="bg-[#0a192f]">高级</option>
              </select>
            </div>
          </div>

          {/* 分析按钮 */}
          <button
            onClick={runAnalysis}
            disabled={analyzing || files.length === 0 || isGuest}
            className="w-full px-6 py-3.5 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed font-medium flex items-center justify-center gap-2"
          >
            {analyzing ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" /> AI 分析中...
              </>
            ) : (
              <>
                <Brain className="w-5 h-5" /> 开始分析
              </>
            )}
          </button>

          {/* 错误提示 */}
          {analysisError && (
            <div className="bg-red-400/[0.06] border border-red-400/20 rounded-xl p-4 text-sm text-red-400">
              ❌ {analysisError}
            </div>
          )}

          {/* 分析结果 */}
          {analysisResult && <AnalysisReport result={analysisResult} />}
        </motion.div>
      )}
    </div>
  );
}
