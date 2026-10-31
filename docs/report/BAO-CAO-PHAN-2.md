<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Báo cáo kỹ thuật DX-Lab — Phần 2: Không gian H-P-D-I, Ứng dụng nghiệp vụ, Trí tuệ nhân tạo và Đánh giá thực nghiệm

> **Dự án:** Trạm điều hành số trên nền tảng DX-OS Open-Core (DX-Lab)  
> **Đội thi:** HaUI.NPC — Khối Phần mềm nguồn mở, Olympic Tin học Sinh viên Việt Nam 2026  
> **Chủ đề:** DX-OS Open-Core  
> **Tài liệu liên quan:** Phần 1 (Kiến trúc Open-Core, Bản quyền và Giấy phép), `docs/ARCHITECTURE.md`, `docs/AUTHZ.md`, `docs/AI.md`

---

## Chương 1: Hiện thực hóa Không gian H-P-D-I trong DX-Lab

Kiến trúc DX-OS Open-Core định hình trạm điều hành số xoay quanh 4 trục năng lực cốt lõi: **Human (Con người)**, **Process (Quy trình)**, **Data (Dữ liệu)** và **Intelligence (Trí tuệ nhân tạo & Tri thức)**. Trong DX-Lab, bốn không gian này không tồn tại như các khối phần mềm rời rạc mà được gắn kết chặt chẽ thông qua giao thức API RESTful thống nhất, được bảo vệ bởi cổng API Gateway độc lập và hệ thống định danh tập trung.

```
       +-------------------------------------------------------------+
       |                 TẦNG 2: KHÔNG GIAN H-P-D-I                  |
       |                                                             |
       |   +-----------------------+     +-----------------------+   |
       |   |       H - Human       |     |      P - Process      |   |
       |   | - Web Portal (BFF)    |     | - SpiffWorkflow BPMN  |   |
       |   | - MCP Assistant       |     | - Hộp việc Task Inbox |   |
       |   | - SSO Keycloak (OIDC) |     | - Phân tách SoD-1/2   |   |
       |   +-----------+-----------+     +-----------+-----------+   |
       |               |                             |               |
       |   +-----------+-----------+     +-----------+-----------+   |
       |   |       D - Data        |     |    I - Intelligence   |   |
       |   | - PostgreSQL RDBMS    |     | - Bảng luật DMN 1.3   |   |
       |   | - JSON Schema Forms   |     | - Hybrid RAG Search   |   |
       |   | - Privacy & Audit     |     | - Human-in-the-loop   |   |
       |   +-----------------------+     +-----------------------+   |
       +------------------------------+------------------------------+
                                      | HTTP/REST + Bearer JWT
                                      v
       +-------------------------------------------------------------+
       |               TẦNG 1: DX-OS OPEN-CORE (HEADLESS)            |
       |  Apache APISIX Gateway  -->  FastAPI Core Engine (Stateful) |
       +-------------------------------------------------------------+
```

### 1.1 Không gian Human (Con người & Tương tác)
Không gian Human đặt người dùng làm trung tâm điều hành, giải quyết bài toán đa dạng hóa phương thức tương tác và minh bạch hóa trách nhiệm cá nhân:
- **Tương tác đa kênh (Multi-interface):**
  - **Giao diện Web tương tác (Portal):** Xây dựng theo mô hình BFF (Backend-for-Frontend) bằng Python sử dụng `prefab-ui==0.21.1` và `fastapi`. Trình duyệt người dùng chỉ duy trì cookie phiên an toàn (`httpOnly`, `SameSite=Lax`), trong khi token OAuth2/OIDC được quản lý tập trung tại máy chủ, ngăn chặn triệt để nguy cơ tấn công XSS đánh cắp token.
  - **Giao diện trợ lý dòng lệnh thông minh (MCP):** Cung cấp máy chủ FastMCP (`dxlab-mcp`) tuân thủ giao thức Model Context Protocol (MCP stdio). Cho phép người dùng và các tác nhân AI thực hiện các lệnh nghiệp vụ (như báo hỏng, kiểm tra việc chờ) bằng ngôn ngữ tự nhiên. Để đảm bảo an toàn, MCP luôn bắt buộc cơ chế hỏi xác nhận (`ctx.elicit`) trước mọi thao tác ghi dữ liệu.
