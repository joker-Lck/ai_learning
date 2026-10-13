import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// 需要老师/管理员角色的路径
const TEACHER_PATHS = ['/teacher'];

// 老师不应进入的学生端路径（入口层）
const STUDENT_ONLY_PATHS = ['/dashboard', '/assessment-quiz'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 只对页面路由添加安全头，跳过 API/静态资源
  if (
    pathname.startsWith('/api') ||
    pathname.startsWith('/_next') ||
    pathname.startsWith('/exports') ||
    pathname.includes('.')
  ) {
    return NextResponse.next();
  }

  // 添加安全头
  const response = NextResponse.next();
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');

  // 角色路由守卫（入口层 — 在服务端 Cookie 检查不便时用客户端二次校验兜底）
  // 这里做轻量 header/query 无法拿到 localStorage，所以只做路径分类标记
  // 真正的角色校验在对应页面的 useEffect 中执行（见 teacher/page.tsx）
  if (TEACHER_PATHS.some(p => pathname.startsWith(p))) {
    response.headers.set('X-Required-Role', 'teacher');
  }

  return response;
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
