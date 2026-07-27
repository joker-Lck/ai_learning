# 移动端开发指南

## 技术选型

| 技术 | 版本 | 用途 |
|------|------|------|
| React Native | 0.76+ | 跨平台移动框架 |
| Expo | 52+ | 开发工具链 |
| Expo Router | 4.0+ | 文件系统路由 |
| NativeWind | 4.0+ | Tailwind CSS for RN |
| Zustand | 4.5+ | 状态管理 |
| Victory Native | 41+ | 数据可视化 |
| React Native Reanimated | 3.16+ | 动画 |

## 项目结构

```
mobile/
├── app/                    # Expo Router 页面
│   ├── _layout.tsx         # 根布局
│   ├── (auth)/             # 认证页面
│   ├── (tabs)/             # Tab 导航页面
│   └── resource/[id].tsx   # 动态路由
├── components/             # 可复用组件
│   ├── ui/                 # 基础 UI 组件
│   ├── chat/               # 聊天组件
│   ├── dashboard/          # 工作台组件
│   └── profile/            # 画像组件
├── lib/                    # 工具库
│   ├── api.ts              # API 客户端
│   ├── auth.ts             # 认证工具
│   └── storage.ts          # 本地存储
├── stores/                 # Zustand 状态管理
├── hooks/                  # 自定义 Hooks
├── constants/              # 常量配置
└── assets/                 # 静态资源
```

## 开发流程

### 1. 环境准备

```bash
# 安装 Node.js 18+
# 安装 Expo CLI
npm install -g expo-cli

# 进入项目目录
cd mobile

# 安装依赖
npm install
```

### 2. 启动开发服务器

```bash
npx expo start
```

- 使用 Expo Go 扫码在真机测试
- 使用 Android Studio / Xcode 模拟器测试

### 3. API 客户端

API 客户端从 Web 端 `frontend/lib/api.ts` 移植，主要改动：

- 用 `expo-secure-store` 替代 `localStorage`
- 用 Expo Router 替代 `window.location.href`
- 添加离线缓存支持

### 4. 状态管理

使用 Zustand，与 Web 端共享状态管理逻辑：

- `useAuthStore` — 认证状态
- `useChatStore` — 聊天状态
- `useUIStore` — UI 状态

### 5. 样式方案

使用 NativeWind（Tailwind CSS for React Native）：

```tsx
import { styled } from 'nativewind';

const StyledView = styled(View);
const StyledText = styled(Text);

function MyComponent() {
  return (
    <StyledView className="flex-1 bg-primary p-4">
      <StyledText className="text-white text-lg font-bold">
        Hello World
      </StyledText>
    </StyledView>
  );
}
```

## 功能模块

### 工作台

- 统计卡片（学习天数/时长/资源数/薄弱项）
- 最近生成资源列表（FlatList + 无限滚动）
- 今日建议（v8.1 升级：AI 学习规划师，分类标签——薄弱/复习/规划/策略）
- 协同动态（活动日志流）

### 学生画像

- 对话式画像构建（聊天界面）
- 9 维度雷达图（victory-native）
- 课程表管理（周视图 + CRUD）
- 成绩管理（列表 + 图表）
- 错题本（两步式极简录入 + 拍照识别 + 标记掌握）

### 学习资源

- 学科/主题选择器
- 7 种资源类型选择（多选卡片）
- 难度级别滑块
- SSE 流式生成进度
- 资源预览（Markdown 渲染）

### 学习路径

- 学习目标输入
- 路径可视化（步骤时间线）
- 进度跟踪（进度条 + 完成状态）

### 智能辅导

- 聊天界面（消息气泡 + 打字机效果）
- SSE 流式输出
- 学科选择器
- Mermaid 图表渲染（WebView 嵌入）
- 代码高亮显示

### 效果评估

- 评估类型选择
- 多维度评分雷达图
- 改进建议列表

### 知识库

- 文档上传（expo-document-picker）
- 文档列表（分页）
- 搜索功能

## 导航结构

```
Tab Navigator (底部导航)
├── 工作台 (Home icon)
├── 辅导 (Chat icon)
├── 资源 (Book icon)
└── 我的 (User icon)
    ├── 学生画像
    ├── 学习路径
    ├── 效果评估
    ├── 知识库
    └── 设置
```

## 构建发布

### 开发构建

```bash
# Android
npx expo run:android

# iOS
npx expo run:ios
```

### 生产构建

```bash
# 安装 EAS CLI
npm install -g eas-cli

# 配置 EAS
eas build:configure

# 构建 Android APK
eas build --platform android --profile preview

# 构建 iOS IPA
eas build --platform ios --profile production
```

## 注意事项

1. **SSE 兼容性**：React Native 的 `fetch` 支持 ReadableStream，但需要 polyfill
2. **文件上传**：使用 `expo-document-picker` 和 `expo-image-picker`
3. **本地存储**：使用 `expo-secure-store` 存储敏感信息（Token）
4. **图表渲染**：使用 Victory Native，不支持 Mermaid（需 WebView 嵌入）
5. **Markdown 渲染**：使用 `react-native-markdown-display`