- **Định danh tập trung và Cơ chế ủy quyền:**
  - Tích hợp máy chủ Keycloak (`quay.io/keycloak/keycloak:26.8.1`) quản trị tài khoản tập trung. Hỗ trợ đầy đủ luồng Authorization Code Flow kết hợp PKCE (cho Portal) và Device Authorization Grant / Direct Grant (cho CLI và script tự động).
  - Áp dụng xác thực 2 bước (TOTP RFC 6238) bắt buộc đối với các vai trò quản lý cấp cao (Trưởng khoa, Trưởng ban, Ban Giám hiệu, Quản trị viên).
  - Hiện thực hóa cơ chế ủy quyền có thời hạn (TUQ. theo `docs/AUTHZ.md` mục 10) thông qua API `/api/delegations`: người được ủy quyền chỉ được thực thi quyền hạn trong khung thời gian ấn định, có căn cứ văn bản và được ghi vết kiểm toán minh bạch.

### 1.2 Không gian Process (Quy trình số hóa & Điều phối)
Không gian Process chuyển dịch toàn bộ các quy trình giấy tờ thủ công sang dạng thức điều phối quy trình tự động có trạng thái (stateful workflow):
- **Bộ máy thực thi tiêu chuẩn mở (BPMN 2.0 Runtime):** Nhúng trực tiếp thư viện `SpiffWorkflow>=3.2` vào Core API thay vì phụ thuộc vào các dịch vụ phần mềm cồng kềnh ngoài. Nhờ đó, quy trình được định nghĩa hoàn toàn bằng chuẩn đồ họa quốc tế BPMN 2.0 (`.bpmn`), cho phép chỉnh sửa trực quan qua Spiff Editor.
- **Quản lý vòng đời và Hộp việc cá nhân hóa (Task Inbox):** Mọi lượt chạy quy trình được gắn một `workflow_id` duy nhất. Các bước xử lý của con người (User Task) được phân bổ chính xác về hộp việc (`GET /api/tasks`) của từng cá nhân dựa trên ma trận vai trò và phạm vi tổ chức (đơn vị kỹ thuật, phòng thí nghiệm trực thuộc).
- **Phân tách nhiệm vụ độc lập (Separation of Duties - SoD):** Bộ máy tự động thực thi luật không kiêm nhiệm:
  - **SoD-1:** Người lập đề xuất sửa chữa không được tự phê duyệt chi phí.
  - **SoD-2:** Kỹ thuật viên đã trực tiếp kiểm tra hoặc sửa chữa thiết bị tuyệt đối không được tham gia nghiệm thu kết quả.

### 1.3 Không gian Data (Dữ liệu thống nhất & Quản trị)
Không gian Data chịu trách nhiệm bảo toàn tính toàn vẹn, nguồn gốc và bảo mật thông tin:
- **Cơ sở dữ liệu cấu trúc duy nhất:** Toàn bộ thực thể quy trình, phiên bản gói, nhiệm vụ, danh mục tài sản và nhật ký kiểm toán được lưu trữ trên PostgreSQL 17. Core API là thành phần duy nhất được cấp quyền kết nối tới cơ sở dữ liệu (ngăn chặn truy cập trực tiếp từ Portal, MCP hay các client ngoài).
- **Mô hình định nghĩa dữ liệu linh hoạt (Dynamic JSON Schema):** Biểu mẫu nghiệp vụ tại mỗi bước được chuẩn hóa theo chuẩn JSON Schema (Draft 2020-12). Hệ thống kiểm tra tính hợp lệ dữ liệu nghiêm ngặt ngay tại tầng Core: từ chối mọi trường lạ nằm ngoài schema, ngăn chặn việc client can thiệp trái phép vào các biến nội bộ của workflow.
- **Bảo vệ dữ liệu cá nhân & Tôn trọng quyền riêng tư:** Tuân thủ Nghị định 13/2023/NĐ-CP, các trường thông tin nhạy cảm (họ tên, email, số điện thoại, tài khoản người làm) được gắn cờ `"x-personal-data": true`. Core API tự động che giấu (`masking`) các trường này khi người xem không thuộc diện có quyền tra cứu thông tin cá nhân.
- **Nhật ký kiểm toán bất biến (Immutable Audit Trail):** Mỗi chuyển dịch trạng thái, phê duyệt hay chỉnh sửa dữ liệu đều ghi nhận một bản ghi Audit bất biến (`POST /api/audit`), lưu trữ đầy đủ: thời điểm (UTC), mã định danh người thao tác, vai trò, địa chỉ IP, hành vi và căn cứ thẩm quyền.

