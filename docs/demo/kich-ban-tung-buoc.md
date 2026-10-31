<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Kịch bản demo từng bước (cho người trình bày)

Bản này dành cho người **chỉ cần nhìn và làm theo**: bấm gì, gõ gì, sẽ thấy gì, nói gì. Phần giải thích kỹ thuật và
câu trả lời chất vấn Hội đồng nằm ở [`kich-ban.md`](kich-ban.md); thứ tự các đoạn A–H giống hệt bản đó.

- **Tổng thời gian: 9 phút 30 giây** (dự phòng 30 giây). Thời lượng từng đoạn ghi ngay đầu đoạn.
- Phiếu, tên người, số tiền, hạn mức, số giấy ủy quyền, tài khoản đều là **giả định**, không phải người thật.
- Mọi nhãn nút, tab, ô nhập dưới đây đã được chạy thử thật trên bản 0.2.1 (xem mục "Đã chạy thử đến đâu" cuối tài liệu).
- Chữ **in đậm** là chữ có trên màn hình. Chữ `trong dấu huyền` là thứ bạn gõ.
- **Làm** = việc bạn thao tác. **Thấy** = điều sẽ hiện ra (nếu khác, xem "Nếu có sự cố"). **Nói** = câu nên nói.

Mật khẩu chung của mọi tài khoản là giá trị `DXLAB_DEMO_PASSWORD` trong tệp `.env` (người trình bày đã biết, không ghi ở
đây). Mã xác thực hai bước (OTP) lấy ở cửa sổ terminal đã chuẩn bị (xem mục 1).

## 1. Chuẩn bị trước khi demo (làm xong trước giờ demo 15 phút)

### 1.1. Dữ liệu và máy

- [ ] Mở terminal, vào thư mục gốc của DX-Lab (thư mục có tệp `.env`).
- [ ] Đưa dữ liệu về sạch: `bash scripts/reset.sh --yes` (mất vài phút, xóa mọi phiếu cũ).
- [ ] Tải mô hình tìm kiếm: `bash scripts/download-models.sh` (chạy **sau** lệnh trên).
- [ ] Đợi khoảng 30 giây, rồi gõ `curl -s localhost:9080/api/health`. Phải thấy `"embedding_model":"ok"`. Nếu thấy
  `missing`, đợi thêm rồi gõ lại.
- [ ] **Có Internet** cho riêng trang Swagger ở đoạn B: trang này tải giao diện từ `cdn.jsdelivr.net`. Mất mạng thì trang
  trắng (xem mục 5). Các phần còn lại chạy hoàn toàn trong máy.

### 1.2. Terminal OTP và lệnh ủy quyền (dán sẵn một lần)

Giữ **một cửa sổ terminal riêng**, để cạnh trình duyệt. Trong thư mục gốc DX-Lab, dán **cả khối** dưới đây một lần (không in
mật khẩu hay khóa ra màn hình). Cần `curl`, `jq`, `python3` (máy macOS đã có `python3`; `jq` cài bằng `brew install jq`).

```bash
set -a; source .env; set +a
otp() { python3 -c 'import hmac,hashlib,struct,time,sys;h=hmac.new(sys.argv[1].encode(),struct.pack(">Q",int(time.time())//30),hashlib.sha1).digest();o=h[-1]&15;print("%06d"%((struct.unpack(">I",h[o:o+4])[0]&0x7fffffff)%1000000))' "$DXLAB_DEMO_OTP_SECRET"; }
uyquyen() {
  T=$(curl -s -X POST http://localhost:8180/realms/dxlab/protocol/openid-connect/token -d client_id=dxlab-cli -d grant_type=password -d username=tk.hai --data-urlencode "password=$DXLAB_DEMO_PASSWORD" -d "totp=$(otp)" | jq -r .access_token)
  curl -s -X POST http://localhost:9080/api/delegations -H "Authorization: Bearer $T" -H 'Content-Type: application/json' \
    -d "$(python3 -c 'import json,datetime as d;n=d.datetime.now(d.timezone.utc);f="%Y-%m-%dT%H:%M:%SZ";print(json.dumps({"delegate":"ptk.hoa","role":"faculty_head","number":"GĐ-UQ-DEMO/2026","starts_at":(n-d.timedelta(minutes=1)).strftime(f),"ends_at":(n+d.timedelta(days=7)).strftime(f)}))')" | jq
}
otp
```

Dòng cuối `otp` in thử một mã 6 số: thấy số là terminal đã sẵn sàng. **Cách dùng trong demo:**

