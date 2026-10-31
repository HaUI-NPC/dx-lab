<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# DX-Lab: Slide Trình bày (v0.2.x)

Bộ slide này gồm đúng 12 slide (tuân thủ giới hạn ≤ 12 slide của DOC-05), phục vụ bảo vệ đồ án / demo hệ thống DX-Lab.

---

## Slide 1: Giới thiệu hệ thống DX-Lab
- **Tên dự án**: DX-Lab (Open-Core Repair & Asset Management Platform).
- **Mục tiêu**: Giải pháp số hóa toàn diện quy trình báo hỏng, sửa chữa, định tuyến, phân quyền và duyệt tài sản theo QĐ 1152/QĐ-ĐHCN và các quy định pháp luật liên quan tại Đại học Công nghiệp Hà Nội (HaUI).
- **Kiến trúc**: Open-Core, tách biệt rõ ràng phần lõi (Core) dùng chung và các ứng dụng nghiệp vụ (`lab-repair`).

---

## Slide 2: Kiến trúc tổng thể & Các tầng hệ thống
Hệ thống được tổ chức thành 4 tầng rõ rệt:
1. **Tầng 1 (Cơ sở hạ tầng & Xác thực)**: Keycloak (OIDC/RBAC/OTP), PostgreSQL (DB + FTS), Apache APISIX (API Gateway).
2. **Tầng 2 (Lõi Core & Quy trình)**: `dxlab-core` FastAPI API, SpiffWorkflow (BPMN/DMN), quản lý định nghĩa gói ứng dụng, kiểm tra 5 lớp phân quyền.
3. **Tầng 3 (Giao diện & Tiện ích)**: Portal H-P-D-I (Prefeb UI), form động, hộp việc của tôi, tra cứu.
4. **Tầng 4 (Ứng dụng nghiệp vụ)**: `lab-repair` (quản lý phòng thí nghiệm, thiết bị, sửa chữa, thay thế, ủy quyền).

---

## Slide 3: Tầng 1 — Xác thực & Phân quyền (Keycloak & APISIX)
- **Keycloak Realm**: Quản lý cây tổ chức Đại học Công nghiệp Hà Nội (`/haui`), các phòng ban, khoa, trung tâm.
- **Vai trò (Roles)**: 18 vai trò chuẩn từ sinh viên (`reporter`), kỹ thuật viên (`it_technician`, `facility_technician`), trưởng phòng (`lab_manager`), trưởng khoa (`faculty_head`), đến Ban Giám đốc và Kiểm soát nội bộ.
- **Xác thực 2 bước (OTP)**: Bắt buộc đối với các vai trò nhạy cảm (`process_admin`, `rule_admin`, `internal_auditor`, `system_admin`).
- **API Gateway (APISIX)**: Định tuyến, kiểm tra token JWT, xác thực chữ ký trước khi đến Core.

---

## Slide 4: Tầng 2 — Lõi xử lý (dxlab-core & SpiffWorkflow)
- **FastAPI Core**: Cung cấp các API REST chuẩn cho quản lý workflow, nhiệm vụ (tasks), định nghĩa (definitions), bản ghi (records), và audit log.
- **SpiffWorkflow**: Thực thi động các tệp BPMN (quy trình nghiệp vụ) và DMN (bảng quyết định thẩm quyền, định tuyến, ưu tiên).
- **4 Cửa kiểm soát định nghĩa**:
  1. `rule_admin` chỉ nạp được bảng luật `.dmn`.
  2. `process_admin` nạp gói quy trình.
  3. Kiểm tra bảo mật mã độc/python code trong biểu thức BPMN/DMN.
  4. `process_owner` (`vice_president`) duyệt kích hoạt phiên bản trước khi áp dụng vào sản xuất.

---

## Slide 5: Phân quyền 5 lớp (5-Layer Authorization)
Core kiểm tra tuần tự 5 lớp cho mọi thao tác nghiệp vụ:
1. **Lớp 1 (Ai là ai)**: Token hợp lệ, vai trò từ nhóm Keycloak (`UNAUTHENTICATED`, `FORBIDDEN_ROLE`). Chặn tài khoản hệ thống (`system_admin`) làm nghiệp vụ (SoD-4).
2. **Lớp 2 (Phạm vi đơn vị)**: Đối tượng phải thuộc đơn vị của người thực hiện hoặc đơn vị con (`FORBIDDEN_SCOPE`).
3. **Lớp 3 (Thẩm quyền hạn mức)**: Kiểm tra hạn mức từ `authority.dmn` hoặc ủy quyền hợp lệ (`FORBIDDEN_AUTHORITY`).
4. **Lớp 4 (Không kiêm nhiệm - SoD)**: Chống tự duyệt, chống tự nghiệm thu việc mình sửa (`dxlabExcludeActorsOf`, `FORBIDDEN_SOD`).
5. **Lớp 5 (Xem dữ liệu cá nhân)**: Che tự động thông tin liên hệ (`x-personal-data` trong JSON Schema), ghi log mỗi lần truy cập (`FORBIDDEN_PERSONAL_DATA`).

---

## Slide 6: Bảng thẩm quyền duyệt & Luật leo thang
- **Phân cấp chi phí sửa chữa** (`apps/lab-repair/authority.dmn`):
  - `0 đ`: Không cần duyệt.
  - `≤ 5.000.000 đ`: Trưởng khoa (`faculty_head`).
  - `≤ 20.000.000 đ`: Hiệu trưởng trường thành viên (`school_head`).
  - `≤ 100.000.000 đ`: Phó Giám đốc phụ trách CSVC (`vice_president` — KT. Giám đốc).
  - `> 100.000.000 đ`: Giám đốc Đại học (`president`).