### 1.4 Không gian Intelligence (Trí tuệ nhân tạo & Tri thức)
Không gian Intelligence bổ trợ cho con người trong việc đưa ra quyết định nhanh chóng và chuẩn xác:
- **Hệ thống luật suy diễn minh bạch (Decision Model and Notation - DMN 1.3):** Tự động hóa việc phân loại mức độ khẩn cấp (P1/P2/P3, tính thời hạn SLA qua `triage.dmn`), định tuyến đơn vị xử lý (`routing.dmn`), và xác định thẩm quyền duyệt chi phí theo các mốc tài chính (`authority.dmn`). Mỗi quyết định đều trả kèm mã lý do cụ thể, đảm bảo tính giải trình tuyệt đối (không có yếu tố "hộp đen").
- **Tìm kiếm tri thức sửa chữa ngữ nghĩa (Hybrid Semantic Search):** Tích hợp công nghệ tìm kiếm kết hợp giữa toàn văn tiếng Việt (PostgreSQL FTS) và vector embedding (`zvec` + FastEmbed). Cung cấp khả năng tra cứu quy trình thao tác chuẩn (SOP) chính xác ngay cả khi người dùng sử dụng từ đồng nghĩa, tiếng Việt không dấu hoặc diễn đạt gián tiếp.

---

## Chương 2: Hiện thực hóa Ứng dụng nghiệp vụ `lab-repair` và Luồng dữ liệu (Data Flow)

### 2.1 Bài toán nghiệp vụ tại Đại học Công nghiệp Hà Nội (HaUI)
Tại các trường đại học kỹ thuật quy mô lớn như HaUI, hệ thống phòng thí nghiệm và xưởng thực hành phân bổ trên nhiều cơ sở với hàng nghìn trang thiết bị đa dạng (máy tính, máy chiếu, thiết bị mạng, điều hòa, máy đo lường, thiết bị hàn...). Trước khi có DX-Lab, công tác quản lý sự cố gặp nhiều thách thức:
1. **Thông tin phân tán, dễ thất lạc:** Giảng viên và sinh viên thường báo hỏng qua tin nhắn hoặc trao đổi miệng, không có biên nhận và không thể theo dõi tiến độ.
2. **Định tuyến sai đơn vị:** Người báo không nắm rõ thiết bị thuộc thẩm quyền của Trung tâm CNTT, Ban Cơ sở vật chất hay Bộ môn/Khoa quản lý, dẫn đến việc chuyển phiếu lòng vòng gây lãng phí thời gian.
3. **Thiếu kiểm soát chi phí và thẩm quyền:** Các sự cố phát sinh kinh phí sửa chữa hoặc thay thế linh kiện thiếu quy trình phê duyệt chặt chẽ theo hạn mức phân cấp của trường ([QC] Đ4.1a, [PL] NĐ 214/2025/NĐ-CP).
4. **Phân mảnh tri thức:** Kinh nghiệm xử lý sự cố nằm trong đầu một số ít cán bộ kỹ thuật lâu năm, thiếu hệ thống lưu trữ và tra cứu hướng dẫn chuẩn hóa (SOP).

### 2.2 Vòng đời xử lý sự cố thiết bị qua 6 bước nghiệp vụ
Ứng dụng `lab-repair` số hóa toàn diện quy trình xử lý sự cố thiết bị phòng thực hành theo chu trình khép kín:

```
 [1. Báo hỏng] (Sinh viên / Giảng viên)
       |
       v  <triage.dmn: Xếp ưu tiên P1/P2/P3> + <routing.dmn: Chọn đơn vị CSVC/CNTT>
 [2. Khảo sát & Dự toán] (Kỹ thuật viên)
       |
       v
 [3. Xác nhận nhu cầu] (Trưởng phòng Lab)
       |
       +---> [Không phát sinh chi phí] --------+
       |                                       |
       v  <authority.dmn: Duyệt theo hạn mức>  |
 [4. Phê duyệt kinh phí] (Trưởng khoa/Ban GH)  |
       |                                       |
       v <-------------------------------------+
 [5. Sửa chữa & Báo cáo] (Kỹ thuật viên)
       |
       v
 [6. Nghiệm thu & Bàn giao] (Trưởng phòng Lab - tuân thủ SoD-2)
       |
       v
  [COMPLETED] -> Lưu trữ hồ sơ, ghi nhận Audit, cập nhật chỉ mục tìm kiếm
```