- Cần mã OTP: nhấn **mũi tên lên** vài lần cho tới dòng `otp`, nhấn **Enter**, đọc 6 số và gõ vào trình duyệt ngay (mã sống 30 giây).
- Cần tạo ủy quyền (đoạn D): gõ `uyquyen`, nhấn **Enter**.
- Một mã OTP **không dùng lại được** cho cùng một tài khoản trong cùng 30 giây. Bị từ chối thì đợi sang mã mới.

### 1.3. Các cửa sổ trình duyệt (mỗi người một phiên riêng)

Các tài khoản **không dùng chung được một trình duyệt**: đăng nhập tài khoản mới sẽ đè phiên cũ (đã thấy khi chạy thử, vì
cookie của `localhost` dùng chung giữa các cổng). Cách dễ nhất: **mỗi người một "hồ sơ" Chrome** (bấm ảnh đại diện góc phải
trên → **Thêm** → tiếp tục không cần tài khoản Google). Cửa sổ ẩn danh chỉ dùng cho **một** người, vì các cửa sổ ẩn danh
thường dùng chung phiên với nhau (kiến thức chung về trình duyệt, chưa kiểm trên máy này). Có Firefox hoặc Edge thì dùng luôn.

Đăng nhập sẵn như sau (địa chỉ `http://localhost:8000`). Cửa sổ đặt tên bằng tay (ví dụ dán nhãn giấy) cho khỏi nhầm:

| Cửa sổ | Tài khoản | Cần OTP | Dùng ở đoạn |
|---|---|---|---|
| 1 | `sv.an` | Không | A, B, C |
| 2 | `ktv.cuong` | Không | C, F, G |
| 3 | `tl.giang` | Không | C, G |
| 4 | `ptk.hoa` | Có | D |
| 5 | `tk.hai` | Có | G |
| 6 | `ht.khanh` | Có | E |

Cách đăng nhập (trang đăng nhập hiện tiếng Anh):

1. Mở `http://localhost:8000`. Trình duyệt chuyển sang trang **Sign in to your account**.
2. Gõ tài khoản vào ô **Username**, mật khẩu vào ô **Password**, bấm **Sign In**.
3. Tài khoản cần OTP sẽ hiện trang có ô **One-time code**: lấy mã ở terminal (mục 1.2), gõ vào, bấm **Sign In**.
4. Thấy tên người ở góc phải trên cùng và nút **Đăng xuất** là đăng nhập xong.

Mở sẵn trong **cửa sổ 1**, thêm một tab thứ hai: `http://localhost:9080/api/docs` (Swagger, **không** cần đăng nhập).

Một ít lưu ý: phiên tự hết hạn sau **30 phút không thao tác** (`docs/AUTHZ.md` mục 10); cửa sổ nào bỏ lâu thì đăng nhập
lại. Nếu bạn buộc phải dùng một trình duyệt cho nhiều người: bấm **Đăng xuất**, chờ vài giây rồi nhấn **F5**; nếu chưa thấy
trang đăng nhập thì mở lại `http://localhost:8000/auth/logout` (khi chạy thử, bấm **Đăng xuất** đã hủy phiên nhưng trang cũ
vẫn đứng yên cho tới khi tải lại).

### 1.4. Kiểm tra cuối (5 phút)

- [ ] Cửa sổ 1, tab **Trạng thái hệ thống**: tất cả 7 dòng ghi **Hoạt động**.
- [ ] Cửa sổ 3 (`tl.giang`), tab **Việc của tôi**: có đúng 1 việc **Chờ xác nhận nhu cầu**.
- [ ] Cửa sổ 6 (`ht.khanh`), tab **Việc của tôi**: có đúng 1 việc **Chờ duyệt** (phiếu 12.000.000 đ).
- [ ] Cửa sổ 4 (`ptk.hoa`), tab **Việc của tôi**: **chưa có** việc nào (ủy quyền chưa tạo).
- [ ] Terminal: gõ `otp` ra 6 số.

## 2. Ai là ai

| Tài khoản | Tên giả định | Vai trò | Làm gì trong demo |
|---|---|---|---|
| `sv.an` | Nguyễn Văn An | sinh viên | báo hỏng máy chiếu |
| `ktv.cuong` | Lê Văn Cường | kỹ thuật viên Trung tâm CNTT | nhận việc, sửa, báo chi phí |
| `tl.giang` | Hoàng Thu Giang | trưởng phòng lab A1-305 | xác nhận nhu cầu, nghiệm thu |
| `tk.hai` | Vũ Đức Hải | trưởng khoa KHMT | ủy quyền, duyệt lại |
| `ptk.hoa` | Ngô Thị Hoa | phó trưởng khoa | duyệt thay (ủy quyền) |
| `ht.khanh` | Bùi Quốc Khánh | hiệu trưởng trường SICT | xem dữ liệu bị che |

## 3. Từng bước

Phiếu xuyên suốt: **máy chiếu phòng A1-305** hỏng bóng, thay hết **3.500.000 đ**, sau sửa thực tế **4.000.000 đ**.

