import React from 'react';
import { TouchableOpacity, Text, ActivityIndicator, View } from 'react-native';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  icon?: React.ReactNode;
  className?: string;
}

export function Button({
  title,
  onPress,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  icon,
  className = '',
}: ButtonProps) {
  const baseStyle = 'flex-row items-center justify-center rounded-lg';
  const sizeStyle = {
    sm: 'px-3 py-2',
    md: 'px-4 py-3',
    lg: 'px-6 py-4',
  }[size];

  const variantStyle = {
    primary: 'bg-accent',
    secondary: 'bg-surface',
    outline: 'border border-accent bg-transparent',
    ghost: 'bg-transparent',
  }[variant];

  const textStyle = {
    primary: 'text-primary font-bold',
    secondary: 'text-text-primary font-bold',
    outline: 'text-accent font-bold',
    ghost: 'text-accent',
  }[variant];

  const textSize = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
  }[size];

  return (
    <TouchableOpacity
      className={`${baseStyle} ${sizeStyle} ${variantStyle} ${disabled ? 'opacity-50' : ''} ${className}`}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.7}
    >
      {loading ? (
        <ActivityIndicator size="small" color={variant === 'primary' ? '#0a192f' : '#64ffda'} />
      ) : (
        <View className="flex-row items-center gap-2">
          {icon}
          <Text className={`${textStyle} ${textSize}`}>{title}</Text>
        </View>
      )}
    </TouchableOpacity>
  );
}
