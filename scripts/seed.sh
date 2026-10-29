#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

# Nạp dữ liệu demo cho lab-repair qua API (APISIX): publish ứng dụng, nạp danh mục và SOP, tạo phiếu mẫu.
# Cần stack đã chạy (scripts/up.sh). Chạy lại nhiều lần không nhân đôi dữ liệu. Logic ở scripts/seed/seed.py.

set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

if command -v uv >/dev/null 2>&1; then
  exec uv run --no-project python scripts/seed/seed.py "$@"
fi
exec python3 scripts/seed/seed.py "$@"