> **Cách đọc "Việc của tôi".** Mỗi dòng trong hộp việc chỉ ghi tên bước (ví dụ **Chờ duyệt**) và **8 ký tự đầu mã phiếu**
> (ví dụ `39e1cb79`), không ghi tiêu đề. Bấm vào **tên bước** (chữ gạch chân) thì form hiện ra, và phần **Chi tiết phiếu**
> bên dưới form ghi tiêu đề, dòng **Lịch sử**. Mã phiếu đổi sau mỗi lần nạp lại dữ liệu; nhận phiếu bằng **tiêu đề**.

### A. Người dùng và bài toán (0:30)

1. **Làm:** ở cửa sổ 1, tab đầu tiên, nhìn trang `http://localhost:8000` (đã đăng nhập `sv.an`).
   **Thấy:** góc phải trên: **Nguyễn Văn An**, `@sv.an`, `reporter`, nút **Đăng xuất**. Dải tab: **Việc của tôi**, **Báo hỏng**,
   **Tra cứu**, **Dashboard**, **Sơ đồ quy trình**, **Trạng thái hệ thống**. Hộp việc của An ghi
   "Không có việc đang chờ bạn xử lý."
   **Nói:** "Trước đây sinh viên báo máy hỏng qua tin nhắn nên hay mất dấu. DX-Lab biến nó thành một quy trình có người
   nhận, có hạn, có lịch sử. Đây là giao diện người dùng, **thành phần H (Human)** của Tầng 2. Việc đăng nhập do
   Keycloak lo, thuộc **Tầng 1**."

### B. Open-Core (1:30)

2. **(0:45)** **Làm:** ở cửa sổ 1, bấm sang **tab thứ hai** (Swagger, `http://localhost:9080/api/docs`). Cuộn nhẹ cho thấy các nhóm
   **Phiếu công việc**, **Hộp việc**, **Tìm kiếm**, **Ủy quyền**. Bấm dòng **GET /api/workflows** (chữ
   "Danh sách phiếu trong phạm vi được xem") → bấm **Try it out** → bấm **Execute**.
   **Thấy:** cuộn xuống mục **Server response**: **Code 401**, chữ **Error: Unauthorized**.
   **Nói:** "Đây là phần lõi của hệ thống, nó không có giao diện, chỉ có API. Tôi gọi mà chưa đăng nhập: cổng API chặn ngay,
   trả 401, tức 'chưa có thẻ ra vào'. Cổng API (APISIX) và API lõi (Core) là **Tầng 1**."
3. **(0:15)** **Làm:** vẫn trên Swagger, kéo lên đầu, bấm dòng **GET /api/health** → **Try it out** → **Execute**.
   **Thấy:** **Code 200** và `"status": "ok"`, `"database": "ok"`, `"embedding_model": "ok"`.
   **Nói:** "Còn cửa kiểm tra sức khỏe thì không cần thẻ, nên trả lời được."
