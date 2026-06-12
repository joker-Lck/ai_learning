'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/stores';
import DashboardContent from '@/components/DashboardContent';
import FloatingMenu from '@/components/layout/FloatingMenu';

export default function DashboardPage() {
  const { restoreAuth } = useAuthStore();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const hasToken = !!localStorage.getItem('auth_token');
    const isGuest = localStorage.getItem('is_guest') === 'true';
    if (!hasToken && !isGuest) {
      window.location.href = '/';
      return;
    }
    restoreAuth();
    setReady(true);
  }, []);

  if (!ready) return null;

  return (
    <div className="min-h-screen" style={{ background: '#0a0a0a' }}>
      <FloatingMenu />
      <DashboardContent />
    </div>
  );
}
