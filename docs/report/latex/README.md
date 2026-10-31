<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Báo cáo kỹ thuật dạng LaTeX

Nguồn của `docs/report/DX-Lab-v0.2.1-bao-cao-ky-thuat.pdf` (9 trang A4, gồm trang bìa). Nội dung biên tập từ
`BAO-CAO-PHAN-1.md` và `BAO-CAO-PHAN-2.md`, cập nhật theo bản `v0.2.1`.

## Biên dịch

Dùng [Tectonic](https://tectonic-typesetting.github.io/) (MIT, động cơ XeTeX, tự tải gói LaTeX ở lần chạy đầu nên cần
mạng). Đã build bằng Tectonic 0.17.0.

```bash
cd docs/report/latex
tectonic -X compile dx-lab-bao-cao-ky-thuat.tex
cp dx-lab-bao-cao-ky-thuat.pdf ../DX-Lab-v0.2.1-bao-cao-ky-thuat.pdf
```

Tectonic ghi PDF cạnh tệp `.tex`; chỉ bản trong `docs/report/` được commit.

## Phông chữ

Tệp dùng `fontspec` với phông hệ thống có đủ dấu tiếng Việt:

| Vai trò | Phông | Ghi chú |
|---|---|---|
| Chính | Times New Roman | có sẵn trên macOS và Windows |
| Không chân | Arial | tiêu đề, nhãn hình |
| Đơn cách | Menlo | chỉ dùng cho tên tệp, lệnh, mã; không có dấu tiếng Việt nên không đặt chữ có dấu trong khối mã |

Trên Linux, cài các phông trên (hoặc đổi ba dòng `\setmainfont`, `\setsansfont`, `\setmonofont` ở đầu tệp sang phông
tương đương như Liberation Serif, Liberation Sans, DejaVu Sans Mono) rồi biên dịch lại.

Các phông Times New Roman, Arial và Menlo là phông hệ thống có bản quyền riêng, không đi kèm repo; PDF đã nhúng phần
glyph cần dùng.
