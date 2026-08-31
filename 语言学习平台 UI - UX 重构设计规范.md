# Verbaia 个人英语学习平台 UI / UX 设计规范

**版本：v1.1 Personal Responsive Final**  
**文档状态：冻结，可直接用于当前项目 UI 开发**  
**适用端：Mobile Web、Tablet Web、Desktop Web**  
**产品范围：单 Owner、英语专项、个人长期使用**

---

## 0. 文档用途与权威性

本文件取代此前面向通用多用户语言平台的 UI / UX 规范，是当前项目唯一正式界面规范。

本次设计目标不是营销获客，也不是普通后台，而是打造一个 Owner 每天愿意打开、可在手机和电脑之间连续学习的英语沉浸式工具。

本文中的“分布式布局”统一解释为 **响应式 / 自适应布局**：

- 手机、平板和电脑共享同一产品、数据和核心能力；
- 不同设备根据屏幕、输入方式和使用场景重新组织布局；
- 不允许把桌面三栏简单缩小塞进手机；
- 不允许移动端缺失核心学习功能；
- 设备切换、刷新和旋转不得丢失学习状态。

如本文件与旧视觉、旧页面或旧讨论冲突，以本文件为准。

---

## 1. 产品定位与范围

产品定位：

> Personal AI-powered English immersive learning workspace.

核心体验：

> 真实英文输入、主动听说读写、清晰进度、长期个性化。

视觉关键词：

```text
Warm
Minimal
Intelligent
Focused
Calm
Premium
Immersive
```

视觉比例：

```text
85% 现代成人教育产品
10% AI 科技感
5% 轻量正反馈
```

### 1.1 必须设计的产品区域

- Login
- Dashboard
- Learn / Journey / Lesson
- Immersion Import 与 Library
- Video Watch / Intensive Listening
- Blind Listening / Dictation
- Shadowing / English Pronunciation
- Video Role Play
- Writing
- Practice
- AI Tutor / Voice Conversation
- Vocabulary
- Progress / Learner Memory
- Settings / Storage
- Light / Dark Theme

### 1.2 明确不设计

- 复杂 Landing Page、Testimonials、Community、Pricing
- 社区、Feed、关注、排行榜和公开评论
- 订阅、支付、套餐和账单
- 多角色 Admin 和组织管理
- 多租户切换
- 复杂通知中心和营销消息
- 非英语学习入口和非英语发音评分
- 儿童化金币、宝箱、宠物和密集 Confetti

根路由行为：

```text
未登录 -> /login
已登录 -> /dashboard
```

无需建设营销首页。

---

## 2. 品牌层

品牌配置不得硬编码在业务组件：

```ts
export const BRAND = {
  name: "Verbaia",
  tagline: "Say hello to the world.",
  product: "Personal English Learning",
}
```

核心品牌文案：

```text
Hello, World.
Say hello to the world.
```

Logo 使用文字标或正式 SVG，不使用 Emoji，不在不同页面改变比例和颜色逻辑。

---

## 3. Design Tokens

所有颜色、字号、间距、圆角、阴影、层级和动画必须由 Token 驱动。业务组件不得大量硬编码 HEX、px 或随机阴影。

### 3.1 Light Theme

```css
:root {
  --color-primary: #5B5CE2;
  --color-primary-hover: #4D4ED1;
  --color-primary-active: #4243BE;
  --color-primary-soft: #EEEEFF;
  --color-on-primary: #FFFFFF;

  --color-success: #58CDB1;
  --color-success-soft: #EAF9F5;
  --color-on-success: #123B32;

  --color-warning: #F6BE4F;
  --color-warning-soft: #FFF7E5;
  --color-on-warning: #442F00;

  --color-danger: #FF8066;
  --color-danger-soft: #FFF0EC;
  --color-on-danger: #57190E;

  --color-info: #5DA9E9;
  --color-info-soft: #EDF6FD;
  --color-on-info: #123B5E;

  --color-background: #F6F7FB;
  --color-surface: #FFFFFF;
  --color-surface-secondary: #F9FAFC;
  --color-text-primary: #161A2B;
  --color-text-secondary: #687086;
  --color-text-tertiary: #687086;
  --color-border: #E8EAF1;
  --color-border-strong: #D8DBE6;
  --color-overlay: rgba(15, 18, 30, 0.48);
  --color-focus: #4546C8;
}
```

