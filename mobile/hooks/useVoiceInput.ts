import { useState, useEffect, useCallback, useRef } from 'react';
import { Platform, Alert } from 'react-native';

interface UseVoiceInputOptions {
  language?: string;
  onResult?: (text: string) => void;
  onError?: (error: string) => void;
}

interface UseVoiceInputReturn {
  isListening: boolean;
  transcript: string;
  startListening: () => Promise<void>;
  stopListening: () => Promise<void>;
  toggleListening: () => Promise<void>;
  isAvailable: boolean;
}

export function useVoiceInput(options: UseVoiceInputOptions = {}): UseVoiceInputReturn {
  const { language = 'zh-CN', onResult, onError } = options;
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isAvailable, setIsAvailable] = useState(false);
  const VoiceRef = useRef<any>(null);

  useEffect(() => {
    // Dynamically import Voice (may not be available on all platforms)
    const initVoice = async () => {
      try {
        const Voice = require('@react-native-voice/voice').default;
        VoiceRef.current = Voice;

        Voice.onSpeechStart = () => {
          setIsListening(true);
        };

        Voice.onSpeechEnd = () => {
          setIsListening(false);
        };

        Voice.onSpeechResults = (e: any) => {
          if (e.value && e.value.length > 0) {
            const text = e.value[0];
            setTranscript(text);
            onResult?.(text);
          }
        };

        Voice.onSpeechError = (e: any) => {
          const errorMsg = e.error?.message || '语音识别失败';
          setIsListening(false);
          onError?.(errorMsg);
        };

        Voice.onSpeechPartialResults = (e: any) => {
          if (e.value && e.value.length > 0) {
            setTranscript(e.value[0]);
          }
        };

        // Check availability
        const available = await Voice.isAvailable();
        setIsAvailable(!!available);
      } catch {
        setIsAvailable(false);
      }
    };

    initVoice();

    return () => {
      if (VoiceRef.current) {
        VoiceRef.current.destroy().catch(() => {});
      }
    };
  }, []);

  const startListening = useCallback(async () => {
    if (!VoiceRef.current) {
      onError?.('语音识别不可用');
      return;
    }

    try {
      setTranscript('');
      await VoiceRef.current.start(language);
      setIsListening(true);
    } catch (err: any) {
      const msg = err.message || '启动语音识别失败';
      onError?.(msg);
      // On web or unsupported platform, show alert
      if (Platform.OS === 'web') {
        Alert.alert('提示', 'Web 端暂不支持语音输入，请使用移动端 App');
      }
    }
  }, [language, onError]);

  const stopListening = useCallback(async () => {
    if (!VoiceRef.current) return;
    try {
      await VoiceRef.current.stop();
      setIsListening(false);
    } catch {
      setIsListening(false);
    }
  }, []);

  const toggleListening = useCallback(async () => {
    if (isListening) {
      await stopListening();
    } else {
      await startListening();
    }
  }, [isListening, startListening, stopListening]);

  return {
    isListening,
    transcript,
    startListening,
    stopListening,
    toggleListening,
    isAvailable,
  };
}
