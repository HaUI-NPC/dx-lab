---
name: dxlab-portal
description: "Dùng khi làm portal của dx-lab (Prefab, BFF Authlib, trang báo hỏng, hộp việc, dashboard, tra cứu, trạng thái) hoặc client MCP: POR-*, INT-02, INT-03."
---

# Portal và client

> Phiên bản 1.0 · 30/10/2026 · bộ skill riêng của DX-Lab, không commit (D-19).

Hợp đồng: `docs/ARCHITECTURE.md` mục 1–3 (portal là Tầng 2, chỉ gọi `/api` qua BFF), mục 8 (Prefab bundled, không bước build Node.js).

## Luật
- Mọi dữ liệu từ core qua BFF bằng **token của người dùng**; không token dịch vụ, không gọi database.
- Form sinh từ JSON Schema + UISchema của gói; không viết cứng trường, nhãn, vai trò, tên đơn vị.
- Hiển thị dữ liệu phiếu bằng tiêu đề từ core (`field_titles`), không in khóa nội bộ hay JSON thô. Tiền `12.000.000 đ`, giờ Việt Nam `30/10/2026 10:53`.
- Lỗi core hiện nguyên `code`, `message`, `request_id`; mã riêng của portal: `FORBIDDEN_ORIGIN` (403), `INTERNAL` 502/504 khi không tới được core.
- Căn cứ có mã `GĐ-` luôn kèm "(giả định)".
- Liên kết nội bộ mở cùng tab (`target="_self"`); Prefab mặc định mở tab mới.
- MCP: tool tên tiếng Việt không dấu `snake_case`, thao tác ghi phải xác nhận, token ở `DXLAB_TOKEN_FILE` (mode 0600).

## Kiểm chứng
- `uv run --all-packages pytest portal/tests`.
- Chạy portal dev `:8001` với core thật, đăng nhập Keycloak bằng tài khoản demo đúng vai trò (OTP nếu vai trò cần); chụp ảnh từng màn hình đã đổi.
- Kiểm cả vai trò **không** được thấy (ví dụ `ht.khanh` không thấy số điện thoại người báo).
