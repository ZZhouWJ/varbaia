# Verbaia 个人英语沉浸式学习平台——开发规格书

**版本：v1.1 Personal Final**  
**文档状态：冻结，可直接用于当前项目开发**  
**基线日期：2026-08-31**  
**上游基础项目：FreeLingo**  
**产品范围：单 Owner、英语专项、个人长期使用、开源自托管**

---

## 0. 文档权威性与术语

本文件取代此前 v1.0 中的微服务方案，是当前项目最高优先级工程规格。

本项目固定采用：

> **Next.js + FastAPI Modular Monolith + PostgreSQL + Redis + Celery + Existing Nginx + External AI APIs**

本文中的“模块化单体”指单个 FastAPI 后端部署，但代码必须按领域模块组织；它不等于把所有业务写进 router 或单文件。

本文中的“分布式布局”统一解释为 **响应式 / 自适应布局**：同一套 Web 产品针对手机、平板、笔记本和桌面显示器提供适配后的信息架构和交互，不表示分布式后端部署。

如本文件与旧讨论、旧提示词或旧微服务设计冲突，以本文件为准。

---

## 1. 冻结产品范围

### 1.1 产品目标

开发一个供 Owner 长期学习英语使用的 AI-native 沉浸式语言学习平台。平台以 FreeLingo 的课程能力为基础，将真实英文视频、精听、听写、跟读、英语发音评测、AI Role Play、阅读、写作、词汇和长期学习画像整合为闭环。

标准学习路径：

```text
URL / Upload
  -> 完整视频导入
  -> 字幕获取 / 云端 ASR
  -> Watch
  -> Intensive Listening
  -> Blind Listening / Dictation
  -> Reading / Vocabulary
  -> Shadowing
  -> English Pronunciation Assessment
  -> AI Role Play
  -> Writing
  -> Feedback
  -> Progress / Learner Memory
```

### 1.2 明确保留

- Owner 登录与安全会话
- FreeLingo 英语课程、学习计划、Lessons、Flashcards、Listening、Reading、Chat、Voice、Memory 和 Progress
- URL 一键导入英文视频，文件上传作为第二入口
- 完整视频播放、字幕、逐句定位和断点续学
- Intensive Listening、Blind Listening、Dictation、Shadowing
- 英语发音评分和音素级反馈（Provider 支持时）
- 基于视频场景的英语 AI Role Play
- Writing Task、结构化反馈、Vocabulary 和 Learner Memory
- 英语 STT、TTS、实时语音对话
- 手机、平板和桌面端响应式体验
- Light / Dark Theme
- 开源自托管所需的安装、备份、恢复和升级文档

### 1.3 明确删除或暂缓

- 非英语目标语言课程扩展和多语言发音评分
- 社区、关注、排行榜、公开评论和社交 Feed
- 复杂营销 Landing Page、Testimonials、Community 和 Pricing
- 订阅、支付、套餐、账单、Freemium 配额
- 多角色 Admin、组织权限、邀请系统和公开注册
- 多租户、团队空间和组织隔离
- 微服务、API Gateway、服务发现和分布式部署
- 跨服务 REST、Service Token、Schema-per-service、Transactional Outbox
- Kafka、RabbitMQ、Kubernetes、Service Mesh、Elasticsearch 和 Grafana Stack
- 复杂通知中心、邮件营销和推送系统

页面内 Toast、导入进度、错误恢复提示属于必要反馈，不属于复杂通知系统。

### 1.4 语言边界

- 学习目标语言固定为英语。
- 初始支持 `en-US` 与 `en-GB` 发音偏好。
- AI 课程、视频训练、STT、TTS 和发音评测均围绕英语实现。
- UI 可保留上游已有英文和简体中文界面，但不新增更多 UI Locale；UI Locale 不改变学习目标语言。
- Provider 不支持某项英语细粒度结果时必须显式降级，不伪造音素或韵律评分。

---

## 2. 固定运行环境

目标部署在现有腾讯云中国大陆服务器：

```text
CPU:       4 Core
RAM:       4 GB class (约 3.6 GiB 可见)
GPU:       None
Disk:      40 GB system disk
Storage:   不扩容，不新增 COS / S3
Network:   China mainland Tencent Cloud
Proxy:     复用宿主机现有 Nginx
```

