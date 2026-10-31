<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# DX-Lab: slide demo (bản 0.2.x)

Bộ slide gồm 12 slide, mỗi slide cách nhau bằng dòng `---`. Số liệu lấy từ `README.md`, `CHANGELOG.md`,
`docs/ARCHITECTURE.md`, `docs/AUTHZ.md`, `docs/AI.md` và `docs/DEPENDENCIES.md` của bản 0.2.0. Hạn mức duyệt, cơ cấu tổ
chức và tài khoản demo là **giả định** của đội HaUI.NPC, không phải số liệu thật của HaUI.

---

## Slide 1: DX-Lab, trạm điều hành số cho phòng thực hành

- Sản phẩm dự thi của đội **HaUI.NPC**, khối Phần mềm nguồn mở OLP 2026, chủ đề DX-OS Open-Core.
- Bài toán: báo hỏng thiết bị phòng thực hành (máy tính, máy chiếu, mạng, điều hòa) qua tin nhắn hay lời nói thì thất lạc,
  không theo dõi được ai đang xử lý, bao lâu thì xong.
- DX-Lab số hóa đầu-cuối: **báo hỏng → định tuyến và xếp ưu tiên → kiểm tra, lập biên bản → xác nhận nhu cầu và duyệt theo
  hạn mức → sửa → nghiệm thu**, có lịch sử audit cho mọi thao tác.
- Bản 0.2.0 chạy được đầu-cuối trên một máy bằng Docker Compose, kèm dữ liệu và 17 tài khoản demo.

---

## Slide 2: Kiến trúc 3 tầng của DX-OS Open-Core

| Tầng | Là gì | Thành phần trong DX-Lab |
|---|---|---|
| **1. Open-Core** (headless) | Nền tảng dùng chung, không có giao diện, không biết ứng dụng cụ thể | `core/`, `deploy/`: Keycloak, Apache APISIX, Core API (FastAPI + SpiffWorkflow), PostgreSQL |
| **2. H-P-D-I** | Không gian Human, Process, Data, Intelligence mà người dùng chạm tới | `portal/` (Prefab), `mcp/` (FastMCP), CLI `dxlab` |
| **3. Ứng dụng** | Gói định nghĩa nạp vào Core, không sửa mã Core | `apps/lab-repair`, `apps/room-booking` |

- Mọi lời gọi tới Core đi qua APISIX, bằng token của chính người dùng; Portal, MCP và CLI không đọc cơ sở dữ liệu.
- Thêm ứng dụng mới = nạp một gói BPMN, DMN, JSON Schema qua `/api/definitions`. `room-booking` được thêm đúng cách đó.

---

## Slide 3: Tầng 1, thành phần Open-Core

| Thành phần | Việc làm | Giấy phép |
|---|---|---|
| **Keycloak 26** | SSO, OIDC, vai trò theo cây đơn vị, xác thực hai bước cho vai trò duyệt | Apache-2.0 |
| **Apache APISIX 3.19** | Cổng duy nhất vào `/api`: kiểm JWT bằng JWKS, giới hạn tần suất, gắn request-id | Apache-2.0 |
| **Core API (FastAPI)** | `/api/definitions`, `workflows`, `tasks`, `records`, `documents`, `search`, `stats`, `delegations` | MIT |
| **SpiffWorkflow** | Chạy BPMN và bảng luật DMN, trạng thái lưu trong PostgreSQL | LGPL-3.0 |
| **PostgreSQL 17, zvec** | Dữ liệu và tìm kiếm toàn văn; chỉ mục vector chạy cục bộ | PostgreSQL License, Apache-2.0 |

- Core kiểm token độc lập với APISIX (cả hai cùng kiểm). Core không trả HTML và không gọi LLM.

---

## Slide 4: Tầng 1, nạp và áp dụng một ứng dụng

- Gói ứng dụng gồm BPMN (quy trình), DMN (định tuyến, ưu tiên, thẩm quyền), form JSON Schema, danh mục.
- Validator từ chối mã script và điều kiện không an toàn; `dxlab validate` dùng chính validator của Core.
- Phân vai: `rule_admin` chỉ nạp được bảng luật `.dmn`; `process_admin` nạp mọi loại tệp; **người khác người nạp**
  (`process_owner`) duyệt thì phiên bản mới được áp dụng.
