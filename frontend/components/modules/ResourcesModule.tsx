'use client';

import {
  Brain, FileText, GitBranch, FileCode, Video, Sparkles, Code, BookOpen,
  Loader2, CheckCircle, ChevronDown, ChevronUp, Maximize2,
} from 'lucide-react';
import { useState } from 'react';
import api from '@/lib/api';
import type { ResourceItem } from './types';
import MarkdownRenderer from '@/components/shared/MarkdownRenderer';

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

/** 将 content_data 转为可读 Markdown */
function contentToMarkdown(data: any, type: string): string {
  if (!data) return '暂无内容';
  if (typeof data === 'string') return data;

  const parts: string[] = [];

  if (data.title) parts.push(`## ${data.title}`);
  if (data.summary) parts.push(data.summary);
  if (data.description) parts.push(data.description);
  if (data.content) parts.push(data.content);
  if (data.introduction) parts.push(data.introduction);

  // 文档 - 章节
  if (data.sections && Array.isArray(data.sections)) {
    for (const sec of data.sections) {
      if (sec.title) parts.push(`### ${sec.title}`);
      if (sec.content) parts.push(sec.content);
      if (sec.items && Array.isArray(sec.items)) {
        parts.push(sec.items.map((item: string) => `- ${item}`).join('\n'));
      }
    }
  }

  // 思维导图
  if (data.root) {
    parts.push(`### 中心主题: ${data.root}`);
    if (data.branches && Array.isArray(data.branches)) {
      for (const branch of data.branches) {
        parts.push(`#### ${branch.topic || branch.name || ''}`);
        if (branch.subtopics && Array.isArray(branch.subtopics)) {
          parts.push(branch.subtopics.map((s: any) => `- ${typeof s === 'string' ? s : s.name || s.topic || JSON.stringify(s)}`).join('\n'));
        }
      }
    }
  }

  // 题库
  if (data.questions && Array.isArray(data.questions)) {
    for (let i = 0; i < data.questions.length; i++) {
      const q = data.questions[i];
      parts.push(`**${i + 1}. ${q.question || q.title || ''}**`);
      if (q.options && Array.isArray(q.options)) {
        q.options.forEach((opt: string, j: number) => {
          parts.push(`${String.fromCharCode(65 + j)}. ${opt}`);
        });
      }
      if (q.answer) parts.push(`> 答案: ${q.answer}`);
      if (q.explanation) parts.push(`> 解析: ${q.explanation}`);
    }
  }

  // 代码
  if (data.code) {
    const lang = data.language || 'python';
    parts.push(`\`\`\`${lang}\n${data.code}\n\`\`\``);
  }

  // 视频脚本 (scenes)
  if (data.scenes && Array.isArray(data.scenes)) {
    if (data.duration_minutes) parts.push(`> 🎬 时长: ${data.duration_minutes} 分钟`);
    for (const scene of data.scenes) {
      const label = scene.scene_id ? `场景 ${scene.scene_id}` : (scene.title || scene.time || '');
      const time = scene.duration_seconds ? ` (${scene.duration_seconds}s)` : '';
      const desc = scene.visual_description || scene.description || scene.content || '';
      const narration = scene.narration || '';
      const effects = Array.isArray(scene.animation_effects) ? scene.animation_effects : [];
      parts.push(`**${label}${time}**`);
      if (desc) parts.push(desc);
      if (narration) parts.push(`> 🎙️ ${narration}`);
      if (effects.length) parts.push(`> ✨ 效果: ${effects.join(', ')}`);
    }
    if (Array.isArray(data.key_visuals) && data.key_visuals.length) {
      parts.push(`### 关键画面\n${data.key_visuals.map((v: string) => `- ${v}`).join('\n')}`);
    }
  }

  // 动画脚本 (frames)
  if (data.frames && Array.isArray(data.frames)) {
    if (data.duration_minutes) parts.push(`> ✨ 时长: ${data.duration_minutes} 分钟`);
    if (data.visual_style) parts.push(`> 🎨 风格: ${data.visual_style}`);
    for (const frame of data.frames) {
      const label = frame.frame_id ? `帧 ${frame.frame_id}` : '';
      const time = frame.timestamp || '';
      const desc = frame.description || '';
      const action = frame.action || '';
      const transition = frame.transition || '';
      parts.push(`**${label}${time ? ` [${time}]` : ''}**`);
      if (desc) parts.push(desc);
      if (action) parts.push(`> 🎬 动作: ${action}`);
      if (transition) parts.push(`> 🔄 转场: ${transition}`);
    }
    if (data.narration_script) {
      parts.push(`### 解说词\n${data.narration_script}`);
    }
  }

  // 通用 script 字段
  if (data.script && !data.scenes && !data.frames) {
    parts.push(data.script);
  }

  // 阅读材料
  if (data.materials && Array.isArray(data.materials)) {
    for (const mat of data.materials) {
      parts.push(`### ${mat.title || ''}`);
      if (mat.content) parts.push(mat.content);
    }
  }

  if (parts.length === 0) {
    return '```json\n' + JSON.stringify(data, null, 2) + '\n```';
  }

  return parts.join('\n\n');
}

