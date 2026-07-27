'use client';

import { useState, useCallback, useEffect } from 'react';
import { Search, Play, Eye, ThumbsUp, Clock, ExternalLink, Loader2, Filter, ChevronLeft, ChevronRight, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '@/lib/api';

interface BilibiliVideo {
  bvid: string;
  aid: number;
  title: string;
  description: string;
  pic: string;
  author: string;
  mid: number;
  play: number;
  danmaku: number;
  duration: string;
  pubdate: number;
  tag: string;
  url: string;
}

interface SearchResult {
  videos: BilibiliVideo[];
  total: number;
  page: number;
  page_size: number;
  keyword: string;
}

const ORDER_OPTIONS = [
  { value: 'totalrank', label: '综合排序' },
  { value: 'click', label: '最多播放' },
  { value: 'pubdate', label: '最新发布' },
  { value: 'dm', label: '最多弹幕' },
];

const DURATION_OPTIONS = [
  { value: 0, label: '全部时长' },
  { value: 4, label: '5分钟以下' },
  { value: 3, label: '5~30分钟' },
  { value: 2, label: '30~60分钟' },
  { value: 1, label: '60分钟以上' },
];

function formatPlayCount(count: number): string {
  if (count >= 10000) {
    return (count / 10000).toFixed(1) + '万';
  }
  return String(count);
}

function formatDuration(duration: string): string {
  // duration 格式: "MM:SS" 或 "HH:MM:SS"
  return duration;
}

function timeAgo(timestamp: number): string {
  const now = Date.now() / 1000;
  const diff = now - timestamp;
  if (diff < 60) return '刚刚';
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前';
  if (diff < 86400) return Math.floor(diff / 3600) + '小时前';
  if (diff < 2592000) return Math.floor(diff / 86400) + '天前';
  if (diff < 31536000) return Math.floor(diff / 2592000) + '个月前';
  return Math.floor(diff / 31536000) + '年前';
}

/** 视频卡片组件 */
function VideoCard({ video, index, onVideoClick }: { video: BilibiliVideo; index: number; onVideoClick?: (video: BilibiliVideo) => void }) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  // 处理封面 URL：通过后端代理加载，避免跨域问题
  const getCoverUrl = (pic: string) => {
    if (!pic) return '';
    // 使用后端代理
    return `/api/agent/bilibili/cover?url=${encodeURIComponent(pic)}`;
  };

  const handleClick = () => {
    onVideoClick?.(video);
    window.open(video.url, '_blank');
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      className="group glass-card overflow-hidden hover:border-purple-400/30 transition-all duration-300 cursor-pointer"
      onClick={handleClick}
    >
      {/* 封面区域 */}
      <div className="relative aspect-video overflow-hidden bg-gradient-to-br from-purple-500/10 to-pink-500/10">
        {!imageError && video.pic ? (
          <img
            src={getCoverUrl(video.pic)}
            alt={video.title}
            className={`w-full h-full object-cover transition-all duration-500 group-hover:scale-105 ${
              imageLoaded ? 'opacity-100' : 'opacity-0'
            }`}
            onLoad={() => setImageLoaded(true)}
            onError={() => setImageError(true)}
            loading="lazy"
            referrerPolicy="no-referrer"
            crossOrigin="anonymous"
          />
        ) : null}

        {/* 加载占位 / 错误占位 */}
        {(!imageLoaded || imageError) && (
          <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-purple-500/20 to-pink-500/20">
            <div className="text-center space-y-2">
              <Play className="w-10 h-10 text-white/30 mx-auto" />
              <p className="text-xs text-white/20 px-4 line-clamp-1">{video.author || 'Bilibili'}</p>
            </div>
          </div>
        )}

        {/* 播放按钮覆盖层 */}
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-all duration-300 flex items-center justify-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            whileHover={{ opacity: 1, scale: 1 }}
            className="opacity-0 group-hover:opacity-100 transition-opacity duration-300"
          >
            <div className="w-12 h-12 rounded-full bg-purple-500/80 flex items-center justify-center backdrop-blur-sm">
              <Play className="w-6 h-6 text-white ml-0.5" />
            </div>
          </motion.div>
        </div>

        {/* 时长标签 */}
        <div className="absolute bottom-2 right-2 px-1.5 py-0.5 rounded bg-black/70 text-white text-xs font-medium backdrop-blur-sm">
          {formatDuration(video.duration)}
        </div>
      </div>

      {/* 信息区域 */}
      <div className="p-3 space-y-2">
        {/* 标题 */}
        <h4 className="text-sm font-medium text-white/90 line-clamp-2 leading-relaxed group-hover:text-purple-300 transition-colors">
          {video.title}
        </h4>

        {/* 作者 */}
        <p className="text-xs text-white/40 truncate">{video.author}</p>

        {/* 统计信息 */}
        <div className="flex items-center gap-3 text-xs text-white/30">
          <span className="flex items-center gap-1">
            <Eye className="w-3 h-3" />
            {formatPlayCount(video.play)}
          </span>
          <span className="flex items-center gap-1">
            <ThumbsUp className="w-3 h-3" />
            {formatPlayCount(video.danmaku)}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {timeAgo(video.pubdate)}
          </span>
        </div>
      </div>
    </motion.div>
  );
}

