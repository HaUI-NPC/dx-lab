#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

# Đưa DX-Lab về trạng thái demo sạch: xóa stack và MỌI dữ liệu (volume), dựng lại, nạp dữ liệu mẫu.
# Dùng: scripts/reset.sh [--yes]   (--yes bỏ qua câu hỏi xác nhận)

set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
if [ "$#" -gt 1 ]; then
  echo "Dùng: scripts/reset.sh [--yes]" >&2
  exit 2
fi


case "${1:-}" in
  "") ;;
  --yes | -y) ;;
  *) echo "Dùng: scripts/reset.sh [--yes]" >&2; exit 2 ;;
esac

if [ "${1:-}" != "--yes" ] && [ "${1:-}" != "-y" ]; then
  echo "Sẽ xóa toàn bộ container và volume của project dxlab (PostgreSQL, Keycloak, tài liệu, mô hình) rồi dựng lại."
  read -r -p "Gõ 'yes' để tiếp tục: " answer
  [ "$answer" = "yes" ] || { echo "Đã hủy."; exit 1; }
fi

docker compose --env-file .env -f deploy/compose.yaml -p dxlab down -v --remove-orphans
scripts/up.sh
scripts/seed.sh