4. **(0:30)** **Làm:** quay lại tab thứ nhất, bấm tab **Trạng thái hệ thống**.
   **Thấy:** 7 dòng đều **Hoạt động**: **Portal**, **Keycloak (đăng nhập)**, **APISIX (cổng API)**, **Core API** (ghi "Phiên bản
   0.2.1"), **PostgreSQL**, **Chỉ mục tìm kiếm**, **Mô hình embedding**.
   **Nói:** "Lõi gồm bốn món nguồn mở: đăng nhập, cổng API, bộ máy quy trình và cơ sở dữ liệu. Giao diện này chỉ là một trong
   các 'khách hàng' của lõi; dòng lệnh và trợ lý cũng gọi lõi theo đúng cách đó."

### C. Quy trình: báo hỏng, định tuyến, xác nhận (1:45)

5. **(0:45)** **Làm:** cửa sổ 1 (`sv.an`), bấm tab **Báo hỏng**. Điền form **Phiếu báo hỏng thiết bị phòng lab**:
   - **Họ và tên** `Nguyễn Văn An`; **Mã sinh viên / Cán bộ** `SV2026001`.
   - **Số điện thoại liên hệ** `0900000001`; **Email liên hệ** `sv.an@example.test`.
   - **Phòng thực hành**: bấm ô **Chọn…** đầu tiên → chọn `lab-a1-305`.
   - **Phân loại thiết bị**: bấm ô **Chọn…** bên cạnh → chọn `projector`.
   - **Mã tài sản / thiết bị** `AST-PROJ-305-01`.
   - **Mức ảnh hưởng** để nguyên `single`; **Mức độ khẩn cấp** để nguyên `normal`; **Có nguy cơ mất an toàn** để trống.
   - **Tiêu đề tóm tắt** `Máy chiếu phòng A1-305 không lên hình`.
   - **Mô tả chi tiết sự cố** `Bật máy chiếu thấy đèn nguồn sáng nhưng không có hình trên màn chiếu. Đã thử đổi cáp HDMI vẫn không được.`
   - Cuối form, tick ô vuông **Đồng thuận xử lý dữ liệu cá nhân (Không tick sẵn)**.
   - Bấm **Gửi phiếu báo hỏng**.

   **Thấy:** dưới nút hiện khung xanh **Đã gửi phiếu báo hỏng**, dòng "Mã phiếu: …  · Trạng thái: **Chờ kiểm tra**". Ghi lại 8 ký tự đầu
   mã phiếu (ví dụ `43f146b1`).
   **Nói:** "Em sinh viên điền form, phiếu có trạng thái ngay. Hệ thống tự biết máy chiếu thuộc Trung tâm CNTT và gửi
   việc về đúng nhóm kỹ thuật viên, không ai phải nhắn tin. Đây là **P (Process)**: quy trình vẽ bằng BPMN/DMN, chạy
   trên bộ máy của **Tầng 1**. Bản thân quy trình 'sửa chữa phòng lab' là **ứng dụng Tầng 3**."
   *Nếu gõ form chậm:* bỏ bước này, dùng phiếu mẫu có sẵn và đi tiếp từ bước 6 (bước 7 vẫn dùng phiếu mẫu riêng).
6. **(0:30)** **Làm:** sang cửa sổ 2 (`ktv.cuong`), bấm **Việc của tôi** (hoặc **F5**).
   **Thấy:** hai việc **Chờ kiểm tra**: một là phiếu mẫu có sẵn, một là phiếu vừa tạo (mã khớp với mã ở bước 5; thường nằm dưới).
   Bấm **tên bước** của phiếu mới: form **Biên bản kiểm tra hiện trạng và đề xuất xử lý** hiện ra. Phần **Chi tiết phiếu** bên dưới
   ghi "Họ và tên người báo hỏng: Nguyễn Văn An", "Số điện thoại liên hệ: 0900000001", và **Lịch sử** có dòng "sv.an · Tạo phiếu: report".
   **Nói:** "Anh Cường thuộc Trung tâm CNTT thấy việc ngay. Đồng thời chú ý: anh được giao việc nên thấy cả số điện thoại
   người báo. Chốc nữa tôi cho các bạn thấy người không liên quan thì không thấy."
   *Không điền form này* (hết thời gian); tiếp bước sau với phiếu mẫu đã kiểm tra sẵn.
7. **(0:30)** **Làm:** sang cửa sổ 3 (`tl.giang`), bấm **Việc của tôi**. Bấm **Chờ xác nhận nhu cầu**. Điền:
   - **Trưởng phòng thí nghiệm** `Hoàng Thu Giang`; **Ngày xác nhận**: gõ ngày hôm nay (ô ngày hiển thị dạng ngày/tháng/năm, bấm vào rồi gõ liền 8 số).
   - Tick **Xác nhận nhu cầu sửa chữa**; **Mức độ ưu tiên** để nguyên `normal`; không tick ô mua sắm mới.
   - **Ý kiến của Trưởng phòng lab** `Máy chiếu dùng hằng ngày cho lớp thực hành, đề nghị thay bóng sớm.`
   - Bấm **Hoàn thành**.

   **Thấy (trước khi bấm):** phần **Chi tiết phiếu** ghi tiêu đề "[Mẫu] Máy chiếu A1-305 mờ hình, nghi hỏng bóng", chi phí dự kiến
   **3.500.000 đ**, báo giá BG-2026-0142. **Thấy (sau khi bấm):** khung xanh **Đã hoàn thành việc**, "Trạng thái: **Chờ duyệt**".
   **Nói:** "Trưởng phòng xác nhận máy này thật sự cần sửa. Phiếu chuyển sang chờ duyệt. Số tiền 3,5 triệu rơi vào mức
   của trưởng khoa, đó là một bảng luật (DMN) tra ra, không ai tự chọn."

### D. Ủy quyền TUQ. (1:45)

*(TUQ. = "thừa ủy quyền": người được giao ký thay trong thời hạn. Portal **chưa có màn hình ủy quyền**, nên bước tạo ủy quyền làm
bằng một lệnh dán sẵn ở terminal. Swagger **không thay được** vì trang đó không có nút **Authorize** để nhập thẻ đăng nhập.)*

8. **(0:30)** **Làm:** chuyển sang terminal đã chuẩn bị, gõ `uyquyen`, nhấn **Enter**.
   **Thấy:** hiện khối chữ với `"number": "GĐ-UQ-DEMO/2026"`, `"delegator": "tk.hai"`, `"delegate": "ptk.hoa"`, `"role": "faculty_head"`
   và dòng cuối `"status": "active"`.
   **Nói:** "Anh Hải, trưởng khoa, ủy quyền cho chị Hoa duyệt thay trong 7 ngày, kèm số giấy ủy quyền. Trên thực tế đây là
   việc của trưởng khoa; ở đây tôi làm bằng lệnh để nhanh."
   *Nếu hiện `null` hay lỗi:* mã OTP bị trùng, đợi 30 giây gõ lại (xem mục 5).
9. **(0:45)** **Làm:** sang cửa sổ 4 (`ptk.hoa`), nhấn **F5**, bấm **Việc của tôi**.
   **Thấy:** có việc **Chờ duyệt** (phiếu mờ hình ở bước 7). Bấm **Chờ duyệt**, điền form **Phê duyệt phương án và chi phí sửa chữa**:
   - **Người duyệt** `Ngô Thị Hoa`.
   - **Vai trò thẩm quyền**: bấm **Chọn…** → chọn `faculty_head`.
   - **Hình thức ký (Trực tiếp, KT., TUQ.)**: bấm ô đang ghi `direct` → chọn `tuq`.
   - **Số giấy ủy quyền (nếu có)** `GĐ-UQ-DEMO/2026` (đúng số giấy ở bước 8).
   - **Quyết định phê duyệt** để nguyên `approved`; **Số tiền phê duyệt (VNĐ)** `3500000`; **Ngày phê duyệt**: ngày hôm nay.
   - **Ý kiến phê duyệt / lý do** `Đồng ý thay bóng máy chiếu theo báo giá BG-2026-0142.`
   - Bấm **Hoàn thành**.

   **Thấy:** **Đã hoàn thành việc**, "Trạng thái: **Đang sửa**".
   **Nói:** "Chị Hoa không phải trưởng khoa, nhưng hệ thống thấy có giấy ủy quyền còn hạn nên cho duyệt. Người ký là chị Hoa,
   hình thức ký ghi rõ TUQ. Quyền duyệt, ủy quyền nằm trong lõi **Tầng 1**, mọi ứng dụng dùng chung."
10. **(0:30) Kiểm tra hồ sơ ghi TUQ.** **Làm:** sang cửa sổ 2 (`ktv.cuong`), nhấn **F5**, bấm **Đang sửa** (việc mới xuất hiện ở hộp việc).
    Cuộn xuống phần **Chi tiết phiếu**.
    **Thấy:** các dòng "Hình thức ký phê duyệt: **tuq**", "Số giấy ủy quyền (Bắt buộc nếu ký TUQ.): **GĐ-UQ-DEMO/2026 (giả định)**",
    "Họ và tên người duyệt: **Ngô Thị Hoa**", và cuối **Lịch sử**: "… ptk.hoa · Duyệt: Chờ duyệt · ký **TUQ.** · căn cứ GĐ-PC-01/2026 (giả định)".
    **Nói:** "Hồ sơ ghi lại ai ký, ký theo hình thức nào, theo giấy nào. Sau này kiểm toán chỉ cần đọc dòng này."
    - **Không làm được trên giao diện:** minh họa "vượt hạn mức bị từ chối" (phiếu mẫu 12.000.000 đ). Việc đó thuộc
      `ht.khanh`, **không hiện** ở hộp việc của `ptk.hoa`, nên không có chỗ để bấm. Đã kiểm bằng API: trả **403**
      `FORBIDDEN_AUTHORITY` ("Ủy quyền đang có không gồm bước duyệt này: khác vai trò, khác đơn vị hoặc vượt hạn mức…"). Chỉ nói miệng:
      "Phiếu 12 triệu vượt hạn mức nên chị Hoa không duyệt thay được."

### E. Dữ liệu (1:00)

11. **(0:30)** **Làm:** sang cửa sổ 6 (`ht.khanh`), bấm **Việc của tôi**, bấm **Chờ duyệt** (phiếu mẫu "[Mẫu] Máy tính trạm A1-305 không lên nguồn",
    **12.000.000 đ**). Cuộn xuống **Chi tiết phiếu**.
    **Thấy:** có tiêu đề, mô tả, chi phí, nhưng **không có** các dòng "Họ và tên người báo hỏng", "Mã sinh viên…", "Số điện thoại liên hệ", "Địa chỉ email liên hệ".
    Chỉ sang cửa sổ 2 (`ktv.cuong`, phiếu ở bước 6) để so: bên đó có đủ các dòng này.
    **Nói:** "Thông tin cá nhân của người báo chỉ người đang xử lý mới thấy. Hiệu trưởng cần quyết định chi tiền, không cần số
    điện thoại sinh viên nên hệ thống che. Đây là **D (Data)**: cơ sở dữ liệu, che dữ liệu cá nhân và nhật ký truy cập thuộc **Tầng 1**.
    Dữ liệu mẫu do đội tự soạn, không có người thật."
12. **(0:30)** **Làm:** vẫn cửa sổ 6, bấm tab **Dashboard**.
    **Thấy:** bốn ô số: **Tổng số phiếu**, **Phiếu quá hạn**, **Chi phí đã duyệt**, **Chi phí thực tế** (ví dụ **11.000.000 ₫** lúc chạy thử; số của bạn có thể khác
    tùy phiếu đã làm); biểu đồ **Số phiếu theo trạng thái** và bảng **Số phiếu theo đơn vị**. Không có tên người nào.
    **Nói:** "Thống kê tổng hợp theo trạng thái và theo đơn vị, không có tên ai. Cùng dữ liệu này có API (như tôi đã cho xem
    ở Swagger) nên nhà trường muốn nối với báo cáo khác cũng được."