1. **Bước 1 — Tiếp nhận báo hỏng (`report`):** Giảng viên hoặc sinh viên phát hiện sự cố điền biểu mẫu trực tuyến. Hệ thống lập tức kích hoạt `triage.dmn` (đánh giá nguy cơ an toàn, mức độ ảnh hưởng phòng học) và `routing.dmn` (xác định đơn vị thụ lý: TT CNTT hoặc Ban CSVC). Phiếu chuyển sang trạng thái `pending_assessment`.
2. **Bước 2 — Khảo sát hiện trạng & Dự toán (`assessment`):** Kỹ thuật viên thuộc đơn vị được phân công nhận việc từ Task Inbox, tiến hành kiểm tra thực tế, xác định nguyên nhân và đưa ra phương án xử lý (sửa chữa tại chỗ, gửi bảo hành hoặc thay thế). Nếu có chi phí, kỹ thuật viên nhập dự toán và tải lên các báo giá tham chiếu.
3. **Bước 3 — Xác nhận nhu cầu (`confirm_need`):** Trưởng phòng thí nghiệm xác nhận sự cần thiết của thiết bị đối với kế hoạch đào tạo của khoa.
4. **Bước 4 — Phê duyệt chi phí (`approval`):** Nếu có chi phí phát sinh, bảng luật `authority.dmn` tự động xác định cấp phê duyệt có thẩm quyền dựa trên số tiền (dưới 5 triệu: Trưởng khoa ký trực tiếp; từ 5 đến 20 triệu: Trưởng ban CSVC; trên 100 triệu: Hiệu trưởng phê duyệt). Cán bộ có thẩm quyền sử dụng xác thực 2 bước để ký duyệt trực tuyến.
5. **Bước 5 — Thực hiện sửa chữa (`repair`):** Kỹ thuật viên tiến hành thay thế linh kiện, căn chỉnh thiết bị, nạp gas/vật tư và ghi nhận biên bản kỹ thuật cùng chi phí thực tế.
6. **Bước 6 — Nghiệm thu & Đóng phiếu (`acceptance`):** Cán bộ quản lý phòng lab kiểm tra thực tế vận hành của thiết bị, ký biên bản nghiệm thu (bắt buộc khác kỹ thuật viên thực hiện để thỏa mãn SoD-2). Phiếu kết thúc ở trạng thái `completed`.

### 2.3 Sơ đồ luồng dữ liệu (Data Flow Diagram - DFD)

Sơ đồ thể hiện đường đi của dữ liệu từ khi tiếp nhận tới khi lưu trữ và xử lý:

```
 +--------------------+       +--------------------+       +--------------------+
 |     NGƯỜI DÙNG     |       |    APISIX GATEWAY  |       |      CORE API      |
 +---------+----------+       +---------+----------+       +---------+----------+
           |                            |                            |
           | 1. Form Data + Bearer JWT  |                            |
           +--------------------------->| 2. Verify JWT & Rate Limit |
           |                            +--------------------------->|
           |                            |                            | 3. Validate Schema
           |                            |                            |    & 5-Layer Authz
           |                            |                            |
           |                            |                  +---------+---------+
           |                            |                  | SPIFFWORKFLOW     |
           |                            |                  | - BpmnWorkflow    |
           |                            |                  | - Evaluate DMN    |
           |                            |                  +---------+---------+
           |                            |                            |
           |                            |            4. Read/Write   v
           |                            |         +---------------------------+
           |                            |         |      POSTGRESQL 17        |
           |                            |         | - workflows & tasks       |
           |                            |         | - records & audit_logs    |
           |                            |         +---------------------------+
           |                            |                            |
           |                            |            5. Hybrid Index v
           |                            |         +---------------------------+
           |                            |         |      ZVEC INDEX DIR       |
           |                            |         | - 384-dim vector chunks   |
           |                            |         +---------------------------+
           | 6. Masked JSON Response    |                            |
           |<---------------------------+----------------------------+
```

