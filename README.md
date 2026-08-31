# Verbaia

一个仅供个人使用的英语沉浸式学习工作台。它将视频导入、精听、听写、跟读、角色扮演、写作、词汇与复习进度整合在同一条学习路径中。

项目的产品范围与视觉交互规范请见：

- [开发规范](./AI_Immersive_Language_Platform_Development_Spec_v1.0.md)
- [UI/UX 规范](./语言学习平台%20UI%20-%20UX%20重构设计规范.md)

## 本地开发

前端需 Node.js 24 与 pnpm 11；后端需 Python 3.12。

```bash
pnpm --dir frontend install
pnpm dev

python3.12 -m venv backend/.venv
backend/.venv/bin/pip install -e 'backend[dev]'
backend/.venv/bin/uvicorn app.main:app --app-dir backend --reload --port 8000
```

默认前端地址为 `http://localhost:3000`，健康检查为 `http://localhost:8000/api/health`。

## 目录

```text
frontend/  Next.js 响应式学习界面
backend/   FastAPI 模块化单体与异步任务边界
infra/     生产部署示例（复用宿主 Nginx）
```

所有媒体处理和 AI 能力均通过可替换的外部服务提供商接口接入；本仓库不会提交任何服务密钥。

## 后续部署（暂不执行）

服务器部署时，复制 `backend/.env.example` 为 `backend/.env`，复制
`infra/.env.example` 为 `infra/.env` 并填写强密码与外部 AI Provider 密钥。确认
宿主 Nginx 已存在后，在 `infra/` 中执行：

```bash
docker compose --env-file .env up -d --build
```

该编排仅在 `127.0.0.1` 暴露前后端端口，再由既有 Nginx 反向代理；不会额外占用
80/443 端口。
