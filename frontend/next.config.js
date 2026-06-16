/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Docker standalone 输出
  output: 'standalone',

  // API 代理配置
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return [
      { source: '/api/:path*', destination: `${backendUrl}/api/:path*` },
      { source: '/ws/:path*', destination: `${backendUrl}/ws/:path*` },
      { source: '/exports/:path*', destination: `${backendUrl}/exports/:path*` },
    ];
  },

  // 安全头 + CSP
  async headers() {
    const isDev = process.env.NODE_ENV === 'development';
    const backendOrigin = process.env.NEXT_PUBLIC_API_ORIGIN || 'http://localhost:8000';

    const cspDirectives = [
      "default-src 'self'",
      isDev ? "script-src 'self' 'unsafe-eval' 'unsafe-inline'" : "script-src 'self' 'unsafe-eval'",
      "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
      "font-src 'self' https://fonts.gstatic.com",
      `img-src 'self' data: blob: ${backendOrigin}`,
      `connect-src 'self' ${backendOrigin} ws://localhost:* wss://localhost:*`,
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
    ];

    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-XSS-Protection', value: '1; mode=block' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
          { key: 'Content-Security-Policy', value: cspDirectives.join('; ') },
          { key: 'Strict-Transport-Security', value: 'max-age=31536000; includeSubDomains' },
        ],
      },
    ];
  },

  // 图片域名白名单
  images: {
    remotePatterns: [
      { protocol: 'http', hostname: 'localhost' },
    ],
    formats: ['image/avif', 'image/webp'],
  },

  // 压缩
  compress: true,
  poweredByHeader: false,

  // 实验性功能
  experimental: {
    optimizeCss: true,
    optimizePackageImports: ['lucide-react', 'framer-motion', 'recharts'],
  },

  // Webpack 配置优化
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
