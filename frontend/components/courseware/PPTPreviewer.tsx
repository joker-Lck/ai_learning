'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '@/lib/api';
import {
  ChevronLeft, ChevronRight, Download, FileText,
  Maximize2, Minimize2, Palette, RotateCcw
} from 'lucide-react';

interface SlideData {
  title: string;
  subtitle?: string;
  content: string[];
  layout?: string;
  background?: any;
  decorations?: any[];
}

interface Theme {
  primary_color?: string;
  secondary_color?: string;
  accent_color?: string;
  bg_color?: string;
  text_color?: string;
  template_style?: string;
}

interface Props {
  slides: SlideData[];
  theme: Theme;
  topic: string;
  subject: string;
  coursewareId: number | null;
}

export default function PPTPreviewer({ slides, theme, topic, subject, coursewareId }: Props) {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const primary = theme?.primary_color || '#0a192f';
  const secondary = theme?.secondary_color || '#64ffda';
  const accent = theme?.accent_color || '#00d4ff';
  const textColor = theme?.text_color || '#333333';

  const goNext = () => setCurrentSlide(Math.min(currentSlide + 1, slides.length - 1));
  const goPrev = () => setCurrentSlide(Math.max(currentSlide - 1, 0));

  // 键盘导航
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowRight' || e.key === ' ') goNext();
    if (e.key === 'ArrowLeft') goPrev();
  };

  return (
    <div
      className="max-w-5xl mx-auto"
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      {/* 工具栏 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-bold text-gray-800">📊 {topic}</h2>
          <span className="px-2 py-1 bg-purple-100 text-purple-600 rounded-lg text-xs font-medium">
            {subject}
          </span>
          <span className="text-sm text-gray-500">
            {slides.length} 页
          </span>
        </div>

        <div className="flex items-center gap-2">
          {coursewareId && (
            <>
              <a
                href={api.getCoursewareDownloadUrl(coursewareId, 'pptx')}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white text-sm font-medium hover:shadow-lg transition-all"
              >
                <Download className="w-4 h-4" />
                下载 PPTX
              </a>
              <a
                href={api.getCoursewareDownloadUrl(coursewareId, 'docx')}
                className="flex items-center gap-2 px-4 py-2 rounded-xl border-2 border-gray-200 text-gray-600 text-sm font-medium hover:bg-gray-50 transition-all"
              >
                <FileText className="w-4 h-4" />
                下载教案
              </a>
            </>
          )}
        </div>
      </div>

      {/* PPT 预览区域 */}
      <div className={`relative ${isFullscreen ? 'fixed inset-0 z-50 bg-black p-8 flex items-center justify-center' : ''}`}>
        <div
          className={`relative bg-gray-200 rounded-2xl p-6 shadow-xl ${isFullscreen ? 'w-full max-w-6xl' : ''}`}
        >
          {/* 16:9 幻灯片 */}
          <AnimatePresence mode="wait">
            <motion.div
              key={currentSlide}
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -30 }}
              transition={{ duration: 0.3 }}
              className="relative bg-white rounded-lg overflow-hidden shadow-2xl"
              style={{ aspectRatio: '16/9' }}
            >
              {(() => {
                const slide = slides[currentSlide];
                const isFirst = currentSlide === 0;

                if (isFirst) {
                  // 封面页
                  return (
                    <div
                      className="w-full h-full flex flex-col items-center justify-center relative"
                      style={{ background: `linear-gradient(135deg, ${primary} 0%, ${primary}dd 100%)` }}
                    >
                      {/* 装饰元素 */}
                      <div
                        className="absolute top-0 right-0 w-1/3 h-full opacity-10"
                        style={{ background: `linear-gradient(90deg, transparent, ${secondary})` }}
                      />
                      <div
                        className="absolute bottom-0 left-0 right-0 h-1.5"
                        style={{ background: secondary }}
                      />

                      {/* 装饰圆 */}
                      <motion.div
                        className="absolute top-8 right-12 w-24 h-24 rounded-full opacity-20"
                        style={{ background: secondary }}
                        animate={{ scale: [1, 1.1, 1] }}
                        transition={{ duration: 3, repeat: Infinity }}
                      />
                      <motion.div
                        className="absolute bottom-16 right-24 w-16 h-16 rounded-full opacity-15"
                        style={{ background: accent }}
                        animate={{ scale: [1, 1.15, 1] }}
                        transition={{ duration: 4, repeat: Infinity }}
                      />

                      <div className="relative z-10 text-center px-8">
                        <motion.h1
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          className="text-4xl font-bold text-white mb-4"
                          style={{ textShadow: '2px 2px 4px rgba(0,0,0,0.3)' }}
                        >
                          {slide.title}
                        </motion.h1>
                        {slide.subtitle && (
                          <motion.p
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.2 }}
                            className="text-lg text-white/80"
                          >
                            {slide.subtitle}
                          </motion.p>
                        )}
                      </div>
                    </div>
                  );
                }

                // 内容页
                return (
                  <div className="w-full h-full flex flex-col">
                    {/* 标题栏 */}
                    <div
                      className="px-8 py-5 flex items-center relative"
                      style={{ background: primary, minHeight: '70px' }}
                    >
                      <div
                        className="absolute bottom-0 left-0 right-0 h-1"
                        style={{ background: accent }}
                      />
                      <h2 className="text-xl font-bold text-white">{slide.title}</h2>
                    </div>

                    {/* 内容区 */}
                    <div className="flex-1 px-8 py-6 overflow-y-auto">
                      {slide.subtitle && (
                        <p className="text-sm text-gray-500 mb-4">{slide.subtitle}</p>
                      )}
                      <ul className="space-y-3">
                        {slide.content.filter(c => c?.trim()).map((point, j) => (
                          <motion.li
                            key={j}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.1 * j }}
                            className="flex items-start gap-3"
                          >
                            <span
                              className="w-2 h-2 rounded-full mt-2 flex-shrink-0"
                              style={{ background: accent }}
                            />
                            <span className="text-base leading-relaxed" style={{ color: textColor }}>
                              {point}
                            </span>
                          </motion.li>
                        ))}
                      </ul>
                    </div>

                    {/* 页脚 */}
                    <div className="px-8 py-3 bg-gray-50 border-t flex justify-between items-center">
                      <span className="text-xs text-gray-400">AI 课件生成系统</span>
                      <span className="text-xs text-gray-400">
                        第 {currentSlide + 1} / {slides.length} 页
                      </span>
                    </div>
                  </div>
                );
              })()}
            </motion.div>
          </AnimatePresence>

          {/* 导航按钮 */}
          <button
            onClick={goPrev}
            disabled={currentSlide === 0}
            className="absolute left-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/90 shadow-lg flex items-center justify-center text-gray-600 hover:bg-white transition-all disabled:opacity-30"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <button
            onClick={goNext}
            disabled={currentSlide === slides.length - 1}
            className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/90 shadow-lg flex items-center justify-center text-gray-600 hover:bg-white transition-all disabled:opacity-30"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* 幻灯片缩略图 */}
      <div className="mt-4 flex gap-2 overflow-x-auto pb-2">
        {slides.map((slide, i) => (
          <button
            key={i}
            onClick={() => setCurrentSlide(i)}
            className={`flex-shrink-0 w-28 h-16 rounded-lg border-2 transition-all overflow-hidden ${
              i === currentSlide
                ? 'border-purple-500 shadow-md shadow-purple-500/30'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div
              className="w-full h-full flex items-center justify-center text-xs font-medium text-white p-1"
              style={{ background: i === 0 ? primary : primary + 'cc' }}
            >
              <span className="truncate text-center">{slide.title}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
