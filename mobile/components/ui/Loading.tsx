import React from 'react';
import { ActivityIndicator, Text, View } from 'react-native';

interface LoadingProps {
  text?: string;
  size?: 'small' | 'large';
}

export function Loading({ text = '加载中...', size = 'large' }: LoadingProps) {
  return (
    <View className="flex-1 items-center justify-center bg-primary">
      <ActivityIndicator size={size} color="#64ffda" />
      {text && (
        <Text className="text-text-secondary mt-3 text-sm">{text}</Text>
      )}
    </View>
  );
}
