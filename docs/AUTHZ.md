<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Phân quyền

Luật phân quyền của DX-Lab cho ứng dụng `lab-repair`: ai là ai, được làm gì, trong phạm vi nào, tới hạn mức nào.
Core thực thi các luật này cho mọi ứng dụng; phần riêng của `lab-repair` (hạn mức, định tuyến, trường dữ liệu cá
nhân) nằm trong tệp của ứng dụng và đổi được mà không sửa mã core.

## 0. Căn cứ và nhãn

Mỗi luật ghi nguồn bằng một trong ba nhãn:

| Nhãn | Nghĩa |
|---|---|
| **[QC]** | Theo QĐ 1152/QĐ-ĐHCN (Quy chế đầu tư, mua sắm, quản lý và sử dụng tài sản của Trường ĐH Công nghiệp Hà Nội, bản ngày 16/8/2024), đội đã đọc toàn văn |
| **[PL]** | Theo văn bản pháp luật, dẫn qua tài liệu tổng hợp; đội chưa đối chiếu toàn văn |
| **[GĐ]** | **Giả định** của đội để hệ thống chạy được và demo được; **không phải** văn bản, số liệu hay cơ cấu thật của HaUI |

Mọi căn cứ mang mã `GĐ-…` khi hiện trên portal, trong tài liệu và lúc demo đều kèm chữ **"giả định"**. Các văn bản
giả định:

| Mã | Tên | Dùng cho |
|---|---|---|
| `GĐ-TC-2026` | Cơ cấu tổ chức và tên đơn vị | Mục 2 |
| `GĐ-PC-01/2026` | Phân cấp sửa chữa tài sản cho trường thành viên và khoa | Mục 5 |
| `GĐ-PCBGĐ-2026` | Phân công Phó Giám đốc phụ trách cơ sở vật chất | Mục 5, 9 |

Thao tác "Duyệt" trong hệ thống là xác nhận nghiệp vụ, **không phải** văn bản điện tử ký số.

## 1. Năm lớp kiểm tra

