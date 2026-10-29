<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Changelog

Toàn bộ thay đổi đáng chú ý của dự án được ghi trong tệp này.

Định dạng dựa trên [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
và dự án tuân theo [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - Chưa phát hành

Ngày phát hành và nội dung tích hợp cuối cùng sẽ được chốt sau khi các phụ thuộc release được merge và kiểm chứng.

### Added

- Giấy phép Apache-2.0 cho mã nguồn và CC BY 4.0 cho tài liệu, kèm toàn văn trong `LICENSES/`.
- Tuân thủ [REUSE 3.3](https://reuse.software/spec-3.3/): SPDX header trong tệp mã, `REUSE.toml` cho tệp không chứa được comment.
- `README.md`, `CONTRIBUTING.md` (yêu cầu DCO sign-off), `SECURITY.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1), `MAINTAINERS.md`.
- uv workspace gồm hai gói tách biệt: `dxlab-core` (Tầng 1, Open-Core headless) và `dxlab-portal` (Tầng 2/3, giao diện Prefab).
- CI GitHub Actions: `reuse lint`, build từng gói rồi cài vào môi trường sạch và import từ ngoài cây mã nguồn, kiểm tra DCO trên PR.
- Mẫu báo lỗi, đề xuất tính năng và định tuyến báo cáo bảo mật cho bug tracker công khai.

### Changed

- Quy trình đóng góp: mọi thay đổi vào `main` qua Pull Request gắn với issue, tên nhánh theo mã việc, chỉ maintainer chính merge, chỉ gộp kiểu rebase.
- `MAINTAINERS.md` ghi người phụ trách và quyền thực tế trên repo; README cập nhật kiến trúc và thành phần dự kiến.

### Fixed

- CI: ghim `astral-sh/setup-uv` theo commit của bản v10.3.2 (action không phát hành tag `v10`).

[Unreleased]: https://github.com/HaUI-NPC/dx-lab/commits/main