/** 搜索结果统计 */
function ResultStats({ total, keyword }: { total: number; keyword: string }) {
  return (
    <div className="flex items-center justify-between">
      <p className="text-sm text-white/50">
        搜索 &quot;{keyword}&quot; 找到 <span className="text-purple-400 font-medium">{formatPlayCount(total)}</span> 个视频
      </p>
    </div>
  );
}

/** 分页组件 */
function Pagination({
  currentPage,
  totalPages,
  onPageChange,
}: {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) {
  if (totalPages <= 1) return null;

  const pages: (number | string)[] = [];
  const maxVisible = 5;

  if (totalPages <= maxVisible) {
    for (let i = 1; i <= totalPages; i++) pages.push(i);
  } else {
    pages.push(1);
    if (currentPage > 3) pages.push('...');
    const start = Math.max(2, currentPage - 1);
    const end = Math.min(totalPages - 1, currentPage + 1);
    for (let i = start; i <= end; i++) pages.push(i);
    if (currentPage < totalPages - 2) pages.push('...');
    pages.push(totalPages);
  }

  return (
    <div className="flex items-center justify-center gap-2 mt-6">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage <= 1}
        className="p-2 rounded-lg glass-button text-white/40 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
      >
        <ChevronLeft className="w-4 h-4" />
      </button>

      {pages.map((page, idx) =>
        typeof page === 'string' ? (
          <span key={`ellipsis-${idx}`} className="px-2 text-white/30">...</span>
        ) : (
          <button
            key={page}
            onClick={() => onPageChange(page)}
            className={`w-8 h-8 rounded-lg text-sm font-medium transition-colors ${
              page === currentPage
                ? 'bg-purple-500 text-white'
                : 'glass-button text-white/40 hover:text-white'
            }`}
          >
            {page}
          </button>
        )
      )}

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage >= totalPages}
        className="p-2 rounded-lg glass-button text-white/40 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
      >
        <ChevronRight className="w-4 h-4" />
      </button>
    </div>
  );
}

// 视频分类
const VIDEO_CATEGORIES = [
  { id: 'all', label: '全部' },
  { id: '深度学习', label: '深度学习' },
  { id: 'Python', label: 'Python' },
  { id: 'RAG与Agent', label: 'RAG与Agent' },
  { id: '计算机视觉', label: '计算机视觉' },
  { id: '前端开发', label: '前端开发' },
  { id: '数据分析', label: '数据分析' },
];

