# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

# Image của portal. Build từ GỐC repo (uv workspace):  docker build -f portal/Dockerfile .
# Image nền ghim theo digest; danh sách image được phép ở docs/ARCHITECTURE.md mục 8.

FROM ghcr.io/astral-sh/uv:0.13.6@sha256:af22a52f5eafef3d78e551599d405c02df61919d18028f0cea8eda93bc9986d0 AS uv

FROM python:3.12-slim-bookworm@sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337 AS build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /src
# Phụ thuộc trước, mã sau: đổi mã không phải tải lại thư viện.
COPY pyproject.toml uv.lock README.md ./
COPY core/pyproject.toml core/pyproject.toml
COPY portal/pyproject.toml portal/pyproject.toml
RUN uv sync --frozen --no-dev --package dxlab-portal --no-install-workspace
COPY LICENSE ./
COPY LICENSES LICENSES
COPY portal/src portal/src
RUN uv sync --frozen --no-dev --package dxlab-portal --no-editable

FROM python:3.12-slim-bookworm@sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337
RUN useradd --system --uid 10001 --home-dir /app dxlab
COPY --from=build /app/.venv /app/.venv
COPY --from=build /src/LICENSE /src/LICENSES /usr/share/doc/dx-lab/
ENV PATH=/app/.venv/bin:$PATH PYTHONUNBUFFERED=1
USER dxlab
WORKDIR /app
EXPOSE 8000
# Renderer Prefab nằm sẵn trong gói prefab-ui: không tải gì lúc chạy, không cần Node.
CMD ["uvicorn", "dxlab_portal.app:app", "--host", "0.0.0.0", "--port", "8000"]
