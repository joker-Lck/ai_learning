'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/stores';
import TeacherDashboard from '@/components/TeacherDashboard';

export default function TeacherPage() {
  const { restoreAuth } = useAuthStore();
  const [ready, setReady] = useState(false);
  const [denied, setDenied] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      window.location.href = '/';
      return;
    }
    restoreAuth();

    // 从 token / localStorage 判断角色
    let role = '';
    try {
      const stored = localStorage.getItem('user_info');
      if (stored) role = JSON.parse(stored).role || '';
    } catch {}
    if (!role) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1] ?? ''));
        role = payload.role || '';
      } catch {}
    }

    if (role === 'teacher' || role === 'admin') {
      setReady(true);
    } else {
      setDenied(true);
    }
  }, []);

  if (denied) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#0a0a0a' }}>
        <div className="text-center">
          <p className="text-white/40 text-lg mb-4">仅限老师 / 管理员访问</p>
          <a href="/dashboard" className="text-purple-400 hover:text-purple-300 underline text-sm">
            返回学生端 →
          </a>
        </div>
      </div>
    );
  }

  if (!ready) return null;

  return <TeacherDashboard />;
}