该服务器还运行其他项目，因此 Verbaia 不得独占整机资源，不得替换、重启或重配置无关容器和服务。

生产环境不运行：

- Ollama 或其他本地 LLM
- Whisper / faster-whisper
- Kokoro 或其他本地 TTS
- Demucs
- 本地神经网络发音模型
- GPU 推理
- 默认全量视频转码

---

## 3. 冻结技术栈

### 3.1 Frontend

```text
Framework:     Next.js 16+ App Router
Language:      TypeScript, strict=true
UI:            shadcn/ui / existing compatible primitives
CSS:           Tailwind CSS + CSS Variables
State:         Zustand
I18n:          next-intl（只保留已有中英文 UI 能力）
Realtime:      WebSocket / SSE
Audio:         Web Audio API / MediaRecorder
Video:         HTML5 video + custom controls
Testing:       Vitest + React Testing Library + Playwright
```

视觉实现以《语言学习平台 UI / UX 重构设计规范》为准；保留上游业务行为，不保留与新设计系统冲突的旧视觉。

### 3.2 Backend

```text
Language:      Python 3.12
Framework:     FastAPI
Validation:    Pydantic v2
ORM:           SQLAlchemy 2 async
Migration:     Alembic（单 migration history）
HTTP Client:   httpx
Task Queue:    Celery 5.6+
Broker:        Redis 7
Database:      PostgreSQL 16
Media:         FFmpeg + ffprobe + yt-dlp
Testing:       pytest + pytest-asyncio
Lint:          Ruff
Type Check:    mypy / pyright-compatible typing
```

### 3.3 Infrastructure

```text
Reverse Proxy: 宿主机现有 Nginx
Containers:    Docker + Docker Compose
TLS:           由现有 Nginx 站点配置负责
Deployment:    单机 Docker Compose
```

---

## 4. 总体架构

```text
                         Browser
                            |
                  HTTPS / WebSocket / SSE
                            |
                    Existing Nginx
                     /             \
                    /               \
             Next.js               FastAPI
            frontend         modular-monolith backend
                                      |
                     +----------------+----------------+
                     |                |                |
                 PostgreSQL         Redis       Celery Worker
                                                       |
                                   +-------------------+----------------+
                                   |                   |                |
                                yt-dlp              FFmpeg      External APIs
                                                                  |  |  |  |
                                                                 LLM STT TTS SOE
```

生产新增容器固定为：

```text
frontend
backend
worker
postgres
redis
```

`backend` 与 `worker` 使用同一 Docker image，启动命令不同。Nginx 不纳入本项目 Compose，不占用新的 80/443 映射。

---

## 5. Repository 结构

```text
repo/
├── frontend/
│   ├── src/app/
│   ├── src/components/
│   ├── src/features/
│   ├── src/lib/
│   ├── messages/
│   └── tests/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── modules/
│   │   │   ├── auth/
│   │   │   ├── learning/
│   │   │   ├── immersion/
│   │   │   ├── conversation/
│   │   │   ├── vocabulary/
│   │   │   └── progress/
│   │   ├── providers/
│   │   │   ├── llm/
│   │   │   ├── stt/
│   │   │   ├── tts/
│   │   │   └── pronunciation/
│   │   ├── jobs/
│   │   ├── db/
│   │   ├── common/
│   │   ├── config.py
│   │   └── main.py
│   ├── migrations/
│   └── tests/
├── infra/
│   ├── nginx-example/
│   ├── compose/
│   └── scripts/
├── data/
│   ├── media/
│   ├── subtitles/
│   ├── thumbnails/
│   ├── tts-cache/
│   └── tmp/
├── docs/
├── specs/
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
├── AGENTS.md
└── README.md
```

模块内部统一采用：

```text
API -> Application Service -> Domain Rule -> Repository / Provider
```

禁止 router 直接写复杂业务逻辑，禁止模块通过未声明的内部文件结构互相读取数据。跨模块调用使用清晰的 application interface，但不通过 HTTP。

---

## 6. 数据库与所有权

使用一个 PostgreSQL 实例、一个数据库和一套 Alembic migration history。代码层按模块划分模型，不创建独立服务 Schema。

