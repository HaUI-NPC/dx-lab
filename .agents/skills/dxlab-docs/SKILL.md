---
name: dxlab-docs
description: "Dùng khi viết tài liệu, báo cáo, slide, kịch bản demo của dx-lab (DOC-*, DEMO-01, README, docs/)."
---

# Tài liệu

> Phiên bản 1.0 · 30/10/2026 · bộ skill riêng của DX-Lab, không commit (D-19).

## Luật
- Tiếng Việt có dấu, ngắn, cho người đọc ngoài đội. Header REUSE CC-BY-4.0 cho `.md` (mẫu trong `CONTRIBUTING.md`).
- **Chỉ mô tả cái đã chạy được**, trên `main` hoặc đã kiểm chứng. Tính năng chưa xong ghi ở mục "Lộ trình".
- Giả định luôn có nhãn "giả định" (mã `GĐ-…`); không trình bày như văn bản hay số liệu thật của HaUI.
- Trích nguồn cho mọi số liệu, quy định, dữ liệu bên thứ ba ([QC], [PL] như AUTHZ mục 0).
- Không đưa phân tích chấm điểm nội bộ, rủi ro nội bộ (`.local/`) ra tài liệu công khai.
- Ảnh chụp không chứa dữ liệu cá nhân thật hay token.
- Lệnh trong tài liệu phải chạy được nguyên văn; đã chạy thử trước khi ghi.
- Không sửa `docs/ARCHITECTURE.md`, `docs/AUTHZ.md`, `CONTRIBUTING.md` nếu issue không cho phép.

## Kiểm chứng
- `uvx reuse lint` xanh; mở bản xem trước Markdown (bảng, Mermaid hiện đúng).
- README/hướng dẫn: một người khác làm theo được từ đầu (QA-01).
