<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Đánh giá trí tuệ nhân tạo và luật: bộ phiếu gán nhãn và câu hỏi tìm kiếm

Tài liệu này ghi số liệu đo của INT-01: độ chính xác của bảng luật `triage.dmn` và `routing.dmn` của `lab-repair` trên 60
phiếu gán nhãn tay, và bộ 20 câu hỏi tìm kiếm cùng đường cơ sở từ khóa. Phần DMN **không dùng mô hình học máy nào**: luật
quyết định, có mã lý do. Tìm kiếm ngữ nghĩa (zvec) do CORE-08 làm; ở đây chỉ có bộ câu hỏi và mốc so sánh.

## Giới hạn cần đọc trước

- **Nhãn do agent soạn hộ, chưa có người rà.** Cả 60 phiếu và nhãn (loại thật, mức ưu tiên, đơn vị kỹ thuật) do một agent
  lập trình viết theo định nghĩa ở `docs/AUTHZ.md` mục 6 và tiêu chí P1/P2/P3 của quy trình. Phiếu là **dữ liệu tổng hợp**,
  không phải phiếu thật của HaUI. Cần một thành viên (kỹ thuật viên hoặc người am hiểu phòng lab) rà lại nhãn trước khi
  dùng số liệu để kết luận; các ca mơ hồ nêu ở phần "Ca sai".
- **Nhãn và luật cùng nguồn.** Bảng ánh xạ loại thiết bị → đơn vị kỹ thuật của người gán nhãn lấy từ AUTHZ mục 6, cũng là nguồn của
  `routing.dmn`; vì thế độ chính xác của định tuyến chủ yếu đo **đầu vào người báo chọn** chứ không đo luật có "thông minh" hay
  không. Mức ưu tiên thì khác: nhãn đọc từ **mô tả tự do**, còn DMN chỉ thấy các trường có cấu trúc người báo điền.
- 60 phiếu là mẫu nhỏ: mỗi phiếu sai thay đổi chỉ số 1,7 điểm phần trăm.
- Thời hạn SLA, ngưỡng mức ưu tiên trong `triage.dmn` là giả định (GĐ) của đội, chưa kiểm với thực tế vận hành.
- Không sửa DMN trong INT-01; mọi ca sai ghi lại để mentor quyết.

## Bộ dữ liệu

`apps/lab-repair/eval/tickets.json`: 60 phiếu tổng hợp với các trường `room_id`, `asset_id`, `asset_category`,
`impact`, `safety_hazard`, `urgency`, mô tả tự do và nhãn do agent tạo. Các trường hợp `other` là đầu vào đối kháng
trực tiếp cho DMN, không hợp lệ với enum biểu mẫu hiện hành; không thể gửi những phiếu đó qua form.

| Nhãn | Giá trị |
|---|---|
| `true_category` | Loại thật của sự cố theo AUTHZ mục 6 (`computer`, `projector`, `network`, `electrical`, `air_conditioner`, `lighting`, `furniture`, `plumbing`, `lab_equipment`) |
| `priority` | `P1` (nguy cơ an toàn, cả phòng không dùng được), `P2` (ảnh hưởng một phần buổi thực hành), `P3` (còn lại) |
| `tech_unit`, `tech_role` | Đơn vị và vai trò kỹ thuật đáng lẽ phải nhận phiếu (`owner_faculty` là khoa sở hữu phòng) |

Phân bố: P1 11 phiếu, P2 21, P3 28; đơn vị `/haui/tt-cntt` 32, `/haui/ban-csvc` 18, `owner_faculty` 10. Một số phiếu cố ý
gài tình huống thật: người báo không đánh dấu nguy cơ an toàn dù mô tả có khói hoặc lộ dây điện, chọn "ảnh hưởng cả phòng"
cho sự cố chỉ ảnh hưởng một phần, báo "gấp" cho việc nhỏ, hoặc chọn loại `other` cho thiết bị thuộc loại khác.

