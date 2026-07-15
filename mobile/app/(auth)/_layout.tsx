import React from 'react';
import { Redirect, Stack } from 'expo-router';
import { useAuthStore } from '@/stores';
import { Loading } from '@/components/ui/Loading';

export default function AuthLayout() {
  const { isLoggedIn, isLoading } = useAuthStore();

  if (isLoading) {
    return <Loading text="正在加载..." />;
  }

  if (isLoggedIn) {
    return <Redirect href="/(tabs)" />;
  }

  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: '#0a192f' },
        animation: 'fade',
      }}
    />
  );
}