### 3.2 Dark Theme

```css
[data-theme="dark"] {
  --color-primary: #8B8DF6;
  --color-primary-hover: #999BF8;
  --color-primary-active: #7A7CE8;
  --color-primary-soft: #272847;
  --color-on-primary: #111226;

  --color-success: #67D8BC;
  --color-success-soft: #19352F;
  --color-on-success: #102E27;

  --color-warning: #F6C768;
  --color-warning-soft: #3A3020;
  --color-on-warning: #382600;

  --color-danger: #FF9A86;
  --color-danger-soft: #3A2421;
  --color-on-danger: #4A1309;

  --color-info: #83C1F2;
  --color-info-soft: #1B3042;
  --color-on-info: #102E46;

  --color-background: #0E1017;
  --color-surface: #171A24;
  --color-surface-secondary: #1E2230;
  --color-text-primary: #F4F5F8;
  --color-text-secondary: #A3AABD;
  --color-text-tertiary: #A3AABD;
  --color-border: #2A3040;
  --color-border-strong: #394154;
  --color-overlay: rgba(0, 0, 0, 0.60);
  --color-focus: #A7A8FF;
}
```

规则：

- Primary 文本与背景组合必须达到 WCAG AA。
- Success、Warning、Danger、Info 不默认使用白字，必须使用对应 `on-*` Token。
- Tertiary 文字不得通过低对比度制造层级；优先用字号、字重和间距。
- 状态不能只靠颜色表达，必须同时有图标、标签或文字。
- Dark Mode 是完整 Theme System，不是页面局部覆盖。

### 3.3 Typography

```css
--font-display: "Sora", "PingFang SC", "Noto Sans SC", sans-serif;
--font-body: "Inter", "PingFang SC", "Noto Sans SC", system-ui, sans-serif;

--text-xs: 12px;
--text-sm: 14px;
--text-base: 16px;
--text-lg: 18px;
--text-xl: 20px;
--text-2xl: 24px;
--text-3xl: 30px;
--text-4xl: 40px;
--text-5xl: 52px;
```

- 字体文件必须随前端自托管，不依赖运行时访问 Google Fonts。
- Mobile 正文和输入框至少 16px，避免 iOS 自动缩放。
- 正文行高 1.5–1.75。
- 桌面长文本每行 60–75 字符；手机每行约 35–60 字符。
- 12px 仅用于非关键 Metadata，不得承载正文、错误或关键操作说明。

### 3.4 Spacing

```css
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
--space-12: 48px;
--space-16: 64px;
--space-20: 80px;
```

统一使用 4 / 8px Grid。优先增加留白，不用装饰填满空间。

### 3.5 Radius、Shadow 与 Layer

```css
--radius-sm: 8px;
--radius-md: 12px;
--radius-lg: 16px;
--radius-xl: 24px;
--radius-full: 999px;

--shadow-sm: 0 1px 2px rgba(15, 18, 30, 0.06);
--shadow-md: 0 8px 24px rgba(15, 18, 30, 0.08);

--z-base: 0;
--z-sticky: 20;
--z-nav: 40;
--z-modal: 100;
--z-toast: 1000;
```

- 默认卡片使用弱边框或 `shadow-sm`，不要边框和重阴影同时堆叠。
- Modal / Drawer 才允许 `shadow-md`。
- 不使用大面积 Glassmorphism、霓虹或多层阴影。

### 3.6 Motion

```css
--motion-fast: 120ms;
--motion-normal: 180ms;
--motion-slow: 240ms;
```

只动画 `transform` 和 `opacity`。动画必须表达状态变化，不得阻塞操作或造成布局跳动。

---

## 4. Icon System

统一使用 Lucide Icons：

