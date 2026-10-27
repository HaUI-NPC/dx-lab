<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Maintainers

Danh sách người chịu trách nhiệm cho từng phần của dự án và người có quyền trên các tài
nguyên nhạy cảm (repo settings, secrets, quyền phát hành).

> **Trạng thái: PLACEHOLDER.** Toàn bộ mục `<...>` bên dưới phải được thay bằng thông tin
> thật trước khi công bố repo hoặc nộp bài. Xem [Việc phải hoàn tất](#việc-phải-hoàn-tất).

## Maintainer

| Vai trò | Tên | Liên hệ | GitHub | Phạm vi phụ trách |
|---|---|---|---|---|
| Lead / phát hành | `<Họ tên>` | `<email>` | `<@handle>` | Cắt release, gắn tag, duyệt merge cuối |
| Open-Core (Tầng 1) | `<Họ tên>` | `<email>` | `@ngothetai` | `core/`, Keycloak, APISIX, workflow, dữ liệu |
| Portal (Tầng 2/3) | `<Họ tên>` | `<email>` | `<@handle>` | `portal/`, giao diện H-P-D-I, ứng dụng báo hỏng |
| Data, Intelligence | `<Họ tên>` | `<email>` | `<@handle>` | Dữ liệu mẫu, provenance, phân loại, hỏi đáp tài liệu |

## Liên hệ bảo mật

| Vai trò | Tên | Liên hệ |
|---|---|---|
| Đầu mối bảo mật | `<Họ tên>` | `<email>` |
| Dự phòng | `<Họ tên>` | `<email>` |

Quy trình báo cáo và cam kết thời gian phản hồi: [`SECURITY.md`](SECURITY.md).
Kênh chính là GitHub private vulnerability reporting; các liên hệ trên là kênh dự phòng.

## Giảng viên hướng dẫn

| Vai trò | Tên | Đơn vị |
|---|---|---|
| Giảng viên hướng dẫn đội | `<Họ tên>` | Trường CNTT & Truyền thông, Đại học Công nghiệp Hà Nội |

## Quyền trên tài nguyên nhạy cảm

Theo `OSPS-GV-01.01` của [OpenSSF Security Baseline](https://baseline.openssf.org/versions/2025-02-25),
dự án công bố ai có quyền gì:

| Tài nguyên | Ai có quyền |
|---|---|
| Admin repository (settings, branch protection) | `<Họ tên>` |
| Quyền merge vào `main` | Toàn bộ maintainer, cần ít nhất một review không phải tác giả |
| Tạo release và tag | `<Họ tên>` (lead) |
| Secrets của CI | `<Họ tên>` (lead) |

Nguyên tắc: tối thiểu **hai người** có quyền admin để dự án không phụ thuộc một cá nhân.

## Trách nhiệm chung

Không giao riêng cho một người — cả đội cùng chịu trách nhiệm:

- Giấy phép và ghi nhận bản quyền (xem skill `oss-compliance`).
- Tài liệu cài đặt và vận hành luôn khớp với hành vi thật.
- Không để chỉ một người biết cách cài đặt hoặc chạy demo.

## Việc phải hoàn tất

Trước khi công bố repo hoặc nộp bài, thay toàn bộ placeholder:

- [ ] Điền tên, email, GitHub handle thật vào các bảng trên.
- [ ] Điền đầu mối bảo mật vào đây và kiểm tra [`SECURITY.md`](SECURITY.md) trỏ đúng.
- [ ] Tạo organization `HaUI-NPC` và repo công khai `HaUI-NPC/dx-lab`.
- [ ] Bật GitHub private vulnerability reporting trong tab `Security`.
- [ ] Bật branch protection cho `main`: yêu cầu PR, yêu cầu CI pass, chặn force-push.
- [ ] Bật xác thực đa yếu tố cho mọi tài khoản có quyền trên repo.
