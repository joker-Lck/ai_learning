import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, ScrollView, FlatList, TouchableOpacity, Alert, RefreshControl } from 'react-native';
import { api } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Loading } from '@/components/ui/Loading';

const RESOURCE_TYPES = [
  { key: 'document', label: '文档', icon: '📄' },
  { key: 'mindmap', label: '思维导图', icon: '🗺️' },
  { key: 'quiz', label: '题库', icon: '📝' },
  { key: 'video', label: '视频', icon: '🎥' },
  { key: 'animation', label: '动画', icon: '🎬' },
  { key: 'code_case', label: '代码', icon: '💻' },
  { key: 'reading', label: '阅读', icon: '📚' },
];

const DIFFICULTIES = [
  { key: 'beginner', label: '初级' },
  { key: 'intermediate', label: '中级' },
  { key: 'advanced', label: '高级' },
];

export default function ResourcesScreen() {
  const [resources, setResources] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [subject, setSubject] = useState('');
  const [topic, setTopic] = useState('');
  const [selectedTypes, setSelectedTypes] = useState<string[]>(['document']);
  const [difficulty, setDifficulty] = useState('intermediate');
  const [showGenerator, setShowGenerator] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [progress, setProgress] = useState('');

  const loadResources = useCallback(async () => {
    try {
      const result: any = await api.getResources({ limit: 20 });
      if (result.success) {
        setResources(result.data?.resources || []);
      }
    } catch (err) {
      console.error('加载资源失败:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadResources();
  }, [loadResources]);

  const handleGenerate = async () => {
    if (!subject.trim() || !topic.trim()) {
      Alert.alert('提示', '请输入学科和主题');
      return;
    }

    setGenerating(true);
    setProgress('正在分析需求...');

    try {
      const result: any = await api.generateResources({
        subject,
        topic,
        resource_types: selectedTypes,
        difficulty,
      });

      if (result.success) {
        Alert.alert('生成成功', `已生成 ${selectedTypes.length} 种资源`);
        setShowGenerator(false);
        loadResources();
      } else {
        Alert.alert('生成失败', result.message || '请重试');
      }
    } catch (err: any) {
      Alert.alert('生成失败', err.message || '网络错误');
    } finally {
      setGenerating(false);
      setProgress('');
    }
  };

  const toggleType = (key: string) => {
    setSelectedTypes((prev) =>
      prev.includes(key) ? prev.filter((t) => t !== key) : [...prev, key]
    );
  };

  if (loading) {
    return <Loading text="加载资源..." />;
  }

  return (
    <View className="flex-1 bg-primary">
      {/* Header */}
      <View className="px-4 pt-16 pb-3 bg-primary-light border-b border-border">
        <View className="flex-row items-center justify-between">
          <View>
            <Text className="text-text-primary text-xl font-bold">学习资源</Text>
            <Text className="text-text-secondary text-xs mt-1">
              AI 生成的个性化学习资料
            </Text>
          </View>
          <TouchableOpacity
            className="bg-accent rounded-lg px-4 py-2"
            onPress={() => setShowGenerator(!showGenerator)}
          >
            <Text className="text-primary font-bold text-sm">
              {showGenerator ? '收起' : '生成'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); loadResources(); }} tintColor="#64ffda" />
        }
      >
        {/* 生成器 */}
        {showGenerator && (
          <View className="px-4 pt-4">
            <Card title="生成新资源">
              <Input
                label="学科"
                placeholder="如：数据结构"
                value={subject}
                onChangeText={setSubject}
              />
              <Input
                label="主题"
                placeholder="如：二叉树遍历"
                value={topic}
                onChangeText={setTopic}
              />

              <Text className="text-text-secondary text-sm mb-2">资源类型</Text>
              <View className="flex-row flex-wrap gap-2 mb-3">
                {RESOURCE_TYPES.map((type) => (
                  <TouchableOpacity
                    key={type.key}
                    className={`px-3 py-2 rounded-lg border ${
                      selectedTypes.includes(type.key)
                        ? 'border-accent bg-accent/10'
                        : 'border-border bg-surface'
                    }`}
                    onPress={() => toggleType(type.key)}
                  >
                    <Text className="text-sm">
                      {type.icon} {type.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text className="text-text-secondary text-sm mb-2">难度</Text>
              <View className="flex-row gap-2 mb-4">
                {DIFFICULTIES.map((d) => (
                  <TouchableOpacity
                    key={d.key}
                    className={`flex-1 py-2 rounded-lg border ${
                      difficulty === d.key
                        ? 'border-accent bg-accent/10'
                        : 'border-border bg-surface'
                    }`}
                    onPress={() => setDifficulty(d.key)}
                  >
                    <Text className={`text-center text-sm ${difficulty === d.key ? 'text-accent' : 'text-text-secondary'}`}>
                      {d.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Button
                title={generating ? progress || '生成中...' : '开始生成'}
                onPress={handleGenerate}
                loading={generating}
                disabled={generating}
              />
            </Card>
          </View>
        )}

        {/* 资源列表 */}
        <View className="px-4 pt-4 pb-8">
          {resources.length === 0 ? (
            <View className="items-center py-16">
              <Text className="text-5xl mb-4">📚</Text>
              <Text className="text-text-primary text-lg font-bold mb-2">暂无资源</Text>
              <Text className="text-text-secondary text-center">
                点击右上角"生成"按钮创建学习资源
              </Text>
            </View>
          ) : (
            resources.map((res) => {
              const typeInfo = RESOURCE_TYPES.find((t) => t.key === res.resource_type);
              return (
                <TouchableOpacity
                  key={res.id}
                  className="bg-primary-light rounded-xl border border-border p-4 mb-3"
                  activeOpacity={0.7}
                >
                  <View className="flex-row items-center mb-2">
                    <Text className="text-xl mr-2">{typeInfo?.icon || '📄'}</Text>
                    <View className="flex-1">
                      <Text className="text-text-primary font-medium" numberOfLines={1}>
                        {res.title}
                      </Text>
                      <Text className="text-text-muted text-xs mt-1">
                        {res.subject} · {typeInfo?.label || res.resource_type} · {res.created_at?.slice(0, 10)}
                      </Text>
                    </View>
                  </View>
                  {res.topic && (
                    <Text className="text-text-secondary text-sm" numberOfLines={2}>
                      {res.topic}
                    </Text>
                  )}
                </TouchableOpacity>
              );
            })
          )}
        </View>
      </ScrollView>
    </View>
  );
}
