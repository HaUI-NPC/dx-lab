---
name: dxlab-commit
description: "Dùng trước mỗi lần git commit trong repo dx-lab: commit nhỏ đúng định dạng, có Signed-off-by (DCO), không lọt secret hay tệp sinh tự động."
---

# Commit

> Phiên bản 1.0 · 30/10/2026 · bộ skill riêng của DX-Lab, không commit (D-19).

## Định dạng
```text
<type>(<scope>): <mô tả tiếng Việt có dấu> (<MÃ-VIỆC>)
```
`scope`: `core`, `portal`, `deploy`, `apps`, `data`, `cli`, `mcp`, `docs`, `ci`... Ví dụ:
`fix(portal): liên kết hộp việc mở cùng tab (POR-03)`. Chi tiết: `CONTRIBUTING.md` mục "Quy ước commit message".

## Luôn
- `git commit -s` (DCO). Thiếu `Signed-off-by` thì check DCO đỏ, không merge được.
- Mỗi commit một ý; commit sửa lỗi review tách riêng, không trộn với thay đổi khác.
- Tệp mới có header SPDX: mã Apache-2.0, tài liệu `.md` CC-BY-4.0 (mẫu trong `CONTRIBUTING.md`); JSON và `SKILL.md` khai báo qua `REUSE.toml` (đã có cho `apps/**`, `deploy/**/*.json`, `data/**`).
- Trước khi commit: `git status --short` và `git diff --cached --stat` để chắc không lọt tệp lạ.

## Không bao giờ commit
`.env`, token, mật khẩu, khóa; `.venv/`, `__pycache__/`, `dist/`; ảnh chụp chứa dữ liệu cá nhân thật; tệp lớn sinh tự động; `.agents/skills/dxlab-*/`.
`uv.lock` chỉ khi chính PR đổi dependency, và phải do `uv lock` sinh ra.
