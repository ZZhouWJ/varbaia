# 实施状态

最后更新：2026-09-01

| 里程碑 | 状态 | 当前证据 / 下一步 |
| --- | --- | --- |
| M0 基线 | 完成 | 已记录 FreeLingo 固定 SHA `d2d16c6c3cd1c1167dbc3f21f7776c09f933eae2`；仅作为参考，不直接混入已排除的商业与社区功能。 |
| M1 基础 | 进行中 | Compose、Nginx 示例、健康检查、Owner CLI、真实 PostgreSQL migration、登录与 Refresh Cookie 轮换已在本机验收；待部署环境验收。 |
| M2 响应式壳 | 完成 | Playwright 已在 1280px 与 375px 验证首页主题、导航和无横向溢出；浅深主题与三种导航均可用。 |
| M3–M9 学习能力 | 进行中 | 本地视频上传、鉴权播放、Range、字幕跳转与断点保存；听写、词库复习、写作、文本 Role Play、浏览器跟读录音已有 Owner 隔离 API 与异步状态链。外部 Provider 未配置时会安全失败；待真实媒体下载、真实 Provider、视频语音 Role Play 与 Learner Memory 闭环。 |
| M10 加固与部署 | 进行中 | Compose 的 Backend 会先迁移，Worker 为真实 Celery 消费者；CI 包含前后端检查、镜像构建和响应式首页 E2E。待本机 Docker build、空目录部署、备份恢复与部署环境验收。 |

不得将“页面可演示”视为项目完成；所有 Definition of Done 条目需逐项提供运行证据。

## Definition of Done 审计（2026-09-01）

已具备运行证据：单 Owner 创建/登录/刷新/退出基础，PostgreSQL migration，Redis + Celery 状态链，URL SSRF 防护，磁盘预算规则，导入/写作/词汇/学习进度的 Owner 持久化接口与本机数据库集成测试，受鉴权本地视频播放、Range、字幕跳转与断点保存，浏览器录音与发音异步任务，写作 AI 任务未配置 Provider 时的安全失败与状态回写，响应式壳、浅深主题、焦点与 Reduced Motion，前后端基础测试、生产构建和 1280/375 首页 Playwright E2E。

尚未完成，不能作为发布条件：真实 URL 媒体下载与云端英语 STT、真实 Provider 的成功调用证据、视频语音 Role Play、Writing/Vocabulary/Progress/Learner Memory 的完整 AI 闭环、Docker build 与从空目录部署、备份恢复、完整核心 E2E，以及服务器部署验收。后续开发和最终邮件均以这些项目完成并取得运行证据为前提。
