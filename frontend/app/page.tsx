'use client';

import dynamic from 'next/dynamic';

const LoginPage = dynamic(() => import('./LoginContent'), { ssr: false });

export default function Page() {
  return <LoginPage />;
}
