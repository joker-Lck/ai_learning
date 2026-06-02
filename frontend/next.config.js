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

  // 增加API路由超时时间(开发环境)
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // 客户端配置
    }
    return config;
  },

  // 开发服务器配置
  serverRuntimeConfig: {
    // 服务器端运行时配置
  },
};

module.exports = nextConfig;
