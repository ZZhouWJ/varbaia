# Verbaia 运维手册

## 部署前检查

1. 安装 Docker Compose v2，并确认宿主 Nginx 已占用并管理 80/443。
2. 在仓库根目录复制 `backend/.env.example` 为 `.env`，设置 32 字符以上的 `JWT_SECRET`、外部 AI Provider 配置和密钥；根目录 `.env` 是本地与 Compose 唯一读取的私密配置文件。
3. 复制 `infra/.env.example` 为 `infra/.env`，设置强随机 `POSTGRES_PASSWORD`。
4. 在 `infra/` 执行 `docker compose --env-file ../.env up -d --build`；Backend 会先执行
   `alembic upgrade head`，端口必须只绑定 `127.0.0.1`。
5. 将 `infra/nginx/varbaia.conf.example` 的域名改为实际域名，测试并 reload 已有 Nginx。
6. 使用 `docker compose ps` 和 `curl http://127.0.0.1:8000/api/health` 检查服务；创建 Owner 后再开放登录。

## 备份

在 `infra/` 中执行，备份文件必须复制至主机外的受控位置：

```bash
docker compose exec -T postgres pg_dump -U varbaia -d varbaia | gzip > varbaia-$(date +%F).sql.gz
docker compose exec -T redis redis-cli SAVE
```

恢复前先停止 Worker 与 Backend，确认备份来源与日期；恢复到空数据库后执行：

```bash
gunzip -c varbaia-YYYY-MM-DD.sql.gz | docker compose exec -T postgres psql -U varbaia -d varbaia
```

完成后启动服务、检查健康端点，并用 Owner 登录验证数据。媒体对象、数据库备份和 `.env` 应采用独立加密备份策略；绝不把它们提交到 Git。

## 回滚

记录每次部署的 Git SHA。发生故障时切回上一个 SHA，执行 `docker compose up -d --build`，再验证健康检查与导入任务队列。涉及数据库 migration 的部署必须先备份；不执行未经验证的降级 migration。
