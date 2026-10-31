---
name: dxlab-pick-issue
description: "Dùng khi được bảo 'lấy việc', 'làm issue tiếp theo', 'bắt đầu issue #N' trong repo dx-lab: chọn issue được gán cho mình, kiểm phụ thuộc, nhận việc, tạo nhánh từ origin/main."
---

# Nhận một issue

> Phiên bản 1.0 · 30/10/2026 · bộ skill riêng của DX-Lab, không commit (D-19).

## Các bước
1. `gh issue list -R HaUI-NPC/dx-lab --assignee @me --state open` rồi chọn theo **milestone sớm nhất**, sau đó ưu tiên `p0` > `p1` > `p2`. Hoặc dùng số issue người dùng chỉ định.
2. `gh issue view <N>`: đọc đủ **Mục tiêu, Phạm vi tệp, Không làm, Phụ thuộc, Xong khi, Cách kiểm chứng**.
3. **Kiểm phụ thuộc:** mỗi issue ở mục "Phụ thuộc" phải `CLOSED` (`gh issue view <dep> --json state`). Chưa đóng: dừng, báo người dùng, không bắt đầu.
4. Kiểm đã có PR cho issue này chưa: `gh pr list --search "<MÃ-VIỆC> in:title" --state all`. Có rồi thì dùng skill `dxlab-address-review` hoặc hỏi, không mở PR thứ hai.
5. Comment nhận việc kèm kế hoạch ≤ 5 bước: `gh issue comment <N> --body "..."`.
6. Nhánh từ `main` mới nhất:
   ```bash
   git fetch origin && git switch -c <type>/<MÃ-VIỆC>-<mô-tả-ngắn> origin/main
   ```
   `type`: `feat`, `fix`, `docs`, `test`, `ci`, `chore`. Ví dụ `feat/POR-06-so-do-quy-trinh`.

## Không bao giờ
- Nhận issue không gán cho mình, hoặc đổi người nhận, nhãn, milestone của issue người khác.
- Tạo nhánh từ nhánh của một PR chưa merge (xem "Không xếp chồng quá 2 tầng" trong `dxlab-contract`).
- Bắt đầu khi phụ thuộc chưa đóng.
