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
  resourceProgress: number;
  resourceCurrentType: string;
  resourceTotal: number;
  resourceDone: number;
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
      if (sec.title || sec.heading) parts.push(`### ${sec.title || sec.heading}`);
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
        q.options.forEach((opt: any, j: number) => {
          const optText = typeof opt === 'string' ? opt : (opt.text || opt.label || JSON.stringify(opt));
          const optLabel = opt.label || String.fromCharCode(65 + j);
          parts.push(`${optLabel}. ${optText}`);
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

  // 关键点
  if (data.key_points && Array.isArray(data.key_points) && data.key_points.length > 0) {
    parts.push(`### 关键点\n${data.key_points.map((p: string) => `- ${p}`).join('\n')}`);
  }

  // 参考资料
  if (data.references && Array.isArray(data.references) && data.references.length > 0) {
    parts.push(`### 参考资料\n${data.references.map((r: string) => `- ${r}`).join('\n')}`);
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
  document: { icon: FileText, color: 'text-purple-400' },
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
  const isVideo = generationType === 'video' || generationType === 'video_with_images' || (mediaUrl && mediaUrl.endsWith('.mp4'));
  const isSvgAnim = generationType === 'svg_animation' || (mediaUrl && mediaUrl.endsWith('.html'));
  const isMindmap = resource.type === 'mindmap' && (resource.content_data?.has_svg || mediaUrl?.includes('mindmap'));
  const isImage = resource.type === 'animation' || generationType === 'tti_image';

  return (
    <div className="border-b border-glass py-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <Icon className={`w-5 h-5 ${typeInfo.color} flex-shrink-0`} />
          <div className="min-w-0 flex-1">
            <span className="font-medium text-white text-base block truncate">{resource.title}</span>
            <span className="text-sm text-white/35">
              {getTypeName(resource.type)}
              {hasMedia && isVideo && <span className="ml-2 text-purple-400">● AI生成视频</span>}
              {hasMedia && isSvgAnim && <span className="ml-2 text-pink-400">● AI生成动画</span>}
              {hasMedia && isMindmap && <span className="ml-2 text-emerald-400">● SVG思维导图</span>}
              {hasMedia && isImage && <span className="ml-2 text-purple-400">● AI生成图片</span>}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1.5 rounded-md glass-button text-white/35 hover:text-white"
          >
            {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
          {hasMedia && (
            <button
              onClick={() => window.open(mediaUrl, '_blank')}
              className="p-1.5 rounded-md glass-button text-white/35 hover:text-white"
              title="全屏打开"
            >
              <Maximize2 className="w-3.5 h-3.5" />
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
            className="px-2.5 py-1 bg-emerald-500/15 text-emerald-400 rounded-md hover:bg-emerald-500/25 transition-colors text-xs flex items-center gap-1"
          >
            导出
          </button>
          {resource.status === 'complete' && <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />}
        </div>
      </div>
      {/* 内容 */}
      {expanded && (
        <div className="px-3 pb-3 border-t border-glass pt-3">
          {/* AI 生成的视频 */}
          {hasMedia && isVideo && (
            <video
              controls
              autoPlay
              src={mediaUrl}
              className="w-full rounded-xl glass shadow-lg mb-3"
              style={{ maxHeight: 450 }}
            />
          )}
          {/* AI 生成的 SVG 动画 (iframe) */}
          {hasMedia && isSvgAnim && (
            <iframe
              src={mediaUrl}
              className="w-full rounded-xl glass shadow-lg mb-3 bg-[#0a0f1e]"
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
  resourceProgress, resourceCurrentType, resourceTotal, resourceDone,
}: ResourcesModuleProps) {
  return (
    <div className="space-y-8">
      <h3 className="text-3xl font-bold text-white">多智能体资源生成</h3>

      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="block text-base font-medium text-white/60 mb-2">学科</label>
            <input type="text" value={subject} onChange={(e) => setSubject(e.target.value)}
              className="w-full px-4 py-3 glass-input text-white placeholder:text-white/20 rounded-lg text-base focus:outline-none" />
          </div>
          <div>
            <label className="block text-base font-medium text-white/60 mb-2">主题</label>
            <input type="text" value={topic} onChange={(e) => setTopic(e.target.value)}
              className="w-full px-4 py-3 glass-input text-white placeholder:text-white/20 rounded-lg text-base focus:outline-none" />
          </div>
        </div>

        <div>
          <label className="block text-base font-medium text-white/60 mb-3">资源类型</label>
          <div className="flex flex-wrap gap-3">
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
                className={`px-4 py-2.5 rounded-lg border transition-all text-base ${
                  selectedTypes.includes(type.id)
                    ? 'border-purple-400/30 bg-purple-400/10 text-purple-400'
                    : 'glass-button text-white/40 hover:text-white/60'
                }`}
              >
                {type.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-base font-medium text-white/60 mb-2">难度级别</label>
          <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}
            className="w-full px-4 py-3 glass-input text-white rounded-lg text-base focus:outline-none [&>option]:bg-[#0f0f0f] [&>option]:text-white">
            <option value="beginner">初级</option>
            <option value="intermediate">中级</option>
            <option value="advanced">高级</option>
          </select>
        </div>

        <button
          onClick={handleGenerateResources}
          disabled={resourceLoading || selectedTypes.length === 0}
          className="w-full py-3.5 bg-purple-500 text-white rounded-lg hover:bg-purple-400 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold text-base transition-colors"
        >
          {resourceLoading ? (
            <><Loader2 className="w-5 h-5 animate-spin" /> 生成中... {resourceDone}/{resourceTotal}
</>
          ) : (
            <><Brain className="w-5 h-5" /> 开始生成资源</>
          )}
        </button>

        {resourceLoading && (
          <div className="space-y-3 mt-4">
            <div className="flex items-center justify-between text-sm text-white/50">
              <span>{resourceCurrentType || '准备中...'}</span>
              <span>{resourceProgress}%</span>
            </div>
            <div className="w-full h-2 glass rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${resourceProgress}%` }}
              />
            </div>
            {resourceTotal > 0 && (
              <div className="flex gap-2 mt-2">
                {Array.from({ length: resourceTotal }).map((_, i) => (
                  <div key={i} className={`flex-1 h-1.5 rounded-full transition-colors duration-300 ${
                    i < resourceDone ? 'bg-emerald-500' : i === resourceDone ? 'bg-purple-500 animate-pulse' : 'glass'
                  }`} />
                ))}
              </div>
            )}
            <div className="grid grid-cols-2 gap-3 mt-4">
              {Array.from({ length: resourceTotal - resourceDone }).map((_, i) => (
                <div key={i} className="glass-card p-4 animate-pulse">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 glass rounded-lg" />
                    <div className="flex-1 space-y-2">
                      <div className="h-4 glass rounded w-3/4" />
                      <div className="h-3 glass rounded w-1/2" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {resources.length > 0 && (
        <div className="space-y-3">
          <h4 className="font-semibold text-white text-sm">生成的资源 ({resources.length})</h4>
          {resources.map((resource, idx) => (
            <ResourceCard key={idx} resource={resource} getTypeName={getTypeName} />
          ))}
        </div>
      )}
    </div>
  );
}
