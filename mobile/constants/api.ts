import Constants from 'expo-constants';

const ENV_API_URL = process.env.EXPO_PUBLIC_API_URL;

export const API_BASE = ENV_API_URL || 'http://localhost:8000/api';

export const TIMEOUT = {
  default: 30000,
  upload: 60000,
  ai: 120000,
  stream: 180000,
};

export const RETRY = {
  maxRetries: 2,
  baseDelay: 1000,
};

export const APP_CONFIG = {
  name: 'AI学习智能体',
  version: '1.0.0',
};
