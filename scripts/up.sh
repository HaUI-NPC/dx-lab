#!/usr/bin/env bash
#
# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

generate_secret() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 24
  else
    head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n'
  fi
}

ENV_FILE=".env"
ENV_EXAMPLE=".env.example"

if [ ! -f "${ENV_FILE}" ]; then
  if [ ! -f "${ENV_EXAMPLE}" ]; then
    echo "Lỗi: Không tìm thấy ${ENV_EXAMPLE} để khởi tạo ${ENV_FILE}." >&2
    exit 1
  fi
  echo "Tạo ${ENV_FILE} từ ${ENV_EXAMPLE}..."
  cp "${ENV_EXAMPLE}" "${ENV_FILE}"
fi

# Sinh ngẫu nhiên các secret đang để trống trong .env
SECRETS=(
  "POSTGRES_PASSWORD"
  "KC_BOOTSTRAP_ADMIN_PASSWORD"
  "DXLAB_PORTAL_CLIENT_SECRET"
  "DXLAB_DEMO_PASSWORD"
  "DXLAB_PORTAL_SESSION_SECRET"
)

for secret_var in "${SECRETS[@]}"; do
  if grep -q -E "^${secret_var}=$" "${ENV_FILE}"; then
    new_val="$(generate_secret)"
    sed -i "s|^${secret_var}=$|${secret_var}=${new_val}|" "${ENV_FILE}"
    echo "Đã sinh secret ngẫu nhiên cho ${secret_var}."
  fi
done

chmod 600 "${ENV_FILE}" 2>/dev/null || true

# Tạo thư mục mount nếu chưa tồn tại
mkdir -p deploy/keycloak deploy/apisix

if [ $# -gt 0 ]; then
  docker compose --env-file "${ENV_FILE}" -f deploy/compose.yaml up -d --wait "$@"
else
  # Khi core/Dockerfile hoặc portal/Dockerfile chưa sẵn sàng (đang trong PR CORE-01 / POR-01),
  # khởi động các dịch vụ hạ tầng đã sẵn sàng để kiểm tra môi trường.
  if [ -f "core/Dockerfile" ] && [ -f "portal/Dockerfile" ] && [ -f "deploy/apisix/apisix.yaml" ]; then
    docker compose --env-file "${ENV_FILE}" -f deploy/compose.yaml up -d --wait
  else
    SERVICES=(postgres keycloak)
    if [ -f "deploy/apisix/apisix.yaml" ]; then
      SERVICES+=(apisix)
    fi
    if [ -f "core/Dockerfile" ]; then
      SERVICES+=(core)
    fi
    if [ -f "portal/Dockerfile" ]; then
      SERVICES+=(portal)
    fi
    echo "Khởi động các dịch vụ sẵn sàng (${SERVICES[*]}):"
    docker compose --env-file "${ENV_FILE}" -f deploy/compose.yaml up -d --wait "${SERVICES[@]}"
  fi
fi
