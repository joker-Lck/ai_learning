import React, { useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, Animated } from 'react-native';

interface ChatBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  isStreaming?: boolean;
}

export function ChatBubble({ role, content, timestamp, isStreaming }: ChatBubbleProps) {
  const isUser = role === 'user';

  return (
    <View className={`flex-row ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <View
        className={`max-w-[85%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-accent rounded-br-sm'
            : 'bg-primary-light border border-border rounded-bl-sm'
        }`}
      >
        <Text
          className={`text-base leading-6 ${
            isUser ? 'text-primary' : 'text-text-primary'
          }`}
        >
          {content}
          {isStreaming && <Text className="text-accent">|</Text>}
        </Text>
        {timestamp && (
          <Text
            className={`text-xs mt-1 ${
              isUser ? 'text-primary/60' : 'text-text-muted'
            }`}
          >
            {timestamp}
          </Text>
        )}
      </View>
    </View>
  );
}

interface ChatInputProps {
  value: string;
  onChangeText: (text: string) => void;
  onSend: () => void;
  placeholder?: string;
  disabled?: boolean;
  onVoicePress?: () => void;
  isListening?: boolean;
  voiceTranscript?: string;
}

export function ChatInput({
  value,
  onChangeText,
  onSend,
  placeholder = '输入你的问题...',
  disabled = false,
  onVoicePress,
  isListening = false,
  voiceTranscript = '',
}: ChatInputProps) {
  // When voice transcript changes, update input
  useEffect(() => {
    if (voiceTranscript && voiceTranscript !== value) {
      onChangeText(voiceTranscript);
    }
  }, [voiceTranscript]);

  return (
    <View className="flex-row items-end gap-2 p-4 bg-primary-light border-t border-border">
      {/* 麦克风按钮 */}
      {onVoicePress && (
        <TouchableOpacity
          className={`w-12 h-12 rounded-full items-center justify-center ${
            isListening ? 'bg-error' : 'bg-surface'
          }`}
          onPress={onVoicePress}
          disabled={disabled}
          activeOpacity={0.7}
        >
          <Text className="text-xl">{isListening ? '⏹' : '🎤'}</Text>
        </TouchableOpacity>
      )}

      {/* 输入框 */}
      <View className="flex-1 bg-surface border border-border rounded-2xl px-4 py-3">
        {isListening ? (
          <View className="flex-row items-center">
            <Text className="text-error text-sm mr-2">●</Text>
            <Text className="text-text-secondary text-base">
              {voiceTranscript || '正在聆听...'}
            </Text>
          </View>
        ) : (
          <TextInput
            className="text-text-primary text-base max-h-32"
            placeholder={placeholder}
            placeholderTextColor="#495670"
            value={value}
            onChangeText={onChangeText}
            multiline
            editable={!disabled}
          />
        )}
      </View>

      {/* 发送按钮 */}
      <TouchableOpacity
        className={`w-12 h-12 rounded-full items-center justify-center ${
          value.trim() && !disabled ? 'bg-accent' : 'bg-surface'
        }`}
        onPress={onSend}
        disabled={!value.trim() || disabled}
        activeOpacity={0.7}
      >
        <Text className="text-lg">↑</Text>
      </TouchableOpacity>
    </View>
  );
}