核心实体至少包括：

```text
users
refresh_sessions
study_plans
lessons
flashcards
vocabulary_items
media_assets
import_jobs
transcripts
sentences
video_lessons
dictation_attempts
shadowing_attempts
pronunciation_results
conversation_sessions
writing_tasks
writing_attempts
learner_weaknesses
progress_records
job_events
```

规则：

- 所有新增业务实体使用 UUIDv7 或 UUID4。
- 第三方 TaskId 只能作为 provider metadata，不能作为业务主键。
- 即使当前只有一个 Owner，所有个人资源仍保存 `owner_user_id`，为安全和未来导出提供边界。
- 删除媒体时保留必要学习统计，清除媒体文件、字幕全文和录音的规则必须明确。
- 任务状态和用户可见进度以 PostgreSQL 为业务真实来源，不依赖 Celery `AsyncResult`。

---

## 7. 单 Owner 鉴权

### 7.1 账户模型

- 系统只支持一个 Owner 账户。
- 不提供公开注册、邀请、角色矩阵或 Admin Panel。
- 首次部署使用一次性 CLI 创建 Owner；CLI 可重复执行但不得创建第二个 Owner。
- `ALLOW_REGISTRATION=false` 为生产固定值。

### 7.2 会话安全

- Access Token 使用短期 JWT，建议 15 分钟。
- Refresh Token 使用 HttpOnly、Secure Cookie，并进行 rotation。
- Cookie 明确设置 SameSite 和 Domain。
- 登录端点必须限流。
- WebSocket 在握手时完成鉴权。
- 所有资源查询必须验证 Owner，防止 IDOR。
- 账户删除或数据清空必须二次确认，并提供备份提示。

---

## 8. Celery 与后台任务

Celery 必须保留，因为视频导入、云端转写和课程生成可能持续数分钟。

初始仅运行一个 Worker：

```text
concurrency = 1
prefetch_multiplier = 1
acks_late = true（仅用于可幂等任务）
```

逻辑队列初始可使用：

```text
default
maintenance
```

也允许初期只使用 `default`，但任务名必须有领域前缀：

```text
immersion.import_media
immersion.transcribe_media
immersion.generate_exercises
immersion.cleanup_job
ai.evaluate_writing
maintenance.cleanup_temp
maintenance.cleanup_expired_media
```

每个后台任务必须：

- 幂等
- 有 soft / hard timeout
- 仅对可恢复错误自动重试
- 指数退避并限制最大重试次数
- 保存 `job_id`、`request_id` 和结构化日志
- 显式写入业务状态
- 可在 Worker 重启后恢复或安全重跑
- 成功、失败和取消时都执行临时文件清理

标准导入状态：

```text
queued
validating
fetching_metadata
downloading
processing_media
fetching_subtitles
transcribing
segmenting
generating_exercises
ready
failed
cancelled
```

客户端统一通过 SSE 获取进度；SSE 断开后使用 `GET` 状态接口恢复，不再同时维护独立轮询主流程。

---

## 9. AI 与 Speech Provider

业务模块不得直接依赖供应商 SDK，必须通过 Provider Protocol：

```python
class LLMProvider(Protocol):
    async def generate(...): ...
    async def stream(...): ...
    async def structured(...): ...

class STTProvider(Protocol): ...
class TTSProvider(Protocol): ...
class PronunciationProvider(Protocol): ...
```

初始 Provider：

```text
LLM:             Qwen OpenAI-compatible, Beijing region
Realtime STT:    Tencent Cloud
Media STT:       Tencent Cloud
TTS:             Tencent Cloud
Pronunciation:   Tencent Cloud SOE-N（新版）English
```

要求：

- 模型名、Base URL、Region 和 API Version 全部由环境变量设置。
- 前端永远不持有第三方 SecretKey。
- 结构化课程、Role Play 和 Writing feedback 必须通过 Pydantic 校验。
- Provider 超时、限流和不可用必须转成统一错误结构。
- 日志记录 Provider、模型、延迟、用量和脱敏后的错误码。
- 英语发音评测使用 SOE-N；不得接入已停止销售的旧 SOE-B 作为新部署默认方案。
- SOE-N 不返回的维度显示“暂不可用”，不得由前端估算伪造。