const TYPE_ICONS: Record<string, { icon: typeof FileText; color: string }> = {
  document: { icon: FileText, color: 'text-cyan-400' },
  mindmap: { icon: GitBranch, color: 'text-emerald-400' },
  quiz: { icon: FileCode, color: 'text-amber-400' },
  video: { icon: Video, color: 'text-purple-400' },
  animation: { icon: Sparkles, color: 'text-pink-400' },
  code: { icon: Code, color: 'text-blue-400' },
  reading: { icon: BookOpen, color: 'text-orange-400' },
};

function ResourceCard({ resource, getTypeName }: { resource: ResourceItem; getTypeName: (t: string) => string }) {
  const [expanded, setExpanded] = useState(false);
  const typeInfo = TYPE_ICONS[resource.type] || { icon: FileText, color: 'text-white/60' };
  const Icon = typeInfo.icon;
  const markdown = contentToMarkdown(resource.content_data, resource.type);

  // 检测是否有实际生成的媒体内容
  const mediaUrl = resource.content_data?.media_url as string | undefined;
  const generationType = resource.content_data?.generation_type as string | undefined;
  const hasMedia = !!mediaUrl;
  const isVideo = generationType === 'video' || (mediaUrl && mediaUrl.endsWith('.mp4'));
  const isSvgAnim = generationType === 'svg_animation' || (mediaUrl && mediaUrl.endsWith('.html'));

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      {/* 头部 */}
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-3 min-w-0">
          <Icon className={`w-5 h-5 ${typeInfo.color} flex-shrink-0`} />
          <div className="min-w-0">
            <span className="font-semibold text-white block truncate">{resource.title}</span>
            <span className="text-xs text-white/40">
              {getTypeName(resource.type)}
              {hasMedia && isVideo && <span className="ml-2 text-purple-400">● AI生成视频</span>}
              {hasMedia && isSvgAnim && <span className="ml-2 text-pink-400">● AI生成动画</span>}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-2 rounded-lg hover:bg-white/[0.06] text-white/40 hover:text-white transition-colors"
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
          {hasMedia && (
            <button
              onClick={() => window.open(mediaUrl, '_blank')}
              className="p-2 rounded-lg hover:bg-white/[0.06] text-white/40 hover:text-white transition-colors"
              title="全屏打开"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          )}
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
                  alert(`导出失败: ${res.message || '未知错误'}`);
                }
              } catch (error: any) {
                alert(`导出失败: ${error.message || '网络错误'}`);
              }
            }}
            className="px-3 py-1.5 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-lg hover:opacity-90 transition text-sm flex items-center gap-1"
          >
            📥 导出
          </button>
          {resource.status === 'complete' && <CheckCircle className="w-4 h-4 text-emerald-400" />}
        </div>
      </div>
      {/* 内容 */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-white/[0.06] pt-4">
          {/* AI 生成的视频 */}
          {hasMedia && isVideo && (
            <video
              controls
              autoPlay
              src={mediaUrl}
              className="w-full rounded-xl border border-white/[0.06] shadow-lg mb-3"
              style={{ maxHeight: 450 }}
            />
          )}
          {/* AI 生成的 SVG 动画 (iframe) */}
          {hasMedia && isSvgAnim && (
            <iframe
              src={mediaUrl}
              className="w-full rounded-xl border border-white/[0.06] shadow-lg mb-3 bg-[#0a0f1e]"
              style={{ height: 400 }}
              title={resource.title}
            />
          )}
          {/* 文本内容（始终显示，或作为无媒体时的 fallback） */}
          {(!hasMedia || markdown.length > 50) && (
            <div className={hasMedia ? 'max-h-[200px] overflow-y-auto' : 'max-h-[500px] overflow-y-auto'}>
              <MarkdownRenderer content={markdown} />
            </div>
          )}
        </div>
      )}
    </div>
  );
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
            className="w-full px-3 py-2 bg-white/[0.04] border border-white/[0.08] text-white rounded-lg focus:border-cyan-400/30 focus:outline-none [&>option]:bg-[#0f1a30] [&>option]:text-white">
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
            <ResourceCard key={idx} resource={resource} getTypeName={getTypeName} />
          ))}
        </div>
      )}
    </div>
  );
}
