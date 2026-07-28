/**
 * 学习能力雷达图 — 9 维度版本
 * 对应学生画像 9 个维度：知识基础、认知风格、学习目标、薄弱环节、学习历史、兴趣领域、资源偏好、专业、年级
 */

export interface RadarDimension {
  dimension: string;
  value: number;
  fullMark: number;
}

interface ProfileLike {
  knowledge_base?: any;
  cognitive_style?: string | string[];
  learning_goals?: any;
  weak_points?: string[] | string;
  learning_history?: any[];
  interest_areas?: string[];
  preferred_resources?: string[];
  major?: string;
  grade_level?: string;
  summary?: string;
}

const LEVEL_MAP: Record<string, number> = {
  '入门': 1, 'beginner': 1, '初级': 2, '基础': 2, '中级': 3, '中等': 3,
  '高级': 4, '精通': 5, 'advanced': 4,
};

const GRADE_MAP: Record<string, number> = {
  '大一': 2, '大二': 3, '大三': 4, '大四': 4, '大四及以上': 4,
  '研究生': 5, '硕士': 5, '博士': 5,
};

const DEFAULTS: RadarDimension[] = [
  { dimension: '知识基础', value: 3, fullMark: 5 },
  { dimension: '认知风格', value: 3, fullMark: 5 },
  { dimension: '学习目标', value: 3, fullMark: 5 },
  { dimension: '兴趣领域', value: 3, fullMark: 5 },
  { dimension: '资源偏好', value: 3, fullMark: 5 },
  { dimension: '学习历史', value: 3, fullMark: 5 },
  { dimension: '薄弱环节', value: 3, fullMark: 5 },
  { dimension: '学习广度', value: 3, fullMark: 5 },
  { dimension: '学习阶段', value: 3, fullMark: 5 },
];

function clamp(v: number): number {
  return Math.max(1, Math.min(5, v));
}

// 1. 知识基础
function scoreKnowledge(profile: ProfileLike): number {
  const kb = profile.knowledge_base;
  if (!kb) return 2;
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

// 2. 认知风格
function scoreCognitive(profile: ProfileLike): number {
  const cs = profile.cognitive_style;
  if (!cs) return 2;
  const arr = Array.isArray(cs) ? cs : [cs];
  if (arr.length === 0) return 2;
  let s = 3;
  if (arr.some(c => c.includes('深度') || c.includes('专注'))) s = 4;
  if (arr.some(c => c.includes('探索') || c.includes('全局'))) s = 4;
  if (arr.length >= 3) s = clamp(s + 1);
  return s;
}

// 3. 学习目标
function scoreGoals(profile: ProfileLike): number {
  const goals = profile.learning_goals;
  if (!goals) return 2;
  if (Array.isArray(goals) && goals.length > 0) return clamp(2 + goals.length);
  if (typeof goals === 'string' && goals.length > 10) return 4;
  if (typeof goals === 'string' && goals.length > 0) return 3;
  return 2;
}

// 4. 兴趣领域
function scoreInterests(profile: ProfileLike): number {
  const areas = profile.interest_areas;
  if (!Array.isArray(areas) || areas.length === 0) return 2;
  if (areas.length >= 5) return 5;
  if (areas.length >= 3) return 4;
  if (areas.length >= 2) return 3;
  return 2;
}

// 5. 资源偏好
function scoreResources(profile: ProfileLike): number {
  const prefs = profile.preferred_resources;
  if (!Array.isArray(prefs) || prefs.length === 0) return 2;
  let s = 3;
  if (prefs.some(p => ['计划', '规划', '定时'].some(k => p.includes(k)))) s = 4;
  if (prefs.length >= 3) s = clamp(s + 1);
  return s;
}

// 6. 学习历史
function scoreHistory(profile: ProfileLike): number {
  const h = profile.learning_history;
  if (!Array.isArray(h) || h.length === 0) return 2;
  if (h.length > 20) return 5;
  if (h.length > 10) return 4;
  if (h.length > 3) return 3;
  return 2;
}

// 7. 薄弱环节（反向：薄弱点越少分越高）
function scoreWeakness(profile: ProfileLike): number {
  const weak = profile.weak_points;
  if (!weak) return 3;
  const arr = Array.isArray(weak) ? weak : [weak];
  if (arr.length === 0) return 5;
  if (arr.length <= 1) return 4;
  if (arr.length <= 3) return 3;
  return 2;
}

// 8. 学习广度（兴趣 + 资源偏好 + 认知风格综合）
function scoreBreadth(profile: ProfileLike): number {
  let count = 0;
  if (Array.isArray(profile.interest_areas) && profile.interest_areas.length > 0) count++;
  if (Array.isArray(profile.preferred_resources) && profile.preferred_resources.length > 0) count++;
  if (profile.cognitive_style) count++;
  if (Array.isArray(profile.learning_goals) && profile.learning_goals.length > 0) count++;
  if (profile.knowledge_base) count++;
  return clamp(count + 1);
}

// 9. 学习阶段（年级 + 专业填充度）
function scoreStage(profile: ProfileLike): number {
  let s = 2;
  if (profile.grade_level) {
    for (const [k, v] of Object.entries(GRADE_MAP)) {
      if (profile.grade_level.includes(k)) { s = v; break; }
    }
  }
  if (profile.major && profile.major.length > 0) s = clamp(s + 1);
  return s;
}

export function computeRadarData(profile: ProfileLike | null): RadarDimension[] {
  if (!profile) return DEFAULTS;

  return [
    { dimension: '知识基础', value: clamp(scoreKnowledge(profile)), fullMark: 5 },
    { dimension: '认知风格', value: clamp(scoreCognitive(profile)), fullMark: 5 },
    { dimension: '学习目标', value: clamp(scoreGoals(profile)), fullMark: 5 },
    { dimension: '兴趣领域', value: clamp(scoreInterests(profile)), fullMark: 5 },
    { dimension: '资源偏好', value: clamp(scoreResources(profile)), fullMark: 5 },
    { dimension: '学习历史', value: clamp(scoreHistory(profile)), fullMark: 5 },
    { dimension: '薄弱环节', value: clamp(scoreWeakness(profile)), fullMark: 5 },
    { dimension: '学习广度', value: clamp(scoreBreadth(profile)), fullMark: 5 },
    { dimension: '学习阶段', value: clamp(scoreStage(profile)), fullMark: 5 },
  ];
}