- **Luật leo thang (E1 — E4)**:
  - **E1**: Người duyệt đồng thời là người tạo phiếu → tự động chuyển lên cấp kế tiếp.
  - **E2**: Chi phí thực tế vượt quá 10% chi phí duyệt → yêu cầu duyệt lại.
  - **E3**: Chống chia nhỏ hóa đơn trong 30 ngày.
  - **E4**: Khẩn cấp an toàn (điện, cháy nổ) → cô lập ngay không cần chờ duyệt.

---

## Slide 7: Cơ chế Ủy quyền (TUQ. / KT.)
- **KT. (Ký thay)**: Phó Giám đốc duyệt thay Giám đốc theo phân công thường trực (`GĐ-PCBGĐ-2026`).
- **TUQ. (Thừa ủy quyền)**:
  - Áp dụng khi người giữ thẩm quyền vắng mặt (ví dụ Trưởng khoa đi công tác).
  - Điều kiện nghiêm ngặt: Bắt buộc có số giấy, thời hạn tối đa 30 ngày, cùng đơn vị, không vượt hạn mức người ủy quyền, không ủy quyền lại, người ủy quyền thu hồi bất kỳ lúc nào.
  - Người nhận ủy quyền dùng tài khoản của chính mình; audit ghi rõ người làm thật, hình thức, người ủy quyền và số giấy.

---

## Slide 8: Tầng 3 — Giao diện & Portal H-P-D-I
- **Framework**: Prefab UI (Python-based frontend).
- **Form động (Dynamic Forms)**: Sinh giao diện nhập liệu tự động từ JSON Schema (`report-schema.json`, `approve-schema.json`).
- **Hộp việc của tôi (My Tasks)**: Danh sách công việc cần xử lý theo vai trò và đơn vị.
- **Dashboard & Tra cứu**:
  - Thống kê tổng hợp trạng thái phiếu, thời gian xử lý.
  - Tra cứu tài sản, phòng thí nghiệm, lịch sử sửa chữa thiết bị.

---

## Slide 9: Tầng 4 — Ứng dụng nghiệp vụ `lab-repair`
- **Quy trình chuẩn**:
  1. Sinh viên / giảng viên (`reporter`) báo hỏng thiết bị (máy chiếu, máy tính, mạng, điện).
  2. Hệ thống định tuyến (`routing.dmn`) chuyển đến đơn vị kỹ thuật (`it_technician` hoặc `facility_technician`).
  3. Kỹ thuật viên lập biên bản xác nhận tình trạng, dự kiến chi phí, đính kèm báo giá.
  4. Trưởng phòng thí nghiệm (`lab_manager`) xác nhận nhu cầu.
  5. Cấp thẩm quyền (`faculty_head`, `school_head`, `vice_president`, `president`) duyệt sửa chữa dựa trên hạn mức.
  6. Kỹ thuật viên tiến hành sửa chữa, ghi nhận chi phí thực tế.
  7. Trưởng phòng thí nghiệm nghiệm thu và bàn giao sử dụng (`acceptance.confirm`).

---

## Slide 10: AI & Công cụ tích hợp (MCP Server & LLM)
- **MCP Server (Model Context Protocol)**:
  - Tích hợp AI assistant trực tiếp với hệ thống DX-Lab core.
  - Hỗ trợ tra cứu quy chế (`docs/AUTHZ.md`, `ARCHITECTURE.md`), kiểm tra trạng thái phiếu và phân tích dữ liệu qua LLM.
- **Phát hiện & che PII tự động**: AI hỗ trợ phát hiện dữ liệu cá nhân trong văn bản tự do để bảo mật thông tin người báo.

---

## Slide 11: Kiểm thử, CI/CD & Đảm bảo chất lượng (QA)
- **Kiểm thử tự động**:
  - Hơn 13 kịch bản kiểm chứng phân quyền toàn diện (`core/tests/test_authz_scenarios.py`).
  - Kiểm tra validator chống mã độc Python trong biểu thức BPMN/DMN.
  - Test chạy trên PostgreSQL thật qua GitHub Actions CI.
- **Tuân thủ mã nguồn & Giấy phép**:
  - `uvx reuse lint` đảm bảo 100% tệp có đủ tiêu đề bản quyền và định danh giấy phép (SPDX).
  - Code chuẩn ruff, black, mypy.

---

## Slide 12: Tổng kết & Hướng phát triển
- **Đã đạt được**:
  - Xây dựng hoàn chỉnh nền tảng Open-Core DX-Lab từ hạ tầng, lõi xử lý, phân quyền 5 lớp đến Portal và ứng dụng `lab-repair`.
  - Tuân thủ đầy đủ quy chế đầu tư, mua sắm và quản lý tài sản (QĐ 1152/QĐ-ĐHCN) kết hợp các quy định pháp luật.
- **Hướng phát triển v0.3.x**:
  - Mở rộng thêm ứng dụng `room-booking` (đặt phòng thí nghiệm).
  - Tích hợp sâu hơn mô hình ngôn ngữ lớn (LLM) cục bộ để tự động phân tích báo hỏng.
- **Q&A**: Cảm ơn Hội đồng và các thầy cô đã lắng nghe!
