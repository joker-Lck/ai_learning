/**
 * Kimi AI API 客户端 - 前端直接调用AI
 */

const KIMI_API_KEY = process.env.NEXT_PUBLIC_KIMI_API_KEY || '';
const KIMI_API_URL = process.env.NEXT_PUBLIC_KIMI_API_URL || 'https://api.moonshot.cn/v1';

/**
 * 调用Kimi API生成内容
 */
export async function callKimiAPI(
  prompt: string,
  options?: {
    maxTokens?: number;
    temperature?: number;
    systemPrompt?: string;
  }
): Promise<string> {
  const {
    maxTokens = 2000,
    temperature = 0.7,
    systemPrompt
  } = options || {};

  try {
    const messages: any[] = [];
    
    if (systemPrompt) {
      messages.push({ role: 'system', content: systemPrompt });
    }
    
    messages.push({ role: 'user', content: prompt });

    const response = await fetch(`${KIMI_API_URL}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${KIMI_API_KEY}`
      },
      body: JSON.stringify({
        model: 'moonshot-v1-8k',
        messages,
        max_tokens: maxTokens,
        temperature,
      })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error?.message || `API请求失败: ${response.status}`);
    }

    const data = await response.json();
    return data.choices[0].message.content;

  } catch (error: any) {
    console.error('Kimi API调用失败:', error);
    throw error;
  }
}

/**
 * 生成思维导图数据
 */
export async function generateMindmap(subject: string, topic: string, difficulty: string) {
  const prompt = `请为${subject}课程的"${topic}"主题生成一个知识点思维导图。

难度级别: ${difficulty}

要求:
1. 包含核心概念和子知识点
2. 层次分明,逻辑清晰
3. 标注重点和难点
4. 使用树状结构表示
5. 确保知识点准确性

输出JSON格式(不要包含其他文字):
{
  "title": "思维导图标题",
  "root": {
    "name": "${topic}",
    "children": [
      {
        "name": "分支1",
        "children": [
          {"name": "子节点1"},
          {"name": "子节点2"}
        ]
      }
    ]
  },
  "key_concepts": ["概念1", "概念2"],
  "difficulty_marks": {"节点名称": "easy/medium/hard"}
}
`;

  const response = await callKimiAPI(prompt, { maxTokens: 1500 });
  
  // 解析JSON
  const jsonMatch = response.match(/\{[\s\S]*\}/);
  if (jsonMatch) {
    try {
      return JSON.parse(jsonMatch[0]);
    } catch (e) {
      console.error('JSON解析失败:', e);
      return { title: `${topic}思维导图`, root: { name: topic, children: [] } };
    }
  }
  
  return { title: `${topic}思维导图`, root: { name: topic, children: [] } };
}

/**
 * 生成练习题目
 */
export async function generateQuiz(subject: string, topic: string, difficulty: string) {
  const prompt = `请为${subject}课程的"${topic}"主题生成一套练习题。

难度级别: ${difficulty}

要求:
1. 包含选择题(5题)、填空题(3题)、解答题(2题)
2. 每道题提供详细解析
3. 标注每题的难度和考察知识点
4. 确保答案准确无误

输出JSON格式(不要包含其他文字):
{
  "title": "${topic}练习题",
  "questions": [
    {
      "id": 1,
      "type": "multiple_choice",
      "question": "题目内容",
      "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
      "answer": "A",
      "explanation": "详细解析",
      "difficulty": "easy/medium/hard",
      "knowledge_point": "考察知识点"
    }
  ],
  "total_questions": 10,
  "estimated_time": 20
}
`;

  const response = await callKimiAPI(prompt, { maxTokens: 2500 });
  
  const jsonMatch = response.match(/\{[\s\S]*\}/);
  if (jsonMatch) {
    try {
      return JSON.parse(jsonMatch[0]);
    } catch (e) {
      console.error('JSON解析失败:', e);
      return { title: `${topic}练习题`, questions: [] };
    }
  }
  
  return { title: `${topic}练习题`, questions: [] };
}

/**
 * 生成课程文档
 */
export async function generateDocument(subject: string, topic: string, difficulty: string) {
  const prompt = `请为${subject}课程的"${topic}"主题生成一份详细的讲解文档。

难度级别: ${difficulty}

要求:
1. 结构清晰,包含:引言、核心概念、详细讲解、实例分析、总结
2. 使用Markdown格式
3. 确保内容准确,避免绝对化表述
4. 长度适中,约800-1200字

输出JSON格式(不要包含其他文字):
{
  "title": "文档标题",
  "sections": [
    {
      "heading": "章节标题",
      "content": "章节内容(Markdown格式)"
    }
  ],
  "key_points": ["关键点1", "关键点2"],
  "estimated_reading_time": 15,
  "references": ["参考资料1"]
}
`;

  const response = await callKimiAPI(prompt, { maxTokens: 2000 });
  
  const jsonMatch = response.match(/\{[\s\S]*\}/);
  if (jsonMatch) {
    try {
      return JSON.parse(jsonMatch[0]);
    } catch (e) {
      console.error('JSON解析失败:', e);
      return { title: `${topic}讲解文档`, sections: [] };
    }
  }
  
  return { title: `${topic}讲解文档`, sections: [] };
}

