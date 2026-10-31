---
name: release-readiness
description: "Dùng skill này khi chuẩn bị hoặc kiểm tra một bản phát hành của DX-Lab: cắt release, gắn tag phiên bản, viết changelog, đóng gói source tarball, tạo checksum và SBOM, kiểm thử cài đặt sạch từ mã nguồn, chuẩn bị nộp bài dự thi, hoặc trả lời 'bản phát hành đã sẵn sàng chưa'. Trigger khi thấy nhắc tới release, phát hành, tag, version, SemVer, changelog, tar.gz, checksum, đóng gói, docker compose, hoặc nộp bài."
---

# Kiểm tra sẵn sàng phát hành — DX-Lab

Quy trình cắt một bản phát hành mà người ngoài tải về, build và chạy được.

**Quy tắc nền:** mỗi mục dưới đây chỉ được đánh dấu đạt khi đã **thực sự chạy** và quan sát
được kết quả. Không suy ra từ việc CI xanh, không suy ra từ việc code "đáng lẽ chạy được".
Một bước fail nghĩa là release chưa đạt — sửa nguồn, không vá bằng tệp nằm ngoài artifact.

## Điều kiện tiên quyết

Chạy skill `oss-compliance` trước. Release có lỗi giấy phép thì không cắt.

## 1. Đánh phiên bản

Theo [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html):

- Dự án chưa ổn định API → dùng `0.y.z`. Không gắn `1.0.0` chỉ vì sắp nộp bài.
- Nội dung một phiên bản đã phát hành là **bất biến**. Cần sửa → phát hành phiên bản mới,
  không sửa đè lên tag cũ.
- Tag Git phải khớp `version` trong `pyproject.toml` của gốc workspace và của từng gói.

## 2. Changelog

Theo [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/):

- Chuyển nội dung `[Unreleased]` sang mục phiên bản mới kèm ngày dạng `YYYY-MM-DD`.
- Nhóm theo `Added` / `Changed` / `Deprecated` / `Removed` / `Fixed` / `Security`.
- Viết cho người dùng: nêu ảnh hưởng và breaking change, không dán `git log`.

## 3. Đóng gói

- Artifact nguồn: `.tar.gz`. **Không** dùng `.zip` làm gói chính — thể lệ liệt kê `.zip`,
  `.rar`, `.arj` trong ví dụ định dạng bị trừ điểm.
- Sinh checksum cho từng artifact:

  ```bash
  shasum -a 256 <artifact> > <artifact>.sha256
  ```

- Artifact **không** được chứa `.venv/`, `node_modules/`, mã thư viện bên thứ ba copy tay,
  secret, hay dữ liệu cá nhân thật.
- Kiểm tra danh mục thành phần trước khi phát hành:

  ```bash
  tar -tzf <artifact>.tar.gz | less
  ```

## 4. Kiểm thử cài đặt sạch — bắt buộc

Thực hiện đủ 5 bước:

1. Build artifact từ bản checkout sạch của đúng commit sẽ gắn tag.
2. Tạo môi trường hoàn toàn mới (venv hoặc container), cài artifact vừa build.
   **Không** dùng editable install, **không** mount source tree.
3. `cd` sang thư mục khác, ngoài cây mã nguồn, rồi chạy entrypoint và health check.
4. Lặp lại từ chính `.tar.gz` của release: giải nén → dựng toàn bộ stack bằng Docker Compose →
   chạy kịch bản demo đầu-cuối → chạy lệnh reset dữ liệu mẫu → chạy lại lần hai.
5. Lưu log và checksum làm bằng chứng.

Bước 3 là bước hay bị bỏ qua nhất và đúng vào tiêu chí trừ điểm
"chương trình không thể hoạt động nếu nằm ngoài thư mục mã nguồn".

## 5. Bảng kê thành phần

- SBOM dependency của artifact (ví dụ `syft <artifact> -o cyclonedx-json`).
- Đối chiếu SBOM với manifest và `uv.lock`: công cụ chỉ thấy được thứ nó quét ra được,
  chênh lệch phải giải thích được.
- Ghi nhận cả image container và model nếu chúng được phân phối kèm.

## 6. Tài liệu đi kèm release

- `README.md` khớp với hành vi thật của phiên bản này, không mô tả tính năng chưa có.
- Hướng dẫn build và chạy đã được kiểm chứng ở bước 4, không phải viết theo trí nhớ.
- Release notes nêu thay đổi đáng chú ý và mọi lỗ hổng đã biết được vá.

## 7. Kiểm tra cuối trước khi công bố

```bash
uvx reuse lint
uv build --all-packages
```

Thêm các mục quan sát trên forge, không kiểm tra được từ máy cục bộ:

- Repo công khai, truy cập được khi chưa đăng nhập.
- Release hiển thị đúng tag, đúng artifact, đúng thời điểm — **trước hạn nộp**.
- Issue tracker mở và có hoạt động thật.

## Mẫu báo cáo

```text
Phiên bản:        <x.y.z>  (tag: <tag>, commit: <sha>)
Changelog:        <đã chuyển khỏi Unreleased? có ngày phát hành?>
Artifact:         <tên tệp, kích thước, sha256>
Nội dung gói:     <đã kiểm tra, không có venv/node_modules/secret>
Cài sạch:         <bước 1-5: kết quả từng bước, log ở đâu>
Chạy ngoài source:<kết quả cụ thể>
Kịch bản demo:    <chạy đầu-cuối trên stack Compose? reset chạy được?>
SBOM:             <tệp, công cụ, chênh lệch so với manifest>
reuse lint:       <exit code>
uv build:         <exit code>
Chưa kiểm chứng:  <mục chưa chạy hoặc chỉ xác minh được trên forge>
```

Mục "Chưa kiểm chứng" để trống chỉ khi đã thực sự chạy hết. Nếu chưa dựng được stack Compose
hoặc kịch bản demo chưa chạy đầu-cuối, ghi đúng như vậy — đừng đánh dấu đạt.
