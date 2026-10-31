<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Kịch bản demo 10 phút và câu trả lời chất vấn

Tài liệu cho vòng HaUI: **10 phút demo + tối đa 5 phút trả lời Hội đồng** (đề mục 9). Chuỗi demo theo đề: người dùng →
Open-Core → quy trình → dữ liệu → Intelligence → kết quả. Mỗi đoạn nói rõ đang chỉ thành phần nào thuộc **Tầng 1**,
**H-P-D-I (Tầng 2)** hay **ứng dụng Tầng 3**.

Kịch bản dùng đúng các tình huống 1, 2, 7, 10 và 11 ở [`docs/AUTHZ.md`](../AUTHZ.md) mục 12 trên dữ liệu mẫu do
`scripts/seed.sh` nạp. Phiếu và tên người trong demo đều là **giả định**, không phải người thật.

> **Trạng thái:** kịch bản này mới được soạn từ repo và chưa được tổng duyệt cả đội trên máy demo. Thời lượng từng đoạn
> là ước tính theo số thao tác; cần chạy thử bằng người thật và chỉnh lại. Những gì chưa có (MCP host kèm LLM, che dữ liệu
> cá nhân bằng OpenMed) **không** nằm trong demo, chỉ được nêu là lộ trình.

## 1. Chuẩn bị trước demo

Làm xong **trước giờ demo ít nhất 15 phút**. Mật khẩu chung của mọi tài khoản demo là giá trị `DXLAB_DEMO_PASSWORD` trong
tệp `.env` (không ghi vào tài liệu này).

| Việc | Lệnh | Kiểm tra |
|---|---|---|
| Đưa về dữ liệu sạch (xóa mọi dữ liệu, dựng lại, nạp lại) | `scripts/reset.sh --yes` | Có dòng báo nạp xong; xóa cả cache mô hình |
| Hoặc chỉ dựng và nạp (máy mới) | `scripts/up.sh` rồi `scripts/seed.sh` | Mọi dịch vụ `healthy`; `seed.sh` chạy lại không nhân đôi dữ liệu |
| Tải mô hình embedding (bắt buộc nếu muốn tìm kiếm hybrid theo ngữ nghĩa) | `scripts/download-models.sh` | Chạy **sau** `reset.sh`. Thiếu mô hình thì `/api/search` chỉ dùng toàn văn |
| Kiểm tra sức khỏe | `curl -s http://localhost:9080/api/health` | `status` là `ok` (hoặc tương đương), có trạng thái cơ sở dữ liệu |
| Chạy thử đầu-cuối tự động (tùy chọn, **tạo thêm một phiếu `[E2E]`**) | `scripts/demo-e2e.sh` | Cuối cùng in "KỊCH BẢN E2E THÀNH CÔNG" |

`scripts/demo-e2e.sh` làm gì: đăng nhập tuần tự `sv.an` → `ktv.dung` → `tl.giang` → `tk.hai` bằng Direct Grant qua Keycloak
(có sinh OTP cho `tk.hai`), tạo phiếu điều hòa 3.500.000 đ, đi hết sáu bước báo hỏng → khảo sát → xác nhận → duyệt → sửa →
nghiệm thu, kiểm trạng thái sau mỗi bước, rồi gọi `/api/search`. Dùng để chắc chắn stack chạy trước demo, không dùng làm
nội dung demo chính.

**Phiên trình duyệt.** Mở sẵn cửa sổ ẩn danh riêng cho từng tài khoản ở `http://localhost:8000` và đăng nhập trước:

| Cửa sổ | Tài khoản | Cần OTP |
|---|---|---|
| 1 | `sv.an` | Không |
| 2 | `tl.giang` | Không |
| 3 | `ptk.hoa` (có `repair.approve` qua ủy quyền) | Có |
| 4 | `tk.hai` | Có |
| 5 | `ktv.cuong` | Không |
| 6 | `ht.khanh` | Có |