/**
 * 构建学生画像（基于对话记录）
 */
export async function buildStudentProfile(conversationLog: Array<{role: string, content: string}>) {
  const conversationText = conversationLog.map(msg => `${msg.role === 'user' ? '学生' : '助手'}: ${msg.content}`).join('\n');
  
  const prompt = `根据以下师生对话记录，分析并构建学生画像。

对话记录:
${conversationText}

请提取以下信息并以JSON格式输出(不要包含其他文字):
{
  "major": "专业名称",
  "grade_level": "年级",
  "knowledge_base": "知识基础描述",
  "cognitive_style": "认知风格(如:视觉型/听觉型/实践型)",
  "learning_goals": "学习目标",
  "weak_points": ["薄弱点1", "薄弱点2"],
  "interest_areas": ["兴趣领域1", "兴趣领域2"],
  "preferred_resources": ["偏好的资源类型"],
  "summary": "用Markdown格式撰写的学生画像综合分析报告。包含：## 学生概况（基本信息一句话总结）、## 学习特征分析（认知风格与学习偏好）、## 知识掌握评估（基础水平与薄弱环节）、## 个性化建议（针对该学生的3-5条具体学习建议）。内容要专业、有温度、有针对性，约300-500字。"
}
`;

  const response = await callKimiAPI(prompt, { maxTokens: 2000 });
  
  const jsonMatch = response.match(/\{[\s\S]*\}/);
  if (jsonMatch) {
    try {
      return JSON.parse(jsonMatch[0]);
    } catch (e) {
      console.error('JSON解析失败:', e);
      return {};
    }
  }
  
  return {};
}

/**
 * AI辅导答疑
 */
export async function tutorAnswer(question: string, subject: string, preferredFormat?: string) {
  const systemPrompt = `你是一位专业的${subject}课程辅导老师。你的任务是帮助学生解答问题，提供清晰、准确、易懂的解释。`;
  
  const formatHint = preferredFormat ? `

学生偏好的回答格式: ${preferredFormat}
- 如果偏好"图解"，请用文字描述图表结构
- 如果偏好"代码示例"，请提供相关代码
- 如果偏好"详细解释"，请给出深入的分析
` : '';

  const prompt = `学生问题: ${question}${formatHint}

请提供:
1. 直接的答案或解释
2. 相关的知识点说明
3. 如果有必要，提供示例或类比
4. 确保内容准确、易懂

请以JSON格式输出(不要包含其他文字):
{
  "text_answer": "详细的文本回答",
  "diagram": "如果需要图表，用文字描述图表结构，否则为空字符串",
  "code_example": "如果有代码示例，提供代码，否则为空字符串",
  "key_points": ["关键点1", "关键点2"]
}
`;

  const response = await callKimiAPI(prompt, { 
    maxTokens: 1500,
    systemPrompt 
  });
  
  const jsonMatch = response.match(/\{[\s\S]*\}/);
  if (jsonMatch) {
    try {
      return JSON.parse(jsonMatch[0]);
    } catch (e) {
      console.error('JSON解析失败:', e);
      return { text_answer: response, diagram: '', code_example: '', key_points: [] };
    }
  }
  
  return { text_answer: response, diagram: '', code_example: '', key_points: [] };
}

/**
 * 生成个性化学习路径
 */
export async function generateLearningPath(learningGoal: string, profile?: any) {
  const profileInfo = profile ? `
学生画像:
- 专业: ${profile.major || '未知'}
- 年级: ${profile.grade_level || '未知'}
- 知识基础: ${profile.knowledge_base || '未知'}
- 薄弱点: ${profile.weak_points?.join(', ') || '无'}
- 兴趣领域: ${profile.interest_areas?.join(', ') || '无'}
` : '';

  const prompt = `请为以下学习目标制定一个个性化的学习路径。

学习目标: ${learningGoal}
${profileInfo}

要求:
1. 将目标分解为多个阶段，每个阶段有明确的学习内容和时间安排
2. 考虑学生的基础和兴趣，推荐合适的学习资源
3. 设置阶段性目标和评估方式
4. 提供学习建议和鼓励

请以JSON格式输出(不要包含其他文字):
{
  "goal": "学习目标",
  "estimated_duration": "预计总时长(如: 8周)",
  "phases": [
    {
      "phase_number": 1,
      "title": "阶段标题",
      "duration": "阶段时长(如: 2周)",
      "description": "阶段描述",
      "topics": ["知识点1", "知识点2"],
      "resources": ["推荐资源1", "推荐资源2"],
      "milestone": "阶段性目标"
    }
  ],
  "recommendations": ["学习建议1", "学习建议2"],
  "tips": "额外的学习提示"
}
`;

  const response = await callKimiAPI(prompt, { maxTokens: 2000 });
  
  const jsonMatch = response.match(/\{[\s\S]*\}/);
  if (jsonMatch) {
    try {
      return JSON.parse(jsonMatch[0]);
    } catch (e) {
      console.error('JSON解析失败:', e);
      return { goal: learningGoal, phases: [] };
    }
  }
  
  return { goal: learningGoal, phases: [] };
}