### F. Intelligence (1:00)

13. **(0:30)** **Làm:** cửa sổ 2 (`ktv.cuong`), bấm tab **Tra cứu**. Gõ vào ô `máy lạnh nhỏ nước xuống sàn` (nhãn ô: "Nhập từ khóa tìm kiếm"), bấm **Tìm kiếm**.
    **Thấy:** dòng "Tìm thấy 8 kết quả · Chế độ: **hybrid**". Kết quả **đầu tiên** là **SOP-FAC-01: Xử lý sự cố điều hòa không mát hoặc chảy nước**, kèm đoạn
    trích ("…nước ngưng tụ nhỏ giọt… xuống sàn nhà…") và nguồn "Tự viết nội dung kỹ thuật · CC-BY-4.0 · data/sop/…".
    Thử thêm `may lanh nho nuoc` (không dấu): kết quả đầu vẫn là hướng dẫn điều hòa.
    **Nói:** "Tôi gõ 'máy lạnh', còn tài liệu viết 'điều hòa', vậy mà hệ thống vẫn tìm đúng bài. Đó là tìm theo nghĩa, chạy ngay
    trong máy, không gửi đi đâu. Đây là **I (Intelligence)**, chạy trên API tìm kiếm của **Tầng 1**."
    - Nếu dòng ghi **Chế độ: fts** (không phải **hybrid**) là chưa tải mô hình: xem mục 5.
