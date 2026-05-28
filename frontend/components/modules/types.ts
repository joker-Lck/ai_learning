// 共享类型定义

export type ModuleType = 'profile' | 'resources' | 'path' | 'tutor' | 'assessment' | null;

export interface DimensionChat {
  dimensionId: string;
  messages: Array<{ role: 'user' | 'assistant'; content: string }>;
  completed: boolean;
}

export interface ProfileData {
  knowledge_base: any;
  cognitive_style: string;
  learning_goals: any;
  weak_points: string[];
  learning_history: any[];
  interest_areas: string[];
  preferred_resources: string[];
  major: string;
  grade_level: string;
  update_time?: string;
}

export interface ResourceItem {
  type: string;
  title: string;
  content_data?: any;
  status: 'generating' | 'complete' | 'error';
}

export interface PathStep {
  step_number: number;
  title: string;
  description: string;
  estimated_time: string;
  resources: string[];
  prerequisites: string[];
}

export interface LearningPath {
  goal: string;
  total_steps: number;
  estimated_duration: string;
  steps: PathStep[];
}

export interface TutorMessage {
  role: 'user' | 'assistant';
  content: string;
  diagram?: string;
  example?: string;
  timestamp: Date;
}

export interface AssessmentResult {
  overall_score: number;
  dimensions: Array<{
    name: string;
    score: number;
    max_score: number;
    level: string;
    feedback: string;
  }>;
  strengths: string[];
  improvements: string[];
  recommendations: string[];
}

export interface ProfileDimension {
  id: string;
  title: string;
  icon: any;
  color: string;
  questions: string[];
  placeholder: string;
}