### 2.4 Tính chất Open-Core và Khả năng mở rộng (Extensibility)
Một ưu điểm kiến trúc nổi bật của DX-Lab là **Tầng 1 (Core Engine) hoàn toàn không chứa mã nghiệp vụ của ứng dụng**:
- Ứng dụng `lab-repair` chỉ là một gói tệp tĩnh nằm trong thư mục `apps/lab-repair/`, bao gồm: sơ đồ quy trình `lab-repair.bpmn`, các bảng luật `.dmn`, các biểu mẫu `*-schema.json` và hướng dẫn kỹ thuật `docs/*.md`.
- Để chứng minh năng lực Open-Core độc lập, đội ngũ phát triển đã nạp thành công ứng dụng thứ hai: **`room-booking` (mượn phòng thực hành)**. Quá trình triển khai `room-booking` được thực hiện hoàn toàn qua API `dxlab publish` mà **không cần chỉnh sửa hay biên dịch lại bất kỳ dòng code nào trong `core/`**.

---

## Chương 3: Không gian Intelligence — Hệ luật quyết định DMN và Tìm kiếm ngữ nghĩa (RAG)

### 3.1 Triết lý thiết kế: Trí tuệ tăng cường và Tính giải trình (Explainable AI)
Trong một hệ thống điều hành cơ quan hành chính và giáo dục như Đại học Công nghiệp Hà Nội, việc ra quyết định liên quan đến an toàn tính mạng, tài sản công và kinh phí tài chính đòi hỏi **tính minh bạch và trách nhiệm giải trình tuyệt đối**. Vì vậy, không gian Intelligence trong DX-Lab áp dụng triết lý "Trí tuệ tăng cường" (Augmented Intelligence) thay vì giao toàn quyền cho các mô hình học máy dạng "hộp đen":
1. **Quyết định định tuyến và phê duyệt:** Sử dụng Hệ luật quyết định tiêu chuẩn DMN 1.3 (Decision Model and Notation). Mọi kết luận đều có thể truy vết ngược lại dòng luật cụ thể kèm mã lý do xác định.
2. **Hỗ trợ tri thức kỹ thuật:** Sử dụng Tìm kiếm ngữ nghĩa kết hợp (Hybrid Semantic Search) để gợi ý các quy trình thao tác chuẩn (SOP), giúp kỹ thuật viên tiếp cận nhanh nhất với kinh nghiệm sửa chữa đã được chuẩn hóa.

### 3.2 Bảng luật quyết định DMN 1.3 trong `lab-repair`
Ba bảng luật quyết định độc lập được thực thi tự động thông qua bộ máy SpiffWorkflow:

#### 1. Xếp mức ưu tiên và thời hạn phản hồi (`triage.dmn`)
Bảng luật nhận đầu vào gồm: `safety_hazard` (có nguy cơ mất an toàn), `impact` (mức độ ảnh hưởng: đơn lẻ hay cả phòng), `urgency` (mức khẩn cấp người báo chọn). Kết quả trả về gồm:
- `priority`: Mức ưu tiên P1 (Khẩn cấp), P2 (Cao), hoặc P3 (Bình thường).
- `sla_hours`: Thời hạn SLA cam kết kiểm tra hiện trường (P1: 4 giờ, P2: 24 giờ, P3: 48 giờ).
- `reason_code`: Mã lý do giải trình (`HAZARD_REPORTED`, `ROOM_BLOCKED`, `REPORTER_URGENT`, `DEFAULT`).

#### 2. Định tuyến đơn vị và vai trò xử lý (`routing.dmn`)
Căn cứ vào danh mục thiết bị (`asset_category`) và đơn vị quản lý tài sản theo `docs/AUTHZ.md` mục 6:
- Thiết bị CNTT (`computer`, `projector`, `network`): Định tuyến tới Trung tâm CNTT (`/haui/tt-cntt`), vai trò kỹ thuật viên CNTT (`it_technician`).
- Thiết bị điện, nước, cơ sở hạ tầng (`electrical`, `air_conditioner`, `lighting`, `plumbing`, `furniture`): Định tuyến tới Ban Cơ sở vật chất (`/haui/ban-csvc`), vai trò kỹ thuật viên CSVC (`facility_technician`).
- Thiết bị thực hành chuyên dụng (`lab_equipment`): Định tuyến tới Khoa chuyên môn sở hữu phòng (`owner_faculty`), vai trò kỹ thuật viên khoa (`faculty_technician`).
- Thiết bị loại khác (`other`): Định tuyến dự phòng về Ban CSVC / chuyên viên CSVC (`facility_officer`) để phân loại thủ công.