- 导航、按钮和状态不使用 Emoji。
- 同层级图标保持统一 stroke、尺寸和对齐。
- Icon-only Button 必须有 `aria-label`、Tooltip 和至少 44×44px 点击区域。
- 手机相邻触控目标间距至少 8px。

Emoji 只允许作为少量内容表达，例如学习连续天数；不能承担唯一状态含义。

---

## 5. 响应式 / 自适应布局系统

### 5.1 断点

```text
xs:   0–639      Phone
sm:   640–767    Large phone / phone landscape
md:   768–1023   Tablet
lg:   1024–1279  Compact desktop / laptop
xl:   1280–1535  Desktop
2xl:  1536+      Large desktop
```

CSS 采用 Mobile First：默认样式为手机，再使用 `md:`、`lg:`、`xl:` 增强。

必须验证：

```text
375 × 812
430 × 932
768 × 1024
1024 × 768
1280 × 800
1440 × 900
```

手机和平板同时验证 portrait 与 landscape。

### 5.2 页面骨架

| Device | Navigation | Content | Secondary content |
|---|---|---|---|
| Phone | Bottom Navigation + compact top bar | Single column | Bottom Sheet / Accordion |
| Tablet | Collapsible Navigation Rail | One or two columns | Inline panel or Sheet |
| Laptop | 220–232px Sidebar | Fluid main | Optional collapsible rail |
| Desktop | 240px Sidebar | Fluid main | Optional 280px right rail |

### 5.3 容器与间距

```text
Phone gutter:       16px
Large phone:        20px
Tablet gutter:      24px
Laptop gutter:      32px
Desktop gutter:     40–48px
Max app content:    1440px
Reading content:    720–840px
Lesson focus area:  840–960px
```

- 页面不得出现整体横向滚动。
- 表格在手机转换为 Card/List；只有无法合理转换的数据表才允许局部横向滚动。
- 使用 `min-height: 100dvh`，不使用会被移动浏览器地址栏破坏的固定 `100vh`。
- Fixed Header、Player Controls 和 Bottom Nav 必须为内容预留空间。
- 使用 `env(safe-area-inset-*)` 保护刘海和手势条。

### 5.4 输入方式适配

Desktop：

- 完整 Keyboard Navigation。
- 视频、听写和跟读提供快捷键。
- Hover 只作为增强，不能成为唯一入口。
- Focus Ring 始终可见。

Mobile / Tablet：

- 所有主要控件至少 44×44px。
- 使用 `touch-action: manipulation`。
- 不依赖 hover。
- 不使用精细拖拽作为唯一操作。
- 麦克风、播放、重播和下一句应在拇指易达区域。
- 软键盘弹起时，听写输入框和提交按钮不得被遮挡。

### 5.5 状态连续性

以下状态在旋转、调整窗口、刷新和返回时必须恢复：

- 当前视频时间与当前句
- 当前训练模式
- Dictation 草稿和已提交结果
- Shadowing 最新录音状态（未提交临时 Blob 可提示丢失）
- Role Play transcript
- Writing 草稿
- 页面滚动和筛选条件

---

## 6. AppShell 与导航

### 6.1 Desktop Sidebar

```text
Verbaia

Dashboard
Learn
Immersion
Practice
AI Tutor
Vocabulary
Progress

Settings
```

- Sidebar 为白色 / Dark Surface，不使用整块高饱和紫色。
- 选中项使用 Primary Soft Background、Primary Icon 和 Primary Text。
- Settings 与主要学习入口保持空间分隔。
- 不显示 Community、Ranking、Reviews、Pricing 或 Admin。

### 6.2 Tablet Navigation Rail

- 768–1023px 默认使用 72–80px Rail。
- 显示 Icon 和可发现的 Label；Label 可在展开时显示，不允许完全无说明。
- 二级入口进入 Drawer 或页面内 Tabs。

### 6.3 Mobile Bottom Navigation

最多五项：

```text
Home
Learn
Immersion
Practice
AI
```

- Icon 与文字同时显示。
- 当前项具有颜色、字重和指示器，不只靠颜色。
- Vocabulary、Progress、Settings 放入 Home 头像菜单或 More Sheet。
- 底栏高度包含 Safe Area；正文底部 Padding 必须覆盖底栏高度。

