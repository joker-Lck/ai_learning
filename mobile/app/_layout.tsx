import '../global.css';
import React, { useEffect } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { View } from 'react-native';
import { useAuthStore } from '@/stores';

export default function RootLayout() {
  const { restoreAuth, isLoading } = useAuthStore();

  useEffect(() => {
    restoreAuth();
  }, []);

  return (
    <View className="flex-1 bg-primary">
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: '#0a192f' },
          animation: 'fade',
        }}
      />
    </View>
  );
}
