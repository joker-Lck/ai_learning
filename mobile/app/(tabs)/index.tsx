import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, ScrollView, RefreshControl, TouchableOpacity } from 'react-native';
import { router } from 'expo-router';
import { useAuthStore } from '@/stores';
import { api } from '@/lib/api';
import { StatsCard, RecentResource, ActivityLog } from '@/components/dashboard/StatsCard';
import { Card } from '@/components/ui/Card';
import { Loading } from '@/components/ui/Loading';

export default function DashboardScreen() {
  const { user, isGuest } = useAuthStore();
  const [stats, setStats] = useState<any>(null);
  const [resources, setResources] = useState<any[]>([]);
  const [activities, setActivities] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [statsRes, resourcesRes, activitiesRes, recsRes] = await Promise.allSettled([
        api.getDashboardStats(),
        api.getResources({ limit: 5 }),
        api.getActivityLogs(5),
        api.getLearningRecommendations(),
      ]);

      if (statsRes.status === 'fulfilled' && (statsRes.value as any).success) {
        setStats((statsRes.value as any).data);
      }
      if (resourcesRes.status === 'fulfilled' && (resourcesRes.value as any).success) {
        setResources((resourcesRes.value as any).data?.resources || []);
      }
      if (activitiesRes.status === 'fulfilled' && (activitiesRes.value as any).success) {
        setActivities((activitiesRes.value as any).data?.logs || []);
      }
      if (recsRes.status === 'fulfilled' && (recsRes.value as any).success) {
        setRecommendations((recsRes.value as any).data?.recommendations || []);
      }
    } catch (err) {
      console.error('加载数据失败:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadData();
  }, [loadData]);

  if (loading) {
    return <Loading text="加载工作台..." />;
  }

  return (
    <ScrollView
      className="flex-1 bg-primary"
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#64ffda" />
      }
    >
      <View className="px-4 pt-16 pb-4">
        {/* 问候 */}
        <View className="mb-6">
          <Text className="text-text-secondary text-sm">
            {new Date().getHours() < 12 ? '早上好' : new Date().getHours() < 18 ? '下午好' : '晚上好'}
          </Text>
          <Text className="text-text-primary text-2xl font-bold mt-1">
            {isGuest ? '游客' : user?.username || '同学'}
          </Text>
          {stats && (
            <Text className="text-text-muted text-sm mt-1">
              已学习 {stats.total_days || 0} 天 · {stats.total_hours || 0} 小时
            </Text>
          )}
        </View>

        {/* 统计卡片 */}
        <View className="flex-row gap-3 mb-6">
          <StatsCard label="学习记录" value={stats?.total_records || 0} icon="📊" />
          <StatsCard label="兴趣领域" value={stats?.interest_count || 0} icon="🎯" color="#ffd166" />
          <StatsCard label="生成资源" value={stats?.resource_count || 0} icon="📚" color="#ff6b6b" />
        </View>

        {/* 快捷入口 */}
        <Card title="快速开始" className="mb-4">
          <View className="flex-row flex-wrap gap-3">
            {[
              { label: 'AI 问答', icon: '💬', route: '/(tabs)/tutor' },
              { label: '资源生成', icon: '📚', route: '/(tabs)/resources' },
              { label: '学生画像', icon: '👤', route: '/(tabs)/profile' },
              { label: '知识库', icon: '📖', route: '/(tabs)/profile' },
            ].map((item) => (
              <TouchableOpacity
                key={item.label}
                className="bg-surface rounded-xl p-3 flex-row items-center flex-1 min-w-[45%]"
                onPress={() => router.push(item.route as any)}
                activeOpacity={0.7}
              >
                <Text className="text-xl mr-2">{item.icon}</Text>
                <Text className="text-text-primary text-sm">{item.label}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </Card>

        {/* 继续学习 */}
        {resources.length > 0 && (
          <Card title="继续学习" className="mb-4">
            {resources.map((res) => (
              <RecentResource
                key={res.id}
                id={res.id}
                title={res.title}
                type={res.resource_type}
                subject={res.subject || '通用'}
                createdAt={res.created_at?.slice(0, 10) || ''}
                onPress={() => router.push(`/(tabs)/resources`)}
              />
            ))}
          </Card>
        )}

        {/* 今日建议 */}
        {recommendations.length > 0 && (
          <Card title="今日建议" className="mb-4">
            <Text className="text-text-secondary text-[10px] mb-2">AI 学习规划师</Text>
            {recommendations.slice(0, 4).map((rec: any, idx: number) => {
              const categoryColors: Record<string, string> = {
                weakness: 'text-red-400',
                review: 'text-amber-400',
                planning: 'text-blue-400',
                strategy: 'text-purple-400',
              };
              const categoryLabels: Record<string, string> = {
                weakness: '薄弱',
                review: '复习',
                planning: '规划',
                strategy: '策略',
              };
              const textColor = categoryColors[rec.category] || 'text-accent';
              const label = categoryLabels[rec.category] || '建议';
              return (
                <TouchableOpacity
                  key={idx}
                  className="flex-row items-start mb-3 p-2 rounded-lg bg-white/[0.02]"
                  onPress={() => router.push('/(tabs)/tutor')}
                >
                  <View className="mr-2 mt-0.5">
                    <Text className={`text-xs font-medium ${textColor}`}>{label}</Text>
                  </View>
                  <View className="flex-1">
                    <Text className="text-text-primary text-sm font-medium">{rec.topic || rec.name}</Text>
                    <Text className="text-text-secondary text-[11px] mt-0.5">{rec.reason}</Text>
                    {rec.detail ? <Text className="text-text-secondary text-[10px] mt-0.5 opacity-50">{rec.detail}</Text> : null}
                  </View>
                </TouchableOpacity>
              );
            })}
          </Card>
        )}

        {/* 协同动态 */}
        <Card title="协同动态" className="mb-4">
          <ActivityLog logs={activities} />
        </Card>
      </View>
    </ScrollView>
  );
}