### 6.4 深层学习页

Lesson、Dictation、Shadowing、Role Play 和 Writing 使用 Focus Mode：

- 隐藏非必要 Sidebar / Right Rail。
- 保留可预测的 Back、当前模式和 Progress。
- Mobile Back 使用顶部明确按钮，同时保持浏览器返回行为。
- 离开未保存内容前提示确认。

---

## 7. Login

不建设复杂营销 Landing Page。

Desktop / Tablet：

```text
Brand + concise learning preview | Login form
```

Mobile：

```text
Logo
Welcome back.
Login form
```

要求：

- 只有 Owner 登录，无注册、邀请、社交登录和套餐入口。
- Email、Password 使用可见 Label，不以 Placeholder 代替。
- 提供 Show / Hide Password、autocomplete 和 Caps Lock 提示。
- 提交时按钮禁用并显示进度。
- 错误显示在字段附近并通过 `role="alert"` 宣告。
- 登录后进入 `/dashboard`。

---

## 8. Dashboard

目标：Owner 登录后 3 秒内知道下一步学什么。

信息优先级：

1. Continue Learning
2. Continue Immersion
3. Today Plan
4. Words / Reviews Due
5. Weekly Progress

Desktop：

```text
Sidebar | Main: Continue + Today Plan | Right Rail: Streak + Goal + Review
```

Tablet：

```text
Rail | Main: Continue + Today Plan
     | Stats 以双列卡片排在下方
```

Mobile：

```text
Greeting
Continue Learning
Continue Immersion
Today Plan horizontal-free list
Compact progress summary
Bottom Navigation
```

禁止顶部堆天气、新闻、社交通知、多个巨大 KPI 或密集成就徽章。

---

## 9. Learn、Journey 与 Lesson

### 9.1 Learning Journey

课程以 CEFR Journey 展示，但当前只展示英语。不同 CEFR Level 有视觉分组，状态同时使用图标和文字：

```text
Completed
Current
Available
Locked
```

Mobile 使用垂直路径，不绘制复杂横向路线。

### 9.2 Lesson Player

```text
Back
Unit / Lesson
Progress
Content
Interaction
Check / Continue
```

- Desktop 最大内容宽度 840–960px。
- Mobile 固定底部 CTA 必须为正文预留空间。
- 一个视图只有一个 Primary CTA。
- 学习过程中不显示无关导航和统计。

---

## 10. Immersion 首页与 Library

Immersion 是产品核心入口，必须进入主导航。

### 10.1 URL-first Import

页面第一视觉区域：

```text
Learn from a real English video

[ Paste a video link........................ ]
[ Import video ]

or upload a file
```

- URL 是第一入口，Upload 是第二入口。
- 输入框有可见 Label 和支持来源说明。
- Import Button 在验证、提交和排队期间显示明确状态。
- Mobile 输入框与按钮纵向堆叠且宽度 100%。
- Desktop 可同一行，但按钮不得压缩输入内容。

### 10.2 Import Progress

显示用户语言，不显示底层 subprocess 文本：

```text
Creating your lesson

✓ Checking the link
✓ Reading video details
● Downloading the video · 42%
○ Finding English subtitles
○ Preparing sentences
○ Creating practice

[ Cancel ]
```

- SSE 断开显示 Reconnecting，不清空现有进度。
- 失败必须显示原因类别、Retry 和 Upload fallback。
- Cancel 是明确的 Secondary / Danger 操作，需确认正在下载的任务。
- Mobile 进度使用纵向 Stepper，不使用过宽 Timeline。

### 10.3 Library

每个视频显示：

```text
Thumbnail
Title / source / duration
Last studied
Overall progress
Watch · Listening · Dictation · Shadowing · Role Play · Writing
Continue
```

Desktop 使用 2–3 列 Card 或紧凑 List；Mobile 固定单列。缩略图必须声明 `aspect-ratio`，避免 CLS。

Empty State：

