# 实施状态

最后更新：2026-09-01

| 里程碑 | 状态 | 当前证据 / 下一步 |
| --- | --- | --- |
| M0 基线 | 完成 | 已记录 FreeLingo 固定 SHA `d2d16c6c3cd1c1167dbc3f21f7776c09f933eae2`；仅作为参考，不直接混入已排除的商业与社区功能。 |
| M1 基础 | 进行中 | Compose、Nginx 示例、健康检查、Owner CLI、真实 PostgreSQL migration、登录与 Refresh Cookie 轮换已在本机验收；待部署环境验收。 |
| M2 响应式壳 | 完成 | 375/768/1280 浏览器实测无横向溢出，浅深主题与三种导航均可用。 |
| M3–M9 学习能力 | 进行中 | 导入、写作、词汇复习和资源学习进度已有 Owner 隔离的持久化 API 与本机 PostgreSQL 集成测试；写作反馈已进入异步状态链，未配置 Provider 时会安全失败；待接入真实媒体、Provider 与完整学习闭环。 |
| M10 加固与部署 | 进行中 | Compose 的 Backend 会先迁移，Worker 已改为真实 Celery 消费者；待 Docker build、空目录部署、备份恢复与核心 E2E 验收。 |

不得将“页面可演示”视为项目完成；所有 Definition of Done 条目需逐项提供运行证据。

## Definition of Done 审计（2026-08-31）

已具备运行证据：单 Owner 创建/登录/刷新/退出基础，PostgreSQL migration，Redis + Celery 状态链，URL SSRF 防护，磁盘预算规则，导入/写作/词汇/学习进度的 Owner 持久化接口与本机数据库集成测试，写作 AI 任务未配置 Provider 时的安全失败与状态回写，响应式壳、浅深主题、焦点与 Reduced Motion，前后端基础测试与构建。

尚未完成，不能作为发布条件：真实媒体下载/上传与清理、外部英语 STT、完整视频 Range 与字幕播放、真实麦克风录音与 Provider 发音评分、视频语音 Role Play、Writing/Vocabulary/Progress/Learner Memory 的完整 AI 闭环、Docker build 与从空目录部署、核心 E2E、真实外部 AI/Speech Provider 集成。后续开发和最终邮件均以这些项目完成并取得运行证据为前提。