- Phiếu đã tạo giữ nguyên luật của phiên bản tạo ra nó; phiếu mới theo phiên bản mới.
- CLI: `dxlab login` (device flow), `whoami`, `validate`, `publish`.

---

## Slide 5: Tầng 1, phân quyền 5 lớp

Core kiểm tuần tự cho mọi thao tác, mặc định từ chối:

1. **Ai là ai**: token hợp lệ, vai trò từ nhóm Keycloak (`FORBIDDEN_ROLE`); `system_admin` không làm được nghiệp vụ (SoD-4).
2. **Phạm vi**: đối tượng thuộc đơn vị của người làm, kể cả đơn vị con (`FORBIDDEN_SCOPE`).
3. **Thẩm quyền**: hạn mức lấy từ `authority.dmn` hoặc ủy quyền còn hạn (`FORBIDDEN_AUTHORITY`).
4. **Không kiêm nhiệm**: không tự duyệt, không tự nghiệm thu việc mình sửa (`FORBIDDEN_SOD`).
5. **Dữ liệu cá nhân**: trường `x-personal-data` bị che với người không được xem, mỗi lần người khác xem đều ghi log.

- 18 vai trò, cây đơn vị `/haui/...`. Vai trò gắn vào nhóm con của đơn vị, Core lấy đoạn cuối làm vai trò.

---

## Slide 6: Tầng 2, bốn không gian H-P-D-I

| Không gian | Thành phần | Có gì trong bản 0.2.0 |
|---|---|---|
| **Human** | Portal (Prefab, BFF đăng nhập OIDC), CLI, MCP | Đăng nhập SSO; 5 tab: Việc của tôi, Báo hỏng, Tra cứu, Dashboard, Trạng thái hệ thống |
| **Process** | SpiffWorkflow qua `/api/workflows`, `/api/tasks` | Hộp việc theo vai trò và phạm vi, thời hạn, lịch sử audit, duyệt phân cấp |
| **Data** | `/api/records`, `/api/documents`, `/api/stats` | Danh mục phòng, thiết bị theo schema, tài liệu có nguồn và giấy phép, dashboard không chứa tên người |
| **Intelligence** | Bảng luật DMN, `/api/search` | Định tuyến và xếp ưu tiên có mã lý do; tìm hướng dẫn sửa chữa kết hợp toàn văn và vector, có trích dẫn |

- Form trên portal sinh từ JSON Schema của ứng dụng, không viết tay từng màn hình.
- MCP server (stdio) có 5 tool dùng token của chính người dùng; thao tác ghi phải xác nhận.

---

## Slide 7: Tầng 2, Intelligence có giải trình, con người quyết định

- Phân loại, định tuyến, xếp ưu tiên là **bảng luật DMN**, không dùng mô hình học máy; mỗi quyết định kèm mã lý do.
- Đo trên 60 phiếu **tổng hợp** do agent gán nhãn, chưa có người rà (`docs/AI.md`): mức ưu tiên đúng 88,3%, định tuyến
  đúng cả đơn vị và vai trò 83,3%. Ca sai và giới hạn ghi trong tài liệu.
- Tìm hướng dẫn sửa chữa: toàn văn PostgreSQL kết hợp vector (zvec, mô hình `paraphrase-multilingual-MiniLM-L12-v2` chạy
  cục bộ); thiếu mô hình thì chỉ dùng toàn văn. Bộ 8 hướng dẫn và 20 câu hỏi đánh giá nằm trong repo.
- Duyệt chi phí, chuyển bước, nghiệm thu luôn do người có thẩm quyền làm.

---

## Slide 8: Tầng 3, hai ứng dụng trên cùng một Core

- **`lab-repair`**: báo hỏng và sửa chữa thiết bị phòng lab. BPMN, 4 bảng luật DMN (định tuyến, xếp ưu tiên, thẩm quyền,
  chi phí vượt), form cho 7 bước, dữ liệu mẫu 4 phòng, 12 tài sản, 8 hướng dẫn sửa chữa.
- **`room-booking`**: đặt phòng thực hành và duyệt, thêm vào mà không sửa mã Core.
- Quy trình `lab-repair`: Báo hỏng → định tuyến → kiểm tra → (nếu có chi phí) xác nhận nhu cầu → duyệt → sửa → nghiệm thu;
  không sửa được thì chuyển đề nghị mua sắm cho Ban CSVC (mua sắm và thanh lý nằm ngoài hệ thống).
