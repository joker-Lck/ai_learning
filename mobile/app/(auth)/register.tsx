import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { router } from 'expo-router';
import { useAuthStore } from '@/stores';
import { api } from '@/lib/api';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

export default function RegisterScreen() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuthStore();

  const handleRegister = async () => {
    if (!username.trim() || !password.trim()) {
      Alert.alert('提示', '请输入用户名和密码');
      return;
    }
    if (password !== confirmPassword) {
      Alert.alert('提示', '两次密码输入不一致');
      return;
    }

    setLoading(true);
    try {
      const result: any = await api.register(username, password, email || undefined);
      if (result.success) {
        Alert.alert('注册成功', '请登录', [
          { text: '确定', onPress: () => router.replace('/(auth)/login') },
        ]);
      } else {
        Alert.alert('注册失败', result.message || '注册失败');
      }
    } catch (err: any) {
      Alert.alert('注册失败', err.message || '网络连接失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView className="flex-1 bg-primary" contentContainerStyle={{ flexGrow: 1 }}>
      <View className="flex-1 justify-center px-8 py-12">
        <View className="items-center mb-8">
          <Text className="text-accent text-2xl font-bold">创建账号</Text>
          <Text className="text-text-secondary text-sm mt-2">
            开始你的个性化学习之旅
          </Text>
        </View>

        <Input
          label="用户名 *"
          placeholder="请输入用户名"
          value={username}
          onChangeText={setUsername}
        />
        <Input
          label="邮箱"
          placeholder="请输入邮箱（可选）"
          value={email}
          onChangeText={setEmail}
        />
        <Input
          label="密码 *"
          placeholder="请输入密码"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />
        <Input
          label="确认密码 *"
          placeholder="请再次输入密码"
          value={confirmPassword}
          onChangeText={setConfirmPassword}
          secureTextEntry
        />

        <Button
          title="注册"
          onPress={handleRegister}
          loading={loading}
          size="lg"
          className="mt-4 mb-4"
        />

        <TouchableOpacity
          onPress={() => router.replace('/(auth)/login')}
          className="items-center py-3"
        >
          <Text className="text-text-secondary">
            已有账号？<Text className="text-accent">立即登录</Text>
          </Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}