---

## 10. Immersion 视频导入

### 10.1 入口

页面：`/immersion`

第一入口：粘贴 URL；第二入口：上传文件。不得要求 Owner 手工下载视频、分离音频或准备字幕。

```http
POST /api/v1/immersion/imports/url
```

```json
{
  "url": "https://...",
  "english_variant": "en-US",
  "start_time": null,
  "end_time": null
}
```

返回 `202 Accepted`：

```json
{
  "job_id": "uuid",
  "status": "queued"
}
```

状态恢复接口：

```http
GET /api/v1/immersion/imports/{job_id}
GET /api/v1/immersion/imports/{job_id}/events
DELETE /api/v1/immersion/imports/{job_id}
```

### 10.2 Upload

支持：

```text
video: mp4, mov, mkv, webm
audio: mp3, m4a, wav
subtitle: srt, vtt
```

- 视频和字幕可以一起上传。
- 必须流式写入隔离临时目录，边接收边统计大小。
- 超过 `MAX_UPLOAD_MB` 立即中止并清理。
- 前端显示上传进度，支持取消。
- MIME、扩展名和实际媒体探测结果必须交叉校验。

### 10.3 URL 安全

- 只允许 `http` / `https`。
- 拒绝 localhost、loopback、RFC1918、link-local、metadata IP 和其他不可公网路由地址。
- DNS resolve 后校验全部 IP。
- 每次 redirect 和下载子请求都重新校验目标。
- 限制 redirect、时长、估算大小、实际下载字节数和总耗时。
- yt-dlp 参数由代码固定生成，用户不能传 flags。
- subprocess 禁止 `shell=True`。
- 每个任务使用 `data/tmp/{job_id}/`。
- 文件名必须净化，最终路径必须验证仍位于允许目录内。
- Cookie 文件如未来启用，必须加密保存、最小权限挂载且不得进入日志或 Git；v1 不把 Cookie 导入作为默认流程。

### 10.4 媒体处理

优先保存浏览器可直接播放的编码：

```text
MP4 + H.264 + AAC
WebM（浏览器兼容时）
```

FFmpeg 优先执行 `probe`、`remux -c copy`、音轨或短片段提取。只有确实无法播放时才允许受限转码。

媒体读取必须支持 HTTP Range、正确 MIME、ETag / Last-Modified 和授权检查。

### 10.5 磁盘策略

当前共享服务器默认值：

```text
MEDIA_PERSISTENT_QUOTA_GB=4
MEDIA_TEMP_QUOTA_GB=1
DISK_MIN_FREE_GB=8
```

- 接任务前检查剩余空间，无法同时满足预估大小、临时空间和安全余量时拒绝导入。
- 成功后立即删除重复原文件、完整 WAV 和中间分片。
- 失败媒体默认 1 小时后清理。
- 不静默删除仍在学习的媒体。
- 达到配额时显示 Storage 管理界面，由 Owner 明确确认删除。
- Docker 镜像和其他项目文件不计入媒体配额，但必须计入磁盘安全判断。

---

## 11. 视频学习模式

### 11.1 Watch

- 完整视频画面
- 英文字幕开关
- 当前句高亮
- 单词点击
- 收藏句子
- 0.75x / 1x / 1.25x
- 逐句 seek、上一句、下一句、重播
- 全屏与断点续播

### 11.2 Intensive Listening

以 sentence 为单位完成 `play -> pause -> replay -> reveal transcript`，可设置循环次数并保存进度。

### 11.3 Blind Listening / Dictation

默认隐藏字幕，用户输入听到的英文。结果输出：

```text
correct
substitution
missing
extra
```

保存 `word_accuracy`、遗漏、额外词、尝试次数和逐句历史。

### 11.4 Shadowing

```text
播放原句 -> 录音 -> SOE-N -> 分数与词/音素反馈 -> 重试
```

显示原声、参考句、用户录音、overall、accuracy、fluency、completeness，以及 Provider 实际支持的 word / phoneme feedback。保存 best 与 latest score。

### 11.5 AI Role Play

根据视频标题、字幕、场景、Owner 弱点和已保存词汇生成角色、目标、表达提示、开场和成功标准。默认使用麦克风；文本输入只作为无麦克风 fallback。

