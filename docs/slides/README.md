<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Slide trình bày DX-Lab v0.2.1

- `slides.md`: nguồn slide viết theo cú pháp [Slidev](https://sli.dev/), 12 slide (đề mục 10 giới hạn tối đa 12).
- `DX-Lab-v0.2.1-slides.pdf`: bản PDF xuất từ `slides.md`, dùng để nộp và chiếu.

Số liệu lấy từ `README.md`, `CHANGELOG.md`, `docs/AI.md` và các tài liệu trong `docs/`. Hạn mức duyệt, cơ cấu tổ chức,
tài khoản demo là **giả định** của đội HaUI.NPC.

## Xem và xuất slide

Slidev (giấy phép MIT) **chỉ dùng để dựng slide**, không thuộc sản phẩm DX-Lab và không được thêm vào repo: repo không có
`package.json` hay lockfile Node. Chạy trong một thư mục tạm ngoài repo, cần Node.js:

```bash
mkdir /tmp/slidev-build && cd /tmp/slidev-build
cp <đường-dẫn-repo>/docs/slides/slides.md .

# Xem trực tiếp trong trình duyệt
npx @slidev/cli slides.md

# Xuất PDF (xuất PDF cần thêm playwright-chromium)
npm i -D @slidev/cli playwright-chromium
npx slidev export slides.md --output dx-lab-slides.pdf --timeout 120000
```

Bản PDF trong repo được dựng bằng `@slidev/cli` 53.0.0 và `playwright-chromium`. Sơ đồ Mermaid được vẽ lúc xuất.
