import React from 'react';
import { TextInput, View, Text } from 'react-native';

interface InputProps {
  label?: string;
  placeholder?: string;
  value: string;
  onChangeText: (text: string) => void;
  secureTextEntry?: boolean;
  multiline?: boolean;
  numberOfLines?: number;
  error?: string;
  className?: string;
}

export function Input({
  label,
  placeholder,
  value,
  onChangeText,
  secureTextEntry,
  multiline,
  numberOfLines = 1,
  error,
  className = '',
}: InputProps) {
  return (
    <View className={`mb-3 ${className}`}>
      {label && (
        <Text className="text-text-secondary text-sm mb-1">{label}</Text>
      )}
      <TextInput
        className={`bg-surface border ${
          error ? 'border-error' : 'border-border'
        } rounded-lg px-4 py-3 text-text-primary text-base`}
        placeholder={placeholder}
        placeholderTextColor="#495670"
        value={value}
        onChangeText={onChangeText}
        secureTextEntry={secureTextEntry}
        multiline={multiline}
        numberOfLines={numberOfLines}
        textAlignVertical={multiline ? 'top' : 'center'}
      />
      {error && (
        <Text className="text-error text-xs mt-1">{error}</Text>
      )}
    </View>
  );
}
