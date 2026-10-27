<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Chính sách bảo mật

## Báo cáo lỗ hổng

**Không mở issue công khai cho lỗ hổng bảo mật.**

Kênh báo cáo riêng tư, theo thứ tự ưu tiên:

1. **GitHub private vulnerability reporting** — tab `Security` của repo → `Report a vulnerability`.
   Đây là kênh chính; hoạt động mà không cần trao đổi email và giữ kín nội dung trao đổi.
2. Liên hệ trực tiếp đầu mối bảo mật trong [`MAINTAINERS.md`](MAINTAINERS.md).

Khi báo cáo, nêu rõ nếu có: phiên bản hoặc commit bị ảnh hưởng, môi trường, các bước tái hiện,
tác động dự đoán và bản vá đề xuất.

## Cam kết phản hồi

| Mốc | Thời hạn |
|---|---|
| Xác nhận đã nhận báo cáo | Trong vòng 14 ngày |
| Đánh giá mức độ ảnh hưởng và phản hồi hướng xử lý | Trong vòng 30 ngày |
| Công bố sau khi có bản vá | Thống nhất với người báo cáo |

Dự án đang trong giai đoạn phát triển của một đội sinh viên, chưa có cam kết hỗ trợ dài hạn
cho các phiên bản cũ. Mọi bản vá bảo mật áp dụng cho nhánh `main` và bản phát hành gần nhất.

## Phạm vi

Trong phạm vi xử lý:

- Mã nguồn thuộc repo này.
- Cấu hình triển khai mẫu và script cài đặt do dự án cung cấp.

Ngoài phạm vi:

- Lỗ hổng của các dịch vụ và thư viện nguồn mở bên thứ ba mà dự án tích hợp (PostgreSQL, Keycloak,
  Apache APISIX, SpiffWorkflow, zvec…). Vui lòng báo cho upstream tương ứng; nếu dự án
  cần nâng phiên bản hoặc đổi cấu hình mặc định để giảm rủi ro, hãy mở issue công khai
  cho phần cấu hình đó.
- Dữ liệu công khai của bên thứ ba dùng làm tập demo.

## Thực hành bảo mật của dự án

- Secret, token và khóa riêng không bao giờ được commit; cấu hình qua biến môi trường.
- Dữ liệu demo là dữ liệu công khai hoặc dữ liệu giả lập, không chứa thông tin cá nhân thật.
- Phụ thuộc được ghim phiên bản trong `uv.lock` và rà giấy phép trước khi thêm mới.
- Dự án tham chiếu [OpenSSF Security Baseline](https://baseline.openssf.org/versions/2025-02-25)
  Level 1 làm mức tối thiểu. Đây là mức tự đánh giá, không phải chứng nhận.