Phiên hết hạn sau **30 phút không thao tác** (`docs/AUTHZ.md` mục 10): đăng nhập lại cửa sổ nào đã bỏ quá lâu.

**Sinh mã OTP** (theo `README.md`, mỗi mã dùng một lần trong 30 giây; hai lần đăng nhập OTP liên tiếp của cùng một tài
khoản phải cách nhau sang chu kỳ mới):

```bash
python3 -c 'import hmac,hashlib,struct,time,sys;h=hmac.new(sys.argv[1].encode(),struct.pack(">Q",int(time.time())//30),hashlib.sha1).digest();o=h[-1]&15;print("%06d"%((struct.unpack(">I",h[o:o+4])[0]&0x7fffffff)%1000000))' "$(grep '^DXLAB_DEMO_OTP_SECRET=' .env | cut -d= -f2-)"
```

**Hàm lấy token cho các lệnh `curl`** (cùng cách `scripts/demo-e2e.sh` dùng; chạy trong thư mục gốc repo, cần `jq`):

```bash
set -a; source .env; set +a
otp() { python3 -c 'import hmac,hashlib,struct,time,sys;h=hmac.new(sys.argv[1].encode(),struct.pack(">Q",int(time.time())//30),hashlib.sha1).digest();o=h[-1]&15;print("%06d"%((struct.unpack(">I",h[o:o+4])[0]&0x7fffffff)%1000000))' "$DXLAB_DEMO_OTP_SECRET"; }
tok() { curl -s -X POST "http://localhost:8180/realms/dxlab/protocol/openid-connect/token" \
  --data-urlencode client_id=dxlab-cli --data-urlencode grant_type=password \
  --data-urlencode "username=$1" --data-urlencode "password=$DXLAB_DEMO_PASSWORD" \
  --data-urlencode "totp=$(otp)" | jq -r .access_token; }
API=http://localhost:9080/api
```

## 2. Tài khoản dùng trong demo

Danh sách đầy đủ ở [`docs/AUTHZ.md`](../AUTHZ.md) mục 11.

| Tài khoản | Vai trò | Dùng ở đoạn |
|---|---|---|
| `sv.an` | `reporter` (sinh viên) | A, B, C |
| `ktv.cuong` | `it_technician` (TT CNTT) | C, G |
| `tl.giang` | `lab_manager` (phòng lab A1-305) | C, G |
| `tk.hai` | `faculty_head` (khoa KHMT) | D, G |
| `ptk.hoa` | `faculty_deputy`, chỉ duyệt khi có ủy quyền TUQ. | D |
| `ht.khanh` | `school_head` | E |

## 3. Kịch bản từng đoạn

Tổng: **9 phút 30 giây**, dự phòng 30 giây. Ai thao tác: *người trình bày* nói và chỉ màn hình; *người thao tác* gõ.
Phân vai cụ thể (ai nói, ai gõ) quyết định khi tổng duyệt.

| Đoạn | Thời lượng | Mốc |
|---|---|---|
| A. Người dùng và bài toán | 0:30 | 0:00–0:30 |
| B. Open-Core (Tầng 1) | 1:30 | 0:30–2:00 |
| C. Quy trình: báo hỏng, định tuyến, xác nhận | 1:45 | 2:00–3:45 |
| D. Ủy quyền TUQ. | 1:45 | 3:45–5:30 |
| E. Dữ liệu | 1:00 | 5:30–6:30 |
| F. Intelligence | 1:00 | 6:30–7:30 |
| G. Chi phí vượt và nghiệm thu: kết quả | 1:30 | 7:30–9:00 |
| H. Tổng kết ba tầng | 0:30 | 9:00–9:30 |

### A. Người dùng và bài toán (0:30)

- **Người thao tác:** cửa sổ 1, `sv.an`, mở `http://localhost:8000`.
- **Nói:** sinh viên báo hỏng thiết bị qua tin nhắn nên mất dấu; DX-Lab số hóa thành quy trình có lịch sử.
- **Chỉ ra:** màn hình chính của portal (tab *Việc của tôi, Báo hỏng, Tra cứu, Dashboard, Trạng thái hệ thống*) là
  **H – Human** (Tầng 2). Đăng nhập đã đi qua Keycloak (**Tầng 1**).