- Tên người, đơn vị và hạn mức trong dữ liệu mẫu là giả định.

---

## Slide 9: Thẩm quyền duyệt, leo thang và ủy quyền

| Chi phí dự kiến | Người duyệt | Hình thức |
|---|---|---|
| 0 | Không cần duyệt | |
| ≤ 5.000.000 | Trưởng khoa (`faculty_head`) | Theo phân cấp |
| ≤ 20.000.000 | Hiệu trưởng trường thành viên (`school_head`) | Theo phân cấp |
| ≤ 100.000.000 | Phó Giám đốc (`vice_president`) | KT. Giám đốc |
| > 100.000.000 | Giám đốc (`president`) | Trực tiếp |

Hạn mức là **giả định** (`GĐ-PC-01/2026`, `GĐ-PCBGĐ-2026`), nằm trong `authority.dmn`, đổi được mà không sửa Core.

- **E1**: người duyệt trùng người tạo phiếu hoặc người xác nhận thì phiếu lên cấp kế tiếp.
- **E2**: chi phí thực tế vượt chi phí đã duyệt quá 10% hoặc vượt hạn mức người duyệt thì duyệt lại.
- **Ủy quyền TUQ.** (`/api/delegations`): có số giấy, tối đa 30 ngày, cùng đơn vị, không vượt hạn mức người ủy quyền;
  audit ghi người làm thật, hình thức, người ủy quyền và số giấy.

---

## Slide 10: Demo đầu-cuối

Chạy `scripts/up.sh`, `scripts/seed.sh`, mở `http://localhost:8000`:

1. `sv.an` báo máy chiếu A1-305 không lên hình; bảng luật định tuyến về Trung tâm CNTT.
2. `ktv.cuong` lập biên bản, dự toán 3.500.000 đ kèm báo giá.
3. `tl.giang` xác nhận nhu cầu; `tk.hai` duyệt theo hạn mức (cả hai đăng nhập có OTP).
4. `ktv.cuong` sửa; `tl.giang` nghiệm thu; phiếu đóng, lịch sử và audit đầy đủ.
5. Thử chặn: `tk.long` (Khoa Điện) duyệt phiếu khoa khác bị từ chối ở lớp phạm vi; `admin.dx` không duyệt được phiếu nào.
6. Tra hướng dẫn sửa chữa trên tab Tra cứu, có trích dẫn nguồn.

`scripts/demo-e2e.sh` chạy lại kịch bản này bằng `curl` qua APISIX.

---

## Slide 11: Triển khai, kiểm thử và tuân thủ nguồn mở

- **Triển khai**: Docker Compose 5 dịch vụ (PostgreSQL, Keycloak, APISIX, Core, portal), image ghim digest SHA-256, mọi
  cổng chỉ nghe trên `127.0.0.1`.
- **Kiểm thử và CI**: pytest chạy trên PostgreSQL 17 thật, quét secret (gitleaks), `dxlab validate apps/`, kiểm DCO.
- **Nguồn mở**: mã Apache-2.0, tài liệu CC BY 4.0; tuân thủ REUSE 3.3 (`uvx reuse lint`); mọi commit ký DCO.
- **Minh bạch phụ thuộc**: `docs/DEPENDENCIES.md` kê toàn bộ gói, image, mô hình, giấy phép, khai báo thành phần đóng gói sẵn
  (Prefab renderer); phát hành kèm `SHA256SUMS` và SBOM.
- Mọi số liệu đo trong tài liệu kèm lệnh tái lập.

---

## Slide 12: Hiện trạng và lộ trình

**Đã chạy được (bản 0.2.0):** Core headless với phân quyền 5 lớp, ủy quyền TUQ., portal 5 tab, CLI, MCP server (5 tool),
ứng dụng `lab-repair` và `room-booking`, triển khai bằng Compose, tài khoản demo giả định.

**Lộ trình sau cuộc thi (chưa có trong bản này):**

- Chạy MCP server với host mã nguồn mở và LLM mở (#36).
- Che dữ liệu cá nhân gõ trong ô văn bản tự do bằng mô hình nhận diện PII, dự kiến OpenMed (#97).
- Đo tải và tối ưu migration bảng `documents` khi dữ liệu lớn (#96).
- Luật chống chia nhỏ chi phí (E3) mới ghi trong thiết kế, chưa làm.

Cảm ơn Hội đồng. Mã nguồn: https://github.com/HaUI-NPC/dx-lab
