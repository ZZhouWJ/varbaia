#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
infra_dir=$(CDPATH= cd -- "$script_dir/.." && pwd)
repo_dir=$(CDPATH= cd -- "$infra_dir/.." && pwd)

: "${BACKUP_DESTINATION:?请设置服务器外部的 BACKUP_DESTINATION}"
mkdir -p "$BACKUP_DESTINATION"
backup_dir=$(CDPATH= cd -- "$BACKUP_DESTINATION" && pwd)

case "$backup_dir" in
  "$repo_dir"|"$repo_dir"/*)
    echo "拒绝将备份写入仓库目录；请使用服务器外部挂载位置。" >&2
    exit 1
    ;;
esac

timestamp=$(date -u +%Y%m%dT%H%M%SZ)
output="$backup_dir/varbaia-postgres-$timestamp.sql.gz"

cd "$infra_dir"
docker compose exec -T postgres pg_dump -U varbaia -d varbaia | gzip > "$output"
docker compose exec -T redis redis-cli SAVE
printf 'created_at=%s\npostgres_dump=%s\n' "$timestamp" "$(basename "$output")" \
  > "$backup_dir/varbaia-backup-$timestamp.manifest"
echo "备份已创建：$output"
