#!/bin/sh
set -eu

mkdir -p /var/lib/varbaia/media
chown -R appuser:appuser /var/lib/varbaia
exec runuser -u appuser -- "$@"