```text
No videos yet.
Paste an English video link to create your first lesson.
[ Import a video ]
```

---

## 11. Immersion Video Workspace

### 11.1 Desktop

```text
Back + Title + Overall progress

Video (minmax 0, 1fr) | Transcript / Sentence panel (360–420px)

Mode tabs: Watch · Listen · Dictation · Shadow · Role Play · Write
Contextual controls / feedback
```

- 视频保持完整 16:9，不裁掉内容。
- Transcript Panel 可滚动，但避免与页面主滚动形成冲突；桌面可使用固定高度工作区。
- 当前句高亮并自动保持在可见区域，但用户手动滚动后暂停强制跟随。

### 11.2 Tablet

```text
Video full width
Mode controls
Transcript / feedback in lower split panel
```

Landscape 可使用 60/40 双栏；Portrait 使用上下布局。

### 11.3 Mobile

```text
Compact top bar
Sticky 16:9 video
Current sentence
Primary controls
Mode-specific content
Bottom navigation hidden in Focus Mode
```

- 视频不得在未交互时自动播放。
- `playsInline`，用户可主动全屏。
- Video 以下的句子、输入与按钮必须能在单手区域操作。
- Transcript 使用 Bottom Sheet 或内联折叠区，不覆盖正在输入的 Dictation。
- 播放控件不得小于 44×44px，重播当前句是最高频控件。

### 11.4 Player Controls

必须具备：

- Play / Pause
- Replay sentence
- Previous / Next sentence
- Subtitle toggle
- 0.75x / 1x / 1.25x
- Timeline 与当前时间
- Fullscreen
- Volume
- Resume position

Keyboard：

```text
Space      Play / Pause（不在输入框时）
R          Replay sentence
ArrowLeft  Previous sentence
ArrowRight Next sentence
S          Toggle subtitle
```

快捷键必须可发现、可关闭，并避免劫持输入框按键。

---

## 12. Watch 与 Intensive Listening

### Watch

- 正常观看完整视频。
- 英文字幕可切换。
- 当前句高亮。
- 单词点击打开 Vocabulary Popover / Sheet。
- 可收藏句子。

### Intensive Listening

核心循环：

```text
Play -> Pause -> Replay -> Reveal transcript -> Next
```

- Desktop 控件横向排列；Mobile 用两行或 Bottom Action Bar。
- Reveal Transcript 前后状态需要平滑但不拖沓。
- 循环次数使用 Select / Segmented Control，不用微小加减按钮。

---

## 13. Blind Listening / Dictation

默认隐藏字幕。

Desktop：

```text
Video / audio context
Sentence counter
Large text input
Replay controls
Check answer
Token-level diff
```

Mobile：

- 输入区使用至少 3 行 textarea。
- 软键盘弹起时视频可缩为 compact player，但不得完全丢失播放控制。
- Check Answer 使用键盘上方或页面底部可见 CTA，不得被遮挡。
- Enter 不默认提交多行输入；提供明确按钮。

Diff 状态：

```text
Correct
Substitution
Missing
Extra
```

颜色之外必须使用下划线样式、图标或文字标签。结果显示 word accuracy、遗漏和额外词，并提供 Replay、Try again、Next。

---

## 14. Shadowing 与英语发音评分

流程：

```text
Listen
Record
Review recording
Analyze
Feedback
Retry / Next
```

录音前：

- 解释麦克风用途。
- 只在用户点击 Record 后请求权限。
- 权限拒绝时提供浏览器设置指引，不循环弹窗。

录音中：

- 显示明确计时、状态文字和轻量 Waveform。
- Stop 是清晰按钮，不依赖手势。
- 页面切后台时安全停止或提示。

反馈显示：

```text
Overall
Accuracy
Fluency
Completeness
Word issues
Phoneme issues（Provider 实际返回时）
```

- 不显示 Provider 未返回的虚假 Prosody / Phoneme 分数。
- Desktop 反馈可在右栏；Mobile 在录音区下方按重要性展开。
- 分数必须搭配文字解释，不使用纯环形颜色图。
- Retry 为 Primary，Next 为 Secondary，避免两个同等高饱和按钮。

