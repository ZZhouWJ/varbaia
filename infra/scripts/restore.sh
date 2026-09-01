#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "用法：$0 /外部备份目录/varbaia-postgres-YYYYMMDDTHHMMSSZ.sql.gz" >&2
  exit 64
fi

dump_file=$1
if [ ! -f "$dump_file" ]; then
  echo "未找到 PostgreSQL 备份文件：$dump_file" >&2
  exit 66
fi

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
infra_dir=$(CDPATH= cd -- "$script_dir/.." && pwd)
cd "$infra_dir"

echo "恢复前请先停止 backend 与 worker，并确认目标数据库为空。"
printf '输入 RESTORE 继续： '
read -r confirmation
if [ "$confirmation" != "RESTORE" ]; then
  echo "已取消恢复。"
  exit 0
fi

gzip -dc "$dump_file" | docker compose exec -T postgres psql -U varbaia -d varbaia
echo "数据库恢复完成；请启动服务并检查 /api/v1/health/ready。"
