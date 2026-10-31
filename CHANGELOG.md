<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Changelog

Toàn bộ thay đổi đáng chú ý của dự án được ghi trong tệp này.

Định dạng dựa trên [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
và dự án tuân theo [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.2] - 2026-11-01

Bản tài liệu nộp bài cho Ban tổ chức. Mã nguồn và hành vi hệ thống không đổi so với 0.2.1.

### Added

- **Báo cáo kỹ thuật duy nhất** dạng LaTeX, kèm PDF có trang bìa và mục lục đánh số trang
  (`docs/report/DX-Lab-v0.2.1-bao-cao-ky-thuat.pdf`, nguồn `docs/report/latex/`, biên dịch bằng Tectonic) (#123).
- **Slide trình bày** dựng bằng Slidev, theme `seriph`, 12 trang, kèm PDF (`docs/slides/`) (#122).
- **Kịch bản demo từng bước** cho người trình bày không chuyên (`docs/demo/kich-ban-tung-buoc.md`), đã chạy thử trên
  bản 0.2.1.

### Changed

- `docs/report/BAO-CAO-PHAN-1.md` và `BAO-CAO-PHAN-2.md` thay bằng trang trỏ sang báo cáo PDF; bản nháp còn trong lịch sử git.

### Fixed

- `docs/AI.md`, báo cáo, slide: số đo tìm kiếm `/api/search` ghi theo kết quả chạy thật trên 0.2.1. Top-1 vẫn là 18/18,
  nhưng hai câu ngoài phạm vi **không** trả rỗng (0/2), khác với ghi chép trước đó (2/2).
- `docs/demo/kich-ban.md`: bỏ bước minh họa câu ngoài phạm vi trả rỗng và câu nói mã lý do hiện trên portal.

### Hạn chế đã biết

- Tìm kiếm chưa trả rỗng với câu hỏi ngoài phạm vi; điểm chưa đủ để đặt ngưỡng.
- Các hạn chế khác của 0.2.1 vẫn còn.

## [0.2.1] - 2026-11-01

Bản nộp bài: thêm ủy quyền TUQ., sơ đồ quy trình trên portal, bộ test 14 kịch bản phân quyền, kịch bản kiểm thử
đầu-cuối và bộ tài liệu nộp bài (README, bảng phụ thuộc, báo cáo kỹ thuật, slide, kịch bản demo, log QA).

### Added

- **Ủy quyền TUQ.** (`/api/delegations`, #18): người giữ vai trò duyệt giao cho người cùng đơn vị duyệt thay tối đa
  30 ngày, bắt buộc số giấy ủy quyền, thu hồi được bất kỳ lúc nào; không vượt vai trò và đơn vị của người ủy quyền;
  người nhận không ủy quyền lại được; phiếu và audit ghi hình thức TUQ., người ủy quyền, số giấy.
- **Sơ đồ quy trình trên portal** (#33): tab mới vẽ sơ đồ Mermaid từ BPMN của phiên bản ứng dụng đang áp dụng.
- **Kiểm thử:** 14 kịch bản phân quyền của `docs/AUTHZ.md` mục 12 chạy trên gói `lab-repair` thật (#38);
  `scripts/demo-e2e.sh` chạy trọn vòng đời phiếu qua APISIX với Keycloak thật (#39).
- **Tài liệu:** README đầy đủ (#47), `docs/DEPENDENCIES.md` (#46), sequence luồng gọi trong `docs/ARCHITECTURE.md` và
  đánh giá trong `docs/AI.md` (#48), báo cáo kỹ thuật hai phần `docs/report/` (#49, #50), slide `docs/slides/` (#51),
  kịch bản demo và câu trả lời chất vấn `docs/demo/kich-ban.md` (#53), log build theo README `docs/qa/` (#41).

### Changed

- Tệp nhị phân trong `docs/report/`, `docs/slides/`, `docs/qa/`, `docs/demo/` được khai báo CC-BY-4.0 qua
  `REUSE.toml` (#100).

### Fixed

- `scripts/demo-e2e.sh` đọc đúng `workflow_id`, `task_id`, `history` và tên tài liệu trong phản hồi của core (#118).

### Hạn chế đã biết

- Portal chưa có màn hình tạo hoặc thu hồi ủy quyền; dùng API (`/api/docs`).
- Chạy MCP với host và LLM (#36), che dữ liệu cá nhân trong văn bản tự do (#97) và đo migration `0006` trên bảng
  `documents` lớn (#96) là lộ trình sau bản này.
- Log QA (#41) chạy trên máy của đội với bản clone và volume Docker mới, chưa chạy trên một máy khác.
- Các hạn chế khác của 0.2.0 vẫn còn (giả định hạn mức và tổ chức, chỉ mục toàn văn 150.000 ký tự đầu, Compose là
  bản demo một máy).

## [0.2.0] - 2026-10-30

Bản phát hành đầu tiên chạy được: dựng toàn bộ hệ thống bằng Docker Compose, đăng nhập bằng tài khoản demo, báo hỏng
và xử lý phiếu đầu-cuối. Không có bản 0.1.0: hai mốc kế hoạch 0.1.0 và 0.2.0 được gộp vào bản này.

### Added

- **Core API (Tầng 1, headless):** FastAPI dưới `/api`, mô tả OpenAPI tại `/api/openapi.json`, lỗi cùng một dạng
  có mã và `request_id`, migration cơ sở dữ liệu tự chạy khi khởi động, `/api/health` báo trạng thái cơ sở dữ liệu,
  chỉ mục tìm kiếm và mô hình embedding.
- **Xác thực:** kiểm token Keycloak qua JWKS; vai trò và đơn vị lấy từ nhóm của người dùng; mặc định từ chối; tài
  khoản quản trị hệ thống không làm được thao tác nghiệp vụ.
- **Định nghĩa ứng dụng** (`/api/definitions`): nạp gói BPMN, DMN và form JSON Schema; validator từ chối mã script và
  điều kiện không an toàn; mỗi lần nạp là một phiên bản mới, người khác người nạp duyệt mới áp dụng; phiếu đã tạo giữ
  nguyên luật của phiên bản tạo ra nó.
- **Quy trình** (`/api/workflows`, `/api/tasks`): tạo và xem phiếu, hộp việc theo vai trò và phạm vi đơn vị, hoàn
  thành bước có kiểm dữ liệu theo form, lịch sử và audit cho mọi thao tác.
- **Phân quyền 5 lớp:** phạm vi theo cây đơn vị; thẩm quyền duyệt theo hạn mức lấy từ bảng luật, có hình thức ký
  thay (KT.); tự leo thang khi người duyệt trùng người báo hoặc người xác nhận; duyệt lại khi chi phí thực tế vượt
  mức đã duyệt; không kiêm nhiệm; che trường dữ liệu cá nhân với người không được xem và ghi log mỗi lần người khác
  xem.
- **Danh mục và tài liệu** (`/api/records`, `/api/documents`): bản ghi kiểm theo schema của ứng dụng, tài liệu tải
  lên có nguồn và giấy phép; tài liệu đính kèm phiếu chỉ hiện với người được xem phiếu.
- **Tìm kiếm** (`/api/search`): kết hợp toàn văn PostgreSQL và tìm theo ngữ nghĩa (zvec), có đoạn trích và nguồn;
  thiếu mô hình thì chỉ dùng toàn văn.
- **Thống kê** (`/api/stats`): số phiếu theo trạng thái, đơn vị, quá hạn và chi phí, chỉ trên phiếu người gọi được
  xem, không có tên người.
- **CLI `dxlab`:** `validate`, `login` (device flow), `logout`, `whoami`, `publish`.
- **Portal (Tầng 2):** đăng nhập Keycloak qua BFF; báo hỏng bằng form sinh từ định nghĩa; hộp việc, xử lý bước và
  lịch sử phiếu; dashboard; tra cứu hướng dẫn sửa chữa có trích dẫn; trang trạng thái hệ thống xem được khi chưa
  đăng nhập.
- **MCP server** (FastMCP, stdio): 5 tool dùng token của chính người dùng, thao tác ghi phải xác nhận.
- **Ứng dụng `lab-repair` (Tầng 3):** quy trình báo hỏng và sửa chữa thiết bị phòng lab với bảng luật định tuyến, xếp
  ưu tiên, thẩm quyền và chi phí vượt; form cho 7 bước; dữ liệu mẫu 4 phòng, 12 tài sản, 8 hướng dẫn sửa chữa; bộ
  đánh giá 60 phiếu gán nhãn (định tuyến đúng 83,3%, mức ưu tiên đúng 88,3%).
- **Ứng dụng `room-booking`:** đặt phòng thực hành và duyệt, thêm vào mà không sửa mã Core.
- **Triển khai:** Docker Compose (PostgreSQL, Keycloak, APISIX, Core, portal), image ghim digest; `scripts/up.sh`,
  `scripts/seed.sh`, `scripts/reset.sh`, `scripts/download-models.sh`; realm Keycloak với cây tổ chức, vai trò,
  17 tài khoản demo tên giả và xác thực hai bước cho vai trò duyệt; APISIX kiểm token, giới hạn tần suất, gắn
  request-id; compose riêng cho Spiff Editor chỉ mở trên `127.0.0.1`.
- **Phát hành và CI:** đẩy tag `v*` sinh `tar.gz`, `SHA256SUMS`, SBOM và trang Release; CI chạy pytest với
  PostgreSQL 17, quét secret (gitleaks), kiểm gói ứng dụng bằng `dxlab validate apps/`.
- Giấy phép Apache-2.0 cho mã nguồn và CC BY 4.0 cho tài liệu, kèm toàn văn trong `LICENSES/`.
- Tuân thủ [REUSE 3.3](https://reuse.software/spec-3.3/): SPDX header trong tệp mã, `REUSE.toml` cho tệp không chứa được comment.
- `README.md`, `CONTRIBUTING.md` (yêu cầu DCO sign-off), `SECURITY.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1), `MAINTAINERS.md`.
- uv workspace gồm hai gói tách biệt: `dxlab-core` (Tầng 1, Open-Core headless) và `dxlab-portal` (Tầng 2/3, giao diện Prefab).
- CI GitHub Actions: `reuse lint`, build từng gói rồi cài vào môi trường sạch và import từ ngoài cây mã nguồn, kiểm tra DCO trên PR.
- Mẫu báo lỗi, đề xuất tính năng và định tuyến báo cáo bảo mật cho bug tracker công khai.

### Changed

- Quy trình đóng góp: mọi thay đổi vào `main` qua Pull Request gắn với issue, tên nhánh theo mã việc, chỉ maintainer chính merge, chỉ gộp kiểu rebase.
- `MAINTAINERS.md` ghi người phụ trách và quyền thực tế trên repo; README cập nhật kiến trúc và thành phần dự kiến.
- README ghi đúng trạng thái và cách chạy của bản này.

### Fixed

- CI: ghim `astral-sh/setup-uv` theo commit của bản v10.3.2 (action không phát hành tag `v10`).

### Hạn chế đã biết

- Hạn mức duyệt, cơ cấu tổ chức và tài khoản demo là **giả định** của đội (mã `GĐ-…`), không phải văn bản hay số
  liệu thật của HaUI.
- Chưa có ủy quyền thừa ủy quyền (TUQ.) (#18).
- Dữ liệu cá nhân gõ trong ô văn bản tự do (mô tả, ý kiến) chưa được nhận diện để che (#97).
- Chỉ mục toàn văn chỉ lấy 150.000 ký tự đầu của mỗi tài liệu (#96).
- Một số lựa chọn trên form còn hiện khóa tiếng Anh (ví dụ `single`, `repair`).
- Cấu hình Compose là bản demo một máy: Keycloak chạy chế độ phát triển, không TLS; không dùng cho môi trường thật.
- Tìm theo ngữ nghĩa cần tải mô hình trước bằng `scripts/download-models.sh`; chưa tải thì chỉ tìm toàn văn.

[Unreleased]: https://github.com/HaUI-NPC/dx-lab/compare/v0.2.2...HEAD
[0.2.2]: https://github.com/HaUI-NPC/dx-lab/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/HaUI-NPC/dx-lab/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/HaUI-NPC/dx-lab/releases/tag/v0.2.0
