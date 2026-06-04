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
  },
};

module.exports = nextConfig;