结束后反馈 Task Completion、Grammar、Vocabulary、Fluency、Pronunciation、Naturalness、Key Corrections 和 Better Expressions。

### 11.6 Writing

每个 Video Lesson 可生成一个英语写作任务。返回结构化 grammar、vocabulary、coherence、task completion、corrected version、key errors 和 better expressions，并按 promotion policy 写入 Learner Memory。

---

## 12. Learner Memory

长期弱点类别：

```text
pronunciation
listening
vocabulary
grammar
fluency
writing
```

仅在以下条件写入长期记忆：

- 同一错误重复达到阈值
- 明显影响交流
- Owner 主动保存
- 英语 CEFR 核心能力缺口

不得把每个微小错误永久保存。复习优先级综合近期性、频率和严重程度。

---

## 13. 前端信息架构

Desktop Sidebar：

```text
Dashboard
Learn
Immersion
Practice
AI Tutor
Vocabulary
Progress

Settings
```

Mobile Bottom Navigation 最多五项：

```text
Home
Learn
Immersion
Practice
AI
```

Vocabulary、Progress 和 Settings 进入 Profile / More 页面，不在底栏继续增加项目。

关键路由：

```text
/login
/dashboard
/learn
/immersion
/immersion/imports/{job_id}
/immersion/{lesson_id}
/immersion/{lesson_id}/dictation
/immersion/{lesson_id}/shadowing
/immersion/{lesson_id}/roleplay
/immersion/{lesson_id}/writing
/practice
/ai-tutor
/vocabulary
/progress
/settings
```

所有关键学习状态必须深链接可恢复；刷新或设备尺寸变化不得丢失当前句、模式、草稿和视频位置。

响应式布局、断点、手机视频训练、触控和无障碍细则以 UI / UX 规范为准。

---

## 14. API 与错误协议

所有 API 使用 `/api/v1`。统一错误结构：

```json
{
  "error": {
    "code": "IMMERSION_IMPORT_FAILED",
    "message": "Unable to import this video source.",
    "request_id": "...",
    "retryable": true,
    "details": null
  }
}
```

不得向客户端返回 traceback、yt-dlp raw stderr、SQL exception、Provider Secret 或内部路径。用户消息必须说明原因类别和下一步操作。

---

## 15. 实时语音

保留 FreeLingo 的 VAD、WebSocket、STT -> LLM -> TTS、流式响应、音频队列、barge-in、对话历史和 inactivity timeout。

实时请求由 FastAPI backend 直接编排 Provider，不经过 Celery。浏览器不直接连接带长期密钥的 Provider。

---

## 16. 可观测性、备份与恢复

必须实现：

- JSON structured logs
- request_id、job_id、user_id（安全时）
- route、HTTP status、task latency、retry count
- Provider、模型、延迟、用量和错误码
- 磁盘总量、剩余空间和媒体占用
- `/health/live` 与 `/health/ready`
- 日志轮转和脱敏

备份至少覆盖：

- PostgreSQL 定时 dump
- `.env` 之外的配置清单
- 必要媒体和字幕索引
- 恢复步骤及定期恢复演练

备份不能只保存在同一系统盘。远程备份目标由 Owner 在部署前明确配置；未配置时生产就绪检查必须报警。

---

## 17. 安全要求

- 生产只通过现有 Nginx 暴露 80/443。
- HTTPS、Secure Cookie、CORS allowlist 和 CSRF-aware cookie flow。
- 密码使用上游当前安全方法或 Argon2id。
- 上传大小、MIME、路径穿越和 SSRF 防护。
- subprocess 参数数组调用，不使用 shell。
- Secret 只来自 env 或权限受控的 secret file。
- 登录、导入和 AI 端点限流。
- WebSocket 鉴权和 Origin 校验。
- 麦克风权限只在用户主动开始录音时请求。
- 录音、视频、字幕和学习数据提供明确删除入口。
- Nginx 配置域名、TLS 和 WebSocket/SSE 转发；不得覆盖其他站点配置。
- 中国大陆公开域名上线前完成所需备案与域名准备。

---

## 18. Environment Variables

至少提供：

