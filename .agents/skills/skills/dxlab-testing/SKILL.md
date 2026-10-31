---
name: dxlab-testing
description: "Dùng khi viết hoặc sửa test trong dx-lab, hoặc làm TEST-01, TEST-02 (pytest core, 14 kịch bản phân quyền, demo-e2e.sh qua APISIX)."
---

# Kiểm thử

> Phiên bản 1.0 · 30/10/2026 · bộ skill riêng của DX-Lab, không commit (D-19).

Luật gốc: `CONTRIBUTING.md` mục "Kiểm thử".

## Viết test khi
Nó bắt được một lỗi hợp lý mà người dùng thấy được: hành vi, ranh giới, quyền, chuyển trạng thái, thứ tự ưu tiên, lỗi trả về.

## Không viết test
- Kiểm giá trị mặc định, chuỗi nội bộ, việc gọi đúng hàm, mock trả lại chính nó, chép lại schema.
- "Không ném lỗi" suông, "danh sách không rỗng".
- Test cũ chỉ kiểm câu chữ hay cách hiện thực: xóa, không viết lại cho khớp.

## Cách làm
- Core: PostgreSQL thật qua `DXLAB_TEST_DATABASE_URL`; token qua fixture `headers_for(username, groups)` trong `conftest.py`.
- Kịch bản phân quyền: một test cho mỗi kịch bản AUTHZ mục 12, kiểm cả mã lỗi (`FORBIDDEN_SCOPE`, `FORBIDDEN_SOD`...) và `details.layer`.
- Sửa lỗi: viết test đỏ trước; kiểm lại bằng cách tạm bỏ bản sửa.
- `demo-e2e.sh` (TEST-02): chỉ dùng curl qua APISIX `:9080` với token tài khoản demo, kiểm mã HTTP và trường trạng thái từng bước, dừng khi sai.
- Test phải xác định: không phụ thuộc thứ tự chạy, giờ hệ thống, mạng ngoài.
