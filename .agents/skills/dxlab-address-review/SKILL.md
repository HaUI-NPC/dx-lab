---
name: dxlab-address-review
description: "Dùng khi PR dx-lab của mình có review hoặc comment cần xử lý, bị xung đột, hoặc cần rebase sau khi main thay đổi."
---

# Xử lý review

> Phiên bản 1.0 · 30/10/2026 · bộ skill riêng của DX-Lab, không commit (D-19).

## Đọc toàn bộ góp ý
```bash
gh pr view <n> --comments
gh api repos/HaUI-NPC/dx-lab/pulls/<n>/comments --jq '.[]|"\(.path):\(.line) \(.body)"'
gh api repos/HaUI-NPC/dx-lab/pulls/<n>/reviews --jq '.[]|"\(.user.login) \(.state) \(.body)"'
```

## Với mỗi góp ý
1. **Tái hiện trước khi sửa** nếu là lỗi: viết test thất bại đúng như mô tả. Không tái hiện được thì trả lời kèm bằng chứng, không sửa mò.
2. Sửa trong commit riêng (`fix(...): ... (<MÃ-VIỆC>)`), chạy lại kiểm chứng.
3. Kiểm test bắt được lỗi: tạm bỏ bản sửa, test phải đỏ; trả lại bản sửa, test xanh.
4. Trả lời trên PR: mỗi góp ý đã làm gì, commit nào, test nào; điều gì cố ý không làm và vì sao. Không tự resolve thread của mentor.

## Xung đột sau khi main đổi (thường gặp với `uv.lock`)
```bash
git fetch origin && git rebase origin/main
# xung đột uv.lock: lấy bản của main rồi sinh lại
# (khi rebase, "--theirs" là commit của nhánh mình, không phải main: đừng dùng)
git checkout origin/main -- uv.lock
uv lock && git add uv.lock && git rebase --continue
git push --force-with-lease
```
- Chỉ `--force-with-lease`, không `--force`; chỉ trên nhánh của chính mình.
- Rebase làm mất approve: ghi trên PR "rebase thuần, `git range-diff` không đổi nội dung" để reviewer approve lại nhanh.
- Chạy lại test sau rebase trước khi đẩy.
