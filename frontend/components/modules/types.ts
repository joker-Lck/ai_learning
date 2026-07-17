// 共享类型定义

export type ModuleType = 'profile' | 'resources' | 'path' | 'tutor' | 'assessment' | 'rag' | 'collaboration' | null;

export interface NavigationContext {
  subject?: string;
  topic?: string;
  learningGoal?: string;
  tutorSubject?: string;
  autoPlan?: boolean;
  autoGenerate?: boolean;
}

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
  diagram?: string | Record<string, any>;
  example?: string | Record<string, any>;
  timestamp: Date;
  evidence_chain?: Array<{
    hop: number;
    doc_id: number;
    title: string;
    content: string;
    score: number;
    relation: string;
  }>;
  logic_graph?: {
    nodes: Array<{ id: string; label: string; type: string }>;
    edges: Array<{ source: string; target: string; relation: string }>;
  };
  confidence?: number;
  hops_used?: number;
}

export interface AssessmentDimension {
  name: string;
  score: number;
  max_score: number;
  level: string;
  feedback: string;
}

export interface KnowledgeMastery {
  overall_score: number;
  topics: Record<string, number>;
}

export interface SkillProgress {
  improvement_areas: string[];
  progress_rate: number;
}

export interface AssessmentResult {
  overall_score: number;
  grade: string;
  dimensions: AssessmentDimension[];
  knowledge_mastery: KnowledgeMastery;
  skill_progress: SkillProgress;
  engagement_level: number;
  time_investment: number;
  strengths: string[];
  weaknesses: string[];
  improvements: string[];
  recommendations: string[];
  recommendation: string;
  next_focus: string[];
  motivational_message: string;
  assessment_type?: string;
  period_start?: string;
  period_end?: string;
  generated_at?: string;
  grade_trend?: string;
  analysis_summary?: string;
  raw_data?: {
    grades?: Array<{ course_name: string; score: number; semester: string }>;
    grade_trend?: Array<{ course: string; score: number; semester: string }>;
    error_notes_count?: number;
    courses_count?: number;
    plans_count?: number;
  };
}

export interface ProfileDimension {
  id: string;
  title: string;
  icon: any;
  color: string;
  questions: string[];
  placeholder: string;
}

// ==================== 学生数据管理类型 ====================

export interface CourseItem {
  name: string;
  day: string;         // 周一~周日
  start_time: string;  // HH:MM
  end_time: string;
  location?: string;
  teacher?: string;
}

export interface CourseSchedule {
  id?: number;
  semester: string;
  courses: CourseItem[];
}

export interface GradeItem {
  id?: number;
  semester: string;
  course_name: string;
  score: number | null;
  credits?: number | null;
  grade_type?: string;  // exam/quiz/homework/overall
  exam_date?: string;
}

export interface ErrorNote {
  id?: number;
  subject: string;
  chapter?: string;
  question: string;
  my_answer?: string;
  correct_answer?: string;
  error_reason?: string;
  tags?: string[];
  mastery?: number;  // 0 or 1
  created_at?: string;
}

export interface StudyPlan {
  id?: number;
  semester: string;
  plan_type: string;  // weekly/exam/custom
  plan_data: StudyPlanData;
  status?: string;
  created_at?: string;
}

export interface StudyPlanData {
  title: string;
  summary: string;
  total_days: number;
  daily_plans: DailyPlan[];
  focus_areas: string[];
  tips: string[];
  raw_text?: string;
}

export interface DailyPlan {
  day: string;
  tasks: PlanTask[];
}

export interface PlanTask {
  time: string;
  subject: string;
  task: string;
  type: string;  // 复习/预习/练习/备考
}

export type ProfileTab = 'profile' | 'schedule' | 'grades' | 'errors';
