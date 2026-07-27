'use client';

import { useState, useCallback, useEffect } from 'react';
import { Search, BookOpen, ExternalLink, Loader2, Filter, ChevronLeft, ChevronRight, Tag, Library, Globe } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '@/lib/api';

interface Book {
  title: string;
  author: string;
  isbn: string;
  cover: string;
  description: string;
  publisher: string;
  year: string;
  nlc_url: string;
  jiumo_url: string;
  tags: string[];
}

// 图书分类
const BOOK_CATEGORIES = [
  { id: 'all', label: '全部' },
  { id: '人工智能', label: '人工智能' },
  { id: '自然语言处理', label: 'NLP' },
  { id: '大模型与RAG', label: '大模型' },
  { id: '计算机科学', label: '计算机' },
  { id: '数据分析', label: '数据分析' },
  { id: '前端开发', label: '前端' },
];

/** 图书卡片组件 */
function BookCard({ book, index, onBookClick }: { book: Book; index: number; onBookClick?: (book: Book, source: 'nlc' | 'jiumo') => void }) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  // 处理封面 URL（优先使用代理，失败后直接加载）
  const getCoverUrl = (cover: string) => {
    if (!cover) return '';
    // 豆瓣图片可以直接加载，无需代理
    if (cover.includes('doubanio.com')) {
      return cover;
    }
    return `/api/agent/books/cover?url=${encodeURIComponent(cover)}`;
  };

  const handleLinkClick = (e: React.MouseEvent, source: 'nlc' | 'jiumo') => {
    e.stopPropagation();
    onBookClick?.(book, source);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      className="group glass-card overflow-hidden hover:border-purple-400/30 transition-all duration-300"
    >
      <div className="flex gap-4 p-4">
        {/* 封面 */}
        <div className="relative w-28 h-40 flex-shrink-0 rounded-lg overflow-hidden bg-gradient-to-br from-purple-500/10 to-pink-500/10">
          {!imageError && book.cover ? (
            <img
              src={getCoverUrl(book.cover)}
              alt={book.title}
              className={`w-full h-full object-cover transition-all duration-500 group-hover:scale-105 ${
                imageLoaded ? 'opacity-100' : 'opacity-0'
              }`}
              onLoad={() => setImageLoaded(true)}
              onError={() => setImageError(true)}
              loading="lazy"
              crossOrigin="anonymous"
            />
          ) : null}

          {/* 加载/错误占位 */}
          {(!imageLoaded || imageError) && (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-br from-purple-500/20 to-pink-500/20">
              <BookOpen className="w-8 h-8 text-white/30 mb-1" />
              <p className="text-[10px] text-white/20 px-2 text-center line-clamp-1">{book.publisher}</p>
            </div>
          )}
        </div>

        {/* 信息区域 */}
        <div className="flex-1 min-w-0 flex flex-col justify-between">
          <div>
            {/* 标题 */}
            <h4 className="text-sm font-semibold text-white/90 line-clamp-2 leading-relaxed group-hover:text-purple-300 transition-colors">
              {book.title}
            </h4>

            {/* 作者 */}
            <p className="text-xs text-white/50 mt-1 truncate">{book.author}</p>

            {/* 出版信息 */}
            <p className="text-xs text-white/30 mt-1">
              {book.publisher} · {book.year}
            </p>

            {/* 简介 */}
            <p className="text-xs text-white/40 mt-2 line-clamp-2 leading-relaxed">
              {book.description}
            </p>

            {/* 标签 */}
            <div className="flex flex-wrap gap-1.5 mt-2">
              {book.tags.slice(0, 3).map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400/70 text-[10px]"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="flex items-center gap-2 mt-3">
            <a
              href={book.nlc_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => handleLinkClick(e, 'nlc')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-500/15 text-blue-400 hover:bg-blue-500/25 transition-colors text-xs"
            >
              <Library className="w-3 h-3" />
              国家图书馆
            </a>
            <a
              href={book.jiumo_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => handleLinkClick(e, 'jiumo')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/15 text-emerald-400 hover:bg-emerald-500/25 transition-colors text-xs"
            >
              <Globe className="w-3 h-3" />
              鸠摩搜书
            </a>
          </div>
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
        搜索 &quot;{keyword}&quot; 找到 <span className="text-purple-400 font-medium">{total}</span> 本图书
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

export default function BookResourceModule() {
  const [keyword, setKeyword] = useState('');
  const [searchKeyword, setSearchKeyword] = useState('');
  const [loading, setLoading] = useState(false);
  const [books, setBooks] = useState<Book[]>([]);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [error, setError] = useState('');
  const [hasSearched, setHasSearched] = useState(false);
  const [activeCategory, setActiveCategory] = useState('all');
  const [recommendLoading, setRecommendLoading] = useState(true);

  const pageSize = 12;
  const totalPages = Math.ceil(total / pageSize);

  // 记录图书浏览活动
  const logBookView = (book: Book, source: 'nlc' | 'jiumo') => {
    try {
      const username = localStorage.getItem('username') || 'guest';
      const logsKey = `activity_logs_${username}`;
      const logs = JSON.parse(localStorage.getItem(logsKey) || '[]');
      const sourceLabel = source === 'nlc' ? '国家图书馆' : '鸠摩搜书';
      logs.unshift({
        id: `book-${Date.now()}`,
        type: 'book_view',
        action: `查阅了图书《${book.title}》(${sourceLabel})`,
        detail: book.tags?.join(', ') || book.author,
        category: activeCategory !== 'all' ? activeCategory : (book.tags?.[0] || '其他'),
        time: new Date().toISOString(),
      });
      localStorage.setItem(logsKey, JSON.stringify(logs.slice(0, 100)));
      window.dispatchEvent(new Event('activity-updated'));
    } catch {}
  };

  // 加载推荐图书
  useEffect(() => {
    loadRecommendBooks('all');
  }, []);

  const loadRecommendBooks = async (category: string) => {
    setRecommendLoading(true);
    setActiveCategory(category);
    try {
      const res: any = await api.getBookRecommend(category, 8);
      if (res.success && res.data) {
        setBooks(res.data.books || []);
      }
    } catch (err) {
      console.error('获取推荐图书失败:', err);
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
        const res: any = await api.searchBooks(keyword.trim(), page, pageSize);

        if (res.success && res.data) {
          setBooks(res.data.books || []);
          setTotal(res.data.total || 0);
          setHasSearched(true);
        } else {
          setError(res.message || '搜索失败');
          setBooks([]);
        }
      } catch (err: any) {
        setError(err.message || '网络错误');
        setBooks([]);
      } finally {
        setLoading(false);
      }
    },
    [keyword]
  );

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
        <h3 className="text-3xl font-bold text-white">图书资源</h3>
        <p className="text-sm text-white/40 mt-1">搜索国家数字图书馆与鸠摩搜书图书资源</p>
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
              placeholder="输入关键词搜索图书..."
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

        {/* 快捷链接 */}
        <div className="flex items-center gap-4">
          <span className="text-sm text-white/40">外部资源:</span>
          <a
            href="https://read.nlc.cn"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 transition-colors text-sm"
          >
            <Library className="w-4 h-4" />
            国家数字图书馆
          </a>
          <a
            href="https://www.jiumodiary.com"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 transition-colors text-sm"
          >
            <Globe className="w-4 h-4" />
            鸠摩搜书
          </a>
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
          <p className="text-sm text-white/40">正在搜索图书资源...</p>
        </div>
      )}

      {/* 搜索结果 */}
      {!loading && hasSearched && (
        <div className="space-y-6">
          <ResultStats total={total} keyword={searchKeyword} />

          {books.length > 0 ? (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {books.map((book, idx) => (
                  <BookCard key={book.isbn} book={book} index={idx} onBookClick={logBookView} />
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
              <BookOpen className="w-12 h-12 text-white/15" />
              <p className="text-sm text-white/40">未找到相关图书</p>
              <p className="text-xs text-white/25">尝试更换关键词或调整筛选条件</p>
            </div>
          )}
        </div>
      )}

      {/* 未搜索时显示推荐图书 */}
      {!loading && !hasSearched && (
        <div className="space-y-6">
          {/* 分类标签 */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm text-white/50 mr-2">分类:</span>
            {BOOK_CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                onClick={() => loadRecommendBooks(cat.id)}
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
              {['深度学习', '机器学习', 'Python', '大模型', '算法', '前端'].map((tag) => (
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

          {/* 推荐图书列表 */}
          <div>
            <h4 className="text-sm font-medium text-white/60 mb-4 flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-purple-400" />
              精选图书资源
            </h4>

            {recommendLoading ? (
              <div className="flex flex-col items-center justify-center py-16 space-y-4">
                <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
                <p className="text-sm text-white/40">加载推荐图书...</p>
              </div>
            ) : books.length > 0 ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {books.map((book, idx) => (
                  <BookCard key={book.isbn} book={book} index={idx} onBookClick={logBookView} />
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 space-y-4">
                <BookOpen className="w-12 h-12 text-white/15" />
                <p className="text-sm text-white/40">暂无推荐图书</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
