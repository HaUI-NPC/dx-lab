---
name: dxlab-implement-issue
description: "Dùng khi đang thực hiện một issue của dx-lab: viết code, tài liệu, dữ liệu theo đúng phạm vi tệp và tiêu chí Xong khi của issue, rồi chạy Cách kiểm chứng."
---

# Làm một issue

> Phiên bản 1.0 · 30/10/2026 · bộ skill riêng của DX-Lab, không commit (D-19).

## Luật
- **Chỉ sửa tệp trong "Phạm vi tệp".** Trước khi commit: `git diff --name-only origin/main...` và đối chiếu từng tệp.
- Theo mẫu có sẵn trên `main` thay vì đặt quy ước mới. Ví dụ route mới của core: `response_model`, `summary` tiếng Việt, lỗi qua `ApiError`, ghi audit trong cùng transaction.
- Không đổi hợp đồng API, không thêm thư viện ngoài `docs/ARCHITECTURE.md` mục 8.
- Không để lại `TODO`, stub, mock giả, test rỗng, dữ liệu "tạm". Phần nào không làm được: ghi vào mục "Rủi ro, còn thiếu" của PR.
- Thiếu thông tin ở một hệ thống khác (core chưa có route, form chưa có trường): làm phần làm được, **không giả lập để báo xong**, ghi rõ trong PR.

## Kiểm chứng (bắt buộc trước khi mở PR)
1. Chạy đúng các lệnh trong "Cách kiểm chứng" của issue, lưu đầu ra thật.
2. Test core cần PostgreSQL thật:
   ```bash
   DXLAB_TEST_DATABASE_URL=postgresql+psycopg://dxlab:dxlab@127.0.0.1:55432/postgres uv run --all-packages pytest core/tests
   ```
   Portal: `uv run --all-packages pytest portal/tests`.
3. Gói ứng dụng: `uv run --package dxlab-core dxlab validate apps/`.
4. `uvx reuse lint` phải xanh.
5. Có giao diện: chạy portal, chụp ảnh bằng tài khoản demo thật.
6. Có API: gọi thật qua APISIX (`http://localhost:9080/api`) bằng token tài khoản demo (AUTHZ mục 11), không qua token quản trị.

Xong khi mọi mục "Xong khi" có bằng chứng. Sau đó dùng `dxlab-commit` rồi `dxlab-open-pr`.