14. **(0:30)** **Làm:** bấm tab **Sơ đồ quy trình**.
    **Thấy:** tiêu đề "Báo hỏng và sửa chữa thiết bị phòng lab — phiên bản 1" và sơ đồ các bước, chia khung theo vai trò (**reporter**, **system**,
    **technician**, **lab_manager**, **approver**). Chỉ vào ô hai viền **Phân loại và xếp ưu tiên**, **Tra thẩm quyền duyệt**,
    **Kiểm tra chi phí thực tế (E2)**.
    **Nói:** "Các ô hai viền là bước tra bảng luật. Luật viết rõ, giải thích được vì sao phiếu này ưu tiên thế này, ai phải duyệt.
    Máy chỉ gợi ý và tra luật; người vẫn là người quyết định cuối."
    - **Không làm được trên giao diện:** xem *mức ưu tiên* và *mã lý do* của từng phiếu. Portal chỉ hiện **Hạn** ở hộp việc; mức ưu tiên và mã lý do
      chỉ có trong dữ liệu API (cần thẻ đăng nhập). Đừng hứa là có.
    - **Không nên làm trước Hội đồng:** gõ `ghế gãy chân`. Khi chạy thử, hệ thống vẫn trả 8 kết quả (kết quả đầu là trạm hàn, không liên quan),
      không trả rỗng. Nếu bị hỏi, trả lời thẳng: tìm kiếm chỉ **xếp hạng**, không cam kết kết quả liên quan khi chưa có hướng dẫn về chủ đề đó.

### G. Chi phí vượt và nghiệm thu: kết quả (1:30)

