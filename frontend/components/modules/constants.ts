import {
  User, BookOpen, Brain, Target, Lightbulb, Sparkles,
  Users, Shield, TrendingUp,
} from 'lucide-react';
import type { ProfileDimension } from './types';

export const PROFILE_DIMENSIONS: ProfileDimension[] = [
  {
    id: 'basic_info',
    title: '基本信息',
    icon: User,
    color: 'from-purple-500 to-purple-400',
    questions: ['请问您的专业是什么？', '您目前是大几的学生？'],
    placeholder: '例如：计算机科学与技术，大三'
  },
  {
    id: 'knowledge_base',
    title: '知识基础',
    icon: BookOpen,
    color: 'from-purple-400 to-purple-300',
    questions: ['您对当前学科的基础如何？', '您已经学习了哪些相关课程？'],
    placeholder: '例如：已学习Python、数据结构'
  },
  {
    id: 'cognitive_style',
    title: '认知风格',
    icon: Brain,
    color: 'from-purple-500 to-purple-400',
    questions: ['您更喜欢哪种学习方式？', '喜欢独自学习还是小组讨论？'],
    placeholder: '例如：喜欢看图表和视频'
  },
  {
    id: 'learning_goals',
    title: '学习目标',
    icon: Target,
    color: 'from-purple-400 to-purple-300',
    questions: ['您学习的主要目标是什么？', '希望多长时间达到什么水平？'],
    placeholder: '例如：3个月内掌握机器学习基础'
  },
  {
    id: 'weak_points',
    title: '薄弱点',
    icon: Lightbulb,
    color: 'from-purple-500 to-purple-400',
    questions: ['学习中遇到的最大困难是什么？', '哪些知识点让您困惑？'],
    placeholder: '例如：数学推导感到困难'
  },
  {
    id: 'interest_areas',
    title: '兴趣领域',
    icon: Sparkles,
    color: 'from-purple-400 to-purple-300',
    questions: ['对哪些应用领域感兴趣？', '有没有特别想做的个人项目？'],
    placeholder: '例如：对计算机视觉感兴趣'
  }
];

export const STATS = [
  { label: '多智能体协同', value: '6个', icon: Brain, color: 'text-purple-400' },
  { label: '资源类型', value: '7种', icon: Users, color: 'text-purple-300' },
  { label: '画像维度', value: '8维', icon: Shield, color: 'text-purple-400' },
  { label: '防幻觉机制', value: '3层', icon: TrendingUp, color: 'text-purple-300' },
];
