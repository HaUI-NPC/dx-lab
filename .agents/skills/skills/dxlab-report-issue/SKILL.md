---
name: dxlab-report-issue
description: "Dùng khi gặp lỗi, lỗ hổng, hoặc việc ngoài phạm vi issue đang làm trong dx-lab: ghi lại thành issue mới thay vì sửa lan trong PR hiện tại."
---

# Báo việc ngoài phạm vi

> Phiên bản 1.0 · 30/10/2026 · bộ skill riêng của DX-Lab, không commit (D-19).

Dùng khi: thấy lỗi ở mảng khác, việc cần làm sau, hay tiêu chí chưa kiểm được. Không sửa lan trong PR đang làm.

```bash
gh issue create -R HaUI-NPC/dx-lab --title "[<MÃ hoặc mảng>] <mô tả ngắn>" --body-file <tệp> --label <area:...>,<p0|p1|p2>
```

Body theo khuôn của dự án: **Mục tiêu, Bối cảnh** (thấy ở PR/commit nào, tái hiện thế nào), **Cần làm, Phụ thuộc, Xong khi** (kiểm chứng được), **Không làm**.

- Lỗi bảo mật hay lộ dữ liệu cá nhân: `p0` hoặc `p1`, nhắc mentor ngay trong PR liên quan.
- Cần mentor quyết (kiến trúc, thư viện, hợp đồng): thêm `needs-mentor`.
- Ghi đúng trạng thái: nếu phụ thuộc là PR chưa merge thì ghi "chưa merge", không ghi "đã merge".
- Không gán người, không đặt milestone thay mentor; nhắc mentor trong body nếu cần.