15. **(0:30)** **Làm:** cửa sổ 2 (`ktv.cuong`), bấm **Việc của tôi**, bấm **Đang sửa**. Điền form **Báo cáo kết quả thực hiện sửa chữa**:
    - **Kỹ thuật viên thực hiện** `Lê Văn Cường`; **Ngày hoàn thành**: ngày hôm nay.
    - **Nội dung công việc đã thực hiện** `Tháo bóng cũ, lắp bóng chính hãng mới, kiểm tra lại hình chiếu.`
    - **Linh kiện thực tế đã thay thế** `Bóng đèn máy chiếu chính hãng`.
    - **Chi phí thực tế (VNĐ)** `4000000`; **Kết quả kỹ thuật** để nguyên `completed`.
    - **Giải trình chênh lệch chi phí** `Giá bóng chính hãng tăng so với báo giá ban đầu.`
    - **Ghi chú kỹ thuật bàn giao** `Đã bàn giao, nên vệ sinh lưới lọc gió mỗi học kỳ.`
    - Bấm **Hoàn thành**.

    **Thấy:** **Đã hoàn thành việc**, "Trạng thái: **Chờ duyệt**" (**quay lại** chờ duyệt, không đi thẳng nghiệm thu).
    **Nói:** "Sửa xong tốn 4 triệu, cao hơn 3,5 triệu đã duyệt 14%, vượt mức 10% cho phép. Hệ thống tự đưa phiếu quay lại cho
    người duyệt. Quy tắc 'vượt chi phí phải duyệt lại' nằm trong **Tầng 1** và bảng luật của **Tầng 3**."
16. **(0:30)** **Làm:** sang cửa sổ 5 (`tk.hai`), bấm **Việc của tôi**, bấm **Chờ duyệt**. Điền:
    - **Người duyệt** `Vũ Đức Hải`; **Vai trò thẩm quyền** chọn `faculty_head`.
    - **Hình thức ký** để nguyên `direct`; **Số giấy ủy quyền** để trống.
    - **Quyết định phê duyệt** để nguyên `approved`; **Số tiền phê duyệt (VNĐ)** `4000000`; **Ngày phê duyệt**: hôm nay.
    - **Ý kiến phê duyệt / lý do** `Đồng ý duyệt lại theo chi phí thực tế 4.000.000 đ.`
    - Bấm **Hoàn thành**.

    **Thấy (trước khi bấm):** ở **Chi tiết phiếu**, chi phí thực tế **4.000.000 đ** và lý do chênh lệch; **Lịch sử** có dòng của `ptk.hoa` ký TUQ. **Thấy (sau khi bấm):**
    "Trạng thái: **Chờ nghiệm thu**".
    **Nói:** "Lần này chính trưởng khoa duyệt lại số tiền thực tế."
17. **(0:30)** **Làm:** sang cửa sổ 3 (`tl.giang`), bấm **Việc của tôi**, bấm **Chờ nghiệm thu**. Điền **Biên bản nghiệm thu và bàn giao thiết bị phòng lab**:
    - **Cán bộ nghiệm thu** `Hoàng Thu Giang`; **Vai trò người nghiệm thu**: chọn `lab_manager`; **Ngày nghiệm thu**: hôm nay.
    - **Tình trạng vận hành thiết bị** để nguyên `normal`; **Kết luận nghiệm thu** để nguyên `accepted`.
    - **Ý kiến nghiệm thu chi tiết** `Máy chiếu lên hình rõ, đã thử trong giờ thực hành.`
    - Tick **Xác nhận bàn giao đưa thiết bị vào sử dụng** (không tick thì không cho hoàn tất).
    - **Trước khi bấm Hoàn thành**, cuộn xuống **Lịch sử**: chỉ lần lượt từng dòng (tạo phiếu, kiểm tra, xác nhận, duyệt TUQ., sửa, duyệt lại).
    - Bấm **Hoàn thành**.

    **Thấy:** khung xanh **Đã hoàn thành việc**, "Trạng thái: **Hoàn tất**".
    **Nói:** "Phiếu hoàn tất, mọi bước đều có tên người, giờ và hình thức ký. Người sửa không được tự nghiệm thu; đó là luật tách quyền,
    nằm trong lõi **Tầng 1**."
    - **Không làm được trên giao diện:** minh họa "người sửa nghiệm thu bị chặn" (tình huống 9). Chưa chạy thử; chỉ nói miệng.

### H. Tổng kết ba tầng (0:30)

18. **Làm:** (không thao tác) mở `README.md` hoặc `docs/ARCHITECTURE.md` mục 1 có sơ đồ ba tầng; hoặc chỉ nhắc lại tab **Sơ đồ quy trình**.
    **Nói:**
    - "**Tầng 1**, phần lõi không giao diện: đăng nhập (Keycloak), cổng API (APISIX), bộ máy quy trình (Core + SpiffWorkflow), cơ sở dữ liệu (PostgreSQL)."
    - "**Tầng 2**, bốn năng lực H-P-D-I: người dùng, quy trình, dữ liệu, thông minh (luật và tìm kiếm). Giao diện web chỉ là một khách hàng của lõi."
    - "**Tầng 3**, ứng dụng nghiệp vụ: sửa chữa lab và đặt phòng. Chỉ là gói tệp nạp vào lõi, không sửa mã của lõi."

## 4. Đã chạy thử đến đâu

Chạy thử thật bằng trình duyệt trên bản 0.2.1 đã nạp dữ liệu mẫu, đúng thứ tự trên (tài khoản, nhãn nút, ô, thông báo đều lấy từ màn hình thật):