### B. Open-Core (1:30)

- **Người thao tác:** terminal và trình duyệt.
- **Lệnh/URL:**
  1. `curl -i http://localhost:9080/api/workflows` (không token) → `401`: APISIX chặn ở cổng (**Tầng 1 – API Gateway**).
  2. Mở `http://localhost:9080/api/docs` (Swagger/OpenAPI của Core, **Tầng 1**), chỉ nhóm `/api/workflows`, `/api/tasks`,
     `/api/definitions`, `/api/search`, `/api/delegations`.
  3. Portal, tab *Trạng thái hệ thống* (cửa sổ 1): các dịch vụ Keycloak, APISIX, Core, PostgreSQL ở trạng thái chạy.
  4. `docker compose -p dxlab ps` để chỉ thấy 5 dịch vụ: `postgres`, `keycloak`, `apisix`, `core`, `portal`.
- **Nói:** Core không trả HTML và không biết ứng dụng nào đang gọi; portal chỉ là một client, CLI và MCP cũng thế
  (`docs/ARCHITECTURE.md` mục 1, 3.6).
- **Thuộc:** Keycloak, APISIX, Core (FastAPI + SpiffWorkflow), PostgreSQL = **Tầng 1**.

### C. Quy trình: báo hỏng, định tuyến, xác nhận (1:45)

*Tình huống 1 và 2 của AUTHZ mục 12.*

1. **(0:45)** Cửa sổ 1, `sv.an`, tab *Báo hỏng*: báo máy chiếu phòng A1-305 không lên hình (nhập đủ trường bắt buộc,
   đồng ý xử lý dữ liệu cá nhân). Chỉ kết quả: phiếu ở trạng thái *Chờ kiểm tra*, được định tuyến về **Trung tâm CNTT**,
   vai trò `it_technician`, kèm mức ưu tiên và mã lý do từ `triage.dmn`/`routing.dmn`. Có thể dùng sẵn phiếu mẫu
   "[Mẫu] Máy chiếu A1-305 không lên hình" do seed tạo nếu nhập form chậm.
   - **P – Process** (H-P-D-I) chạy trên bộ máy BPMN/DMN của **Tầng 1**; **ứng dụng `lab-repair` là Tầng 3**
     (`apps/lab-repair/lab-repair.bpmn`).
2. **(0:30)** Cửa sổ 5, `ktv.cuong`, tab *Việc của tôi*: thấy việc vừa vào hàng đợi. Chỉ rằng `ktv.dung` (Ban CSVC)
   không thấy việc này vì khác đơn vị (lớp 2, phạm vi).
3. **(0:30)** Cửa sổ 2, `tl.giang`, tab *Việc của tôi*: phiếu mẫu "[Mẫu] Máy chiếu A1-305 mờ hình, nghi hỏng bóng" (biên bản
   thay bóng 3.500.000 đ do seed lập) đang *Chờ xác nhận nhu cầu*; bấm hoàn thành bước xác nhận. Phiếu chuyển sang
   *Chờ duyệt*, thẩm quyền theo `authority.dmn` là trưởng khoa `tk.hai` (tình huống 2).
- **Kiểm chứng ở đoạn D:** phiếu "[Mẫu] Máy chiếu A1-305 mờ hình, nghi hỏng bóng" được dùng tiếp ở D và G.

### D. Ủy quyền TUQ. (1:45)

