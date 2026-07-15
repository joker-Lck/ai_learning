import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { router } from 'expo-router';
import { useAuthStore } from '@/stores';
import { api } from '@/lib/api';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

export default function LoginScreen() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, setGuest } = useAuthStore();

  const handleLogin = async () => {
    if (!username.trim() || !password.trim()) {
      Alert.alert('提示', '请输入用户名和密码');
      return;
    }

    setLoading(true);
    try {
      const result: any = await api.login(username, password);
      if (result.success) {
        await login(result.user, result.token);
        router.replace('/(tabs)');
      } else {
        Alert.alert('登录失败', result.message || '用户名或密码错误');
      }
    } catch (err: any) {
      Alert.alert('登录失败', err.message || '网络连接失败');
    } finally {
      setLoading(false);
    }
  };

  const handleGuest = () => {
    setGuest();
    router.replace('/(tabs)');
  };

  return (
    <ScrollView className="flex-1 bg-primary" contentContainerStyle={{ flexGrow: 1 }}>
      <View className="flex-1 justify-center px-8 py-12">
        {/* Logo */}
        <View className="items-center mb-10">
          <Text className="text-5xl mb-4">🎓</Text>
          <Text className="text-accent text-2xl font-bold text-center">
            AI学习智能体
          </Text>
          <Text className="text-text-secondary text-sm mt-2 text-center">
            基于多智能体的个性化学习资源生成系统
          </Text>
        </View>

        {/* 表单 */}
        <View className="mb-6">
          <Input
            label="用户名"
            placeholder="请输入用户名"
            value={username}
            onChangeText={setUsername}
          />
          <Input
            label="密码"
            placeholder="请输入密码"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
          />
        </View>

        <Button
          title="登录"
          onPress={handleLogin}
          loading={loading}
          size="lg"
          className="mb-4"
        />

        <View className="flex-row items-center my-4">
          <View className="flex-1 h-px bg-border" />
          <Text className="text-text-muted px-4">或</Text>
          <View className="flex-1 h-px bg-border" />
        </View>

        <Button
          title="游客模式体验"
          onPress={handleGuest}
          variant="outline"
          size="lg"
          className="mb-4"
        />

        <TouchableOpacity
          onPress={() => router.push('/(auth)/register')}
          className="items-center py-3"
        >
          <Text className="text-text-secondary">
            还没有账号？<Text className="text-accent">立即注册</Text>
          </Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}