#### 3. Phân cấp thẩm quyền duyệt chi phí (`authority.dmn`)
Căn cứ vào dự toán chi phí (`estimated_cost_vnd`) và đơn vị yêu cầu, bảng luật xác định cấp phê duyệt có thẩm quyền theo quy chế tài chính và luật đấu thầu ([QC] Đ4.1a, [PL] NĐ 214/2025/NĐ-CP):

| Hạn mức chi phí | Cấp thẩm quyền (`approver_role`) | Đơn vị duyệt (`approver_unit`) | Số báo giá tối thiểu | Căn cứ pháp lý / Quy chế |
|---|---|---|---|---|
| Dưới 5.000.000 đ | Trưởng khoa (`faculty_head`) | Khoa quản lý | 1 báo giá / ước tính | [QC] Sửa chữa nhỏ tài sản đặc thù |
| Từ 5 đến 20 triệu đ | Trưởng ban CSVC (`facility_officer`) | `/haui/ban-csvc` | 1 báo giá chính thức | [QC] Mức ủy quyền ban chức năng |
| Từ 20 đến 100 triệu đ | Hiệu phó phụ trách CSVC (`vice_president`) | Ban Giám hiệu | 3 báo giá cạnh tranh | [QC] Tham khảo thực tiễn đại học |
| Trên 100.000.000 đ | Hiệu trưởng (`president`) | Ban Giám hiệu | 3 báo giá + Hội đồng | [PL] Gói mua sắm/sửa chữa lớn |

### 3.3 Công nghệ Tìm kiếm tri thức kết hợp (Hybrid Semantic Search)
Để giải quyết bài toán gợi ý hướng dẫn sửa chữa (SOP), DX-Lab xây dựng mô hình tìm kiếm kết hợp chạy hoàn toàn cục bộ (offline):

```
  Câu truy vấn của người dùng: "máy lạnh nhỏ nước xuống sàn"
                |
                +-------------------------------+
                |                               |
                v                               v
      [PostgreSQL FTS (0.7)]          [zvec Embedding (0.3)]
      to_tsvector & dxlab_unaccent    sentence-transformers MiniLM-L12
      Khớp từ khóa: "nước", "sàn"     Khớp ngữ nghĩa: "máy lạnh" = "điều hòa"
                |                               |
                +---------------+---------------+
                                |
                                v
             [Thuật toán kết hợp điểm số - Hybrid Score]
             Score = 0.7 * Rank_FTS + 0.3 * (1 - Distance / 0.8)
                                |
                                v
     [Lọc phân quyền AUTHZ] -> Trả về SOP điều hòa kèm trích dẫn
```

- **Toàn văn FTS (Trọng số 0.7):** Sử dụng `to_tsvector` của PostgreSQL kết hợp hàm bỏ dấu tiếng Việt `dxlab_unaccent`. FTS đảm bảo độ chính xác tuyệt đối với các thuật ngữ kỹ thuật, mã hiệu thiết bị (ví dụ: "HDMI", "Fluke", "R410A").
- **Vector Embedding (Trọng số 0.3):** Sử dụng mô hình `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` chạy qua thư viện `fastembed` và lưu trữ trong thư viện vector C++ `zvec`. Mô hình xử lý xuất sắc các trường hợp từ đồng nghĩa địa phương ("máy lạnh" thay vì "điều hòa"), câu hỏi viết không dấu hoặc diễn đạt triệu chứng gián tiếp.
- **Ngưỡng khoảng cách an toàn (Threshold 0.8):** Các vector có khoảng cách cosine $> 0.8$ sẽ bị triệt tiêu điểm số về 0, đảm bảo hệ thống không gợi ý tài liệu sai lệch đối với các câu hỏi nằm ngoài phạm vi tri thức hiện có.

---

## Chương 4: Đánh giá thực nghiệm định lượng và Phân tích giới hạn

### 4.1 Đánh giá độ chính xác của hệ luật quyết định DMN

