#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

# Tải mô hình bằng chính môi trường và volume của core; chạy scripts/up.sh trước.
# CORE-08 cung cấp fastembed trong image core. Không ghi mô hình vào mã nguồn.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
if [[ ! -f .env || ! -f deploy/compose.yaml ]]; then
  echo "Cần deploy/compose.yaml và .env; hãy thiết lập DX-Lab trước." >&2
  exit 1
fi

docker compose --env-file .env -f deploy/compose.yaml run --rm --no-deps \
  --entrypoint python core -c '
import os
from fastembed import TextEmbedding

model = os.environ.get("DXLAB_EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
cache = os.environ["DXLAB_MODEL_CACHE_DIR"]
TextEmbedding(model_name=model, cache_dir=cache)
# Kiểm lại bằng đường đọc offline mà core sử dụng.
TextEmbedding(model_name=model, cache_dir=cache, local_files_only=True)
print(f"Đã tải và kiểm tra offline {model} trong {cache}.")
'