*Tình huống 7 của AUTHZ mục 12. Tính năng `/api/delegations` đã có trên `main` (#18).* Portal hiện **chưa có màn hình
ủy quyền**, nên bước tạo ủy quyền làm qua API.

1. **(0:30)** Terminal, `tk.hai` ủy quyền TUQ. cho `ptk.hoa` 7 ngày (số giấy là giả định cho demo):

   ```bash
   T=$(tok tk.hai)
   curl -s -X POST "$API/delegations" -H "Authorization: Bearer $T" -H 'Content-Type: application/json' \
     -d "{\"delegate\":\"ptk.hoa\",\"role\":\"faculty_head\",\"number\":\"GĐ-UQ-DEMO/2026\",
          \"starts_at\":\"$(date -u -v-1M +%Y-%m-%dT%H:%M:%SZ)\",\"ends_at\":\"$(date -u -v+7d +%Y-%m-%dT%H:%M:%SZ)\"}" | jq
   ```

   (Trên Linux thay `date -u -v-1M` bằng `date -u -d '-1 min'` và `-v+7d` bằng `-d '+7 days'`.) Kết quả `status: active`.
2. **(0:45)** Cửa sổ 3, `ptk.hoa`, tab *Việc của tôi*: có việc duyệt phiếu 3.500.000 đ vừa xác nhận ở đoạn C; duyệt với
   số tiền 3.500.000 (hình thức ký là TUQ. và số giấy do Core điền theo giấy đang dùng). Phiếu chuyển *Đang sửa*.
3. **(0:30)** Lớp 3 của phân quyền: phiếu mẫu 12.000.000 đ "[Mẫu] Máy tính trạm A1-305 không lên nguồn" thuộc thẩm quyền
   `ht.khanh`; `ptk.hoa` duyệt phiếu này bị từ chối `FORBIDDEN_AUTHORITY` vì vượt hạn mức của người ủy quyền (đã có
   test ở `core/tests/test_delegations.py`; nếu portal không cho bấm, minh họa bằng
   `curl -X POST $API/tasks/<task_id>/complete` với token `ptk.hoa`, lấy `task_id` từ `GET $API/tasks`). Quay lại phiếu 3.500.000 đ
   ở *Việc của tôi* (cửa sổ 3) để chỉ lịch sử: hình thức ký TUQ., số giấy, người làm thật `ptk.hoa`.
- **Nói:** ủy quyền có thời hạn tối đa 30 ngày, không vượt hạn mức, không ủy quyền lại (`docs/AUTHZ.md` mục 9).
- **Thuộc:** ủy quyền, phân quyền 5 lớp, SoD là mã **Tầng 1** (Core) dùng chung mọi ứng dụng; **H – Human** là người ủy
  quyền và người nhận; ứng dụng `lab-repair` là **Tầng 3**.

### E. Dữ liệu (1:00)

*Tình huống 11 của AUTHZ mục 12.*

1. **(0:30)** Cửa sổ 6, `ht.khanh`, mở một phiếu mẫu (qua *Việc của tôi*, hoặc `GET $API/workflows/<id>` bằng token
   `ht.khanh`): **không thấy số điện thoại và email** người báo (che theo `x-personal-data`). Cửa sổ 5, `ktv.cuong` (đang được
   giao phiếu) thấy đủ.
2. **(0:30)** Tab *Dashboard*: thống kê theo trạng thái và đơn vị (`GET /api/stats`, không có tên người). Chỉ thêm
   Swagger `/api/docs` rằng cùng dữ liệu có REST API cho mọi client.
- **Thuộc:** **D – Data** (Tầng 2); PostgreSQL, che dữ liệu cá nhân, audit là **Tầng 1**. Nguồn dữ liệu mẫu và quyền sử
  dụng khai ở `DATA_SOURCES.yml`; dữ liệu do đội biên soạn, không có dữ liệu cá nhân thật.

### F. Intelligence (1:00)

- **Điều kiện:** đã chạy `scripts/download-models.sh` (xem mục 1). Không có mô hình thì chỉ có tìm toàn văn.
- **Người thao tác:** cửa sổ 5, `ktv.cuong`, tab *Tra cứu*.
  1. **(0:30)** Nhập "máy lạnh nhỏ nước xuống sàn" (không dấu cũng được: "may lanh nho nuoc"): kết quả là hướng dẫn về điều
     hòa dù câu hỏi dùng chữ "máy lạnh", có đoạn trích và nguồn; chỉ ra chế độ hiển thị là `hybrid` (không phải `fts`). Đây là tìm kiếm
     **hybrid**: toàn văn PostgreSQL + vector (`fastembed` + `zvec`).
  2. **(0:30)** Không demo câu ngoài phạm vi: "ghế gãy chân" hiện vẫn trả kết quả không liên quan (`docs/AI.md`, Q19).
     Mức ưu tiên và **mã lý do** của `triage.dmn` không hiện trên portal; nếu cần, nói và chỉ bảng luật trong
     `apps/lab-repair/triage.dmn`.
- **Nói:** Intelligence ở đây gồm luật DMN giải thích được và tìm kiếm ngữ nghĩa cục bộ, không gọi dịch vụ ngoài. Con
  người vẫn là người quyết định cuối (`docs/AI.md`, báo cáo `docs/report/DX-Lab-v0.2.1-bao-cao-ky-thuat.pdf`).
- **Thuộc:** **I – Intelligence** (Tầng 2) chạy bằng bộ máy DMN và `/api/search` của **Tầng 1**.

### G. Chi phí vượt và nghiệm thu: kết quả (1:30)

*Tình huống 10 của AUTHZ mục 12 (luật E2), tiếp từ phiếu 3.500.000 đ ở đoạn D.*

1. **(0:30)** Cửa sổ 5, `ktv.cuong`, hoàn thành bước *Đang sửa* với **chi phí thực tế 4.000.000 đ** (vượt 14% so với
   3.500.000 đã duyệt, quá ngưỡng 10% của `apps/lab-repair/overrun.dmn`). Phiếu **quay lại *Chờ duyệt*** (duyệt lại
   theo chi phí thực tế), vẫn dòng 2 của bảng thẩm quyền.
2. **(0:30)** Cửa sổ 4, `tk.hai`, tab *Việc của tôi*: duyệt lại 4.000.000 đ. Phiếu chuyển *Chờ nghiệm thu*.
3. **(0:30)** Cửa sổ 2, `tl.giang` nghiệm thu: phiếu **hoàn tất**; mở chi tiết phiếu để chỉ lịch sử từng bước. Nếu còn
   thời gian, nhắc tình huống 9: người đã sửa (`ktv.cuong`) nghiệm thu sẽ bị `FORBIDDEN_SOD` (SoD-2), có test ở core.
- **Thuộc:** E2 và SoD là mã **Tầng 1** dùng chung; bảng luật `overrun.dmn`, `authority.dmn` và biểu mẫu là gói **Tầng 3**.

### H. Tổng kết ba tầng (0:30)

Nói và chỉ lại sơ đồ ở `README.md` hoặc `docs/ARCHITECTURE.md` mục 1:

- **Tầng 1** (headless): Keycloak, APISIX, Core + SpiffWorkflow, PostgreSQL.
- **Tầng 2** (H-P-D-I): portal (Human), BPMN/DMN chạy qua Core (Process), thống kê, tra cứu, che dữ liệu (Data),
  DMN và tìm kiếm hybrid (Intelligence); cùng MCP server và CLI `dxlab`.
- **Tầng 3**: `apps/lab-repair`, `apps/room-booking`, chỉ là gói tệp nạp qua `/api/definitions`, không sửa `core/`.

## 4. Phương án dự phòng

| Sự cố | Cách xử lý ngay trong demo |
|---|---|
| Một dịch vụ không lên (`docker compose -p dxlab ps` có dịch vụ lỗi) | Chạy `scripts/up.sh` (không xóa dữ liệu); nếu vẫn lỗi, nói rõ nguyên nhân và chuyển sang phương án ghi hình/ảnh chụp |
| Dữ liệu hỏng hoặc phiếu mẫu đã bị dùng ở lần chạy thử | `scripts/reset.sh --yes` (mất vài phút), rồi `scripts/download-models.sh` |
| Cổng 8000, 8180 hoặc 9080 bị chiếm | Dừng tiến trình đang chiếm cổng; không đổi cổng giữa chừng (cổng là hợp đồng ở `docs/ARCHITECTURE.md` mục 4) |
| Portal lỗi giao diện hoặc đăng nhập nghẽn | Làm cùng thao tác bằng API/Swagger tại `http://localhost:9080/api/docs`, hoặc chạy `scripts/demo-e2e.sh` để Hội đồng thấy chuỗi báo hỏng → nghiệm thu bằng lệnh |
| OTP bị từ chối do trùng trong cửa sổ 30 giây | Đợi sang chu kỳ mới rồi sinh mã mới (`demo-e2e.sh` cũng tự đợi như vậy) |
| Phiên hết hạn do quá 30 phút không thao tác | Đăng nhập lại cửa sổ đó trước khi vào đoạn cần dùng |
| Tìm kiếm ngữ nghĩa không ra (chưa tải mô hình) | Nói rõ hệ thống tự lùi về tìm toàn văn (`CHANGELOG.md` mục 0.2.0); chạy `scripts/download-models.sh` cho lần sau |
| Bước tạo ủy quyền báo lỗi | Kiểm số giấy, thời hạn (tối đa 30 ngày) và token đúng `tk.hai`; xem `GET $API/delegations` |
| Mạng ngoài mất | Demo chạy hoàn toàn cục bộ, không cần Internet sau khi đã dựng xong và tải mô hình |
| Mọi cách trên đều không chạy | Dùng video demo 3–5 phút (khuyến nghị ở đề mục 10; **chưa có trong repo tại thời điểm viết**) và mở repo/release để chứng minh tái lập |

## 5. Câu trả lời chất vấn (đề mục 13)

Mỗi câu trả lời ngắn, có dẫn tệp để Hội đồng kiểm.

1. **Open-Core nằm ở đâu? Thành phần nào headless, ứng dụng nào dùng?** Ở `deploy/` và `core/`: Keycloak, APISIX, Core API
   (FastAPI + SpiffWorkflow), PostgreSQL. Core không trả HTML. Portal, MCP server, CLI `dxlab` (Tầng 2) và ứng dụng
   `lab-repair`, `room-booking` (Tầng 3) đều gọi qua APISIX bằng token người dùng. `docs/ARCHITECTURE.md` mục 1, 3.
2. **Vì sao chọn stack này? Nguồn mở nào, giấy phép gì?** Chọn thành phần nguồn mở chuẩn, tích hợp thay vì tự viết lại:
   Keycloak (Apache-2.0), APISIX (Apache-2.0), PostgreSQL (PostgreSQL License), SpiffWorkflow (LGPL-3.0, BPMN/DMN chuẩn
   mở và nhúng được vào Core), mô hình MiniLM (Apache-2.0). Mã của dự án Apache-2.0, tài liệu CC BY 4.0, đủ REUSE 3.3.
   Bảng đầy đủ có phiên bản, digest, vai trò: `docs/DEPENDENCIES.md`.
3. **Đổi ứng dụng nghiệp vụ thì Open-Core có phải đổi không?** Không. Ứng dụng là gói `.bpmn`, `.dmn`, `*-schema.json` nạp
   qua `/api/definitions`; validator từ chối gói có mã. `room-booking` được nạp theo cách này mà không sửa `core/` hay
   `portal/` (`docs/ARCHITECTURE.md` mục 1; `apps/room-booking/README.md`). Chỉ sửa Core khi cần một năng lực nền tảng mới dùng
   chung (quy tắc ở `CONTRIBUTING.md`).
4. **Identity/SSO, Gateway, Data, Workflow là dịch vụ dùng chung thế nào?** Keycloak cấp JWT cho mọi client
   (`deploy/keycloak/realm.json`); APISIX là điểm vào duy nhất, kiểm JWT, giới hạn tốc độ (`deploy/apisix/apisix.yaml`);
   chỉ Core đọc/ghi PostgreSQL; SpiffWorkflow trong Core chạy mọi quy trình nạp vào, không riêng ứng dụng nào
   (`docs/ARCHITECTURE.md` mục 3.6).
5. **Điểm nào là H-P-D-I chứ không chỉ dashboard CRUD?** Quy trình có trạng thái, người xử lý, thời gian, lịch sử
   (P); tài khoản, nhóm, vai trò, ủy quyền, hộp việc theo vai trò (H); schema, che dữ liệu cá nhân, audit, thống kê qua REST (D);
   luật DMN có mã lý do và tìm kiếm hybrid (I). Dashboard chỉ là một tab. Xem báo cáo `docs/report/DX-Lab-v0.2.1-bao-cao-ky-thuat.pdf`.
6. **AI/ML dùng ở đâu? Đầu vào, mô hình, đánh giá, giới hạn?** (a) DMN `triage`, `routing`, `authority`: luật có mã lý do, không học máy; (b)
   tìm kiếm hybrid dùng `paraphrase-multilingual-MiniLM-L12-v2` (Apache-2.0) cùng toàn văn PostgreSQL, trên hướng dẫn sửa chữa do
   đội soạn. Đánh giá bằng 60 phiếu tổng hợp và 20 câu hỏi ở `apps/lab-repair/eval/`; **nhãn do agent soạn, chưa có người
   rà, nên số liệu chỉ mang tính tham khảo** và DMN không đọc được mô tả tự do. Quyết định cuối luôn thuộc con người. `docs/AI.md`.
   LLM và che dữ liệu cá nhân bằng OpenMed (#36, #97) **chưa có**, là lộ trình.
7. **Nguồn dữ liệu/API ngừng hoạt động thì sao?** Hệ thống không phụ thuộc API bên ngoài khi chạy: dữ liệu mẫu và
   hướng dẫn sửa chữa nằm trong repo (`data/`, `DATA_SOURCES.yml`), mô hình embedding tải một lần vào volume rồi chạy
   offline. Thiếu mô hình thì `/api/search` tự lùi về toàn văn (`docs/ARCHITECTURE.md` mục 5; `CHANGELOG.md`).
8. **Build toàn bộ hệ thống từ source trên máy mới được không?** Được: `uv sync --all-packages`, `uv build --all-packages`,
   rồi `scripts/up.sh`, `scripts/seed.sh` (`README.md`). CI cài sạch từng gói và import từ ngoài cây mã
   (`.github/workflows/ci.yml`); bản `v0.2.0` kèm `tar.gz`, `SHA256SUMS`, SBOM. Chưa tổng duyệt cả đội trên một máy hoàn toàn mới
   ngoài môi trường phát triển.
9. **Tăng từ 100 lên 100.000 người dùng thì kiến trúc đổi thế nào?** **Chưa đo tải**; cấu hình hiện tại là một máy
   (Keycloak `start-dev`, `docs/ARCHITECTURE.md` mục 4). Hướng đi, chưa kiểm chứng: Keycloak chạy chế độ `start` với TLS và
   cơ sở dữ liệu riêng; nhiều bản sao Core sau APISIX vì trạng thái quy trình nằm trong PostgreSQL; PostgreSQL tách máy,
   có sao lưu; xem lại chỉ mục `zvec` đang ở volume cục bộ. Issue #96 theo dõi hiệu năng chỉ mục văn bản lớn.
10. **Cộng đồng muốn đóng góp module mới thì quy trình là gì?** Mở issue mô tả trước, tạo nhánh `<type>/<MÃ-VIỆC>-<mô-tả>`,
    commit có `Signed-off-by` (DCO), header SPDX cho tệp mới, mở PR draft theo mẫu, CI xanh (REUSE, build, DCO, gitleaks, pytest),
    cần review người khác, maintainer gộp bằng rebase (`CONTRIBUTING.md`, `MAINTAINERS.md`). Module nghiệp vụ mới là
    một gói trong `apps/<tên>/`, kiểm bằng `dxlab validate`.