Đội ngũ phát triển đã tiến hành đo lường thực nghiệm độc lập bằng script `apps/lab-repair/eval/measure_dmn.py` trên tập dữ liệu kiểm thử gồm **60 phiếu sự cố tổng hợp** (`tickets.json`) bao quát 9 chủng loại thiết bị và các tình huống đối kháng:

#### 1. Bảng chỉ số tổng hợp

| Tiêu chí đánh giá | Số ca đúng / Tổng | Độ chính xác | Ghi chú đánh giá |
|---|---|---|---|
| **Đơn vị kỹ thuật (`tech_unit`)** | **57 / 60** | **95.0%** | Bảng `routing.dmn` phân luồng cực kỳ chuẩn xác |
| **Mức ưu tiên (`priority`)** | **53 / 60** | **88.3%** | Đánh giá qua `triage.dmn` dựa trên trường cấu trúc |
| **Vai trò xử lý (`tech_role`)** | **50 / 60** | **83.3%** | Điểm số ảnh hưởng bởi các ca thiết bị loại `other` |
| **Định tuyến toàn phần (Đơn vị + Vai trò)** | **50 / 60** | **83.3%** | Cả đơn vị và vai trò đều khớp nhãn gán tay |

#### 2. Ma trận nhầm lẫn mức ưu tiên (Priority Confusion Matrix)

| Nhãn tay \ DMN dự đoán | P1 (Khẩn cấp) | P2 (Cao) | P3 (Bình thường) |
|---|---|---|---|
| **P1** | **8** | 1 | 2 |
| **P2** | 1 | **19** | 1 |
| **P3** | 0 | 2 | **26** |

#### 3. Phân tích nguyên nhân 17 ca sai lệch
Toàn bộ 17 ca sai đều được ghi nhận chi tiết tại `docs/AI.md` và phân thành các nhóm nguyên nhân cụ thể:
1. **Người báo không đánh dấu nguy cơ an toàn dù mô tả có cháy nổ (3 ca: T03, T07, T10):** Đây là nhóm ca sai nghiêm trọng nhất. Người báo mô tả máy tính bốc khói, đồng hồ vỡ vỏ hở điện nhưng không tích ô `safety_hazard`, dẫn đến việc DMN xếp P3 (SLA 48 giờ thay vì 4 giờ). **Kết luận:** DMN thuần túy không thể đọc văn bản tự do; cần giải pháp bổ trợ từ giao diện (bắt buộc xác nhận an toàn) và trao quyền cho kỹ thuật viên nâng mức ưu tiên tại bước khảo sát.
2. **Người báo phóng đại mức độ ảnh hưởng (1 ca: T09):** Máy chiếu hỏng giảng viên có thể dùng bảng, nhưng người báo chọn "ảnh hưởng cả phòng" khiến DMN xếp vọt lên P1 (`ROOM_BLOCKED`).
3. **Dòng luật `REPORTER_URGENT` (2 ca: T53, T54):** Người báo ghi "gấp" vì sắp thi, khiến DMN nâng từ P3 lên P2.
4. **Các ca thiết bị loại `other` (10 ca):** Thiết bị thuộc danh mục khác nhưng người báo chọn `other`, kích hoạt nhánh dự phòng chuyển về Ban CSVC / chuyên viên phân loại lại.

### 4.2 Đánh giá hiệu năng Tìm kiếm tri thức kết hợp (Hybrid Search)

Đánh giá trên bộ 20 truy vấn thử nghiệm (`apps/lab-repair/eval/queries.json`), gồm 18 câu hỏi có hướng dẫn SOP trong hệ thống và 2 câu hỏi đối kháng ngoài phạm vi:

| Phương pháp tìm kiếm | Top-1 (18 câu có SOP) | Top-3 (18 câu có SOP) | Câu ngoài phạm vi (Q19, Q20) |
|---|---|---|---|
| **Đường cơ sở từ khóa (TF-IDF)** | 17 / 18 (94.4%) | 17 / 18 (94.4%) | 0 / 2 đúng (Gán nhầm tài liệu) |
| **Hybrid Search Core (/api/search)** | **18 / 18 (100.0%)** | **18 / 18 (100.0%)** | **2 / 2 đúng (Trả về rỗng)** |