export default function VideoResourceModule() {
  const [keyword, setKeyword] = useState('');
  const [searchKeyword, setSearchKeyword] = useState('');
  const [loading, setLoading] = useState(false);
  const [videos, setVideos] = useState<BilibiliVideo[]>([]);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [order, setOrder] = useState('totalrank');
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState('');
  const [hasSearched, setHasSearched] = useState(false);
  const [activeCategory, setActiveCategory] = useState('all');
  const [recommendLoading, setRecommendLoading] = useState(true);

  const pageSize = 12;
  const totalPages = Math.ceil(total / pageSize);

  // 记录视频浏览活动
  const logVideoView = (video: BilibiliVideo) => {
    try {
      const username = localStorage.getItem('username') || 'guest';
      const logsKey = `activity_logs_${username}`;
      const logs = JSON.parse(localStorage.getItem(logsKey) || '[]');
      logs.unshift({
        id: `video-${Date.now()}`,
        type: 'video_view',
        action: `观看了视频《${video.title}》`,
        detail: video.tag || video.author,
        category: activeCategory !== 'all' ? activeCategory : (video.tag || '其他'),
        time: new Date().toISOString(),
      });
      localStorage.setItem(logsKey, JSON.stringify(logs.slice(0, 100)));
      window.dispatchEvent(new Event('activity-updated'));
    } catch {}
  };

  // 加载推荐视频
  useEffect(() => {
    loadRecommendVideos('all');
  }, []);

  const loadRecommendVideos = async (category: string) => {
    setRecommendLoading(true);
    setActiveCategory(category);
    try {
      const res: any = await api.getBilibiliRecommend(category, 8);
      if (res.success && res.data) {
        setVideos(res.data.videos || []);
      }
    } catch (err) {
      console.error('获取推荐视频失败:', err);
    } finally {
      setRecommendLoading(false);
    }
  };

  const handleSearch = useCallback(
    async (page = 1) => {
      if (!keyword.trim()) return;

      setLoading(true);
      setError('');
      setSearchKeyword(keyword.trim());
      setCurrentPage(page);

      try {
        const res: any = await api.searchBilibiliVideos(keyword.trim(), page, pageSize, order, duration);

        if (res.success && res.data) {
          const videoList = res.data.videos || [];
          setVideos(videoList);
          setTotal(res.data.total || 0);
          setHasSearched(true);
          if (videoList.length === 0) {
            setError('未找到相关视频，请尝试其他关键词');
          }
        } else {
          setError(res.message || '搜索失败');
          setVideos([]);
          setHasSearched(true);
        }
      } catch (err: any) {
        setError(err.message || '网络错误');
        setVideos([]);
        setHasSearched(true);
      } finally {
        setLoading(false);
      }
    },
    [keyword, order, duration]
  );

  // 返回推荐
  const handleBackToRecommend = () => {
    setHasSearched(false);
    setKeyword('');
    setError('');
    loadRecommendVideos('all');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch(1);
    }
  };

  const handlePageChange = (page: number) => {
    handleSearch(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="space-y-6">
      {/* 标题 */}
      <div>
        <h3 className="text-3xl font-bold text-white">视频资源</h3>
        <p className="text-sm text-white/40 mt-1">搜索 Bilibili 学习视频资源</p>
      </div>

      {/* 搜索区域 */}
      <div className="space-y-4">
        {/* 搜索框 */}
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30" />
            <input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入关键词搜索 Bilibili 视频..."
              className="w-full pl-12 pr-4 py-3.5 glass-input text-white placeholder:text-white/20 rounded-lg text-base focus:outline-none focus:border-purple-400/50"
            />
          </div>
          <button
            onClick={() => handleSearch(1)}
            disabled={loading || !keyword.trim()}
            className="px-6 py-3.5 bg-purple-500 text-white rounded-lg hover:bg-purple-400 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-semibold text-base transition-colors"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Search className="w-5 h-5" />
            )}
            搜索
          </button>
        </div>

        {/* 筛选器 */}
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-white/30" />
            <span className="text-sm text-white/40">排序:</span>
            <div className="flex gap-2">
              {ORDER_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => {
                    setOrder(opt.value);
                    if (hasSearched) handleSearch(1);
                  }}
                  className={`px-3 py-1.5 rounded-lg text-xs transition-colors ${
                    order === opt.value
                      ? 'bg-purple-500/20 text-purple-400 border border-purple-400/30'
                      : 'glass-button text-white/40 hover:text-white/60'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-white/30" />
            <span className="text-sm text-white/40">时长:</span>
            <div className="flex gap-2">
              {DURATION_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => {
                    setDuration(opt.value);
                    if (hasSearched) handleSearch(1);
                  }}
                  className={`px-3 py-1.5 rounded-lg text-xs transition-colors ${
                    duration === opt.value
                      ? 'bg-purple-500/20 text-purple-400 border border-purple-400/30'
                      : 'glass-button text-white/40 hover:text-white/60'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-lg bg-red-500/10 border border-red-400/20 text-red-400 text-sm"
        >
          {error}
        </motion.div>
      )}

      {/* 加载状态 */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-16 space-y-4">
          <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
          <p className="text-sm text-white/40">正在搜索视频资源...</p>
        </div>
      )}

      {/* 搜索结果 */}
      {!loading && hasSearched && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <ResultStats total={total} keyword={searchKeyword} />
            <button
              onClick={handleBackToRecommend}
              className="px-4 py-2 rounded-lg glass-button text-sm text-white/50 hover:text-white transition-colors flex items-center gap-2"
            >
              <ChevronLeft className="w-4 h-4" />
              返回推荐
            </button>
          </div>

          {videos.length > 0 ? (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {videos.map((video, idx) => (
                  <VideoCard key={video.bvid} video={video} index={idx} onVideoClick={logVideoView} />
                ))}
              </div>

              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={handlePageChange}
              />
            </>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 space-y-4">
              <Search className="w-12 h-12 text-white/15" />
              <p className="text-sm text-white/40">{error || '未找到相关视频'}</p>
              <p className="text-xs text-white/25">尝试更换关键词或返回推荐</p>
              <button
                onClick={handleBackToRecommend}
                className="px-4 py-2 rounded-lg bg-purple-500/20 text-purple-400 hover:bg-purple-500/30 transition-colors text-sm"
              >
                查看推荐视频
              </button>
            </div>
          )}
        </div>
      )}

      {/* 未搜索时显示默认推荐视频 */}
      {!loading && !hasSearched && (
        <div className="space-y-6">
          {/* 分类标签 */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm text-white/50 mr-2">分类:</span>
            {VIDEO_CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                onClick={() => loadRecommendVideos(cat.id)}
                className={`px-4 py-2 rounded-lg text-sm transition-colors ${
                  activeCategory === cat.id
                    ? 'bg-purple-500/20 text-purple-400 border border-purple-400/30'
                    : 'glass-button text-white/40 hover:text-white/60'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>

          {/* 热门搜索标签 */}
          <div className="flex items-center gap-3">
            <span className="text-sm text-white/50">热门搜索:</span>
            <div className="flex flex-wrap gap-2">
              {['Python教程', '机器学习', '深度学习', '数据分析', '前端开发', 'RAG'].map((tag) => (
                <button
                  key={tag}
                  onClick={() => {
                    setKeyword(tag);
                    setTimeout(() => handleSearch(1), 100);
                  }}
                  className="px-3 py-1.5 rounded-full glass-button text-xs text-white/40 hover:text-purple-400 hover:border-purple-400/30 transition-colors"
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>

          {/* 推荐视频列表 */}
          <div>
            <h4 className="text-sm font-medium text-white/60 mb-4 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" />
              精选学习资源
            </h4>

            {recommendLoading ? (
              <div className="flex flex-col items-center justify-center py-16 space-y-4">
                <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
                <p className="text-sm text-white/40">加载推荐视频...</p>
              </div>
            ) : videos.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {videos.map((video, idx) => (
                  <VideoCard key={video.bvid} video={video} index={idx} onVideoClick={logVideoView} />
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 space-y-4">
                <Play className="w-12 h-12 text-white/15" />
                <p className="text-sm text-white/40">暂无推荐视频</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
