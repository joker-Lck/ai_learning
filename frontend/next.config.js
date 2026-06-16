/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // API 代理配置 (开发环境)
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
      {
        source: '/ws/:path*',
        destination: 'http://localhost:8000/ws/:path*',
      },
      {
        source: '/exports/:path*',
        destination: 'http://localhost:8000/exports/:path*',
      },
    ];
  },

  // 图片域名白名单（remotePatterns 替代已废弃的 domains）
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
      },
    ],
    formats: ['image/avif', 'image/webp'],
  },

  // 压缩配置
  compress: true,

  // 生产环境优化
  poweredByHeader: false,

  // 实验性功能
  experimental: {
    optimizeCss: true,
    optimizePackageImports: ['lucide-react', 'framer-motion', 'recharts'],
  },

  // Webpack配置优化
  webpack: (config, { dev, isServer }) => {
    if (!dev && !isServer) {
      config.optimization.splitChunks = {
        chunks: 'all',
        minSize: 20000,
        maxSize: 244000,
        minChunks: 1,
        maxAsyncRequests: 30,
        maxInitialRequests: 30,
        cacheGroups: {
          defaultVendors: {
            test: /[\\/]node_modules[\\/]/,
            priority: -10,
            reuseExistingChunk: true,
          },
          default: {
            minChunks: 2,
            priority: -20,
            reuseExistingChunk: true,
          },
        },
      };
    }
    return config;
  },
};

module.exports = nextConfig;