#### Phân tích điểm cải thiện then chốt:
- **Xử lý từ đồng nghĩa & Phân ly ngữ cảnh (Câu Q10):** Với câu hỏi *"wifi chập chờn rớt liên tục"*, đường cơ sở TF-IDF bị từ *"chập chờn"* kéo sang tài liệu chiếu sáng (xếp hạng 7). Mô hình vector của Core đã nhận diện chính xác ngữ cảnh mạng viễn thông và xếp đúng về `sop-mat-ket-noi-mang-lan` (Top-1).
- **Triệt tiêu ảo giác và gán nhầm (Câu Q19, Q20):** Với các câu hỏi *"ghế gãy chân"* và *"vòi nước bị rò"* (hệ thống chưa có SOP), đường cơ sở từ khóa vẫn trả về tài liệu điểm thấp. Cơ chế ngưỡng khoảng cách vector $0.8$ của Core đã loại bỏ hoàn toàn các kết quả này, trả về danh sách rỗng (đạt độ chính xác 100%).

### 4.3 Giới hạn kỹ thuật và Nguyên tắc Con người làm trung tâm (Human-in-the-loop)
Thực nghiệm đã chỉ ra các giới hạn kỹ thuật tự nhiên của hệ thống:
1. **Hệ luật cứng (Rule-based limitations):** DMN phụ thuộc hoàn toàn vào tính trung thực và chính xác của dữ liệu đầu vào có cấu trúc.
2. **Tài nguyên mô hình nhỏ (Small Model Footprint):** Việc lựa chọn mô hình `MiniLM-L12` (~470 MB) nhằm mục tiêu tối ưu tài nguyên phần cứng (chạy tốt trên CPU thông thường không cần GPU), song mô hình có thể gặp khó khăn với các từ viết tắt dị biệt.

**Nguyên tắc Human-in-the-loop:** Nhận thức rõ các giới hạn trên, thiết kế của DX-Lab quán triệt nguyên tắc: **AI và Hệ luật chỉ đóng vai trò phân luồng tự động và trợ lý gợi ý**. Quyền quyết định điều chỉnh mức ưu tiên, phê duyệt chi phí mua sắm vật tư và ký biên bản nghiệm thu bàn giao **luôn thuộc về con người có thẩm quyền**.

---

## Chương 5: Kết luận và Đóng góp của Dự án

### 5.1 Các kết quả nổi bật đã đạt được
1. **Hiện thực hóa thành công trạm điều hành số Open-Core:** Tách biệt triệt để Tầng 1 (Core API headless) và Tầng 2 (H-P-D-I). Chứng minh tính độc lập khi triển khai ứng dụng `room-booking` mà không sửa đổi một dòng mã Core nào.
2. **Tuân thủ chuẩn mở quốc tế:** Định nghĩa quy trình bằng BPMN 2.0 đồ họa, hệ luật DMN 1.3 minh bạch, biểu mẫu JSON Schema chuẩn Draft 2020-12, và kiến trúc API RESTful chuẩn OpenAPI 3.1.
3. **An toàn và tuân thủ pháp lý cao:** Kiểm soát quyền truy cập 5 lớp (`docs/AUTHZ.md`), phân tách nhiệm vụ độc lập SoD, bảo vệ dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP và ghi nhận nhật ký kiểm toán bất biến.
4. **Hiệu năng và độ chính xác thực nghiệm cao:** Bảng luật DMN đạt độ chính xác định tuyến 95.0%; tìm kiếm ngữ nghĩa Hybrid RAG đạt độ chính xác Top-1 100% trên tập câu hỏi đánh giá.
5. **Tuân thủ bản quyền nguồn mở 100%:** 243/243 tệp mã nguồn và tài liệu tuân thủ nghiêm ngặt đặc tả REUSE 3.3 (Apache-2.0 cho mã, CC-BY-4.0 cho tài liệu).

### 5.2 Lộ trình phát triển tiếp theo
- Tích hợp mô hình ngôn ngữ lớn cục bộ (Local LLM) để phân tích trường văn bản tự do, tự động cảnh báo các nguy cơ an toàn bỏ sót (Issue #97).
- Tối ưu hóa hiệu năng cơ sở dữ liệu khi chỉ mục văn bản `documents` đạt quy mô lớn (Issue #96).
- Mở rộng giao tiếp MCP Client trên các thiết bị di động và máy tính bảng chuyên dụng cho kỹ thuật viên hiện trường (Issue #36).