Core kiểm theo thứ tự cho mỗi thao tác; lớp đầu tiên không đạt thì từ chối và trả về lớp đã chặn
(xem [định dạng lỗi](../CONTRIBUTING.md#định-dạng-lỗi)).

| Lớp | Câu hỏi | Dữ liệu nằm ở | Mã lỗi khi chặn |
|---|---|---|---|
| 1. Ai là ai | Token hợp lệ không, người này giữ vai trò gì ở đơn vị nào? | Keycloak: nhóm theo cây tổ chức | `UNAUTHENTICATED` (401), `FORBIDDEN_ROLE` |
| 2. Phạm vi | Đối tượng có thuộc đơn vị của người làm (kể cả đơn vị con) không? | Core, so cây đơn vị | `FORBIDDEN_SCOPE` |
| 3. Thẩm quyền | Hạn mức của vai trò có đủ không, hoặc có ủy quyền còn hạn không? | `authority.dmn` của ứng dụng, `/api/delegations` | `FORBIDDEN_AUTHORITY` |
| 4. Không kiêm nhiệm | Người này có đang tự duyệt việc mình đề xuất, tự nghiệm thu việc mình sửa không? | Thuộc tính `dxlabExcludeActorsOf` trên bước BPMN | `FORBIDDEN_SOD` |
| 5. Xem dữ liệu cá nhân | Người này có được thấy liên hệ của người báo không? | `x-personal-data` trong JSON Schema; core che | Không báo lỗi: trường bị che; xuất dữ liệu bị từ chối với `FORBIDDEN_PERSONAL_DATA` |

Mặc định **từ chối**: hành động không có trong mục 4 bị từ chối.

## 2. Cây tổ chức — [GĐ] `GĐ-TC-2026`

Tên Trường Công nghệ thông tin và Truyền thông và các khoa lấy theo trang công khai của trường; mã phòng, đường dẫn,
các ban, Trường Điện – Điện tử và Khoa Điện là giả định.

```text
/haui                                   Đại học Công nghiệp Hà Nội
  /ban-giam-doc                         Ban Giám đốc
  /ban-csvc                             Ban Cơ sở vật chất        (QĐ 1152 gọi: Phòng Quản trị)
  /ban-khtc                             Ban Kế hoạch – Tài chính  (QĐ 1152 gọi: Phòng Tài chính – Kế toán)
  /ban-dbcl-ksnb                        Ban Đảm bảo chất lượng – Kiểm soát nội bộ
  /tt-cntt                              Trung tâm Công nghệ thông tin
  /sict                                 Trường Công nghệ thông tin và Truyền thông
    /khmt                               Khoa Khoa học máy tính
      /lab-a1-305                       Phòng thực hành máy tính A1-305
      /lab-a1-306                       Phòng thực hành máy tính A1-306
    /mmt                                Khoa Mạng máy tính và Truyền thông
      /lab-a1-601                       Phòng thực hành mạng A1-601
  /truong-dien-dien-tu                  Trường Điện – Điện tử
    /khoa-dien                          Khoa Điện
      /lab-a10-201                      Phòng thí nghiệm điện A10-201
```

**Vai trò gắn với đơn vị là một nhóm con mang tên khóa vai trò.** Trưởng phòng A1-305 là thành viên nhóm
`/haui/sict/khmt/lab-a1-305/lab_manager`. Token có claim `groups` chứa đường dẫn đầy đủ; core lấy đoạn cuối làm vai
trò, phần trước làm đơn vị. Một người giữ nhiều vai trò thì thuộc nhiều nhóm con.

Tên hiển thị tiếng Việt của đơn vị nằm ở thuộc tính nhóm trong Keycloak. Đổi tên đơn vị (ví dụ "Phòng Quản trị"
thành "Ban Cơ sở vật chất") là sửa dữ liệu Keycloak, không sửa mã.

## 3. Vai trò

| Khóa | Tên hiển thị | Gắn ở | Ghi chú |
|---|---|---|---|
| `reporter` | Người báo hỏng | Mọi tài khoản đã đăng nhập | Mặc định, không cần nhóm |
| `lab_technician` | Kỹ thuật viên phòng thí nghiệm | Khoa hoặc phòng lab | Thiết bị chuyên dùng |
| `it_technician` | Cán bộ kỹ thuật TT CNTT | `/haui/tt-cntt` | Máy tính, máy chiếu, mạng |
| `facility_technician` | Cán bộ kỹ thuật Ban CSVC | `/haui/ban-csvc` | Điện, điều hòa, chiếu sáng, bàn ghế |
| `lab_manager` | Trưởng phòng thí nghiệm | Phòng lab | Xác nhận nhu cầu, nghiệm thu; **không duyệt chi** |
| `faculty_head` | Trưởng khoa | Khoa | Duyệt theo mục 5 |
| `faculty_deputy` | Phó trưởng khoa | Khoa | Chỉ duyệt khi có ủy quyền TUQ. |
| `school_head` | Hiệu trưởng trường thành viên | Trường thành viên | Duyệt theo mục 5 |
| `facility_officer` | Chuyên viên Ban CSVC | `/haui/ban-csvc` | Tổng hợp, định tuyến lại, nhận phiếu mua sắm |
| `facility_director` | Trưởng Ban CSVC | `/haui/ban-csvc` | Xem toàn trường, báo cáo |
| `finance_officer` | Chuyên viên Ban KH-TC | `/haui/ban-khtc` | Chỉ xem phiếu có chi phí |
| `vice_president` | Phó Giám đốc phụ trách cơ sở vật chất | `/haui/ban-giam-doc` | Duyệt "KT. Giám đốc" |
| `president` | Giám đốc Đại học | `/haui/ban-giam-doc` | Thẩm quyền gốc [QC] Đ7, Đ15.1 |
| `internal_auditor` | Chuyên viên kiểm soát nội bộ | `/haui/ban-dbcl-ksnb` | Đọc audit; xuất dữ liệu cá nhân có lý do, có log |
| `process_admin` | Cán bộ thiết kế quy trình | `/haui/tt-cntt` | Nạp mọi loại tệp của gói ứng dụng |
| `rule_admin` | Người soạn bảng luật | `/haui/ban-csvc` | Chỉ nạp bảng luật `.dmn` |
| `process_owner` | Chủ quy trình | `/haui/ban-giam-doc` | Duyệt phiên bản định nghĩa trước khi áp dụng |
| `system_admin` | Quản trị hệ thống | `/haui/tt-cntt` | **Không có quyền nghiệp vụ nào** |

Lane trong BPMN dùng vai trò trừu tượng: `reporter`; `technician` (core chọn đúng vai trò kỹ thuật theo
`routing.dmn`); `lab_manager` (phòng không có trưởng lab thì `faculty_head`); `approver` (core tính người đủ thẩm quyền
từ `authority.dmn`, không gắn cứng người nào).

## 4. Hành động

| Hành động | Ý nghĩa | Ai | Phạm vi |
|---|---|---|---|
| `report.create` | Tạo phiếu báo hỏng | `reporter` | Mọi tài sản đang hoạt động |
| `request.read` | Xem phiếu | Mục 8 | Mục 8 |
| `routing.override` | Đổi đơn vị kỹ thuật đã định tuyến | `facility_officer` | Toàn trường |
| `technical_assessment.confirm` | Lập **biên bản xác nhận tình trạng**: nguyên nhân, phương án, chi phí dự kiến [QC] Đ15.4b | Kỹ thuật viên của đơn vị được định tuyến | Phiếu được giao |
| `repair.perform` | Ghi nhận đã sửa, chi phí thực tế | Kỹ thuật viên được giao | Phiếu được giao |
| `repair.endorse` | Xác nhận nhu cầu sửa có chi phí [QC] Đ10.7, Đ15.1 | `lab_manager` của phòng; không có thì `faculty_head` | Phòng / khoa |
| `repair.approve` | Duyệt sửa có chi phí | Mục 5 | Mục 5 |
| `acceptance.confirm` | Nghiệm thu, bàn giao sử dụng | `lab_manager`; không có thì `faculty_head` | Phòng / khoa |
| `procurement.request` | Xuất phiếu đề nghị mua mới, thay thế, gửi Ban CSVC [QC] Đ15.4b | `lab_manager`, `faculty_head` | Phòng / khoa |
| `disposal.propose` | Đề nghị thanh lý [QC] Đ15.4c, Đ24 | `facility_officer` | Toàn trường |
| `reporter_contact.read` | Xem họ tên, mã, số điện thoại, email người báo | Mục 8 | Mục 8 |
| `personal_data.export` | Xuất dữ liệu cá nhân | `internal_auditor`, bắt buộc nhập lý do | Toàn trường |
| `delegation.create`, `delegation.revoke` | Tạo, thu hồi ủy quyền | Người giữ thẩm quyền gốc | Thẩm quyền của chính mình |
| `definition.publish` | Nạp gói ứng dụng | `rule_admin` (chỉ `.dmn`), `process_admin` (mọi loại tệp) | — |
| `definition.activate` | Duyệt phiên bản để áp dụng | `process_owner` | — |

Mua sắm, chọn nhà thầu, hợp đồng, thanh toán, thanh lý nằm **ngoài hệ thống**: hệ thống chỉ xuất phiếu và ghi trạng thái.

## 5. Thẩm quyền duyệt theo hạn mức — `apps/lab-repair/authority.dmn`

Chỉ áp cho sửa chữa khôi phục, không thay đổi công năng, quy mô ([PL] TT 65/2021/TT-BTC Đ3.1). Chi phí dự kiến là
tổng chi phí một lần sửa cho một tài sản, đã gồm VAT, lấy từ biên bản tình trạng. Bảng đọc từ trên xuống, dừng ở
dòng khớp đầu tiên:

| # | Loại việc | Chi phí dự kiến (đồng) | Người duyệt | Phạm vi | Hình thức | Căn cứ |
|---|---|---|---|---|---|---|
| 1 | `repair` | 0 | Không cần duyệt | — | — | [QC] Đ15.4b |
| 2 | `repair` | ≤ 5.000.000 | `faculty_head` | Khoa sở hữu phòng | Theo phân cấp | `GĐ-PC-01/2026` (giả định) |
| 3 | `repair` | ≤ 20.000.000 | `school_head` | Trường thành viên | Theo phân cấp | `GĐ-PC-01/2026` (giả định) |
| 4 | `repair` | ≤ 100.000.000 | `vice_president` | Toàn đại học | **KT. Giám đốc** | `GĐ-PCBGĐ-2026` (giả định) |
| 5 | `repair` | > 100.000.000 | `president` | Toàn đại học | Trực tiếp | [QC] Đ7, Đ15.1 |
| 6 | `replace` (không sửa được, mua mới) | Bất kỳ | Ngoài hệ thống: `procurement.request` gửi Ban CSVC | — | — | [QC] Đ15.4b |
| 7 | `upgrade` (cải tạo, nâng cấp) | Bất kỳ | Ngoài hệ thống | — | — | [PL] TT 65/2021/TT-BTC Đ3.1 |

Số báo giá phải đính kèm biên bản tình trạng (bảng `quotes` trong cùng tệp): dưới 20.000.000 đồng cần 1 (báo giá hoặc
ước tính của kỹ thuật viên); từ 20.000.000 đồng cần 3.

QĐ 1152 không ghi hạn mức tiền cho sửa chữa; hiệu trưởng có thể phân cấp cho đơn vị ([QC] Đ9.3, Đ10.3). Bỏ các dòng
2–4 (không có quyết định phân cấp) thì hệ thống vẫn đúng quy chế: mọi phiếu có chi phí lên dòng 5. Lý do chọn mốc
giả định:

| Mốc | Lý do |
|---|---|
| 5 triệu | [QC] Đ4.1a: tài sản cố định đặc thù tính từ nguyên giá 5 triệu đồng, nên sửa dưới mức này coi là sửa nhỏ |
| 20 triệu | Mốc "từ 20 triệu phải có 3 báo giá" trong một quy trình công khai của trường đại học khác; chỉ là thực tiễn tham khảo |
| 100 triệu | [PL] Mốc mua sắm giá trị nhỏ tại khoản 4 Điều 80 NĐ 214/2025/NĐ-CP (sửa đổi bởi NĐ 349/2026/NĐ-CP) |

Luật leo thang (core thực thi):

| Mã | Luật |
|---|---|
| E1 | Người duyệt theo bảng cũng là người tạo phiếu hoặc người xác nhận nhu cầu → chuyển lên dòng kế tiếp |
| E2 | Chi phí thực tế vượt chi phí đã duyệt quá 10%, hoặc vượt hạn mức của người đã duyệt → duyệt lại theo chi phí thực tế |
| E3 | Chống chia nhỏ: tra bảng bằng tổng chi phí đã duyệt cho cùng tài sản trong 30 ngày cộng chi phí mới (chưa làm) |
| E4 | Khẩn cấp an toàn (điện, cháy nổ): kỹ thuật viên được cô lập, ngắt thiết bị ngay không cần duyệt; chi phí sửa vẫn theo bảng |

## 6. Định tuyến — `apps/lab-repair/routing.dmn`

| Loại sự cố / thiết bị | Đơn vị kỹ thuật | Vai trò xử lý | Căn cứ |
|---|---|---|---|
| `computer`, `projector` | `/haui/tt-cntt` | `it_technician` | [QC] Đ15.4b |
| `network` | `/haui/tt-cntt` | `it_technician` | [GĐ] |
| `electrical`, `air_conditioner`, `lighting`, `furniture`, `plumbing` | `/haui/ban-csvc` | `facility_technician` | [QC] Đ15.4b |
| `lab_equipment` (máy hiện sóng, bộ thí nghiệm…) | Khoa sở hữu phòng | `lab_technician` | [GĐ]; Ban CSVC được thông báo |
| Còn lại | `/haui/ban-csvc` | `facility_officer` định tuyến lại | [GĐ] |

Mức ưu tiên và thời hạn xử lý do `triage.dmn` quyết định, kèm mã lý do.

## 7. Không kiêm nhiệm — [GĐ], căn cứ chung [PL] Luật Kế toán 88/2015/QH13 Đ39

| Mã | Luật | Thực thi |
|---|---|---|
| SoD-1 | Người tạo phiếu không duyệt (`repair.approve`) phiếu đó | Bước duyệt khai báo loại người làm bước báo hỏng; core kiểm |
| SoD-2 | Người lập biên bản hoặc người sửa không nghiệm thu (`acceptance.confirm`) | Bước nghiệm thu khai báo loại người làm bước kiểm tra, bước sửa |
| SoD-3 | Người xác nhận nhu cầu khác người duyệt; trùng thì leo thang E1 | Bước duyệt + E1 |
| SoD-4 | Tài khoản có `system_admin` không làm được hành động nghiệp vụ nào | Core từ chối |
| SoD-5 | Người nạp định nghĩa không tự duyệt áp dụng phiên bản đó | Core từ chối |

## 8. Xem phiếu và dữ liệu cá nhân — [PL] Luật 91/2025/QH15, NĐ 356/2025/NĐ-CP + [GĐ]

Trường dữ liệu cá nhân (đánh dấu `x-personal-data: true`): họ tên, mã sinh viên hoặc mã cán bộ, số điện thoại, email
của người báo.

| Vai trò | Thấy phiếu nào | Thấy liên hệ người báo |
|---|---|---|
| `reporter` | Phiếu của mình | Của chính mình |
| Kỹ thuật viên | Phiếu được giao + hàng đợi của đơn vị kỹ thuật | Có, khi phiếu đang giao cho mình |
| `lab_manager` | Phiếu của phòng | Có |
| `faculty_head`, `faculty_deputy` | Phiếu của khoa | Có |
| `school_head` | Phiếu của trường thành viên | Không (che) |
| `facility_officer`, `facility_director` | Toàn trường | Không |
| `finance_officer` | Toàn trường, chỉ phiếu có chi phí | Không |
| `vice_president`, `president` | Toàn trường | Không |
| `internal_auditor` | Toàn trường + audit | Có; mỗi lần xem ghi log, xuất phải nhập lý do |
| `system_admin` | Không thấy nội dung nghiệp vụ | Không |

- Mọi lần xem liên hệ hoặc xuất dữ liệu cá nhân đều ghi log; bản ghi log không chứa chính dữ liệu cá nhân.
- Dashboard chỉ có số liệu tổng hợp, không có tên người.
- Lần báo hỏng đầu tiên hiện thông báo xử lý dữ liệu (mục đích: liên hệ để xử lý sự cố). Ô xác nhận **không tick
  sẵn**; hệ thống lưu phiên bản thông báo và thời điểm xác nhận.
- Lưu giữ [GĐ]: liên hệ người báo được ẩn danh hóa 12 tháng sau khi phiếu đóng. Nhật ký sửa chữa của tài sản
  (sổ theo dõi sửa chữa, [QC] Đ20.2c) giữ suốt vòng đời tài sản, đã ẩn danh người báo.
- Người báo hỏng **không** mặc nhiên là người gây hỏng; xác định trách nhiệm, bồi thường ([QC] Đ23.4a) là quy trình
  riêng, không thuộc hệ thống.

## 9. Ủy quyền — [PL] NĐ 30/2020/NĐ-CP Đ13 + [GĐ]

| Hình thức | Dùng khi | Điều kiện trong hệ thống |
|---|---|---|
| **KT.** (ký thay) | Phó Giám đốc duyệt thay Giám đốc trong lĩnh vực được phân công | Cấu hình thường trực theo `GĐ-PCBGĐ-2026` (giả định), là dòng 4 của mục 5; audit ghi "KT. Giám đốc" |
| **TUQ.** (thừa ủy quyền) | Người giữ thẩm quyền vắng, ví dụ trưởng khoa đi công tác | Bắt buộc số giấy ủy quyền; từ ngày – đến ngày, **tối đa 30 ngày** [GĐ]; đúng hành động và phạm vi; **không vượt hạn mức của người ủy quyền**; người nhận cùng đơn vị; **không ủy quyền lại**; người ủy quyền thu hồi được bất kỳ lúc nào |
| **Q.** (quyền) | Được giao quyền cấp trưởng | Coi như giữ vai trò cấp trưởng: gán nhóm trong Keycloak, không qua `/api/delegations` |
| **TL.** (thừa lệnh) | Văn bản hành chính | Không dùng cho duyệt sửa chữa |

Người được ủy quyền dùng **tài khoản của chính mình**. Audit ghi người làm thật, hình thức, người ủy quyền, số giấy.

## 10. Xác thực — [GĐ]

- Xác thực hai bước (OTP của Keycloak) bắt buộc cho vai trò có `repair.approve` và cho `process_admin`, `rule_admin`,
  `process_owner`, `internal_auditor`, `system_admin`.
- Phiên đăng nhập hết hạn sau 30 phút không thao tác. Keycloak chỉ đặt được thời hạn này cho cả realm, nên áp cho
  mọi tài khoản, không riêng tài khoản có xác thực hai bước.
- Mỗi người một tài khoản; không có tài khoản dùng chung.

## 11. Tài khoản demo — [GĐ], tên giả, không phải người thật

Mọi tài khoản dùng chung mật khẩu đặt qua biến `DXLAB_DEMO_PASSWORD` ([`ARCHITECTURE.md`](ARCHITECTURE.md) mục 5),
**chỉ dùng cho demo**. Tài khoản phải xác thực hai bước được nạp sẵn một khóa OTP chung từ biến
`DXLAB_DEMO_OTP_SECRET`, để script demo (`seed.sh`, `demo-e2e.sh`) đăng nhập không cần điện thoại. Cột "Nhóm" là
đơn vị; tài khoản là thành viên nhóm con `<đơn vị>/<vai trò>`.

| Username | Tên giả | Vai trò | Nhóm |
|---|---|---|---|
| `sv.an` | Nguyễn Văn An | `reporter` (sinh viên) | — |
| `gv.binh` | Trần Thị Bình | `reporter` (giảng viên KHMT) | — |
| `ktv.cuong` | Lê Văn Cường | `it_technician` | `/haui/tt-cntt` |
| `ktv.dung` | Phạm Thị Dung | `facility_technician` | `/haui/ban-csvc` |
| `ktv.duc` | Đỗ Minh Đức | `lab_technician` | `/haui/sict/khmt` |
| `tl.giang` | Hoàng Thu Giang | `lab_manager` | `/haui/sict/khmt/lab-a1-305` |
| `tk.hai` | Vũ Đức Hải | `faculty_head` | `/haui/sict/khmt` |
| `ptk.hoa` | Ngô Thị Hoa | `faculty_deputy` | `/haui/sict/khmt` |
| `ht.khanh` | Bùi Quốc Khánh | `school_head` | `/haui/sict` |
| `tk.long` | Đặng Văn Long | `faculty_head` | `/haui/truong-dien-dien-tu/khoa-dien` |
| `csvc.lan` | Mai Thị Lan | `facility_officer`, `rule_admin` | `/haui/ban-csvc` |
| `kt.oanh` | Phan Thị Oanh | `finance_officer` | `/haui/ban-khtc` |
| `pgd.minh` | Trịnh Văn Minh | `vice_president`, `process_owner` | `/haui/ban-giam-doc` |
| `gd.nam` | Lý Thành Nam | `president` | `/haui/ban-giam-doc` |
| `ksnb.phuong` | Hồ Thị Phương | `internal_auditor` | `/haui/ban-dbcl-ksnb` |
| `qt.son` | Tạ Văn Sơn | `process_admin` | `/haui/tt-cntt` |
| `admin.dx` | — | `system_admin` | `/haui/tt-cntt` |

## 12. Kịch bản kiểm chứng

Dùng làm test của core và kịch bản demo.

| # | Tình huống | Kết quả mong đợi |
|---|---|---|
| 1 | `sv.an` báo máy chiếu A1-305 không lên hình | Định tuyến TT CNTT, vào hàng đợi `it_technician` |
| 2 | `ktv.cuong` lập biên bản: thay bóng đèn, 3.500.000 | Chờ `tl.giang` xác nhận nhu cầu, rồi chờ `tk.hai` duyệt (dòng 2) |
| 3 | Biên bản 12.000.000 | Người duyệt `ht.khanh` (dòng 3) |
| 4 | Biên bản 60.000.000 | Người duyệt `pgd.minh`, audit ghi "KT. Giám đốc"; thiếu 3 báo giá thì không gửi duyệt được |
| 5 | Biên bản 150.000.000 | Người duyệt `gd.nam` (dòng 5) |
| 6 | `tk.long` (Khoa Điện) bấm duyệt phiếu ở A1-305 | Từ chối ở lớp 2 (phạm vi) |
| 7 | `tk.hai` ủy quyền TUQ. cho `ptk.hoa` 7 ngày | `ptk.hoa` duyệt được 3.500.000 (audit "TUQ. Trưởng khoa"); duyệt 12.000.000 bị từ chối (vượt hạn mức người ủy quyền); sau hạn bị từ chối |
| 8 | `tk.hai` tự báo hỏng, rồi là người duyệt theo bảng | Leo thang E1 lên `ht.khanh` |
| 9 | `ktv.cuong` đã sửa, bấm nghiệm thu | Từ chối ở lớp 4 (SoD-2) |
| 10 | Đã duyệt 3.500.000, chi phí thực tế 4.000.000 (vượt 14%) | Duyệt lại (E2), vẫn dòng 2, người duyệt `tk.hai` |
| 11 | `ht.khanh` mở phiếu | Không thấy số điện thoại người báo; `ktv.cuong` đang được giao thì thấy |
| 12 | Không sửa được | `tl.giang` xuất phiếu đề nghị mua sắm gửi Ban CSVC; phiếu chuyển "Đã chuyển Ban CSVC" |
| 13 | `csvc.lan` đổi hạn mức trưởng khoa từ 5 lên 10 triệu; `pgd.minh` duyệt phiên bản | Phiếu mới 8.000.000 do `tk.hai` duyệt; phiếu tạo trước giữ luật cũ, người duyệt `ht.khanh` |
| 14 | `admin.dx` bấm duyệt bất kỳ phiếu nào | Từ chối (SoD-4) |

## 13. Mỗi luật nằm ở đâu

| Luật | Nơi đặt | Ai được đổi |
|---|---|---|
| Cây tổ chức, vai trò, tài khoản demo, xác thực hai bước, thời hạn phiên | `deploy/keycloak/realm.json` | Dữ liệu Keycloak |
| Định tuyến, ưu tiên và thời hạn, thẩm quyền, số báo giá | `apps/lab-repair/routing.dmn`, `triage.dmn`, `authority.dmn` | `rule_admin` nạp, `process_owner` duyệt |
| Không kiêm nhiệm SoD-1 … SoD-3 | Thuộc tính bước trong `apps/lab-repair/lab-repair.bpmn` | `process_admin` nạp, `process_owner` duyệt |
| Trường dữ liệu cá nhân | `apps/lab-repair/*-schema.json` (`x-personal-data`) | `process_admin` nạp, `process_owner` duyệt |
| Phạm vi theo cây, ủy quyền, che dữ liệu, log xem, E1 … E3, SoD-4, SoD-5 | Mã core, dùng chung cho mọi ứng dụng | Lập trình viên, qua review và bản phát hành mới |
| Nhãn "giả định" của căn cứ `GĐ-…` | Portal hiển thị theo tiền tố mã căn cứ | Lập trình viên portal |
