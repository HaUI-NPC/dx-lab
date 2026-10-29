#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

if [ "$#" -ne 0 ]; then
  echo "Dùng: scripts/up.sh (luôn khởi động toàn bộ dịch vụ)." >&2
  exit 2
fi
for cmd in docker openssl; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "Lỗi: cần cài '$cmd'." >&2; exit 1; }
done
[ -f .env.example ] || { echo "Lỗi: không thấy .env.example." >&2; exit 1; }

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Đã tạo .env từ .env.example."
fi
chmod 600 .env

# Bổ sung biến mới mà không ghi đè cấu hình hiện có.
while IFS= read -r line || [ -n "$line" ]; do
  if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)= ]]; then
    key="${BASH_REMATCH[1]}"
    if ! grep -q -E "^${key}=" .env; then
      printf '\n%s\n' "$line" >> .env
      echo "Đã thêm biến ${key} vào .env."
    fi
  fi
done < .env.example

# Ghi qua tệp tạm để không phụ thuộc cú pháp sed -i giữa macOS và Linux.
tmp="$(mktemp "${TMPDIR:-/tmp}/dxlab-env.XXXXXX")"
trap 'rm -f "$tmp"' EXIT
while IFS= read -r line || [ -n "$line" ]; do
  if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=$ ]]; then
    key="${BASH_REMATCH[1]}"
    printf '%s=%s\n' "$key" "$(openssl rand -hex 24)" >> "$tmp"
    echo "Đã sinh secret ngẫu nhiên cho ${key}."
  else
    printf '%s\n' "$line" >> "$tmp"
  fi
done < .env
cat "$tmp" > .env

docker compose --env-file .env -f deploy/compose.yaml up -d --build --wait

env_value() { grep -E "^$1=" .env | tail -n 1 | cut -d= -f2-; }
portal_url="$(env_value DXLAB_PORTAL_PUBLIC_URL)"
keycloak_url="$(env_value DXLAB_KEYCLOAK_PUBLIC_URL)"
printf '\nDX-Lab đã chạy (mọi service healthy):\n  Portal    %s\n  API       http://localhost:9080/api\n  Keycloak  %s\n' "${portal_url:-http://localhost:8000}" "${keycloak_url:-http://localhost:8180}"
