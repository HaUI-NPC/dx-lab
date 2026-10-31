---
name: dxlab-deploy
description: "Dùng cho việc triển khai của dx-lab: compose.yaml, scripts/up.sh, reset.sh, seed.sh, realm Keycloak, APISIX standalone, Spiff Editor, release workflow, build máy sạch (DEP-*, REL-01, QA-01, APP-05)."
---

# Triển khai (compose, Keycloak, APISIX)

> Phiên bản 1.0 · 30/10/2026 · bộ skill riêng của DX-Lab, không commit (D-19).

Hợp đồng: `docs/ARCHITECTURE.md` mục 4 (cổng, URL, issuer công khai và nội bộ), 5 (biến môi trường), 8 (image được phép).

## Luật
- Image **ghim digest**: `docker image inspect --format '{{index .RepoDigests 0}}' <image>`. Chỉ image trong mục 8.
- Cấu hình qua biến môi trường; secret dạng `${BIẾN}`, không giá trị mặc định trong mã. Thiếu biến thì dừng, báo tên biến, không in giá trị.
- Biến mới phải có trong `.env.example` (tệp hợp đồng: cần mentor duyệt). Từng gặp: thiếu `DXLAB_DEMO_OTP_SECRET` làm Keycloak import khóa OTP rỗng và `seed.sh` dừng.
- Mọi service có healthcheck; `up.sh` chờ **tất cả** healthy rồi in URL.
- Build image core/portal: context là gốc repo (uv workspace), `dockerfile: core/Dockerfile`. `.dockerignore` ở gốc loại `.env`, `.git`, `.local`, `.venv`.
- Keycloak: issuer là URL công khai `http://localhost:8180/realms/dxlab`; container gọi `http://keycloak:8080`. Token có `aud` chứa `dxlab-core`, claim `groups` đường dẫn đầy đủ.
- Dữ liệu demo nạp **qua API** (seed dùng tài khoản demo qua APISIX), không ghi thẳng bảng.

## Stack dùng chung
- Compose project `dxlab`. Không `down -v` khi người khác đang dùng; báo trước trên nhóm.
- Dừng tạm để giữ dữ liệu: `docker stop` hoặc `docker compose stop`, không `down -v`.

## Kiểm chứng
- `scripts/up.sh` → `docker ps` mọi service healthy; `curl -s localhost:9080/api/health` 200; không token → 401.
- `scripts/reset.sh --yes` rồi `scripts/seed.sh` **hai lần**: lần hai không tạo gì mới (đếm hàng trước/sau).
- QA-01: làm theo README trên máy sạch, ghi log từng lệnh.