---

## 15. Video Role Play

开始页显示：

```text
Scenario
Your role
AI role
Goal
Useful expressions
Difficulty
[ Start speaking ]
```

会话中：

- 默认语音输入，文本输入是无麦克风 fallback。
- AI 与 Owner transcript 使用文档级排版，不做巨大聊天气泡。
- 录音、AI Thinking、TTS Playing、Listening 状态必须清楚。
- Stop Session 始终可达。
- Mobile 主要录音按钮位于拇指区，Transcript 在其上方滚动。

结束反馈：

```text
Task Completion
Grammar
Vocabulary
Fluency
Pronunciation
Naturalness
Key Corrections
Better Expressions
```

Desktop 使用 Main + Feedback Rail；Mobile 使用 Summary 后按 Accordion 展开详细项。

---

## 16. Writing

页面结构：

```text
Video context / prompt
Writing textarea
Word count
Save status
Submit for feedback
Structured feedback
Corrected version
Better expressions
```

- 自动保存草稿并显示 `Saved` / `Saving` / `Offline`。
- Mobile textarea 至少占可用视口的 40%，软键盘不遮挡提交。
- 离开未保存草稿时确认。
- AI 反馈使用明确章节，不用一大段自由文本。
- Corrected Version 提供与原文对照，但手机改为顺序展示，禁止并排挤压。

---

## 17. AI Tutor 与 Voice Conversation

AI Tutor 不是普通 ChatGPT 套壳。

模式：

```text
Tutor
Scenario
Free Talk
```

支持 Correction、Explanation、Vocabulary、Pronunciation 和 Try Again。

- Desktop 可用主对话 + 学习反馈侧栏。
- Tablet 反馈侧栏折叠。
- Mobile 单列，模式切换使用可横向容纳的 Segmented Control；不得产生页面横向滚动。
- AI Streaming 显示可访问的状态，网络失败保留已生成文本并提供 Retry。

---

## 18. Vocabulary、Progress 与 Memory

### Vocabulary

Word Card 包含：

```text
Word
IPA
Part of speech
English definition
Example
Source video / lesson
Seen count
Next review
Listen / Speak / Save
```

Mobile 单列；Desktop 可双列或 Master–Detail。操作不得只显示 Icon。

### Progress

优先展示：

```text
Learning time
Videos completed
Listening accuracy
Shadowing trend
Words learned
Lessons completed
Consistency
CEFR progress
```

图表必须：

- 有单位、时间范围、Tooltip 和文字摘要。
- Mobile 自动减少 Tick，不旋转难读标签。
- 不只靠红绿区分。
- 无数据时显示指导性 Empty State。

### Learner Memory

按 Listening、Pronunciation、Vocabulary、Grammar、Fluency、Writing 分组，说明错误来源、出现次数、最近时间和建议练习。允许 Owner 删除或标记已掌握。

---

## 19. Settings 与 Storage

只保留个人使用必要设置：

- English variant：en-US / en-GB
- UI locale：沿用已有 English / 简体中文
- Theme：System / Light / Dark
- Playback defaults
- Microphone test
- AI / Speech Provider 状态（只显示是否配置，不显示 Secret）
- Storage usage 与媒体删除
- Data export / backup status
- Logout / Delete data

删除操作必须：

- 与普通设置分区。
- 使用 Danger 样式和确认对话框。
- 明确影响范围。
- 大批量删除优先提供备份或导出提示。

---

## 20. 公共组件体系

```text
components/
  ui/
    Button
    IconButton
    Card
    Input
    Textarea
    Select
    SegmentedControl
    Badge
    Progress
    Modal
    Drawer
    BottomSheet
    Tooltip
    Tabs
    Toast
    Skeleton
    EmptyState
    ErrorState

  layout/
    AppShell
    DesktopSidebar
    TabletRail
    MobileNav
    Topbar
    PageHeader
    FocusLayout

  immersion/
    ImportForm
    ImportProgress
    VideoCard
    VideoWorkspace
    VideoPlayer
    TranscriptPanel
    SentenceControls
    DictationEditor
    DictationDiff
    ShadowRecorder
    PronunciationFeedback
    RolePlaySession
    WritingEditor

  learning/
    Journey
    LessonCard
    VocabularyCard
    LearningProgress

  ai/
    AIMessage
    UserMessage
    TutorModeTabs
    ScenarioCard
    EvaluationPanel
```

