import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// 需要认证的路由
const PROTECTED_ROUTES = ['/dashboard'];
// 不需要认证的路由
const PUBLIC_ROUTES = ['/', '/api'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 只对页面路由生效，跳过 API/静态资源
  if (
    pathname.startsWith('/api') ||
    pathname.startsWith('/_next') ||
    pathname.startsWith('/exports') ||
    pathname.includes('.') // 静态文件
  ) {
    return NextResponse.next();
  }

  // 检查是否访问受保护路由
  const isProtected = PROTECTED_ROUTES.some((route) => pathname.startsWith(route));

  if (isProtected) {
    // 检查认证 token（从 cookie 或 header）
    const token =
      request.cookies.get('auth_token')?.value ||
      request.headers.get('authorization')?.replace('Bearer ', '');

    if (!token) {
      // 未登录，重定向到首页
      const url = request.nextUrl.clone();
      url.pathname = '/';
      url.searchParams.set('redirect', pathname);
      return NextResponse.redirect(url);
    }
  }

  // 继续请求，添加安全头
  const response = NextResponse.next();

  // 安全头（补充 next.config.js 的 headers）
  response.headers.set('X-Request-Path', pathname);

  return response;
}

export const config = {
  matcher: [
    /*
     * 匹配所有页面路由，排除：
     * - _next/static（静态文件）
     * - _next/image（图片优化）
     * - favicon.ico
     */
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};
