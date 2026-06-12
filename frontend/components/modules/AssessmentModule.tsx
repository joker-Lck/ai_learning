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
    <div className="space-y-8">
      <h3 className="text-3xl font-bold text-white">学习效果评估</h3>

      {/* Tab 切换 */}
      <div className="flex gap-2 p-1 border-b border-white/[0.06]">
        <button
          onClick={() => setAssessTab('assess')}
          className={`flex-1 px-3 py-2 rounded-md font-medium text-sm transition-colors ${
            assessTab === 'assess' ? 'bg-white/[0.06] text-white' : 'text-white/35 hover:text-white/55'
          }`}
        >
          <span className="flex items-center justify-center gap-1.5"><BarChart3 className="w-3.5 h-3.5" /> AI 综合评估</span>
        </button>
        <button
          onClick={() => setAssessTab('analyze')}
          className={`flex-1 px-3 py-2 rounded-md font-medium text-sm transition-colors ${
            assessTab === 'analyze' ? 'bg-white/[0.06] text-white' : 'text-white/35 hover:text-white/55'
          }`}
        >
          <span className="flex items-center justify-center gap-1.5"><FileText className="w-3.5 h-3.5" /> 资料分析</span>
        </button>
      </div>

      {/* Tab 1: AI 综合评估 */}
      {assessTab === 'assess' && (
        <div className="space-y-3">
          {!assessment ? (
            <div className="text-center py-10">
              <BarChart3 className="w-12 h-12 mx-auto mb-3 text-white/15" />
              <h4 className="text-base font-semibold text-white/50 mb-1">开始学习效果评估</h4>
              <p className="text-xs text-white/35 mb-4">基于您的学习行为和画像特征，进行多维度综合评估</p>
              <button
                onClick={handleAssess}
                disabled={assessLoading}
                className="px-5 py-2.5 bg-purple-500 text-white rounded-lg hover:bg-purple-400 disabled:opacity-50 font-medium flex items-center gap-2 mx-auto transition-colors"
              >
                {assessLoading ? <><Loader2 className="w-5 h-5 animate-spin" /> 评估中...</> : <><Award className="w-5 h-5" /> 开始评估</>}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {/* 综合评分卡片 */}
              <div className="bg-purple-500 rounded-lg p-4 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-base font-semibold mb-0.5">综合评分</h4>
                    <p className="text-white/60 text-xs">
                      评估周期: {assessment.period_start || '--'} 至 {assessment.period_end || '--'}
                    </p>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold">{assessment.overall_score ?? '--'}</div>
                    <p className="text-white/70 text-[10px] mt-0.5">满分 100</p>
                  </div>
                </div>
                {assessment.grade && (
                  <div className="mt-2 inline-block px-2.5 py-0.5 bg-white/15 rounded-md text-xs font-medium">
                    {assessment.grade}
                  </div>
                )}
                {assessment.generated_at && (
                  <p className="text-white/40 text-[10px] mt-1.5">生成时间: {assessment.generated_at}</p>
                )}
              </div>

              {/* 多维度评分 */}
              {assessment.dimensions?.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {assessment.dimensions.map((dim, idx) => (
                    <div key={idx} className="border border-white/[0.06] rounded-lg p-3 bg-white/[0.02]">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="font-medium text-sm text-white">{dim.name}</span>
                        <span className="text-[10px] text-white/35">{dim.score}/{dim.max_score} · {dim.level}</span>
                      </div>
                      <div className="w-full bg-white/[0.06] rounded-full h-1.5 mb-1.5">
                        <div
                          className="bg-purple-500 h-1.5 rounded-full transition-all duration-700"
                          style={{ width: `${(dim.score / dim.max_score) * 100}%` }}
                        />
                      </div>
                      <p className="text-[11px] text-white/35">{dim.feedback}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* 详细指标卡片 */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {assessment.knowledge_mastery?.overall_score !== undefined && (
                  <div className="border border-white/[0.06] rounded-lg p-2.5 text-center bg-white/[0.02]">
                    <div className="text-lg font-bold text-purple-400">{Math.round(assessment.knowledge_mastery.overall_score * 100)}%</div>
                    <p className="text-[10px] text-white/35 mt-0.5">知识掌握度</p>
                  </div>
                )}
                {assessment.engagement_level !== undefined && (
                  <div className="border border-white/[0.06] rounded-lg p-2.5 text-center bg-white/[0.02]">
                    <div className="text-lg font-bold text-emerald-400">{Math.round(assessment.engagement_level * 100)}%</div>
                    <p className="text-[10px] text-white/35 mt-0.5">学习参与度</p>
                  </div>
                )}
                {assessment.time_investment !== undefined && (
                  <div className="border border-white/[0.06] rounded-lg p-2.5 text-center bg-white/[0.02]">
                    <div className="text-lg font-bold text-amber-400">{assessment.time_investment}h</div>
                    <p className="text-[10px] text-white/35 mt-0.5">学习时长</p>
                  </div>
                )}
                {assessment.skill_progress?.progress_rate !== undefined && (
                  <div className="border border-white/[0.06] rounded-lg p-2.5 text-center bg-white/[0.02]">
                    <div className="text-lg font-bold text-violet-400">+{Math.round(assessment.skill_progress.progress_rate * 100)}%</div>
                    <p className="text-[10px] text-white/35 mt-0.5">技能进步</p>
                  </div>
                )}
              </div>

              {/* 各主题掌握度 */}
              {assessment.knowledge_mastery?.topics && Object.keys(assessment.knowledge_mastery.topics).length > 0 && (
                <div className="border border-white/[0.06] rounded-lg p-4 bg-white/[0.02]">
                  <h5 className="font-semibold text-white mb-2 text-sm flex items-center gap-2">
                    <BarChart3 className="w-3.5 h-3.5 text-purple-400" /> 各科目成绩分布
                  </h5>
                  {/* 成绩柱状图 */}
                  <div className="flex items-end gap-1.5 h-32 mb-3">
                    {Object.entries(assessment.knowledge_mastery.topics).slice(0, 10).map(([topic, score], i) => {
                      const height = Math.max(score * 100, 8);
                      const color = score >= 0.8 ? 'from-purple-500 to-purple-400' :
                                   score >= 0.6 ? 'from-amber-500 to-amber-400' :
                                   'from-red-500 to-red-400';
                      return (
                        <div key={i} className="flex-1 flex flex-col items-center gap-0.5">
                          <span className="text-[9px] text-white/45">{Math.round(score * 100)}</span>
                          <div className={`w-full bg-gradient-to-t ${color} rounded-t-sm transition-all duration-700`}
                               style={{ height: `${height}%` }} />
                          <span className="text-[9px] text-white/35 truncate w-full text-center">{topic.slice(0, 4)}</span>
                        </div>
                      );
                    })}
                  </div>
                  {/* 掌握度列表 */}
                  <div className="space-y-1.5">
                    {Object.entries(assessment.knowledge_mastery.topics).map(([topic, score], i) => (
                      <div key={i}>
                        <div className="flex items-center justify-between mb-0.5">
                          <span className="text-xs text-white/60">{topic}</span>
                          <span className="text-[10px] text-white/35">{Math.round(score * 100)}%</span>
                        </div>
                        <div className="w-full bg-white/[0.06] rounded-full h-1">
                          <div
                            className="h-1 rounded-full transition-all duration-700"
                            style={{
                              width: `${score * 100}%`,
                              background: score >= 0.8 ? 'linear-gradient(to right, #6643FF, #8B7AFF)' :
                                         score >= 0.6 ? 'linear-gradient(to right, #f59e0b, #fbbf24)' :
                                         'linear-gradient(to right, #ef4444, #f87171)',
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 数据总览 */}
              {assessment.raw_data && (
                <div className="border border-white/[0.06] rounded-lg p-4 bg-white/[0.02]">
                  <h5 className="font-semibold text-white mb-2 text-sm">学习数据总览</h5>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    <div className="bg-white/[0.04] rounded-md p-2.5 text-center">
                      <div className="text-lg font-bold text-purple-400">{assessment.raw_data.grades?.length || 0}</div>
                      <p className="text-[10px] text-white/35 mt-0.5">录入课程成绩</p>
                    </div>
                    <div className="bg-white/[0.04] rounded-md p-2.5 text-center">
                      <div className="text-lg font-bold text-emerald-400">{assessment.raw_data.courses_count || 0}</div>
                      <p className="text-[10px] text-white/35 mt-0.5">课表课程数</p>
                    </div>
                    <div className="bg-white/[0.04] rounded-md p-2.5 text-center">
                      <div className="text-lg font-bold text-amber-400">{assessment.raw_data.error_notes_count || 0}</div>
                      <p className="text-[10px] text-white/35 mt-0.5">错题记录</p>
                    </div>
                    <div className="bg-white/[0.04] rounded-md p-2.5 text-center">
                      <div className="text-lg font-bold text-violet-400">{assessment.raw_data.plans_count || 0}</div>
                      <p className="text-[10px] text-white/35 mt-0.5">学习计划</p>
                    </div>
                  </div>
                </div>
              )}

              {/* 成绩趋势 */}
              {assessment.raw_data?.grade_trend && assessment.raw_data.grade_trend.length > 0 && (
                <div className="border border-white/[0.06] rounded-lg p-4 bg-white/[0.02]">
                  <h5 className="font-semibold text-white mb-2 text-sm flex items-center gap-2">
                    <TrendingUp className="w-3.5 h-3.5 text-purple-400" /> 成绩趋势
                    {assessment.grade_trend && (
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        assessment.grade_trend === '上升' ? 'bg-emerald-400/15 text-emerald-400' :
                        assessment.grade_trend === '稳定' ? 'bg-amber-400/15 text-amber-400' :
                        'bg-red-400/15 text-red-400'
                      }`}>{assessment.grade_trend}</span>
                    )}
                  </h5>
                  <div className="space-y-1.5">
                    {assessment.raw_data.grade_trend.map((item, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <span className="text-[10px] text-white/35 w-16 truncate">{item.semester}</span>
                        <span className="text-xs text-white/55 w-20 truncate">{item.course}</span>
                        <div className="flex-1 bg-white/[0.06] rounded-full h-1.5">
                          <div                           className="h-1.5 rounded-full transition-all duration-700"
                               style={{
                                 width: `${item.score}%`,
                                 background: item.score >= 80 ? 'linear-gradient(to right, #6643FF, #8B7AFF)' :
                                            item.score >= 60 ? 'linear-gradient(to right, #f59e0b, #fbbf24)' :
                                            'linear-gradient(to right, #ef4444, #f87171)',
                               }} />
                        </div>
                        <span className="text-xs font-medium text-white/50 w-8 text-right">{item.score}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 详细分析总结 */}
              {assessment.analysis_summary && (
                <div className="border border-white/[0.06] rounded-lg p-4 bg-white/[0.02] border-blue-400/20">
                  <h5 className="font-semibold text-blue-400 mb-1.5 text-sm flex items-center gap-2"><Sparkles className="w-3.5 h-3.5" /> 详细分析</h5>
                  <p className="text-xs text-white/50 leading-relaxed whitespace-pre-line">{assessment.analysis_summary}</p>
                </div>
              )}

              {/* 技能提升领域 */}
              {assessment.skill_progress?.improvement_areas?.length > 0 && (
                <div className="border border-white/[0.06] rounded-lg p-4 bg-white/[0.02] border-violet-400/20">
                  <h5 className="font-semibold text-violet-400 mb-1.5 text-sm">需提升的技能</h5>
                  <div className="flex flex-wrap gap-1.5">
                    {assessment.skill_progress.improvement_areas.map((area, i) => (
                      <span key={i} className="px-2 py-0.5 bg-violet-400/10 text-violet-300 text-[11px] rounded-md">{area}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* 优势与不足 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {assessment.strengths?.length > 0 && (
                  <div className="border border-white/[0.06] rounded-lg p-3 border-emerald-400/15 bg-white/[0.02]">
                    <h5 className="font-semibold text-emerald-400 mb-1.5 flex items-center gap-2 text-sm"><CheckCircle className="w-3.5 h-3.5" /> 学习优势</h5>
                    <ul className="text-xs text-white/50 space-y-0.5">
                      {assessment.strengths.map((s, idx) => <li key={idx} className="flex items-start gap-1.5"><span className="text-emerald-400 mt-0.5">•</span>{s}</li>)}
                    </ul>
                  </div>
                )}
                {assessment.weaknesses?.length > 0 && (
                  <div className="border border-white/[0.06] rounded-lg p-3 border-amber-400/15 bg-white/[0.02]">
                    <h5 className="font-semibold text-amber-400 mb-1.5 flex items-center gap-2 text-sm"><AlertCircle className="w-3.5 h-3.5" /> 薄弱环节</h5>
                    <ul className="text-xs text-white/50 space-y-0.5">
                      {assessment.weaknesses.map((w, idx) => <li key={idx} className="flex items-start gap-1.5"><span className="text-amber-400 mt-0.5">•</span>{w}</li>)}
                    </ul>
                  </div>
                )}
                {assessment.weaknesses?.length > 0 && (
                  <div className="border border-white/[0.06] rounded-lg p-4 bg-white/[0.02] border-amber-400/20">
                    <h5 className="font-semibold text-amber-400 mb-2 flex items-center gap-2 text-sm"><AlertCircle className="w-4 h-4" /> 薄弱环节</h5>
                    <ul className="text-sm text-white/60 space-y-1">
                      {assessment.weaknesses.map((w, idx) => <li key={idx} className="flex items-start gap-1.5"><span className="text-amber-400 mt-0.5">•</span>{w}</li>)}
                    </ul>
                  </div>
                )}
              </div>

              {/* 改进建议 */}
              {assessment.improvements?.length > 0 && (
                <div className="border border-white/[0.06] rounded-lg p-3 border-orange-400/15 bg-white/[0.02]">
                  <h5 className="font-semibold text-orange-400 mb-1.5 flex items-center gap-2 text-sm"><TrendingUp className="w-3.5 h-3.5" /> 改进建议</h5>
                  <div className="space-y-1.5">
                    {assessment.improvements.map((imp, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <div className="w-4 h-4 rounded-full bg-orange-500/20 flex items-center justify-center text-orange-400 text-[9px] font-bold flex-shrink-0 mt-0.5">{i + 1}</div>
                        <p className="text-xs text-white/50">{imp}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 学习建议 */}
              {assessment.recommendations?.length > 0 && (
                <div className="border border-white/[0.06] rounded-lg p-3 border-purple-400/15 bg-white/[0.02]">
                  <h5 className="font-semibold text-purple-400 mb-1.5 flex items-center gap-2 text-sm"><Lightbulb className="w-3.5 h-3.5" /> 学习建议</h5>
                  <div className="space-y-1.5">
                    {assessment.recommendations.map((rec, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <div className="w-4 h-4 rounded-full bg-purple-500/20 flex items-center justify-center text-purple-400 text-[9px] font-bold flex-shrink-0 mt-0.5">{i + 1}</div>
                        <p className="text-xs text-white/50">{rec}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 综合建议 */}
              {assessment.recommendation && (
                <div className="border border-white/[0.06] rounded-lg p-3 border-blue-400/15 bg-white/[0.02]">
                  <h5 className="font-semibold text-blue-400 mb-1.5 text-sm flex items-center gap-2"><Sparkles className="w-3.5 h-3.5" /> 综合建议</h5>
                  <p className="text-xs text-white/50 leading-relaxed">{assessment.recommendation}</p>
                </div>
              )}

              {/* 下一步重点 */}
              {assessment.next_focus?.length > 0 && (
                <div className="border border-white/[0.06] rounded-lg p-3 border-indigo-400/15 bg-white/[0.02]">
                  <h5 className="font-semibold text-indigo-400 mb-1.5 text-sm">下一步重点</h5>
                  <div className="space-y-1">
                    {assessment.next_focus.map((f, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs text-white/50">
                        <span className="w-1 h-1 rounded-full bg-indigo-400 flex-shrink-0" />
                        {f}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 鼓励话语 */}
              {assessment.motivational_message && (
                <div className="border border-white/[0.06] rounded-lg p-3 border-pink-400/15 bg-white/[0.02] text-center">
                  <p className="text-xs text-pink-300/70">{assessment.motivational_message}</p>
                </div>
              )}

              <button
                onClick={handleAssess}
                disabled={assessLoading}
                className="w-full py-2.5 bg-purple-500 text-white rounded-lg hover:bg-purple-400 disabled:opacity-50 font-medium flex items-center justify-center gap-2 transition-colors"
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
            className={`rounded-xl border-2 border-dashed p-6 text-center cursor-pointer transition-colors ${
              analysisDragOver ? 'border-purple-400/40 bg-cyan-400/5' : 'border-white/[0.06] bg-white/[0.02] hover:border-white/[0.12]'
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
            <Upload className={`w-10 h-10 mx-auto mb-3 ${analysisDragOver ? 'text-purple-400' : 'text-white/25'}`} />
            <p className="text-base font-medium text-white/50 mb-1">拖拽文件到此处，或 <span className="text-purple-400 underline">点击选择</span></p>
            <p className="text-sm text-white/25">支持 PDF、Word、PPT、TXT、Markdown、图片 · 单文件 10MB · 最多 10 个</p>
          </div>

          {/* 文件列表 */}
          {analysisFiles.length > 0 && (
            <div className="border border-white/[0.06] rounded-xl p-4 bg-white/[0.02]">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-medium text-white/50">已选 {analysisFiles.length} 个文件 ({formatFileSize(analysisFiles.reduce((s, f) => s + f.size, 0))})</span>
                <button onClick={() => setAnalysisFiles([])} className="text-[11px] text-red-400/60 hover:text-red-400">清空</button>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {analysisFiles.map((f, i) => (
                  <div key={i} className="flex items-center gap-2 bg-white/[0.04] rounded-md px-2.5 py-1.5 text-xs group">
                    <span>{getFileIcon(f.name)}</span>
                    <span className="text-white/50 max-w-[120px] truncate">{f.name}</span>
                    <span className="text-white/25 text-[10px]">{formatFileSize(f.size)}</span>
                    <button onClick={(e) => { e.stopPropagation(); removeAnalysisFile(i); }} className="opacity-0 group-hover:opacity-100 text-white/25 hover:text-red-400/80">
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 可选参数 */}
          <div className="border border-white/[0.06] rounded-xl p-4 bg-white/[0.02]">
            <p className="text-sm text-white/25 mb-3">以下为可选参数，帮助 AI 更精准分析</p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <input value={analysisSubject} onChange={(e) => setAnalysisSubject(e.target.value)} placeholder="学科（如：机器学习）"
                  className="px-4 py-3 bg-white/[0.04] border border-white/[0.06] text-white placeholder:text-white/20 rounded-lg text-base focus:border-purple-500/30 focus:outline-none" />
                <input value={analysisTopic} onChange={(e) => setAnalysisTopic(e.target.value)} placeholder="主题（如：神经网络）"
                  className="px-4 py-3 bg-white/[0.04] border border-white/[0.06] text-white placeholder:text-white/20 rounded-lg text-base focus:border-purple-500/30 focus:outline-none" />
                <select value={analysisDifficulty} onChange={(e) => setAnalysisDifficulty(e.target.value)}
                  className="px-4 py-3 bg-white/[0.04] border border-white/[0.06] text-white rounded-lg text-base focus:border-purple-500/30 focus:outline-none [&>option]:bg-[#0f0f0f] [&>option]:text-white">
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
            className="w-full py-2.5 bg-emerald-500 text-white rounded-lg hover:bg-emerald-400 disabled:opacity-50 font-medium flex items-center justify-center gap-2 transition-colors"
          >
            {analyzing ? <><Loader2 className="w-5 h-5 animate-spin" /> AI 分析中...</> : <><Sparkles className="w-5 h-5" /> 开始分析</>}
          </button>

          {/* 分析结果 */}
          {analysisResult && (
            <div className="space-y-3">
              <div className="bg-purple-500 rounded-lg p-4 text-white text-center">
                <h4 className="text-base font-semibold mb-2">学习效果评分</h4>
                <div className="text-4xl font-bold mb-0.5">{analysisResult.overall_score || '--'}</div>
                <p className="text-white/70 text-xs">满分 100</p>
              </div>

              {analysisResult.knowledge_overview && (
                <div className="border border-white/[0.06] rounded-lg p-3 bg-white/[0.02]">
                  <h5 className="font-semibold text-white mb-1.5 text-sm">知识总览</h5>
                  <p className="text-xs text-white/50 leading-relaxed">{analysisResult.knowledge_overview}</p>
                </div>
              )}

              {analysisResult.knowledge_points?.length > 0 && (
                <div className="border border-white/[0.06] rounded-lg p-3 bg-white/[0.02]">
                  <h5 className="font-semibold text-white mb-2 text-sm">知识点分析</h5>
                  <div className="space-y-1.5">
                    {analysisResult.knowledge_points.map((kp: any, i: number) => (
                      <div key={i} className="bg-white/[0.03] rounded-md p-2.5">
                        <div className="flex items-center gap-1.5 mb-0.5">
                          <span className="font-medium text-xs text-white">{kp.point}</span>
                          {kp.importance && (
                            <span className={`text-[9px] px-1.5 py-0.5 rounded-sm ${
                              kp.importance === 'high' ? 'bg-red-400/15 text-red-400/80' :
                              kp.importance === 'medium' ? 'bg-amber-400/15 text-amber-400' :
                              'bg-emerald-400/15 text-emerald-400'
                            }`}>
                              {kp.importance === 'high' ? '重要' : kp.importance === 'medium' ? '中等' : '了解'}
                            </span>
                          )}
                          {kp.mastery_level && (
                            <span className={`text-[9px] px-1.5 py-0.5 rounded-sm ${
                              kp.mastery_level === 'good' ? 'bg-emerald-400/15 text-emerald-400' :
                              kp.mastery_level === 'moderate' ? 'bg-amber-400/15 text-amber-400' :
                              'bg-red-400/15 text-red-400/80'
                            }`}>
                              {kp.mastery_level === 'good' ? '已掌握' : kp.mastery_level === 'moderate' ? '部分掌握' : '需加强'}
                            </span>
                          )}
                        </div>
                        {kp.description && <p className="text-[10px] text-white/35">{kp.description}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {analysisResult.strengths?.length > 0 && (
                  <div className="border border-white/[0.06] rounded-lg p-3 border-emerald-400/15 bg-white/[0.02]">
                    <h5 className="font-semibold text-emerald-400 mb-1.5 text-sm">学习优势</h5>
                    <ul className="text-xs text-white/50 space-y-0.5">{analysisResult.strengths.map((s: string, i: number) => <li key={i}>• {s}</li>)}</ul>
                  </div>
                )}
                {analysisResult.weaknesses?.length > 0 && (
                  <div className="border border-white/[0.06] rounded-lg p-3 border-red-400/15 bg-white/[0.02]">
                    <h5 className="font-semibold text-red-400/80 mb-1.5 text-sm">薄弱环节</h5>
                    <ul className="text-xs text-white/50 space-y-0.5">{analysisResult.weaknesses.map((w: string, i: number) => <li key={i}>• {w}</li>)}</ul>
                  </div>
                )}
                {analysisResult.weaknesses?.length > 0 && (
                  <div className="border border-white/[0.06] rounded-lg p-4 bg-white/[0.02] border-red-400/20">
                    <h5 className="font-semibold text-red-400/80 mb-2 text-sm">⚠️ 薄弱环节</h5>
                    <ul className="text-sm text-white/60 space-y-1">{analysisResult.weaknesses.map((w: string, i: number) => <li key={i}>• {w}</li>)}</ul>
                  </div>
                )}
              </div>

              {analysisResult.learning_gaps?.length > 0 && (
                <div className="border border-white/[0.06] rounded-lg p-3 border-amber-400/15 bg-white/[0.02]">
                  <h5 className="font-semibold text-amber-400 mb-1.5 text-sm">学习缺口</h5>
                  <ul className="text-xs text-white/50 space-y-0.5">{analysisResult.learning_gaps.map((g: string, i: number) => <li key={i}>• {g}</li>)}</ul>
                </div>
              )}

              {analysisResult.difficulty_assessment && (
                <div className="border border-white/[0.06] rounded-lg p-3 border-purple-400/15 bg-white/[0.02]">
                  <h5 className="font-semibold text-purple-400 mb-1.5 text-sm">难度评估</h5>
                  <p className="text-xs text-white/50">{analysisResult.difficulty_assessment}</p>
                </div>
              )}

              {analysisResult.study_recommendations?.length > 0 && (
                <div className="border border-white/[0.06] rounded-lg p-3 border-purple-400/15 bg-white/[0.02]">
                  <h5 className="font-semibold text-purple-400 mb-1.5 text-sm">学习建议</h5>
                  <div className="space-y-1.5">
                    {analysisResult.study_recommendations.map((rec: any, i: number) => (
                      <div key={i} className="flex items-start gap-2">
                        <div className="w-4 h-4 rounded-full bg-purple-500/20 flex items-center justify-center text-purple-400 text-[9px] font-bold flex-shrink-0 mt-0.5">{i + 1}</div>
                        <p className="text-xs text-white/50">{typeof rec === 'string' ? rec : rec.recommendation || rec.title || JSON.stringify(rec)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {analysisResult.summary && (
                <div className="border border-white/[0.06] rounded-lg p-3 border-emerald-400/15 bg-white/[0.02]">
                  <h5 className="font-semibold text-emerald-400 mb-1.5 text-sm">AI 总结</h5>
                  <p className="text-xs text-white/50 leading-relaxed">{analysisResult.summary}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
