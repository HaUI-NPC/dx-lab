---
name: dxlab-dependency
description: "Dùng bất cứ khi nào muốn thêm hoặc nâng thư viện Python, image container, mô hình AI, hoặc dữ liệu bên thứ ba vào dx-lab."
---

# Thêm dependency

> Phiên bản 1.0 · 30/10/2026 · bộ skill riêng của DX-Lab, không commit (D-19).

1. Kiểm danh sách được phép: `docs/ARCHITECTURE.md` mục 8. **Không có trong danh sách: dừng**, comment trên issue, gắn `needs-mentor`, chờ duyệt.
2. Đã được phép:
   - Python: thêm vào `pyproject.toml` của đúng gói; gói pre-1.0 ghim `==`, gói khác `>=`; chạy `uv lock` (không sửa tay `uv.lock`).
   - Image: ghim digest.
   - Mô hình: giấy phép theo model card, chỉ tải bằng `scripts/download-models.sh`, không tải lúc chạy.
3. Ghi vào `docs/DEPENDENCIES.md` trong cùng PR: tên, phiên bản, giấy phép, nguồn.
4. Giấy phép theo skill `oss-compliance`; giấy phép cấm phân phối lại hoặc không OSI cho thành phần lõi: dừng, báo mentor.
5. PR đổi `uv.lock` dễ xung đột với PR khác: merge sớm, giữ nhỏ.
