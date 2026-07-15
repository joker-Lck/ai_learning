import React from 'react';
import { View, Text, FlatList, TouchableOpacity } from 'react-native';

interface StatsCardProps {
  label: string;
  value: string | number;
  icon: string;
  color?: string;
}

export function StatsCard({ label, value, icon, color = '#64ffda' }: StatsCardProps) {
  return (
    <View className="bg-primary-light rounded-xl border border-border p-4 flex-1">
      <Text className="text-2xl mb-1">{icon}</Text>
      <Text className="text-text-secondary text-xs mb-1">{label}</Text>
      <Text className="text-xl font-bold" style={{ color }}>
        {value}
      </Text>
    </View>
  );
}

interface RecentResourceProps {
  id: number;
  title: string;
  type: string;
  subject: string;
  createdAt: string;
  onPress: () => void;
}

export function RecentResource({ title, type, subject, createdAt, onPress }: RecentResourceProps) {
  const typeIcons: Record<string, string> = {
    document: '📄',
    mindmap: '🗺️',
    quiz: '📝',
    video: '🎥',
    animation: '🎬',
    code_case: '💻',
    reading: '📚',
  };

  return (
    <TouchableOpacity
      className="bg-surface rounded-xl border border-border p-4 mb-2 flex-row items-center"
      onPress={onPress}
      activeOpacity={0.7}
    >
      <Text className="text-2xl mr-3">{typeIcons[type] || '📄'}</Text>
      <View className="flex-1">
        <Text className="text-text-primary font-medium" numberOfLines={1}>
          {title}
        </Text>
        <Text className="text-text-secondary text-xs mt-1">
          {subject} · {createdAt}
        </Text>
      </View>
      <Text className="text-accent text-sm">查看</Text>
    </TouchableOpacity>
  );
}

interface ActivityLogProps {
  logs: Array<{
    id: number;
    action: string;
    detail: string;
    created_at: string;
  }>;
}

export function ActivityLog({ logs }: ActivityLogProps) {
  if (logs.length === 0) {
    return (
      <View className="py-8 items-center">
        <Text className="text-text-muted">暂无活动记录</Text>
      </View>
    );
  }

  return (
    <View>
      {logs.slice(0, 5).map((log) => (
        <View key={log.id} className="flex-row items-start mb-3">
          <View className="w-2 h-2 rounded-full bg-accent mt-2 mr-3" />
          <View className="flex-1">
            <Text className="text-text-primary text-sm">{log.detail}</Text>
            <Text className="text-text-muted text-xs mt-1">{log.created_at}</Text>
          </View>
        </View>
      ))}
    </View>
  );
}
