'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useAuthStore, useUIStore } from '@/stores';
import Sidebar from '@/components/layout/Sidebar';
import DashboardContent from '@/components/DashboardContent';

export default function DashboardPage() {
  const router = useRouter();
  const { isLoggedIn, isGuest, restoreAuth } = useAuthStore();
  const { sidebarOpen } = useUIStore();
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    restoreAuth();
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (hydrated && !isLoggedIn && !isGuest) {
      router.push('/');
    }
  }, [hydrated, isLoggedIn, isGuest, router]);

  if (!hydrated || (!isLoggedIn && !isGuest)) return null;

  return (
    <div className="flex min-h-screen" style={{ background: '#060d1f' }}>
      <Sidebar />
      <main
        className={`flex-1 transition-all duration-300 ${
          sidebarOpen ? 'ml-64' : 'ml-20'
        }`}
      >
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: 'spring', stiffness: 200, damping: 25 }}
          className="p-8"
        >
          <DashboardContent />
        </motion.div>
      </main>
    </div>
  );
}
