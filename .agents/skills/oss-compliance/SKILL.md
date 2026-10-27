---
name: oss-compliance
description: "Dùng skill này khi làm bất cứ việc gì chạm tới tuân thủ nguồn mở của DX-Lab: thêm hoặc sửa giấy phép, thêm SPDX header, thêm dependency hoặc tập dữ liệu mới, rà soát trước khi commit hoặc mở PR, kiểm tra repo theo tiêu chí chấm điểm PoF của đề tuyển chọn HaUI và thể lệ OLP Phần mềm nguồn mở 2026, xử lý mã hoặc dữ liệu bên thứ ba, quyết định giấy phép cho tệp mới, hoặc trả lời câu hỏi kiểu 'repo đã đúng chuẩn nguồn mở chưa'. Trigger khi thấy nhắc tới REUSE, SPDX, LICENSE, Apache-2.0, CC BY, ShareAlike, SBOM, bundling, vendoring, BTC, VFOSSA, PoF, hoặc điểm trừ."
---

# Tuân thủ nguồn mở — DX-Lab

Rà soát tuân thủ theo đề tuyển chọn HaUI 2026, thể lệ OLP PMNM 2026 và các tiêu chuẩn đã chốt cho dự án.

**Quy tắc nền:** skill này chỉ hướng dẫn kiểm tra và thu thập bằng chứng. Nó **không**
tuyên bố dự án đã tuân thủ, không kết luận tương thích pháp lý, và không quy đổi ra điểm
của BTC. Việc nào cần con người quyết định thì phải nói rõ là cần con người quyết định.

## Nguồn sự thật

| Nội dung | Nguồn |
|---|---|
| Yêu cầu nguồn mở bắt buộc, rubric 100 điểm, lỗi bị trừ điểm | Đề tuyển chọn HaUI mục 5, 11, 12 (`docs/De_thi_PMNM_HaUI_2026_BAN_CHINH_THUC.pdf`, chỉ có trên máy đội, không commit) |
| Thể lệ vòng Quốc gia | <https://vfossa.vn/tin-tuc/the-le-olp-phan-mem-nguon-mo-nam-2026-760.html> |
| Quyết định giấy phép theo loại tài sản | Mục "Giấy phép" trong `README.md` |

Trích dẫn tiêu chí từ nguồn trên, đừng nhắc lại từ trí nhớ.

## Lệnh kiểm tra bắt buộc

```bash
uvx reuse lint            # bản quyền + giấy phép cấp tệp
uv build --all-packages   # mọi gói build được từ mã nguồn
```

Không bao giờ tự báo "pass" khi chưa chạy thật và chưa đọc exit code.

## Quyết định giấy phép cho tệp mới

| Loại tệp | SPDX identifier | Cách khai báo |
|---|---|---|
| Mã nguồn, script, cấu hình build (`.py`, `.sh`, `.toml`, `.yml`) | `Apache-2.0` | Comment header ở đầu tệp |
| Tài liệu (`.md`) | `CC-BY-4.0` | Comment header HTML |
| Tệp không comment được (`.json`, ảnh, `.pptx`, `uv.lock`) | Theo loại nội dung | Mục `[[annotations]]` trong `REUSE.toml` |
| `SKILL.md` | `Apache-2.0` | `REUSE.toml` — **không** chèn header |
| Dữ liệu bên thứ ba | Giữ nguyên giấy phép gốc | `REUSE.toml` + manifest nguồn |

**Bẫy đã biết:** `SKILL.md` bắt buộc mở đầu bằng YAML frontmatter. Chèn comment phía trên
sẽ làm hỏng frontmatter và skill mất `name`/`description`. Luôn khai báo qua `REUSE.toml`.

Mẫu header:

```python
# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0
```

```markdown
<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->
```

Dùng giấy phép mới → thêm toàn văn vào `LICENSES/<SPDX-ID>.txt` **trong cùng PR**, lấy bản
chuẩn từ <https://github.com/spdx/license-list-data/tree/main/text>. REUSE quy định
`LICENSES/` chỉ được chứa giấy phép đang thực sự dùng: không thêm sẵn "để dành", và xóa
khi giấy phép không còn tệp nào tham chiếu.

## Giới hạn của `reuse lint` — đọc kỹ trước khi kết luận

REUSE 3.3 loại các tệp sau khỏi phạm vi kiểm tra: tệp bị VCS ignore, tệp rỗng (0 byte),
`LICENSES/`, `LICENSE`/`COPYING`, `REUSE.toml`, thư mục `.reuse/`, submodule.

Hệ quả thực tế:

- Lint xanh **không** chứng minh `README.md` có nội dung — tệp rỗng vẫn qua.
- Lint xanh **không** phủ những gì đã bị `.gitignore`. Không dùng `.gitignore` để giấu
  tài sản thực sự được phân phối; chỉ ignore thứ thật sự không phát hành.
- Lint **không** xét tương thích giữa các giấy phép, và không xác minh người ghi header
  có thực quyền cấp phép.

Khi tạo fixture để thử negative case, dùng tệp **có nội dung, được Git theo dõi, thiếu header**.
Tệp rỗng hoặc bị ignore sẽ cho cảm giác an toàn giả.

## Checklist theo tiêu chí PoF (Phần I — 50 điểm)

Chạy theo thứ tự; mỗi mục ghi lại bằng chứng quan sát được, không ghi "OK" suông.

### I.1 — Quản lý mã nguồn (5đ)

