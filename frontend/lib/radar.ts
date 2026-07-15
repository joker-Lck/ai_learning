/**
 * 学习能力雷达图 — 共享评分逻辑
 * 工作台和学生画像页面使用同一套计算规则
 */

export interface RadarDimension {
  dimension: string;
  value: number;
  fullMark: number;
}

interface ProfileLike {
  knowledge_base?: any;
  learning_goals?: any;
  learning_history?: any[];
  preferred_resources?: string[];
  cognitive_style?: string;
  interest_areas?: string[];
  weak_points?: string[];
}

const LEVEL_MAP: Record<string, number> = {
  '入门': 1, '初级': 2, '基础': 2, '中级': 3, '中等': 3, '高级': 4, '精通': 5,
};

const DEFAULTS: RadarDimension[] = [
  { dimension: '知识基础', value: 3, fullMark: 5 },
  { dimension: '学习目标', value: 3, fullMark: 5 },
  { dimension: '记忆能力', value: 3, fullMark: 5 },
  { dimension: '自控力', value: 3, fullMark: 5 },
  { dimension: '专注度', value: 3, fullMark: 5 },
  { dimension: '学习深度', value: 3, fullMark: 5 },
];

function clamp(v: number): number {
  return Math.max(1, Math.min(5, v));
}

function scoreKnowledge(profile: ProfileLike): number {
  const kb = profile.knowledge_base;
  if (!kb) return 3;
  if (typeof kb === 'object' && kb.level) {
    return LEVEL_MAP[kb.level] ?? (kb.topics?.length > 5 ? 4 : kb.topics?.length > 2 ? 3 : 2);
  }
  if (typeof kb === 'string') {
    for (const [k, v] of Object.entries(LEVEL_MAP)) {
      if (kb.includes(k)) return v;
    }
  }
  return 3;
}

function scoreGoals(profile: ProfileLike): number {
  const goals = profile.learning_goals;
  if (!goals) return 3;
  if (Array.isArray(goals) && goals.length > 0) return clamp(2 + goals.length);
  if (typeof goals === 'string' && goals.length > 10) return 4;
  if (typeof goals === 'string' && goals.length > 0) return 3;
  return 3;
}

function scoreMemory(profile: ProfileLike): number {
  const h = profile.learning_history;
  if (!Array.isArray(h)) return 3;
  if (h.length > 20) return 5;
  if (h.length > 10) return 4;
  if (h.length > 3) return 3;
  return 2;
}

function scoreSelfControl(profile: ProfileLike): number {
  const prefs = profile.preferred_resources;
  if (!Array.isArray(prefs)) return 3;
  let s = 3;
  if (prefs.some(p => ['计划', '规划', '定时'].some(k => p.includes(k)))) s = 4;
  if (prefs.length >= 3) s = clamp(s + 1);
  return s;
}

function scoreFocus(profile: ProfileLike): number {
  const cs = profile.cognitive_style;
  if (!cs) return 3;
  if (cs.includes('深度') || cs.includes('专注')) return 4;
  if (cs.includes('视觉') || cs.includes('动觉')) return 3;
  if (cs.includes('听觉')) return 3;
  return 3;
}

function scoreDepth(profile: ProfileLike): number {
  const interests = profile.interest_areas;
  const weak = profile.weak_points;
  let s = 3;
  if (Array.isArray(interests) && interests.length > 3) s = 4;
  if (Array.isArray(interests) && interests.length > 6) s = 5;
  if (Array.isArray(weak) && weak.length > 3) s = clamp(s - 1);
  return s;
}

export function computeRadarData(profile: ProfileLike | null): RadarDimension[] {
  if (!profile) return DEFAULTS;

  return [
    { dimension: '知识基础', value: clamp(scoreKnowledge(profile)), fullMark: 5 },
    { dimension: '学习目标', value: clamp(scoreGoals(profile)), fullMark: 5 },
    { dimension: '记忆能力', value: clamp(scoreMemory(profile)), fullMark: 5 },
    { dimension: '自控力', value: clamp(scoreSelfControl(profile)), fullMark: 5 },
    { dimension: '专注度', value: clamp(scoreFocus(profile)), fullMark: 5 },
    { dimension: '学习深度', value: clamp(scoreDepth(profile)), fullMark: 5 },
  ];
}
