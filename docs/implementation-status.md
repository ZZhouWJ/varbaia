# 实施状态

最后更新：2026-09-01

| 里程碑 | 状态 | 当前证据 / 下一步 |
| --- | --- | --- |
| M0 基线 | 完成 | 已记录 FreeLingo 固定 SHA `d2d16c6c3cd1c1167dbc3f21f7776c09f933eae2`；仅作为参考，不直接混入已排除的商业与社区功能。 |
| M1 基础 | 进行中 | `/api/v1` 契约与统一错误结构（错误码、请求 ID、可重试标记）、Compose、Nginx 示例、健康检查、Owner CLI、真实 PostgreSQL migration、登录与 Refresh Cookie 轮换已在本机验收；待部署环境验收。 |
| M2 响应式壳 | 完成 | Playwright 已在 1280px 与 375px 验证首页主题、导航和无横向溢出；浅深主题与三种导航均可用，导航、听写草稿和写作草稿可在刷新后恢复，前端不依赖运行时 Google Fonts。 |
| M3–M9 学习能力 | 进行中 | 本地或获准 URL 视频导入、鉴权播放、Range、字幕跳转与断点保存；导入具备取消、重试和上传 fallback；听写、词库复习、结构化写作反馈、语音 Role Play（含结束后的任务完成度、语法、词汇、流利度、发音、自然度与表达建议）、浏览器跟读录音、SOE-N Adapter 与 Learner Memory 均已有 Owner 隔离 API、异步状态链和离线测试。待真实媒体下载与云端 Provider 端到端证据。 |
| M10 加固与部署 | 进行中 | Compose 的 Backend 会先迁移，Worker 为真实 Celery 消费者；CI 包含前后端检查、后端 mypy、镜像构建和响应式首页 E2E，导入任务中间状态与公开 API 枚举保持一致；已提供请求 ID、JSON 访问日志、Compose 日志轮转、Cookie Domain/Secure/SameSite 与跨站 Origin 防护、用户可见任务错误脱敏、拒绝仓库内目标的外部备份/恢复脚本及备份目标健康提示。待本机 Docker build、空目录部署、实际备份恢复与部署环境验收。 |

不得将“页面可演示”视为项目完成；所有 Definition of Done 条目需逐项提供运行证据。

## Definition of Done 审计（2026-09-01）

已具备运行证据：单 Owner 创建/登录/刷新/退出基础，PostgreSQL migration，Redis + Celery 状态链，URL SSRF 防护，磁盘预算规则，yt-dlp 远程下载 Adapter 与签名/大小边界，导入/写作/词汇/学习进度/Learner Memory/角色扮演结束反馈的 Owner 持久化接口及本机 PostgreSQL 集成测试，受鉴权本地视频播放、Range、字幕跳转与断点保存，浏览器录音、腾讯云英语 ASR/TTS Role Play 链路与发音异步任务，腾讯云 SOE-N 英文句子评测 Adapter（含已验证 signer、Mock WebSocket 生命周期、正式字段映射与音频边界校验），结构化写作反馈、响应式壳、浅深主题、焦点与 Reduced Motion，前后端基础测试、生产构建和 standalone 模式下的 Playwright 响应式首页与 Owner Mock 学习闭环 E2E。

尚未完成，不能作为发布条件：一次真实 URL 媒体下载与云端英语 STT、一次真实 SOE-N 音频端到端评分、一次真实语音 Role Play、Docker build 与从空目录部署、备份恢复、完整核心 E2E，以及服务器部署验收。后续开发和最终邮件均以这些项目完成并取得运行证据为前提。