```text
APP_ENV=production
PUBLIC_BASE_URL=
OWNER_EMAIL=
ALLOW_REGISTRATION=false

DATABASE_URL=postgresql+asyncpg://...
REDIS_BROKER_URL=redis://...
REDIS_CACHE_URL=redis://...

JWT_PRIVATE_KEY_PATH=
JWT_PUBLIC_KEY_PATH=
COOKIE_DOMAIN=
COOKIE_SECURE=true
COOKIE_SAMESITE=lax

LLM_PROVIDER=qwen_openai_compatible
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
LLM_TIMEOUT_SECONDS=60

STT_PROVIDER=tencent
TTS_PROVIDER=tencent
PRONUNCIATION_PROVIDER=tencent_soe_new_age
TENCENT_REGION=
TENCENT_APP_ID=
TENCENT_SECRET_ID=
TENCENT_SECRET_KEY=

MEDIA_ROOT=/data/media
MEDIA_TEMP_ROOT=/data/tmp
MEDIA_PERSISTENT_QUOTA_GB=4
MEDIA_TEMP_QUOTA_GB=1
DISK_MIN_FREE_GB=8
MAX_UPLOAD_MB=
MAX_VIDEO_DURATION_MINUTES=

CELERY_CONCURRENCY=1
CELERY_TASK_SOFT_TIME_LIMIT=
CELERY_TASK_TIME_LIMIT=
LOG_LEVEL=INFO
```

`.env.example` 只包含 placeholder，不包含任何真实密钥。

---

## 19. Testing 与质量门槛

### 19.1 Unit

- 模块 domain rule 和 application service
- Dictation token diff
- transcript segmentation
- Provider normalization
- 任务幂等和状态转换
- 配额、路径和 SSRF 判断
- Learner Memory promotion

### 19.2 Integration

- PostgreSQL、Redis 和 Celery
- Auth 与 refresh rotation
- 本地 fixture URL 导入
- FFmpeg / ffprobe fixture
- Mock Provider
- HTTP Range
- SSE 重连与状态恢复

### 19.3 E2E

Playwright 至少覆盖：

1. Owner 登录
2. Dashboard 继续学习
3. URL 导入 fixture video
4. 查看导入进度并恢复连接
5. Watch 与断点续播
6. Dictation
7. Shadowing mock score
8. Role Play mock voice/text
9. Writing
10. Progress persistence
11. Light / Dark
12. 375、430、768、1024、1280、1440 宽度

### 19.4 CI

```text
frontend lint
frontend typecheck
frontend unit tests
backend ruff
backend typecheck
backend unit tests
migration validation
Docker build
critical E2E
```

不得提交失败测试、真实 Secret、注释掉的旧实现或无法回滚的 migration。

---

## 20. 开发里程碑

### Milestone 0 — Reproducible Baseline

- Clone FreeLingo 并记录固定 commit SHA
- 保留 AGPL-3.0 文件
- 记录上游测试结果和当前行为
- 在隔离开发环境启动上游，不直接占用生产 80/443

### Milestone 1 — Personal Foundation

- 删除商业化、多角色和多语言目标范围
- 建立单 Owner bootstrap CLI
- 建立统一配置、日志、健康检查和 Compose
- 复用现有 Nginx，提供独立站点配置示例

### Milestone 2 — Design System 与响应式 AppShell

- Design Tokens、字体、Button、Card、Input、Modal、Toast、Skeleton
- Desktop Sidebar、Tablet Rail、Mobile Bottom Navigation
- Light / Dark、Safe Area、Focus、Reduced Motion

### Milestone 3 — FreeLingo 英语核心回归

- Dashboard、Learn、Lesson、Listening、Reading、Flashcards、AI Tutor、Voice、Progress、Memory
- 删除无关入口但不破坏保留能力

### Milestone 4 — Celery 与媒体基础

- 单 Worker、job state、retry、cleanup、quota、SSE
- yt-dlp / FFmpeg adapter 和安全边界

### Milestone 5 — Import 与 Video Player

- URL / Upload、字幕 / ASR、分句、Range、完整视频、手机端适配

### Milestone 6 — Listening 与 Dictation

- Intensive、Blind、token diff、历史和断点恢复

### Milestone 7 — Shadowing 与英语发音评分

