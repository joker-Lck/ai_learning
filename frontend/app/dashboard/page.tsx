'use client';

import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useAuthStore, useUIStore } from '@/stores';
import Sidebar from '@/components/layout/Sidebar';
import DashboardContent from '@/components/DashboardContent';

export default function DashboardPage() {
  const router = useRouter();
  const { isLoggedIn } = useAuthStore();
  const { sidebarOpen } = useUIStore();

  useEffect(() => {
    if (!isLoggedIn) {
      router.push('/');
    }
  }, [isLoggedIn, router]);

  if (!isLoggedIn) return null;

  return (
    <div className="flex min-h-screen bg-surface-secondary">
      <Sidebar />
      <main
        className={`flex-1 transition-all duration-300 ${
          sidebarOpen ? 'ml-64' : 'ml-20'
        }`}
      >
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="p-8"
        >
          <DashboardContent />
        </motion.div>
      </main>
    </div>
  );
}