业务页面不得重复实现同类 UI。公共组件必须具备 Default、Hover、Pressed、Focus、Disabled、Loading 和 Error 状态。

---

## 21. Loading、Empty、Error 与反馈

每个 API 页面必须处理：

```text
Loading
Empty
Error
Success
```

- 页面加载使用 Skeleton，并预留最终内容尺寸，减少 CLS。
- 持续超过 1 秒的操作显示阶段或进度。
- AI 使用轻量 Animated Dots，但必须有屏幕阅读器文本。
- Toast 自动消失时间 3–5 秒，并使用 `aria-live="polite"`。
- 错误必须包含原因类别和恢复操作；不显示 `500 Internal Server Error`。
- 导入、转写、录音分析等关键失败不能只用 Toast，必须保留页面级错误状态。

---

## 22. Button 与 Form

Button 高度：

```text
Small:   36px（仅桌面紧凑区域）
Default: 44px
Large:   52px
```

- 同一视觉区域原则上一个 Primary CTA。
- 异步提交期间禁用重复点击并显示 Loading。
- Disabled 使用语义属性、视觉弱化和不可点击光标。
- Danger 与 Primary 操作空间分隔。

Form：

- 每个字段有可见 Label。
- Input / Textarea 默认最小高度 44px。
- Error 显示在对应字段下方并通过 `role="alert"` 宣告。
- 长表单按逻辑分组，优先渐进披露。
- Submit 失败时聚焦第一个错误字段。

---

## 23. Accessibility

最低要求：WCAG 2.2 AA。

- 正文对比度 ≥ 4.5:1；大型文字和非文本 UI ≥ 3:1。
- 所有功能可通过键盘完成。
- Focus Ring 2–4px、清晰且不被裁剪。
- 提供 Skip to Main Content。
- Heading 按 H1 -> H2 -> H3 顺序。
- Icon-only Button、录音状态、播放器状态有可理解的 Accessible Name。
- Modal / Sheet 打开时管理焦点，关闭后返回触发元素。
- 页面路由变化后将焦点移到主内容标题。
- 字幕、Transcript 和录音状态可被屏幕阅读器理解。
- Color 不作为唯一状态。
- 支持 200% Zoom，无关键内容裁切。
- `prefers-reduced-motion: reduce` 时关闭 Page Transition、Shake、Celebration 和装饰动画。
- 触控目标至少 44×44px，间距至少 8px。

---

## 24. Performance

- 不使用背景自动播放视频、Heavy WebGL、巨大 Lottie 或复杂 Canvas。
- 视频由用户主动播放，使用 `preload="metadata"` 或更保守策略。
- 缩略图使用 WebP / AVIF、响应式尺寸和 Lazy Loading。
- 图片和视频容器声明尺寸或 `aspect-ratio`。
- Sora / Inter 自托管，`font-display: swap`；只预加载关键字重。
- 按路由拆分 Immersion、AI Tutor 和图表代码。
- 50 项以上 Library / Transcript 列表评估虚拟化。
- 高频时间更新和滚动处理进行节流，避免播放器每帧触发全页渲染。
- CLS < 0.1；主要点击反馈在 100ms 内出现。
- 慢网时保留低带宽模式和清晰重试，不自动加载整段视频。

---

## 25. Dark Mode

- 所有核心页面必须同时设计 Light / Dark，不从单一主题自动推断。
- 视频周围可以使用更深 Surface，但不能让其他页面变成赛博朋克。
- Border、Focus、Hover、Pressed、Disabled、Success 和 Error 在两套主题中都可辨认。
- Modal Scrim 使用 48–60% 黑色，确保前景清晰。
- 图表和 Diff 结果在 Dark Mode 下单独验证对比度。

