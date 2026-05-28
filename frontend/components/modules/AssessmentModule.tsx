'use client';

import {
  BarChart3, FileText, Loader2, Award, TrendingUp, CheckCircle, AlertCircle,
  Lightbulb, Sparkles, Upload, X,
} from 'lucide-react';
import type { AssessmentResult } from './types';

interface AssessmentModuleProps {
  assessLoading: boolean;
  assessment: AssessmentResult | null;
  assessTab: 'assess' | 'analyze';
  setAssessTab: (tab: 'assess' | 'analyze') => void;
  handleAssess: () => void;
  // 分析相关
  analysisFiles: File[];
  setAnalysisFiles: React.Dispatch<React.SetStateAction<File[]>>;
  analysisDragOver: boolean;
  setAnalysisDragOver: (v: boolean) => void;
  analyzing: boolean;
  analysisResult: any;
  analysisFileInputRef: React.RefObject<HTMLInputElement>;
  analysisSubject: string;
  setAnalysisSubject: (v: string) => void;
  analysisTopic: string;
  setAnalysisTopic: (v: string) => void;
  analysisDifficulty: string;
  setAnalysisDifficulty: (v: string) => void;
  addAnalysisFiles: (fileList: FileList) => void;
  removeAnalysisFile: (idx: number) => void;
  formatFileSize: (bytes: number) => string;
  getFileIcon: (name: string) => string;
  handleAnalyze: () => void;
}

