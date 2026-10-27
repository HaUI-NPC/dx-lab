<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Maintainers

Người chịu trách nhiệm cho dự án và người có quyền trên các tài nguyên nhạy cảm
(cài đặt repo, secret, quyền phát hành), theo `OSPS-GV-01.01` của
[OpenSSF Security Baseline](https://baseline.openssf.org/versions/2025-02-25).

## Maintainer chính

| GitHub | Vai trò | Phạm vi |
|---|---|---|
| [@ngothetai](https://github.com/ngothetai) | Mentor đội HaUI.NPC, maintainer chính | Kiến trúc Open-Core, `core/`, định nghĩa quy trình trong `apps/`; review và **merge mọi PR**; cắt release |

## Thành viên đội thi

| GitHub | Vai trò |
|---|---|
| [@datthanhngobn](https://github.com/datthanhngobn) | Thành viên |
| [@kenchjm1991](https://github.com/kenchjm1991) | Thành viên |
| [@truongnguyenk7z-ship-it](https://github.com/truongnguyenk7z-ship-it) | Thành viên |

Công việc được giao theo issue; ai phụ trách việc gì xem người được gán trên từng issue.

## Liên hệ bảo mật

Kênh chính: GitHub private vulnerability reporting (tab `Security` → `Report a vulnerability`), đã bật trên repo.
Đầu mối xử lý: [@ngothetai](https://github.com/ngothetai). Quy trình và cam kết thời gian phản hồi:
[`SECURITY.md`](SECURITY.md).

## Quyền trên tài nguyên nhạy cảm

| Tài nguyên | Ai có quyền |
|---|---|
| Admin repository (cài đặt, bảo vệ nhánh) | @ngothetai |
| Merge vào `main` | Chỉ @ngothetai; cần ít nhất một review chấp thuận của người khác tác giả và CI xanh |
| Đẩy nhánh, mở PR | Mọi thành viên đội |
| Tạo release và tag | @ngothetai |
| Secret của CI | @ngothetai |

Bảo vệ nhánh `main` đang bật: bắt buộc PR, 1 review, 3 kiểm tra CI (REUSE, build sạch, DCO), áp cả với admin,
lịch sử thẳng, cấm force-push và xóa nhánh, chỉ @ngothetai được merge.

## Trách nhiệm chung

Cả đội cùng chịu trách nhiệm, không giao riêng một người:

- Giấy phép và ghi nhận bản quyền (xem skill `oss-compliance`).
- Tài liệu cài đặt và vận hành luôn khớp với hành vi thật.
- Không để chỉ một người biết cách cài đặt hoặc chạy demo.

## Việc phải hoàn tất

- [x] Tạo organization `HaUI-NPC` và repo công khai `HaUI-NPC/dx-lab`.
- [x] Bật GitHub private vulnerability reporting.
- [x] Bật bảo vệ nhánh `main`.
- [ ] Bật xác thực đa yếu tố (MFA) cho mọi tài khoản có quyền trên repo.
