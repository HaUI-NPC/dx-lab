---
name: dxlab-open-pr
description: "Dùng khi đã xong tiêu chí Xong khi của một issue dx-lab và cần mở pull request: tự rà diff, mở draft theo mẫu với bằng chứng chạy thật, chờ CI xanh rồi chuyển ready và yêu cầu review."
---

# Mở pull request

> Phiên bản 1.0 · 30/10/2026 · bộ skill riêng của DX-Lab, không commit (D-19).

## Tự rà trước
- `git fetch origin && git rebase origin/main` (nhánh phải dựa trên `main` mới nhất).
- `git diff --name-only origin/main...`: chỉ tệp trong "Phạm vi tệp".
- Chạy lại kiểm chứng sau rebase (xem `dxlab-implement-issue`).

## Mở
```bash
git push -u origin HEAD
gh pr create --draft --base main --title "<type>(<scope>): <mô tả> (<MÃ-VIỆC>)" --body-file <tệp>
```
Body theo `.github/pull_request_template.md`, đủ các mục:
- `Closes #<N>`.
- **Thay đổi:** gạch đầu dòng ngắn.
- **Kiểm chứng:** lệnh đã chạy và **kết quả thật** (dán đầu ra). Không ghi "đã test" suông, không dùng kết quả server giả làm bằng chứng.
- **Ảnh chụp:** bắt buộc nếu đổi giao diện.
- **Tự rà:** tick đúng sự thật. Ô `CHANGELOG.md` để trống và ghi "REL-02 tổng hợp" (không tự sửa).
- **Rủi ro, còn thiếu:** giới hạn, việc để lại (ghi số issue).

## Sau khi mở
1. `gh pr checks <n> --watch`. Đỏ thì sửa; không chuyển ready khi CI đỏ.
2. `gh pr ready <n>`, rồi `gh pr edit <n> --add-reviewer ngothetai` và thêm một thành viên khác để review chéo.
3. **Sau khi đã có approve, không đẩy thêm commit** nếu không cần: đẩy là mất approve.

## Không bao giờ
Tự merge, tự approve, đẩy thẳng `main`, mở PR có base là nhánh của PR khác chưa merge (trừ khi mentor đồng ý, tối đa 2 tầng).