| Bước | Trạng thái |
|---|---|
| 1–4 (A, B) | Đã chạy. Swagger `401` và `200` đã thấy thật |
| 5–7 (C) | Đã chạy; `ktv.cuong` thấy phiếu mới với đủ thông tin người báo; `tl.giang` xác nhận → **Chờ duyệt** |
| 8–10 (D) | Đã chạy; ủy quyền bằng lệnh dán sẵn (kết quả `active`); duyệt TUQ. → **Đang sửa**; hồ sơ ghi `tuq` và số giấy. Phần "vượt hạn mức" **chỉ kiểm bằng API**, không có trên giao diện |
| 11–12 (E) | Đã chạy |
| 13–14 (F) | Đã chạy. **Khác bản cũ:** `ghế gãy chân` **không** trả rỗng |
| 15–17 (G) | Đã chạy tới **Hoàn tất**. Chưa chạy thử "người sửa nghiệm thu bị chặn" (SoD-2) |
| 18 (H) | Chỉ nói, không thao tác |

Chưa kiểm: bản chạy trên máy demo thật, hai người cùng thao tác, đo thời gian bằng người thật (thời lượng là ước tính theo thao tác).

## 5. Nếu có sự cố

| Triệu chứng | Làm gì |
|---|---|
| Trang Swagger (`:9080/api/docs`) trắng, chỉ có chữ tiêu đề | Giao diện Swagger tải từ internet (jsdelivr). Mất mạng thì chuyển sang terminal gõ `curl -i http://localhost:9080/api/workflows`, chỉ dòng `HTTP/1.1 401`; nói "đây là cùng việc tôi vừa làm trên Swagger" |
| Nhập OTP bị từ chối / `uyquyen` báo `null` hay lỗi | Mã 6 số chỉ dùng một lần trong 30 giây cho cùng một tài khoản. Đợi sang mã mới: nhấn mũi tên lên + Enter để sinh lại, gõ lại ngay |
| Đăng nhập tài khoản mới nhưng vẫn thấy tên người cũ | Trình duyệt dùng chung phiên: dùng hồ sơ/cửa sổ riêng (mục 1.3), hoặc mở `http://localhost:8000/auth/logout` rồi đăng nhập lại |
| Bấm **Đăng xuất** mà trang đứng yên | Chờ vài giây, nhấn **F5** (chạy thử: phiên đã bị hủy, trang cũ chưa tải lại) |
| **Việc của tôi** không thấy việc vừa làm xong ở bước trước | Nhấn **F5**; kiểm tra đúng tài khoản (xem mục 2) |
| `ptk.hoa` không có việc **Chờ duyệt** ở bước 9 | Kiểm tra bước 7 đã **Hoàn thành** (phiếu đang **Chờ duyệt**) và bước 8 có dòng `"status": "active"`; chạy lại `uyquyen` rồi nhấn **F5** |
| `ptk.hoa` bấm **Hoàn thành** bị từ chối | Kiểm tra **Vai trò thẩm quyền** là `faculty_head`, **Hình thức ký** là `tuq` và **Số giấy ủy quyền** đúng `GĐ-UQ-DEMO/2026` |
| Tìm kiếm ghi **Chế độ: fts**, kết quả không theo nghĩa | Chưa có mô hình. Nói thẳng: "chưa tải mô hình nên đang tìm theo từ khóa". Sau demo chạy `bash scripts/download-models.sh` |
| Phiếu mẫu đã bị dùng ở lần chạy thử trước (hộp việc không như mục 1.4) | `bash scripts/reset.sh --yes`, rồi `bash scripts/download-models.sh`, rồi đợi 30 giây và kiểm `curl -s localhost:9080/api/health` |
| Một dịch vụ không lên (tab **Trạng thái hệ thống** có dòng khác **Hoạt động**) | Gõ `bash scripts/up.sh` (không xóa dữ liệu), chờ 1–2 phút rồi bấm **Kiểm tra lại** |
| Portal lỗi hoặc đăng nhập nghẽn giữa chừng | **Phương án dự phòng:** terminal gõ `bash scripts/demo-e2e.sh`; nó tự đi hết chuỗi báo hỏng → khảo sát → xác nhận → duyệt → sửa → nghiệm thu và in "KỊCH BẢN E2E THÀNH CÔNG". Nó **tạo thêm một phiếu `[E2E]`**, nên nhớ reset sau buổi demo. Nói rõ cho Hội đồng đây là bản chạy tự động |
| Mọi cách trên đều không chạy | Dùng video demo (khuyến nghị ở đề mục 10; **chưa có trong repo**) và mở repo/release để chứng minh tái lập |