- Repo truy cập được từ Internet khi **chưa đăng nhập**, có web viewer xem source và lịch sử.
- Lịch sử có commit trung gian và review thật, không phải một commit dồn cuối kỳ.

### I.2 — Giấy phép OSI-approved (10đ; mỗi lỗi −5)

- `LICENSE` ở gốc chứa **toàn văn** Apache-2.0. URL hay chuỗi SPDX không thay được toàn văn.
- Mọi tệp mã có khai báo giấy phép → `uvx reuse lint`.
- README nêu rõ phạm vi cấp phép cho từng loại tài sản (mã / tài liệu / dữ liệu).
- Không có mã hay dữ liệu bên thứ ba bị cấp phép sai. **Kiểm tra riêng** mọi thứ có
  điều khoản cấm phân phối lại — thứ đó không được nằm trong repo.
- Apache-2.0 §4 khi phân phối lại: kèm bản sao license (a); ghi rõ tệp đã sửa đổi (b);
  giữ notices liên quan (c); giữ NOTICE nếu upstream có (d). NOTICE **không** bắt buộc tự tạo
  khi không có nghĩa vụ tương ứng.

### I.3 — Bản phát hành (5đ)

- Có release tạo **trước hạn nộp**, gắn tag phiên bản bất biến.
- Artifact nguồn dùng `.tar.gz` kèm checksum. Thể lệ liệt kê `.zip`, `.rar`, `.arj` trong
  ví dụ định dạng bị trừ điểm → không nộp `.zip` làm gói chính.

### I.4 — Build từ mã nguồn (10đ; mỗi lỗi −5)

- Có hướng dẫn build đủ để người ngoài làm theo trên máy sạch.
- Cấu hình qua biến môi trường hoặc tệp config, **không** phải sửa source hay header.
- Toolchain hoàn toàn nguồn mở.
- Chạy được **ngoài** thư mục mã nguồn — xem quy trình 5 bước trong skill
  `release-readiness` mục 4. Editable install (`pip install -e`) không chứng minh được tiêu chí này.

### I.5 — Thư viện và bundling (10đ; mỗi lỗi −5)

- Phụ thuộc khai báo qua manifest, tải từ chỉ mục công khai.
- Không commit `.venv/`, `node_modules/`, mã thư viện copy tay, artifact build.
- Bắt buộc phải bundle → khai báo tên + phiên bản từng thành phần và lý do
  (theo mẫu `bundled(<name>) = <version>` của Fedora).
- Không sửa mã bên thứ ba rồi giấu: patch phải conditionalize và gửi upstream.

### I.6 — Tài liệu và giao tiếp (10đ; mỗi lỗi −5)

- Bug tracker công khai, có issue thật và phản hồi thật.
- `CHANGELOG.md` theo phiên bản, viết cho người dùng. `git log` thô không tính.
- `README.md` đủ để người lạ hiểu, cài và chạy.

## Khi thêm dependency hoặc tập dữ liệu mới

1. Ghi lại: tên, phiên bản, nguồn, giấy phép, ngày lấy, checksum.
2. Đối chiếu giấy phép với mục "Giấy phép" trong `README.md`.
3. Dữ liệu CC BY-SA khi chia sẻ: giữ attribution/notices/source URI mà upstream cung cấp,
   ghi rõ đã sửa gì; bản chuyển thể phải dùng giấy phép cùng License Elements hoặc
   BY-SA Compatible License. Lưu ý: chỉ biến đổi kỹ thuật (đổi định dạng) **không** tự
   tạo Adapted Material; nhưng trích xuất phần đáng kể của cơ sở dữ liệu có thể phát sinh
   nghĩa vụ riêng.
4. Giấy phép cấm phân phối lại, hoặc không phải OSI-approved cho thành phần lõi → **dừng lại
   và báo người phụ trách**, đừng tự quyết.

## SBOM — hai tầng, không thay thế nhau

| Tầng | Công cụ | Trả lời câu hỏi |
|---|---|---|
| Giấy phép cấp tệp của repo | `reuse spdx` | Từng tệp trong repo thuộc giấy phép nào |
| Thành phần thực tế của artifact | `syft` (CycloneDX/SPDX) | Bản phát hành thực sự chứa package nào |

Một tầng không thay tầng kia. SBOM cũng không chứng nhận không có CVE và không kết luận
tương thích giấy phép.

## Việc phải hỏi người, không tự quyết

Các điểm sau còn mơ hồ trong thể lệ. Khi gặp, nêu rõ là điểm cần BTC giải thích thay vì đoán:

- Header SPDX ngắn có đủ cho yêu cầu "giấy phép ghi trong từng tệp mã" không.
- BTC hiểu "bundling" thế nào với OCI image, wheel và bộ cài offline.
- Cách xử lý nếu bắt buộc phải nộp `.zip`.

## Báo cáo kết quả rà soát

Trả về theo dạng:

```text
Đã chạy:      uvx reuse lint → <exit code, tóm tắt>
              uv build --all-packages → <exit code>
Đạt:          <tiêu chí + bằng chứng quan sát được>
Chưa đạt:     <tiêu chí + tệp/dòng cụ thể + cách sửa>
Cần con người: <quyết định giấy phép, điểm cần hỏi BTC>
Chưa kiểm tra: <những gì nằm ngoài khả năng kiểm tra cục bộ, ví dụ trạng thái repo từ xa>
```

Luôn có mục "Chưa kiểm tra". Bỏ trống mục đó gần như luôn là thiếu trung thực: trạng thái
repo công khai, issue tracker và release chỉ xác minh được trên forge, không phải từ máy cục bộ.