---

## 26. 实施顺序

### P0 — Foundation

```text
Design Tokens
Typography
Theme
Button / Form / Card
Loading / Empty / Error
Responsive AppShell
Desktop Sidebar
Tablet Rail
Mobile Bottom Navigation
Focus Layout
```

### P1 — Daily Learning

```text
Login
Dashboard
Learn / Journey
Lesson Player
Vocabulary
Progress
```

### P2 — Immersion Core

```text
Import
Import Progress
Library
Video Workspace
Watch
Intensive Listening
Dictation
```

### P3 — Speaking 与闭环

```text
Shadowing
Pronunciation Feedback
Video Role Play
Writing
AI Tutor / Voice
Learner Memory
Settings / Storage
```

每个阶段先完成公共组件和三类设备布局，再迁移页面。不得一次性替换所有页面后统一修复。

---

## 27. 验收标准

### 27.1 Product Scope

- 页面中不存在 Community、Ranking、Reviews、Pricing、Subscription、Billing、Admin 或 Tenant 入口。
- 学习目标固定为英语；发音评测只展示英语能力。
- 未登录进入 Login，已登录进入 Dashboard。

### 27.2 Responsive

在 375、430、768、1024、1280、1440px：

- 无页面级 Horizontal Overflow。
- 无文字裁切、按钮重叠、Modal 溢出。
- 手机使用 Bottom Nav，平板使用 Rail，桌面使用 Sidebar。
- 视频始终保持完整画面和正确比例。
- 输入法弹起后 Dictation、Writing 和 Chat 仍可操作。
- 固定导航和播放器不遮挡内容。
- Portrait / Landscape 切换不丢失状态。

### 27.3 Immersion

- URL Import 是第一入口。
- 导入进度、失败、重试、取消和 Upload fallback 完整。
- Watch、Listening、Dictation、Shadowing、Role Play、Writing 都有独立且连贯的界面。
- 手机端所有视频模式功能完整，不依赖桌面 Hover 或右键。

### 27.4 Accessibility

- Keyboard、Focus、Contrast、Screen Reader、Zoom 和 Reduced Motion 正常。
- 所有触控目标 ≥44×44px。
- 状态不只靠颜色。
- 录音和播放器状态可被辅助技术识别。

### 27.5 Visual Consistency

- 所有页面使用统一颜色、字体、圆角、阴影、图标和间距。
- 无旧 UI 与新 UI 混杂。
- 无业务组件硬编码品牌色。
- Light / Dark 均通过检查。

### 27.6 UX Clarity

- 登录后 3 秒内知道下一步学什么。
- 进入 Immersion 后 3 秒内知道如何导入或继续视频。
- 进入训练模式后 3 秒内知道当前句、当前进度和下一动作。
- AI Tutor / Role Play 中 3 秒内知道如何开始说话。

---

## 28. 最终设计原则

1. Content first.
2. One clear primary action per view.
3. Mobile is an intentional layout, not a compressed desktop.
4. Desktop uses space to improve focus, not to add noise.
5. Video remains complete and central to immersion learning.
6. AI feels integrated, not bolted on.
7. Learning progress is always understandable.
8. Gamification supports learning and never dominates it.
9. Use whitespace before decoration.
10. Professional enough for adult daily use; warm enough to return tomorrow.

---

## 29. 冻结摘要

```text
Product        = Personal English Learning
User           = Single Owner
Platforms      = Mobile + Tablet + Desktop Web
Layout         = Responsive / Adaptive
Navigation     = Mobile Bottom Nav / Tablet Rail / Desktop Sidebar
Core           = Learn + Immersion + Practice + AI + Vocabulary + Progress
Theme          = Light + Dark
Accessibility  = WCAG 2.2 AA
Landing        = None; Login or Dashboard redirect
Excluded       = Multi-language, community, ranking, reviews,
                 payment, multi-role admin, multi-tenant,
                 distributed backend UI, complex notifications
```

未经 Owner 明确修改本规范，不得重新加入已排除的页面和入口。
