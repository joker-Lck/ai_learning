/**
 * RAG 知识库管理 — 上传学习资料、查看已有文档
 */
'use client';
import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Database, Upload, FileText, Loader2, CheckCircle2,
  AlertCircle, BookOpen, Trash2, RefreshCw,
} from 'lucide-react';
import { api } from '@/lib/api';

interface RagDoc {
  id: number;
  title: string;
  subject: string;
  file_type: string;
  upload_time: string;
}

interface UploadResult {
  filename: string;
  success: boolean;
  doc_id?: number;
  knowledge_points?: number;
  summary?: string;
  message?: string;
}

const fadeUp = {
  hidden: { opacity: 0, y: 12 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.05 } }),
};

export default function RagKnowledgeModule() {
  const [files, setFiles] = useState<File[]>([]);
  const [subject, setSubject] = useState('');
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<UploadResult[] | null>(null);
  const [docs, setDocs] = useState<RagDoc[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  // 加载已有文档
  const loadDocs = async () => {
    setLoadingDocs(true);
    try {
      const res = await api.getRagDocuments();
      if (res.success) setDocs(res.data?.documents || []);
    } catch { /* ignore */ }
    setLoadingDocs(false);
  };

  useEffect(() => { loadDocs(); }, []);

  const addFiles = (fileList: FileList | null) => {
    if (!fileList) return;
    const newFiles = Array.from(fileList).filter((f) => {
      const ext = f.name.split('.').pop()?.toLowerCase() || '';
      return ['txt', 'md', 'pdf', 'doc', 'docx', 'ppt', 'pptx'].includes(ext);
    });
    setFiles((prev) => [...prev, ...newFiles]);
  };

  const removeFile = (idx: number) => setFiles((prev) => prev.filter((_, i) => i !== idx));

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    setResults(null);
    try {
      const res = await api.uploadToRag(files, subject);
      if (res.success) {
        setResults(res.data?.results || []);
        setFiles([]);
        loadDocs();
      } else {
        setResults([{ filename: '', success: false, message: res.message }]);
      }
    } catch (e: any) {
      setResults([{ filename: '', success: false, message: e.message }]);
    }
    setUploading(false);
  };

  return (
    <div className="space-y-6">
      {/* 上传区域 */}
      <div className="rounded-2xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-xl p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/20 flex items-center justify-center">
            <Database className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <h3 className="text-white font-bold text-lg">上传到知识库</h3>
            <p className="text-white/40 text-sm">上传学习资料，系统自动解析并存入 RAG 知识库</p>
          </div>
        </div>

        {/* 学科标签 */}
        <div className="mb-4">
          <label className="text-white/50 text-sm mb-2 block">学科标签（可选）</label>
          <input
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="如：机器学习、数据结构、高等数学..."
            className="w-full max-w-sm bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-2.5 text-white text-sm placeholder:text-white/20 focus:outline-none focus:border-cyan-400/40"
          />
        </div>

        {/* 拖拽上传 */}
        <div
          onDrop={(e) => { e.preventDefault(); setDragOver(false); addFiles(e.dataTransfer.files); }}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onClick={() => fileRef.current?.click()}
          className={`
            border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all
            ${dragOver
              ? 'border-emerald-400/50 bg-emerald-400/5'
              : 'border-white/[0.08] bg-white/[0.02] hover:border-emerald-400/30'}
          `}
        >
          <input
            ref={fileRef}
            type="file"
            multiple
            accept=".txt,.md,.pdf,.doc,.docx,.ppt,.pptx"
            className="hidden"
            onChange={(e) => addFiles(e.target.files)}
          />
          <Upload className={`w-10 h-10 mx-auto mb-3 ${dragOver ? 'text-emerald-400' : 'text-white/30'}`} />
          <p className="text-white/60 text-sm">
            拖拽文件到这里，或 <span className="text-emerald-400 underline">点击选择</span>
          </p>
          <p className="text-white/30 text-xs mt-2">支持 TXT / MD / PDF / DOC / PPT，单文件最大 20MB</p>
        </div>

        {/* 文件列表 */}
        <AnimatePresence>
          {files.length > 0 && (
            <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} className="mt-4 space-y-2">
              {files.map((f, i) => (
                <motion.div key={`${f.name}-${i}`} variants={fadeUp} initial="hidden" animate="visible" custom={i}
                  className="flex items-center gap-3 bg-white/[0.04] rounded-xl px-4 py-2.5"
                >
                  <FileText className="w-4 h-4 text-emerald-400/70 flex-shrink-0" />
                  <span className="text-white/80 text-sm truncate flex-1">{f.name}</span>
                  <span className="text-white/30 text-xs">{(f.size / 1024).toFixed(0)}KB</span>
                  <button onClick={() => removeFile(i)} className="text-white/30 hover:text-red-400 transition-colors">
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </motion.div>
              ))}
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="w-full mt-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-bold py-3 rounded-xl hover:brightness-110 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
              >
                {uploading ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> AI 解析中...</>
                ) : (
                  <><Upload className="w-4 h-4" /> 上传并解析（{files.length} 个文件）</>
                )}
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* 上传结果 */}
        <AnimatePresence>
          {results && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mt-4 space-y-2">
              {results.map((r, i) => (
                <div key={i} className={`flex items-start gap-3 rounded-xl px-4 py-3 ${
                  r.success ? 'bg-emerald-500/10 border border-emerald-500/20' : 'bg-red-500/10 border border-red-500/20'
                }`}>
                  {r.success ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-white/80 text-sm font-medium">{r.filename || '上传'}</p>
                    {r.success ? (
                      <p className="text-emerald-300/70 text-xs mt-1">
                        doc_id={r.doc_id} · {r.knowledge_points} 个知识点
                        {r.summary && <><br />摘要: {r.summary.slice(0, 80)}...</>}
                      </p>
                    ) : (
                      <p className="text-red-300/70 text-xs mt-1">{r.message}</p>
                    )}
                  </div>
                </div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 已有文档列表 */}
      <div className="rounded-2xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-cyan-400" />
            <h3 className="text-white font-bold">知识库文档</h3>
            <span className="text-white/30 text-xs">({docs.length})</span>
          </div>
          <button onClick={loadDocs} disabled={loadingDocs} className="text-white/40 hover:text-cyan-400 transition-colors">
            <RefreshCw className={`w-4 h-4 ${loadingDocs ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {docs.length === 0 ? (
          <p className="text-white/30 text-sm text-center py-6">暂无文档，上传学习资料开始构建知识库</p>
        ) : (
          <div className="space-y-2 max-h-80 overflow-y-auto scrollbar-thin">
            {docs.map((doc, i) => (
              <motion.div key={doc.id} variants={fadeUp} initial="hidden" animate="visible" custom={i}
                className="flex items-center gap-3 bg-white/[0.03] rounded-xl px-4 py-3 hover:bg-white/[0.05] transition-colors"
              >
                <FileText className="w-4 h-4 text-cyan-400/60 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-white/80 text-sm truncate">{doc.title}</p>
                  <p className="text-white/30 text-xs">{doc.subject} · {doc.file_type?.toUpperCase()}</p>
                </div>
                <span className="text-white/20 text-xs flex-shrink-0">{doc.upload_time?.slice(0, 10)}</span>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