## Đo độ chính xác DMN

Lệnh (chạy từ gốc repo; SpiffWorkflow nằm trong danh sách thư viện cho phép ở `docs/ARCHITECTURE.md` mục 8):

```bash
uv run --with "spiffworkflow>=3.2" python apps/lab-repair/eval/measure_dmn.py
```

Mỗi phiếu chạy qua quy trình thật `lab-repair.bpmn` đến bước `pending_assessment`, rồi đọc `priority`, `tech_unit`, `tech_role`
do `triage.dmn` và `routing.dmn` trả. Kết quả trên nhánh `feat/APP-01-lab-repair` (PR #69):

Bộ phiếu: 60 phiếu từ tickets.json

| Chỉ số | Đúng / Tổng |
|---|---|
| Mức ưu tiên (triage.dmn) | 53/60 = 88.3% |
| Đơn vị kỹ thuật (routing.dmn: tech_unit) | 57/60 = 95.0% |
| Vai trò xử lý (routing.dmn: tech_role) | 50/60 = 83.3% |
| Định tuyến đúng cả đơn vị và vai trò | 50/60 = 83.3% |
| Loại được chọn khớp loại thật (đầu vào, không phải do DMN) | 47/60 = 78.3% |

Ma trận nhầm lẫn mức ưu tiên (hàng = nhãn tay, cột = DMN):

| Nhãn \ DMN | P1 | P2 | P3 |
|---|---|---|---|
| P1 | 8 | 1 | 2 |
| P2 | 1 | 19 | 1 |
| P3 | 0 | 2 | 26 |


### Ca sai

17 phiếu sai (7 về mức ưu tiên, 10 về định tuyến, không phiếu nào sai cả hai). Phân loại theo nguyên nhân:

| Nguyên nhân | Phiếu | Nhận xét |
|---|---|---|
| Người báo không đánh dấu `safety_hazard` dù mô tả có nguy cơ an toàn | T03, T07, T10 | **Nghiêm trọng nhất**: sự cố an toàn bị xếp P3 (T03, T10) hoặc P2 (T07); SLA kiểm tra 48 giờ thay vì 4 giờ. DMN không đọc được mô tả tự do. Cách giảm rủi ro thuộc form (đặt câu hỏi an toàn bắt buộc, có gợi ý) hoặc kỹ thuật viên tiếp nhận nâng mức; không sửa được chỉ bằng `triage.dmn` |
| Người báo chọn "ảnh hưởng cả phòng" cho sự cố chỉ ảnh hưởng một phần | T09 | Xếp P1 (`ROOM_BLOCKED`) thay vì P2: xếp thừa mức, tốn nguồn lực kỹ thuật |
| Dòng `REPORTER_URGENT` (`urgency` = `high` hoặc `critical` → P2) | T53, T54 | Người báo ghi "gấp" cho việc nhỏ, bị xếp P2 thay vì P3. Mentor quyết có giữ dòng này không: bỏ thì giảm xếp thừa nhưng mất tín hiệu khẩn của người báo |
| Nhãn mơ hồ | T30 | Điều hòa kêu to không mất mát; người gán nhãn xếp P2 vì ảnh hưởng nghe giảng, DMN xếp P3. Cần người rà nhãn |
| Loại `other` được chọn cho thiết bị thuộc loại khác | T23, T40, T59 (máy tính), T32 (điện) | Dòng "Còn lại" của `routing.dmn` gửi tới Ban CSVC / `facility_officer`. T23, T40, T59 đi **sai đơn vị** (đáng lẽ TT CNTT); T32 đúng đơn vị, sai vai trò |
| `other` đối kháng cho loại `furniture`, `plumbing` | T12, T27, T44, T46, T49, T56 | Form hiện hành không chấp nhận `other`; đây chỉ là kiểm tra dòng dự phòng DMN, không phải các phiếu gửi qua form |

Kết quả nguyên văn của script cho các ca sai:

```text
Ca sai (17 phiếu):

- T03 [lab-a1-305, loại chọn computer]
  ưu tiên: nhãn P1, DMN P3 (DEFAULT)
  → mô tả có nguy cơ an toàn nhưng người báo không đánh dấu safety_hazard
  → urgency=normal, impact=single, safety_hazard=False: «Máy tính giảng viên bốc khói nhẹ ở phần nguồn rồi tắt.»
- T07 [lab-a10-201, loại chọn lab_equipment]
  ưu tiên: nhãn P1, DMN P2 (REPORTER_URGENT)
  → mô tả có nguy cơ an toàn nhưng người báo không đánh dấu safety_hazard
  → urgency=high, impact=single, safety_hazard=False: «Đồng hồ vạn năng vỡ vỏ, lộ dây bên trong, có nguy cơ giật khi đo.»
- T09 [lab-a1-305, loại chọn projector]
  ưu tiên: nhãn P2, DMN P1 (ROOM_BLOCKED)
  → người báo chọn ảnh hưởng cả phòng, người gán nhãn đánh giá chỉ ảnh hưởng một phần
  → urgency=normal, impact=whole_room, safety_hazard=False: «Máy chiếu hỏng, cả lớp ngồi chờ, giảng viên dùng bảng thay thế được.»
- T10 [lab-a1-601, loại chọn network]
  ưu tiên: nhãn P1, DMN P3 (DEFAULT)
  → mô tả có nguy cơ an toàn nhưng người báo không đánh dấu safety_hazard
  → urgency=normal, impact=single, safety_hazard=False: «Bộ đổi nguồn của AP WiFi nóng chảy nhựa, có khói, đã ngắt điện.»
- T12 [lab-a1-306, loại chọn other]
  định tuyến: nhãn /haui/ban-csvc / facility_technician, DMN /haui/ban-csvc / facility_officer
  → người báo chọn loại other (loại thật plumbing)
- T23 [lab-a1-306, loại chọn other]
  định tuyến: nhãn /haui/tt-cntt / it_technician, DMN /haui/ban-csvc / facility_officer
  → người báo chọn loại other (loại thật computer)
- T27 [lab-a1-306, loại chọn other]
  định tuyến: nhãn /haui/ban-csvc / facility_technician, DMN /haui/ban-csvc / facility_officer
  → người báo chọn loại other (loại thật furniture)
- T30 [lab-a1-305, loại chọn air_conditioner]
  ưu tiên: nhãn P2, DMN P3 (DEFAULT)
  → giá trị urgency/impact người báo chọn dẫn tới mức khác nhãn
  → urgency=normal, impact=single, safety_hazard=False: «Điều hòa kêu to bất thường suốt buổi, ảnh hưởng nghe giảng.»
- T32 [lab-a10-201, loại chọn other]
  định tuyến: nhãn /haui/ban-csvc / facility_technician, DMN /haui/ban-csvc / facility_officer
  → người báo chọn loại other (loại thật electrical)
- T40 [lab-a1-306, loại chọn other]
  định tuyến: nhãn /haui/tt-cntt / it_technician, DMN /haui/ban-csvc / facility_officer
  → người báo chọn loại other (loại thật computer)
- T44 [lab-a10-201, loại chọn other]
  định tuyến: nhãn /haui/ban-csvc / facility_technician, DMN /haui/ban-csvc / facility_officer
  → người báo chọn loại other (loại thật furniture)
- T46 [lab-a1-601, loại chọn other]
  định tuyến: nhãn /haui/ban-csvc / facility_technician, DMN /haui/ban-csvc / facility_officer
  → người báo chọn loại other (loại thật plumbing)
- T49 [lab-a1-306, loại chọn other]
  định tuyến: nhãn /haui/ban-csvc / facility_technician, DMN /haui/ban-csvc / facility_officer
  → người báo chọn loại other (loại thật furniture)
- T53 [lab-a1-306, loại chọn computer]
  ưu tiên: nhãn P3, DMN P2 (REPORTER_URGENT)
  → giá trị urgency/impact người báo chọn dẫn tới mức khác nhãn
  → urgency=high, impact=single, safety_hazard=False: «Máy số 4 khởi động chậm, em báo gấp vì sắp thi giữa kỳ.»
- T54 [lab-a1-601, loại chọn computer]
  ưu tiên: nhãn P3, DMN P2 (REPORTER_URGENT)
  → giá trị urgency/impact người báo chọn dẫn tới mức khác nhãn
  → urgency=high, impact=single, safety_hazard=False: «Máy in hết mực đen, em cần in báo cáo ngay chiều nay.»
- T56 [lab-a10-201, loại chọn other]
  định tuyến: nhãn /haui/ban-csvc / facility_technician, DMN /haui/ban-csvc / facility_officer
  → người báo chọn loại other (loại thật furniture)
- T59 [lab-a1-306, loại chọn other]
  định tuyến: nhãn /haui/tt-cntt / it_technician, DMN /haui/ban-csvc / facility_officer
  → người báo chọn loại other (loại thật computer)
```

Gợi ý chỉ để mentor cân nhắc, chưa áp dụng:

- Form hiện hành dùng danh mục AUTHZ và không chấp nhận `other`; các ca `other` chỉ đánh giá nhánh dự phòng của DMN.
- Cân nhắc dòng `REPORTER_URGENT`.

## Bộ 20 câu hỏi tìm kiếm

`apps/lab-repair/eval/queries.json`: 20 câu, 18 câu có đúng một hướng dẫn trong `data/sop/` (APP-03) và 2 câu không có hướng
dẫn tương ứng (`ghế gãy chân`, `vòi nước bị rò`; kết quả đúng là không trả tài liệu hoặc điểm rất thấp). Câu hỏi gồm
tiếng Việt có dấu, không dấu, từ đồng nghĩa (`máy lạnh` cho điều hòa), cách diễn đạt gián tiếp (`phòng lab không vào được internet`).

Chỉ số đề xuất cho CORE-08 và A/B mô hình embedding (Q-16): **top-1 và top-3 trên 18 câu có đáp án**; trên 2 câu không có đáp án đo
tỷ lệ trả rỗng hoặc điểm dưới ngưỡng.

Đường cơ sở từ khóa (TF-IDF bỏ dấu, chỉ thư viện chuẩn), để CORE-08 có mốc:

```bash
python3 apps/lab-repair/eval/measure_search_baseline.py --sop-dir data/sop
```

8 tài liệu, 20 câu hỏi

| # | Câu hỏi | Mong đợi | Top-1 (điểm) | Hạng đúng |
|---|---|---|---|---|
| Q01 | máy chiếu không lên hình | sop-may-chieu-mat-tin-hieu | sop-may-chieu-mat-tin-hieu (13.12) | 1 |
| Q02 | máy chiếu báo đèn đỏ nhấp nháy | sop-may-chieu-mat-tin-hieu | sop-may-chieu-mat-tin-hieu (15.12) | 1 |
| Q03 | may chieu khong nhan hdmi | sop-may-chieu-mat-tin-hieu | sop-may-chieu-mat-tin-hieu (16.69) | 1 |
| Q04 | hình chiếu bị mờ nhòe | sop-may-chieu-mat-tin-hieu | sop-may-chieu-mat-tin-hieu (10.89) | 1 |
| Q05 | máy tính bật lên không có gì | sop-pc-khong-len-nguon | sop-pc-khong-len-nguon (15.49) | 1 |
| Q06 | may tinh khong len nguon | sop-pc-khong-len-nguon | sop-pc-khong-len-nguon (14.22) | 1 |
| Q07 | PC tự sập nguồn giữa chừng | sop-pc-khong-len-nguon | sop-pc-khong-len-nguon (13.55) | 1 |
| Q08 | phòng lab không vào được internet | sop-mat-ket-noi-mang-lan | sop-mat-ket-noi-mang-lan (14.72) | 1 |
| Q09 | mất mạng lan cả phòng | sop-mat-ket-noi-mang-lan | sop-mat-ket-noi-mang-lan (12.94) | 1 |
| Q10 | wifi chập chờn rớt liên tục | sop-mat-ket-noi-mang-lan | sop-den-chieu-sang-chap-chon (6.62) | 7 |
| Q11 | điều hòa chạy nhưng không mát | sop-dieu-hoa-khong-mat-chay-nuoc | sop-dieu-hoa-khong-mat-chay-nuoc (13.49) | 1 |
| Q12 | máy lạnh nhỏ nước xuống sàn | sop-dieu-hoa-khong-mat-chay-nuoc | sop-dieu-hoa-khong-mat-chay-nuoc (25.02) | 1 |
| Q13 | đèn trong phòng nhấp nháy | sop-den-chieu-sang-chap-chon | sop-den-chieu-sang-chap-chon (9.79) | 1 |
| Q14 | thay bóng đèn máng đôi | sop-den-chieu-sang-chap-chon | sop-den-chieu-sang-chap-chon (13.93) | 1 |
| Q15 | máy in bị kẹt giấy | sop-may-in-ket-giay-mo-muc | sop-may-in-ket-giay-mo-muc (21.75) | 1 |
| Q16 | bản in có vệt đen | sop-may-in-ket-giay-mo-muc | sop-may-in-ket-giay-mo-muc (20.12) | 1 |
| Q17 | trạm hàn không nóng | sop-tram-han-khong-nong | sop-tram-han-khong-nong (13.13) | 1 |
| Q18 | đồng hồ vạn năng Fluke không lên màn hình | sop-dao-dong-ky-dong-ho-van-nang | sop-dao-dong-ky-dong-ho-van-nang (23.79) | 1 |
| Q19 | ghế gãy chân | (không có) | sop-tram-han-khong-nong (2.70) | — |
| Q20 | vòi nước bị rò | (không có) | sop-dieu-hoa-khong-mat-chay-nuoc (13.16) | — |

Top-1: 17/18 = 94.4%   Top-3: 17/18 = 94.4%

Nhận xét: đường cơ sở từ khóa đúng 17/18; câu sai là Q10 (`wifi chập chờn rớt liên tục`): SOP mạng không chứa từ `wifi chập chờn`
theo cách người dùng viết nên khớp nhầm sang SOP chiếu sáng qua từ `chập chờn`; đây đúng là loại câu cần khớp nghĩa. Với 2 câu không có
đáp án, đường cơ sở vẫn trả tài liệu đứng đầu (điểm 2,70 và 13,16): **cần ngưỡng điểm hoặc dùng độ tương đồng vector** để trả rỗng. Câu
hỏi do người viết khi đã biết nội dung 8 SOP nên đường cơ sở có thể lạc quan; nên bổ sung câu do người ngoài dự án viết.

Các câu tìm kiếm **chưa được chạy với `/api/search`** vì CORE-08 chưa có; khi có, chạy cùng bộ câu hỏi và dán kết quả vào mục này.

## Tái lập

| Việc | Lệnh |
|---|---|
| Sinh lại bảng số liệu DMN | `uv run --with "spiffworkflow>=3.2" python apps/lab-repair/eval/measure_dmn.py` |
| Mốc tìm kiếm từ khóa | `python3 apps/lab-repair/eval/measure_search_baseline.py --sop-dir data/sop` |
| Đổi bộ phiếu | Sửa `apps/lab-repair/eval/tickets.json`, chạy lại lệnh đầu |

Thư mục `eval/` được bỏ qua khi `dxlab validate` và `dxlab publish`.
