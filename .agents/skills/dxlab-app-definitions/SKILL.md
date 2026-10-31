---
name: dxlab-app-definitions
description: "Dùng khi làm gói ứng dụng trong apps/ hoặc dữ liệu mẫu data/ của dx-lab: JSON Schema form, uischema, process_model.json, records schema, DATA_SOURCES (APP-02, APP-03, APP-05). Không dùng để viết BPMN/DMN."
---

# Gói ứng dụng và dữ liệu mẫu

> Phiên bản 1.0 · 30/10/2026 · bộ skill riêng của DX-Lab, không commit (D-19).

Hợp đồng: `docs/ARCHITECTURE.md` mục 7 (cấu trúc gói, quy ước Spiff, `data_defaults`, `record_bindings`), `docs/AUTHZ.md` (danh mục, trường cá nhân).

## Luật
- **Không viết hoặc sửa `.bpmn` / `.dmn`** (chỉ mentor, D-10). Cần đổi thì hỏi trên issue.
- Form: `<bước>-schema.json` + `<bước>-uischema.json`, tên trường khớp với biến BPMN/DMN đọc (đối chiếu trước khi đổi tên).
- Trường cá nhân: `"x-personal-data": true`. Với văn bản tự do (mô tả, ý kiến) không có cách che tự động (#97); đừng thêm ô chữ tự do khi không cần.
- Lựa chọn: `oneOf` với `const` + `title` tiếng Việt (portal hiển thị `title`); không chỉ `enum` khóa tiếng Anh.
- Ô đồng thuận không tick sẵn; không thêm chú thích nội bộ vào `title`.
- Danh mục (`records/<loại>-record.json`): đơn vị theo cây AUTHZ (`org_path`), không tự đặt mã ngoài cây.
- Dữ liệu mẫu có nguồn, giấy phép, nhãn "giả định" và ghi trong `DATA_SOURCES.yml`; không dữ liệu cá nhân thật.

## Kiểm chứng
- `uv run --package dxlab-core dxlab validate apps/` hợp lệ.
- Nạp thật qua `dxlab publish` (tài khoản `process_admin`), duyệt bằng `process_owner` khác người nạp, tạo phiếu và đi qua bước có form vừa đổi.
- Dữ liệu: nạp qua `/api/records` bằng `facility_officer`, mọi bản ghi qua schema.