- MediaRecorder、回放、SOE-N、word / phoneme feedback、best / latest

### Milestone 8 — Video Role Play

- 场景生成、实时语音、目标与结束反馈

### Milestone 9 — Writing 与 Learner Memory

- Writing evaluation、Vocabulary、弱点提升和复习推荐

### Milestone 10 — Production Hardening

- 限流、备份恢复、磁盘保护、移动端真机、Nginx/TLS、部署文档
- 在共享 4C4G 服务器进行资源压测，不干扰其他项目

每个里程碑完成后更新 `docs/implementation-status.md`，保证系统可启动、可测试、可回滚。

---

## 21. Definition of Done

项目 v1 完成必须同时满足：

1. 单 Owner 可安全创建、登录、刷新会话和退出。
2. FreeLingo 保留的英语核心功能可用。
3. 可粘贴视频 URL 或上传视频，无需手工准备音频和字幕。
4. 无字幕时自动调用云端英语 STT。
5. 显示完整视频并支持 Range、字幕、逐句导航和断点续播。
6. Watch、Intensive Listening、Blind Listening、Dictation 可用。
7. 真实麦克风 Shadowing 和英语细粒度发音评分可用。
8. 基于视频的语音 AI Role Play 可用。
9. Writing、Vocabulary、Progress 和 Learner Memory 形成闭环。
10. 所有 AI / Speech 计算走外部 Provider，服务器不运行本地模型。
11. Celery 任务可恢复、可重试、幂等并有业务状态。
12. 手机、平板和桌面端均无横向溢出、遮挡和关键功能缺失。
13. Light / Dark、Keyboard、Focus、Screen Reader 和 Reduced Motion 通过验收。
14. 媒体配额和磁盘安全余量不会写满系统盘。
15. 只新增 5 个容器，并复用现有 Nginx。
16. CI、Docker build 和核心 E2E 通过。
17. 可从空目录部署，并有备份与恢复文档。

---

## 22. 明确禁止

```text
禁止拆成多个 FastAPI 微服务
禁止新增 API Gateway 或跨服务 REST
禁止多租户、支付、套餐、社区、排行和复杂通知
禁止扩展非英语目标语言和非英语发音评分
禁止前端直接持有 Provider Secret
禁止服务器运行本地 LLM / Whisper / TTS / Demucs
禁止用 SQLite 替换 PostgreSQL
禁止用同步 HTTP 等待长任务完成
禁止把 Celery task_id 当业务 job_id
禁止默认全量视频转码
禁止将视频课程退化为 audio + subtitle
禁止拼接 shell command
禁止无限制下载任意 URL
禁止任务结束后遗留大量临时媒体
禁止未经确认自动删除 Owner 的学习媒体
禁止项目 Compose 接管或破坏宿主机现有 Nginx 和其他项目
禁止一次性大爆炸重写 FreeLingo
```

---

## 23. 上游与许可证

- 上游：`https://github.com/ArtCC/freelingo`
- 许可证：AGPL-3.0；Fork 必须保留许可证并履行网络使用场景下的源码提供义务。
- 参考：`https://github.com/Oliviaviaviavia/english-trainer`
- English Trainer 为 MIT；直接复用代码时保留必要许可证和版权声明。
- 第一次开发提交必须记录所用 FreeLingo commit SHA，之后不自动追随移动的 `main`。

---

## 24. 冻结摘要

```text
Product             = Personal English Immersive Learning
Owner Model         = Single Owner
Base                = FreeLingo Fork, pinned commit
Architecture        = FastAPI Modular Monolith
Frontend            = Next.js 16+
Database            = One PostgreSQL 16 database
Async               = Redis 7 + Single Celery Worker
Reverse Proxy       = Existing host Nginx
Deployment          = 5 new Docker containers on one server
AI / Speech         = External APIs only
Pronunciation       = English, Tencent SOE-N initially
Media               = URL-first, full video required
Responsive          = Mobile + Tablet + Desktop adaptive UI
Excluded            = Multi-language, social, ranking, reviews,
                      complex landing, payment, multi-role admin,
                      multi-tenant, distributed backend, complex notifications
```

未经 Owner 明确修改本规格，不得重新引入上述已排除范围。
