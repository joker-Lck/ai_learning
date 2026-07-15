import React from 'react';
import { View, Text, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { router } from 'expo-router';
import { useAuthStore } from '@/stores';
import { Card } from '@/components/ui/Card';

const MENU_ITEMS = [
  { label: '学生画像', icon: '👤', description: '9 维度动态画像' },
  { label: '学习路径', icon: '🗺️', description: '个性化学习规划' },
  { label: '效果评估', icon: '📊', description: '多维度学习评估' },
  { label: '知识库', icon: '📖', description: 'RAG 知识库管理' },
  { label: '课程表', icon: '📅', description: '课程表管理' },
  { label: '成绩管理', icon: '📝', description: '成绩录入与统计' },
  { label: '错题本', icon: '❌', description: '错题收集与复习' },
  { label: '学习计划', icon: '📋', description: 'AI 学习计划生成' },
];

export default function ProfileScreen() {
  const { user, isGuest, logout } = useAuthStore();

  const handleLogout = () => {
    Alert.alert('退出登录', '确定要退出吗？', [
      { text: '取消', style: 'cancel' },
      {
        text: '退出',
        style: 'destructive',
        onPress: async () => {
          await logout();
          router.replace('/(auth)/login');
        },
      },
    ]);
  };

  const handleMenuPress = (label: string) => {
    // 各功能模块暂用 Alert 提示，后续可跳转到具体页面
    Alert.alert(label, '该功能正在开发中');
  };

  return (
    <ScrollView className="flex-1 bg-primary">
      <View className="px-4 pt-16 pb-4">
        {/* 用户信息 */}
        <Card className="mb-6">
          <View className="flex-row items-center">
            <View className="w-16 h-16 rounded-full bg-accent/20 items-center justify-center mr-4">
              <Text className="text-3xl">{isGuest ? '👤' : '🎓'}</Text>
            </View>
            <View className="flex-1">
              <Text className="text-text-primary text-xl font-bold">
                {isGuest ? '游客' : user?.username || '用户'}
              </Text>
              <Text className="text-text-secondary text-sm mt-1">
                {isGuest ? '游客模式 · 功能受限' : `${user?.role || 'student'} · ID: ${user?.id}`}
              </Text>
            </View>
          </View>
        </Card>

        {/* 功能菜单 */}
        <Card title="功能模块" className="mb-6">
          <View className="flex-row flex-wrap gap-3">
            {MENU_ITEMS.map((item) => (
              <TouchableOpacity
                key={item.label}
                className="bg-surface rounded-xl p-3 flex-row items-center w-[47%]"
                onPress={() => handleMenuPress(item.label)}
                activeOpacity={0.7}
              >
                <Text className="text-2xl mr-3">{item.icon}</Text>
                <View className="flex-1">
                  <Text className="text-text-primary text-sm font-medium">
                    {item.label}
                  </Text>
                  <Text className="text-text-muted text-xs mt-1" numberOfLines={1}>
                    {item.description}
                  </Text>
                </View>
              </TouchableOpacity>
            ))}
          </View>
        </Card>

        {/* 设置 */}
        <Card title="设置" className="mb-6">
          <TouchableOpacity
            className="flex-row items-center justify-between py-3 border-b border-border"
            onPress={() => Alert.alert('关于', 'AI学习智能体 v1.0.0\n基于多智能体的个性化学习资源生成系统')}
          >
            <Text className="text-text-primary">关于</Text>
            <Text className="text-text-muted">v1.0.0</Text>
          </TouchableOpacity>
          <TouchableOpacity
            className="flex-row items-center justify-between py-3"
            onPress={handleLogout}
          >
            <Text className="text-error">退出登录</Text>
            <Text className="text-text-muted">→</Text>
          </TouchableOpacity>
        </Card>
      </View>
    </ScrollView>
  );
}
