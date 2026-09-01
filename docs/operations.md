# Verbaia 运维手册

## 部署前检查

1. 安装 Docker Compose v2，并确认宿主 Nginx 已占用并管理 80/443。
2. 在仓库根目录复制 `backend/.env.example` 为 `.env`，设置 32 字符以上的 `JWT_SECRET`、`COOKIE_DOMAIN`、生产环境 `COOKIE_SECURE=true`、外部 AI Provider 配置、腾讯云凭据（`TENCENTCLOUD_SECRET_ID`、`TENCENTCLOUD_SECRET_KEY`、`TENCENTCLOUD_APP_ID`、英语 ASR / TTS 参数）和位于服务器外部挂载位置的 `BACKUP_DESTINATION`；根目录 `.env` 是本地与 Compose 唯一读取的私密配置文件。
3. 复制 `infra/.env.example` 为 `infra/.env`，设置强随机 `POSTGRES_PASSWORD`。
4. 在 `infra/` 执行 `docker compose --env-file ../.env up -d --build`；Backend 会先执行
   `alembic upgrade head`，端口必须只绑定 `127.0.0.1`。
5. 将 `infra/nginx/varbaia.conf.example` 的域名改为实际域名，测试并 reload 已有 Nginx。
6. 使用 `docker compose ps` 和 `curl http://127.0.0.1:8000/api/health` 检查服务；创建 Owner 后再开放登录。

Backend 镜像会安装 FFmpeg 和项目锁定的 `yt-dlp`。首次验收请分别使用一段短英文公开视频、一次浏览器跟读录音和一次 Role Play 录音，确认下载、转写、评分与 TTS 都有对应的业务结果；不要在日志或工单中记录完整签名 URL 或任何 Secret。

## 备份

备份文件必须写至服务器外部的受控挂载位置；`/api/health/ready` 会显示 `backup=not_configured`，直至设置 `BACKUP_DESTINATION`。使用仓库提供的脚本：

```bash
cd infra
BACKUP_DESTINATION=/mnt/remote-backups/varbaia sh ./scripts/backup.sh
```

恢复前先停止 Worker 与 Backend，确认备份来源与日期，并恢复到空数据库：

```bash
cd infra
sh ./scripts/restore.sh /mnt/remote-backups/varbaia/varbaia-postgres-YYYYMMDDTHHMMSSZ.sql.gz
```

完成后启动服务、检查健康端点，并用 Owner 登录验证数据。媒体对象、数据库备份和 `.env` 应采用独立加密备份策略；绝不把它们提交到 Git。

## 回滚

记录每次部署的 Git SHA。发生故障时切回上一个 SHA，执行 `docker compose up -d --build`，再验证健康检查与导入任务队列。涉及数据库 migration 的部署必须先备份；不执行未经验证的降级 migration。
