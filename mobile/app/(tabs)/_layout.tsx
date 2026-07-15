import React from 'react';
import { Redirect, Tabs } from 'expo-router';
import { useAuthStore } from '@/stores';
import { Loading } from '@/components/ui/Loading';
import { View, Text } from 'react-native';

function TabIcon({ name, focused }: { name: string; focused: boolean }) {
  const icons: Record<string, string> = {
    index: '🏠',
    tutor: '💬',
    resources: '📚',
    profile: '👤',
  };
  return (
    <View className="items-center">
      <Text className="text-xl">{icons[name] || '📄'}</Text>
      {focused && <View className="w-1 h-1 rounded-full bg-accent mt-1" />}
    </View>
  );
}

export default function TabsLayout() {
  const { isLoggedIn, isLoading } = useAuthStore();

  if (isLoading) {
    return <Loading text="正在加载..." />;
  }

  if (!isLoggedIn) {
    return <Redirect href="/(auth)/login" />;
  }

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: '#112240',
          borderTopColor: '#233554',
          borderTopWidth: 1,
          height: 60,
          paddingBottom: 8,
          paddingTop: 8,
        },
        tabBarActiveTintColor: '#64ffda',
        tabBarInactiveTintColor: '#8892b0',
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: '工作台',
          tabBarIcon: ({ focused }) => <TabIcon name="index" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="tutor"
        options={{
          title: '辅导',
          tabBarIcon: ({ focused }) => <TabIcon name="tutor" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="resources"
        options={{
          title: '资源',
          tabBarIcon: ({ focused }) => <TabIcon name="resources" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: '我的',
          tabBarIcon: ({ focused }) => <TabIcon name="profile" focused={focused} />,
        }}
      />
    </Tabs>
  );
}
