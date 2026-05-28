'use client';

import {
  Brain, FileText, GitBranch, FileCode, Video, Sparkles, Code, BookOpen,
  Loader2, CheckCircle,
} from 'lucide-react';
import api from '@/lib/api';
import type { ResourceItem } from './types';

interface ResourcesModuleProps {
  subject: string;
  setSubject: (v: string) => void;
  topic: string;
  setTopic: (v: string) => void;
  selectedTypes: string[];
  setSelectedTypes: React.Dispatch<React.SetStateAction<string[]>>;
  difficulty: string;
  setDifficulty: (v: string) => void;
  resourceLoading: boolean;
  resources: ResourceItem[];
  handleGenerateResources: () => void;
  getTypeName: (type: string) => string;
}

export default function ResourcesModule({
  subject, setSubject, topic, setTopic, selectedTypes, setSelectedTypes,
  difficulty, setDifficulty, resourceLoading, resources, handleGenerateResources, getTypeName,
}: ResourcesModuleProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-white">多智能体资源生成</h3>

      <div className="glass-card rounded-xl p-4 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-white/60 mb-1">学科</label>
            <input type="text" value={subject} onChange={(e) => setSubject(e.target.value)}
              className="w-full px-3 py-2 bg-white/[0.04] border border-white/[0.08] text-white placeholder:text-white/15 rounded-lg focus:border-cyan-400/30 focus:outline-none" />
          </div>
          <div>
            <label className="block text-sm font-medium text-white/60 mb-1">主题</label>
            <input type="text" value={topic} onChange={(e) => setTopic(e.target.value)}
              className="w-full px-3 py-2 bg-white/[0.04] border border-white/[0.08] text-white placeholder:text-white/15 rounded-lg focus:border-cyan-400/30 focus:outline-none" />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-white/60 mb-2">资源类型</label>
          <div className="flex flex-wrap gap-2">
            {[
              { id: 'document', label: ' 文档', icon: FileText },
              { id: 'mindmap', label: ' 思维导图', icon: GitBranch },
              { id: 'quiz', label: ' 题库', icon: FileCode },
              { id: 'video', label: '🎥 视频', icon: Video },
              { id: 'animation', label: '✨ 动画', icon: Sparkles },
              { id: 'code', label: '💻 代码', icon: Code },
              { id: 'reading', label: '📖 阅读', icon: BookOpen },
            ].map(type => (
              <button
                key={type.id}
                onClick={() => setSelectedTypes(prev => prev.includes(type.id) ? prev.filter(t => t !== type.id) : [...prev, type.id])}
                className={`px-3 py-2 rounded-lg border transition-all text-sm ${
                  selectedTypes.includes(type.id)
                    ? 'border-cyan-400/30 bg-cyan-400/10 text-cyan-400'
                    : 'border-white/[0.08] bg-white/[0.02] text-white/40 hover:border-white/[0.15] hover:text-white/60'
                }`}
              >
                {type.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-white/60 mb-1">难度级别</label>
          <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}
            className="w-full px-3 py-2 bg-white/[0.04] border border-white/[0.08] text-white rounded-lg focus:border-cyan-400/30 focus:outline-none">
            <option value="beginner">初级</option>
            <option value="intermediate">中级</option>
            <option value="advanced">高级</option>
          </select>
        </div>

        <button
          onClick={handleGenerateResources}
          disabled={resourceLoading || selectedTypes.length === 0}
          className="w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold"
        >
          {resourceLoading ? (
            <><Loader2 className="w-5 h-5 animate-spin" /> 生成中...</>
          ) : (
            <><Brain className="w-5 h-5" /> 开始生成资源</>
          )}
        </button>
      </div>

      {resources.length > 0 && (
        <div className="space-y-3">
          <h4 className="font-bold text-white">生成的资源 ({resources.length})</h4>
          {resources.map((resource, idx) => (
            <div key={idx} className="glass-card rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  {resource.type === 'document' && <FileText className="w-5 h-5 text-cyan-400" />}
                  {resource.type === 'mindmap' && <GitBranch className="w-5 h-5 text-emerald-400" />}
                  {resource.type === 'quiz' && <FileCode className="w-5 h-5 text-amber-400" />}
                  <span className="font-semibold text-white">{resource.title}</span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      const previewWindow = window.open('', '_blank');
                      if (previewWindow) {
                        const content = resource.content_data ? JSON.stringify(resource.content_data, null, 2) : '暂无内容数据';
                        previewWindow.document.write(`<html><head><title>${resource.title} - 预览</title><style>body{font-family:Arial,sans-serif;padding:40px;line-height:1.6;max-width:900px;margin:0 auto}h1{color:#2563eb;border-bottom:2px solid #e5e7eb;padding-bottom:10px}pre{background:#f3f4f6;padding:16px;border-radius:8px;overflow-x:auto;white-space:pre-wrap;word-wrap:break-word;font-size:14px}</style></head><body><h1>${resource.title}</h1><pre>${content.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre></body></html>`);
                        previewWindow.document.close();
                      }
                    }}
                    className="px-3 py-1 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:opacity-90 transition-colors text-sm flex items-center gap-1"
                  >
                    👁️ 预览
                  </button>
                  <button
                    onClick={async () => {
                      try {
                        const res: any = await api.exportResource(resource);
                        if (res.success && res.data) {
                          const filePath: string = res.data.file_path.replace(/\\/g, '/');
                          const fileName = filePath.split('/').pop() || filePath;
                          const a = document.createElement('a');
                          a.href = `/exports/${fileName}`;
                          a.download = res.data.filename || fileName;
                          document.body.appendChild(a);
                          a.click();
                          document.body.removeChild(a);
                        } else {
                          alert(`❌ 导出失败: ${res.message || '未知错误'}`);
                        }
                      } catch (error: any) {
                        alert(`❌ 导出失败: ${error.message || '网络错误'}`);
                      }
                    }}
                    className="px-3 py-1 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-lg hover:opacity-90 transition-colors text-sm flex items-center gap-1"
                  >
                    📥 导出
                  </button>
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                </div>
              </div>
              <div className="text-sm text-white/60 whitespace-pre-wrap">
                {resource.content_data ? JSON.stringify(resource.content_data, null, 2) : '暂无内容'}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
