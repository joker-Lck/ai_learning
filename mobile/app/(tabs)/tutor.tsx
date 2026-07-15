import React, { useState, useRef, useCallback } from 'react';
import { View, Text, FlatList, KeyboardAvoidingView, Platform, Alert } from 'react-native';
import { useChatStore } from '@/stores';
import { api } from '@/lib/api';
import { ChatBubble, ChatInput } from '@/components/chat/ChatBubble';
import { useVoiceInput } from '@/hooks/useVoiceInput';

export default function TutorScreen() {
  const [input, setInput] = useState('');
  const { messages, isGenerating, addMessage, appendToLastMessage, setGenerating, clearMessages } = useChatStore();
  const flatListRef = useRef<FlatList>(null);

  // 语音输入
  const {
    isListening,
    transcript: voiceTranscript,
    toggleListening,
    isAvailable: voiceAvailable,
  } = useVoiceInput({
    language: 'zh-CN',
    onResult: (text) => {
      setInput(text);
    },
    onError: (err) => {
      Alert.alert('语音识别失败', err);
    },
  });

  const handleSend = useCallback(async () => {
    const question = input.trim();
    if (!question || isGenerating) return;

    // 如果正在录音，先停止
    if (isListening) {
      await toggleListening();
    }

    // 添加用户消息
    const userMsg = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: question,
      timestamp: new Date().toLocaleTimeString(),
    };
    addMessage(userMsg);
    setInput('');

    // 添加 AI 占位消息
    const aiMsg = {
      id: (Date.now() + 1).toString(),
      role: 'assistant' as const,
      content: '',
      timestamp: new Date().toLocaleTimeString(),
      isStreaming: true,
    };
    addMessage(aiMsg);
    setGenerating(true);

    try {
      // 使用 SSE 流式输出
      const token = await api.getToken();
      const response = await fetch(`${process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api'}/stream/tutor`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ question, subject: '智能辅导' }),
      });

      if (!response.ok) {
        throw new Error('请求失败');
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('无法读取响应');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === 'text_delta' && data.content) {
              appendToLastMessage(data.content);
            } else if (data.type === 'complete') {
              // 流结束
            } else if (data.type === 'error') {
              appendToLastMessage(`\n\n${data.message || '生成失败'}`);
            }
          } catch {
            // skip malformed lines
          }
        }
      }
    } catch (err: any) {
      appendToLastMessage(`\n\n${err.message || '网络错误，请确认后端服务已启动'}`);
    } finally {
      setGenerating(false);
    }
  }, [input, isGenerating, isListening, addMessage, appendToLastMessage, setGenerating, toggleListening]);

  return (
    <KeyboardAvoidingView
      className="flex-1 bg-primary"
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={0}
    >
      {/* Header */}
      <View className="px-4 pt-16 pb-3 bg-primary-light border-b border-border">
        <View className="flex-row items-center justify-between">
          <View>
            <Text className="text-text-primary text-xl font-bold">智能辅导</Text>
            <Text className="text-text-secondary text-xs mt-1">
              {isGenerating ? 'AI 正在思考...' : isListening ? '正在聆听...' : '随时提问，即时解答'}
            </Text>
          </View>
          {messages.length > 0 && (
            <Text
              className="text-accent text-sm"
              onPress={() => clearMessages()}
            >
              清空
            </Text>
          )}
        </View>
      </View>

      {/* 消息列表 */}
      {messages.length === 0 ? (
        <View className="flex-1 items-center justify-center px-8">
          <Text className="text-5xl mb-4">💬</Text>
          <Text className="text-text-primary text-lg font-bold mb-2">
            有什么想问的？
          </Text>
          <Text className="text-text-secondary text-center leading-6">
            我可以帮你解答学习问题、解释概念、提供示例代码等
          </Text>
          {voiceAvailable && (
            <Text className="text-text-muted text-xs mt-4">
              点击 🎤 按钮使用语音输入
            </Text>
          )}
          <View className="mt-6 w-full">
            {['什么是快速排序？', '解释二叉树的遍历', '帮我理解递归'].map((q) => (
              <Text
                key={q}
                className="text-accent bg-surface rounded-xl px-4 py-3 mb-2 text-sm"
                onPress={() => {
                  setInput(q);
                }}
              >
                {q}
              </Text>
            ))}
          </View>
        </View>
      ) : (
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <ChatBubble
              role={item.role}
              content={item.content}
              timestamp={item.timestamp}
              isStreaming={item.isStreaming}
            />
          )}
          contentContainerStyle={{ padding: 16 }}
          onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        />
      )}

      {/* 输入框（带语音按钮） */}
      <ChatInput
        value={input}
        onChangeText={setInput}
        onSend={handleSend}
        disabled={isGenerating}
        onVoicePress={voiceAvailable ? toggleListening : undefined}
        isListening={isListening}
        voiceTranscript={voiceTranscript}
      />
    </KeyboardAvoidingView>
  );
}