export default function AssessmentModule({
  assessLoading, assessment, assessTab, setAssessTab, handleAssess,
  analysisFiles, setAnalysisFiles, analysisDragOver, setAnalysisDragOver,
  analyzing, analysisResult, analysisFileInputRef,
  analysisSubject, setAnalysisSubject, analysisTopic, setAnalysisTopic,
  analysisDifficulty, setAnalysisDifficulty,
  addAnalysisFiles, removeAnalysisFile, formatFileSize, getFileIcon, handleAnalyze,
}: AssessmentModuleProps) {
  return (
    <div className="space-y-5">
      <h3 className="text-xl font-bold text-white">学习效果评估</h3>

      {/* Tab 切换 */}
      <div className="flex gap-2 bg-white/[0.04] rounded-xl p-1 border border-white/[0.06]">
        <button
          onClick={() => setAssessTab('assess')}
          className={`flex-1 px-4 py-2.5 rounded-lg font-medium text-sm transition-all ${
            assessTab === 'assess' ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white' : 'text-white/40 hover:text-white/60'
          }`}
        >
          <span className="flex items-center justify-center gap-2"><BarChart3 className="w-4 h-4" /> AI 综合评估</span>
        </button>
        <button
          onClick={() => setAssessTab('analyze')}
          className={`flex-1 px-4 py-2.5 rounded-lg font-medium text-sm transition-all ${
            assessTab === 'analyze' ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white' : 'text-white/40 hover:text-white/60'
          }`}
        >
          <span className="flex items-center justify-center gap-2"><FileText className="w-4 h-4" /> 资料分析</span>
        </button>
      </div>

      {/* Tab 1: AI 综合评估 */}
      {assessTab === 'assess' && (
        <div className="space-y-4">
          {!assessment ? (
            <div className="text-center py-12">
              <BarChart3 className="w-16 h-16 mx-auto mb-4 text-white/20" />
              <h4 className="text-lg font-semibold text-white/60 mb-2">开始学习效果评估</h4>
              <p className="text-sm text-white/40 mb-5">基于您的学习行为和画像特征，进行多维度综合评估</p>
              <button
                onClick={handleAssess}
                disabled={assessLoading}
                className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-xl hover:opacity-90 disabled:opacity-50 font-medium flex items-center gap-2 mx-auto"
              >
                {assessLoading ? <><Loader2 className="w-5 h-5 animate-spin" /> 评估中...</> : <><Award className="w-5 h-5" /> 开始评估</>}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="bg-gradient-to-r from-cyan-500 to-blue-500 rounded-2xl p-6 text-white text-center">
                <h4 className="text-lg font-semibold mb-3">综合评分</h4>
                <div className="text-5xl font-bold mb-1">{assessment.overall_score}</div>
                <p className="text-white/80 text-sm">满分 100 分</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {assessment.dimensions.map((dim, idx) => (
                  <div key={idx} className="glass-card rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold text-sm text-white">{dim.name}</span>
                      <span className="text-xs text-white/40">{dim.score}/{dim.max_score} · {dim.level}</span>
                    </div>
                    <div className="w-full bg-white/[0.06] rounded-full h-2 mb-2">
                      <div className="bg-gradient-to-r from-cyan-500 to-blue-500 h-2 rounded-full" style={{ width: `${(dim.score / dim.max_score) * 100}%` }} />
                    </div>
                    <p className="text-xs text-white/40">{dim.feedback}</p>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="glass-card rounded-xl p-4 border-emerald-400/20">
                  <h5 className="font-semibold text-emerald-400 mb-2 flex items-center gap-2 text-sm"><CheckCircle className="w-4 h-4" /> 优势</h5>
                  <ul className="text-sm text-white/60 space-y-1">{assessment.strengths.map((s, idx) => <li key={idx}>• {s}</li>)}</ul>
                </div>
                <div className="glass-card rounded-xl p-4 border-amber-400/20">
                  <h5 className="font-semibold text-amber-400 mb-2 flex items-center gap-2 text-sm"><AlertCircle className="w-4 h-4" /> 改进建议</h5>
                  <ul className="text-sm text-white/60 space-y-1">{assessment.improvements.map((imp, idx) => <li key={idx}>• {imp}</li>)}</ul>
                </div>
              </div>

              <div className="glass-card rounded-xl p-4 border-cyan-400/20">
                <h5 className="font-semibold text-cyan-400 mb-2 flex items-center gap-2 text-sm"><Lightbulb className="w-4 h-4" /> 学习建议</h5>
                <ul className="text-sm text-white/60 space-y-1">{assessment.recommendations.map((rec, idx) => <li key={idx}>• {rec}</li>)}</ul>
              </div>

              <button
                onClick={handleAssess}
                disabled={assessLoading}
                className="w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-xl hover:opacity-90 disabled:opacity-50 font-medium flex items-center justify-center gap-2"
              >
                {assessLoading ? <><Loader2 className="w-5 h-5 animate-spin" /> 重新评估中...</> : <><TrendingUp className="w-5 h-5" /> 重新评估</>}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: 资料分析 */}
      {assessTab === 'analyze' && (
        <div className="space-y-4">
          {/* 上传区域 */}
          <div
            onDrop={(e) => { e.preventDefault(); setAnalysisDragOver(false); addAnalysisFiles(e.dataTransfer.files); }}
            onDragOver={(e) => { e.preventDefault(); setAnalysisDragOver(true); }}
            onDragLeave={() => setAnalysisDragOver(false)}
            onClick={() => (analysisFileInputRef as any).current?.click()}
            className={`rounded-2xl border-2 border-dashed p-8 text-center cursor-pointer transition-colors ${
              analysisDragOver ? 'border-cyan-400/50 bg-cyan-400/5' : 'border-white/[0.08] bg-white/[0.02] hover:border-cyan-400/30'
            }`}
          >
            <input
              ref={analysisFileInputRef as any}
              type="file"
              multiple
              accept=".txt,.md,.pdf,.doc,.docx,.ppt,.pptx,.jpg,.jpeg,.png"
              className="hidden"
              onChange={(e) => { if (e.target.files) addAnalysisFiles(e.target.files); e.target.value = ''; }}
            />
            <Upload className={`w-10 h-10 mx-auto mb-3 ${analysisDragOver ? 'text-cyan-400' : 'text-white/30'}`} />
            <p className="text-sm font-medium text-white/60 mb-1">拖拽文件到此处，或 <span className="text-cyan-400 underline">点击选择</span></p>
            <p className="text-xs text-white/30">支持 PDF、Word、PPT、TXT、Markdown、图片 · 单文件 10MB · 最多 10 个</p>
          </div>

          {/* 文件列表 */}
          {analysisFiles.length > 0 && (
            <div className="glass-card rounded-2xl p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold text-white/60">已选 {analysisFiles.length} 个文件 ({formatFileSize(analysisFiles.reduce((s, f) => s + f.size, 0))})</span>
                <button onClick={() => setAnalysisFiles([])} className="text-xs text-red-400/80 hover:text-red-400">清空</button>
              </div>
              <div className="flex flex-wrap gap-2">
                {analysisFiles.map((f, i) => (
                  <div key={i} className="flex items-center gap-2 bg-white/[0.06] rounded-lg px-3 py-2 text-sm group">
                    <span>{getFileIcon(f.name)}</span>
                    <span className="text-white/60 max-w-[140px] truncate">{f.name}</span>
                    <span className="text-xs text-white/30">{formatFileSize(f.size)}</span>
                    <button onClick={(e) => { e.stopPropagation(); removeAnalysisFile(i); }} className="opacity-0 group-hover:opacity-100 text-white/30 hover:text-red-400/80">
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 可选参数 */}
          <div className="glass-card rounded-2xl p-4">
            <p className="text-xs text-white/30 mb-3">以下为可选参数，帮助 AI 更精准分析</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <input value={analysisSubject} onChange={(e) => setAnalysisSubject(e.target.value)} placeholder="学科（如：机器学习）"
                className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] text-white placeholder:text-white/15 rounded-lg text-sm focus:border-cyan-400/30 focus:outline-none" />
              <input value={analysisTopic} onChange={(e) => setAnalysisTopic(e.target.value)} placeholder="主题（如：神经网络）"
                className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] text-white placeholder:text-white/15 rounded-lg text-sm focus:border-cyan-400/30 focus:outline-none" />
              <select value={analysisDifficulty} onChange={(e) => setAnalysisDifficulty(e.target.value)}
                className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] text-white rounded-lg text-sm focus:border-cyan-400/30 focus:outline-none">
                <option value="beginner">初级</option>
                <option value="intermediate">中级</option>
                <option value="advanced">高级</option>
              </select>
            </div>
          </div>

          {/* 分析按钮 */}
          <button
            onClick={handleAnalyze}
            disabled={analyzing || analysisFiles.length === 0}
            className="w-full py-3 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-xl hover:opacity-90 disabled:opacity-50 font-medium flex items-center justify-center gap-2"
          >
            {analyzing ? <><Loader2 className="w-5 h-5 animate-spin" /> AI 分析中...</> : <><Sparkles className="w-5 h-5" /> 开始分析</>}
          </button>

          {/* 分析结果 */}
          {analysisResult && (
            <div className="space-y-4">
              <div className="bg-gradient-to-r from-emerald-500 to-teal-500 rounded-2xl p-6 text-white text-center">
                <h4 className="text-lg font-semibold mb-3">学习效果评分</h4>
                <div className="text-5xl font-bold mb-1">{analysisResult.overall_score || '--'}</div>
                <p className="text-white/80 text-sm">满分 100</p>
              </div>

              {analysisResult.knowledge_overview && (
                <div className="glass-card rounded-xl p-4">
                  <h5 className="font-semibold text-white mb-2 text-sm"> 知识总览</h5>
                  <p className="text-sm text-white/60 leading-relaxed">{analysisResult.knowledge_overview}</p>
                </div>
              )}

              {analysisResult.knowledge_points?.length > 0 && (
                <div className="glass-card rounded-xl p-4">
                  <h5 className="font-semibold text-white mb-3 text-sm"> 知识点分析</h5>
                  <div className="space-y-2">
                    {analysisResult.knowledge_points.map((kp: any, i: number) => (
                      <div key={i} className="bg-white/[0.04] rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-sm text-white">{kp.point}</span>
                          {kp.importance && (
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                              kp.importance === 'high' ? 'bg-red-400/15 text-red-400/80' :
                              kp.importance === 'medium' ? 'bg-amber-400/15 text-amber-400' :
                              'bg-emerald-400/15 text-emerald-400'
                            }`}>
                              {kp.importance === 'high' ? '重要' : kp.importance === 'medium' ? '中等' : '了解'}
                            </span>
                          )}
                          {kp.mastery_level && (
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                              kp.mastery_level === 'good' ? 'bg-emerald-400/15 text-emerald-400' :
                              kp.mastery_level === 'moderate' ? 'bg-amber-400/15 text-amber-400' :
                              'bg-red-400/15 text-red-400/80'
                            }`}>
                              {kp.mastery_level === 'good' ? '已掌握' : kp.mastery_level === 'moderate' ? '部分掌握' : '需加强'}
                            </span>
                          )}
                        </div>
                        {kp.description && <p className="text-xs text-white/40">{kp.description}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {analysisResult.strengths?.length > 0 && (
                  <div className="glass-card rounded-xl p-4 border-emerald-400/20">
                    <h5 className="font-semibold text-emerald-400 mb-2 text-sm">✅ 学习优势</h5>
                    <ul className="text-sm text-white/60 space-y-1">{analysisResult.strengths.map((s: string, i: number) => <li key={i}>• {s}</li>)}</ul>
                  </div>
                )}
                {analysisResult.weaknesses?.length > 0 && (
                  <div className="glass-card rounded-xl p-4 border-red-400/20">
                    <h5 className="font-semibold text-red-400/80 mb-2 text-sm">⚠️ 薄弱环节</h5>
                    <ul className="text-sm text-white/60 space-y-1">{analysisResult.weaknesses.map((w: string, i: number) => <li key={i}>• {w}</li>)}</ul>
                  </div>
                )}
              </div>

              {analysisResult.learning_gaps?.length > 0 && (
                <div className="glass-card rounded-xl p-4 border-amber-400/20">
                  <h5 className="font-semibold text-amber-400 mb-2 text-sm"> 学习缺口</h5>
                  <ul className="text-sm text-white/60 space-y-1">{analysisResult.learning_gaps.map((g: string, i: number) => <li key={i}>• {g}</li>)}</ul>
                </div>
              )}

              {analysisResult.difficulty_assessment && (
                <div className="glass-card rounded-xl p-4 border-purple-400/20">
                  <h5 className="font-semibold text-purple-400 mb-2 text-sm"> 难度评估</h5>
                  <p className="text-sm text-white/60">{analysisResult.difficulty_assessment}</p>
                </div>
              )}

              {analysisResult.study_recommendations?.length > 0 && (
                <div className="glass-card rounded-xl p-4 border-cyan-400/20">
                  <h5 className="font-semibold text-cyan-400 mb-2 text-sm"> 学习建议</h5>
                  <div className="space-y-2">
                    {analysisResult.study_recommendations.map((rec: any, i: number) => (
                      <div key={i} className="flex items-start gap-2">
                        <div className="w-5 h-5 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0 mt-0.5">{i + 1}</div>
                        <p className="text-sm text-white/60">{typeof rec === 'string' ? rec : rec.recommendation || rec.title || JSON.stringify(rec)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {analysisResult.summary && (
                <div className="glass-card rounded-xl p-4 border-emerald-400/20">
                  <h5 className="font-semibold text-emerald-400 mb-2 text-sm"> AI 总结</h5>
                  <p className="text-sm text-white/60 leading-relaxed">{analysisResult.summary}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
