<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Kịch bản demo: nhìn và làm theo

**Người hỗ trợ thao tác:** làm lần lượt A–H bên dưới. **Người thuyết trình:** đọc câu “Nói” hoặc dùng [bản giải thích và trả lời câu hỏi](kich-ban.md).

Dự kiến **9 phút 30 giây**, dự phòng 30 giây; cần tổng duyệt để chốt thời gian. Tên người, tài khoản, phiếu, số tiền và giấy ủy quyền đều **giả định**.

## Trước khi bắt đầu

Nhờ người kỹ thuật làm [phần chuẩn bị cuối tài liệu](#chuan-bi-ky-thuat), rồi bàn giao máy với các cửa sổ đã đăng nhập:

| Nhãn cửa sổ | Tài khoản | Người đang đóng vai |
|---|---|---|
| **1 — An** | `sv.an` | Nguyễn Văn An — sinh viên báo hỏng |
| **2 — Cường** | `ktv.cuong` | Lê Văn Cường — kỹ thuật viên |
| **3 — Giang** | `tl.giang` | Hoàng Thu Giang — trưởng phòng lab |
| **4 — Hoa** | `ptk.hoa` | Ngô Thị Hoa — phó trưởng khoa, duyệt thay |
| **5 — Hải** | `tk.hai` | Vũ Đức Hải — trưởng khoa |
| **6 — Khánh** | `ht.khanh` | Bùi Quốc Khánh — hiệu trưởng |
| **Lệnh** | Không đăng nhập trình duyệt | Cửa sổ Terminal đã chuẩn bị sẵn |

- [ ] Nhận đủ cửa sổ, có nhãn để chuyển đúng người. **Không đăng xuất hoặc đổi tài khoản trong buổi demo.**
- [ ] Cửa sổ **1 — An** có thêm tab **Swagger** (trang thử gọi hệ thống).
- [ ] Biết ai hỗ trợ kỹ thuật khi có lỗi; không tự chạy lệnh xóa dữ liệu.

**Cách đọc:** chữ **đậm** là chỗ cần tìm/bấm; chữ `như thế này` là nội dung cần nhập. “Tải lại” = bấm nút mũi tên vòng tròn cạnh thanh địa chỉ. Mọi ô ngày đều chọn **ngày hôm nay**.

**Cách mở việc:** bấm **Việc của tôi** → bấm tên bước gạch chân, chẳng hạn **Chờ duyệt**. Nếu có nhiều việc, xem 8 ký tự đầu mã phiếu; mở ra rồi kiểm tra tiêu đề trong **Chi tiết phiếu** bên dưới biểu mẫu.

> **Có hai phiếu máy chiếu, đừng nhầm:** bước 5–6 dùng phiếu vừa tạo để cho thấy việc đến đúng người. Từ bước 7 đến hết demo dùng phiếu có sẵn **[Mẫu] Máy chiếu A1-305 mờ hình, nghi hỏng bóng**.

## A. Giới thiệu bài toán · 30 giây

**1. Cửa sổ 1 — An:** mở tab đầu tiên. Góc trên phải phải có tên **Nguyễn Văn An**.

> **Nói:** “Thay vì báo hỏng qua tin nhắn rồi mất dấu, sinh viên gửi phiếu. Hệ thống theo dõi ai xử lý và đã làm đến đâu.”

## B. Cho thấy hệ thống đang chạy · 1 phút 30 giây

| Bước | Làm theo | Đúng khi thấy |
|---|---|---|
| **2** | **1 — An**, chuyển sang tab **Swagger**. Bấm **GET /api/workflows** → **Try it out** → **Execute**. Cuộn tới **Server response**. | **Code 401**, **Error: Unauthorized**. Đây là kết quả mong đợi, không phải demo bị lỗi. |
| **3** | Kéo lên, bấm **GET /api/health** → **Try it out** → **Execute**. | **Code 200**; `status`, `database`, `embedding_model` đều là `ok`. |
| **4** | Quay về tab đầu → **Trạng thái hệ thống**. | Cả 7 dòng đều **Hoạt động**. |

> **Nói:** “Chưa đăng nhập thì không lấy được danh sách phiếu. Kiểm tra sức khỏe hệ thống thì được phép. Phần lõi dùng chung này là Tầng 1.”

## C. Báo hỏng và chuyển đúng người · 1 phút 45 giây

### 5. An gửi phiếu mới

**1 — An** → **Báo hỏng**. Điền theo bảng:

| Ô trên màn hình | Nhập / chọn |
|---|---|
| Họ và tên | `Nguyễn Văn An` |
| Mã sinh viên / Cán bộ | `SV2026001` |
| Số điện thoại liên hệ | `0900000001` |
| Email liên hệ | `sv.an@example.test` |
| Phòng thực hành | `lab-a1-305` |
| Phân loại thiết bị | `projector` |
| Mã tài sản / thiết bị | `AST-PROJ-305-01` |
| Tiêu đề tóm tắt | `Máy chiếu phòng A1-305 không lên hình` |
| Mô tả chi tiết sự cố | `Bật máy chiếu thấy đèn nguồn sáng nhưng không có hình trên màn chiếu. Đã thử đổi cáp HDMI vẫn không được.` |

Giữ **Mức ảnh hưởng** = `single`, **Mức độ khẩn cấp** = `normal`; không tick **Có nguy cơ mất an toàn**.
Tick **Đồng thuận xử lý dữ liệu cá nhân (Không tick sẵn)** → **Gửi phiếu báo hỏng**.

**Kiểm tra:** khung xanh **Đã gửi phiếu báo hỏng**, trạng thái **Chờ kiểm tra**. Ghi lại **8 ký tự đầu mã phiếu**.

*Nếu không đủ thời gian nhập:* bỏ bước 5; ở bước 6 mở phiếu mẫu **Chờ kiểm tra** có sẵn.

### 6. Cường nhận được việc

**2 — Cường** → **Việc của tôi** → tải lại nếu chưa thấy phiếu → bấm **Chờ kiểm tra** có mã vừa ghi.

**Kiểm tra:** dưới biểu mẫu, **Chi tiết phiếu** có tên **Nguyễn Văn An** và số điện thoại **0900000001** (nếu vừa tạo ở bước 5). **Chỉ cho xem, không điền biểu mẫu này.**

### 7. Giang xác nhận nhu cầu — chuyển sang phiếu mẫu

**3 — Giang** → **Việc của tôi** → **Chờ xác nhận nhu cầu**.
Kiểm tra tiêu đề **[Mẫu] Máy chiếu A1-305 mờ hình, nghi hỏng bóng**, chi phí **3.500.000 đ**, rồi điền:

| Ô trên màn hình | Nhập / chọn |
|---|---|
| Trưởng phòng thí nghiệm | `Hoàng Thu Giang` |
| Ngày xác nhận | Hôm nay |
| Xác nhận nhu cầu sửa chữa | Tick |
| Mức độ ưu tiên | Giữ `normal`; không tick ô mua sắm mới |
| Ý kiến của Trưởng phòng lab | `Máy chiếu dùng hằng ngày cho lớp thực hành, đề nghị thay bóng sớm.` |

Bấm **Hoàn thành** → phải thấy **Chờ duyệt**.

> **Nói:** “Phiếu mới đã đến đúng kỹ thuật viên. Để tiết kiệm thời gian, từ đây dùng phiếu mẫu đã kiểm tra sẵn. Trưởng phòng xác nhận cần sửa; hệ thống tự chọn cấp duyệt theo số tiền.”

## D. Hoa duyệt thay trưởng khoa · 1 phút 45 giây

### 8. Tạo ủy quyền

Mở cửa sổ **Lệnh** → gõ `uyquyen` → **Enter**.
Phải thấy `"status": "active"`, người giao `tk.hai`, người nhận `ptk.hoa`, số giấy `GĐ-UQ-DEMO/2026` (giả định).

### 9. Hoa duyệt 3,5 triệu

**4 — Hoa** → tải lại → **Việc của tôi** → **Chờ duyệt** của phiếu máy chiếu mẫu.

| Ô trên màn hình | Nhập / chọn |
|---|---|
| Người duyệt | `Ngô Thị Hoa` |
| Vai trò thẩm quyền | `faculty_head` |
| Hình thức ký (Trực tiếp, KT., TUQ.) | Đổi `direct` thành `tuq` |
| Số giấy ủy quyền (nếu có) | `GĐ-UQ-DEMO/2026` |
| Quyết định phê duyệt | Giữ `approved` |
| Số tiền phê duyệt (VNĐ) | `3500000` — không có dấu chấm |
| Ngày phê duyệt | Hôm nay |
| Ý kiến phê duyệt / lý do | `Đồng ý thay bóng máy chiếu theo báo giá BG-2026-0142.` |

Bấm **Hoàn thành** → phải thấy **Đang sửa**.

### 10. Cho xem dấu vết duyệt thay

**2 — Cường** → tải lại → **Việc của tôi** → **Đang sửa** → cuộn tới **Chi tiết phiếu**.
Chỉ vào tên **Ngô Thị Hoa**, hình thức ký **tuq**, số giấy **GĐ-UQ-DEMO/2026 (giả định)** và dòng ký **TUQ.** trong **Lịch sử**. Chưa điền báo cáo sửa chữa.

> **Nói:** “Trưởng khoa giao quyền cho chị Hoa trong 7 ngày. Chị duyệt thay, gọi là thừa ủy quyền — TUQ. Hồ sơ vẫn ghi rõ người duyệt và giấy ủy quyền.”

## E. Che thông tin cá nhân, xem thống kê · 1 phút

| Bước | Làm theo | Đúng khi thấy |
|---|---|---|
| **11** | **6 — Khánh** → **Việc của tôi** → **Chờ duyệt**. Kiểm tra phiếu **[Mẫu] Máy tính trạm A1-305 không lên nguồn**, **12.000.000 đ**. Cuộn tới **Chi tiết phiếu**; không duyệt phiếu này. | Có nội dung và chi phí, **không có** họ tên, mã sinh viên, điện thoại, email người báo. Muốn đối chiếu: quay sang **2 — Cường**, mở lại phiếu **Chờ kiểm tra** ở bước 6, nơi có thông tin liên hệ. |
| **12** | **6 — Khánh** → **Dashboard**. | Tổng số phiếu, phiếu quá hạn, chi phí đã duyệt/thực tế; biểu đồ theo trạng thái, bảng theo đơn vị. Không có tên người. Số liệu có thể khác giữa các lần demo. |

> **Nói:** “Hiệu trưởng cần xem chi phí, không cần số điện thoại sinh viên nên phần đó được che. Báo cáo tổng hợp cũng không hiện tên người.”

## F. Tìm hướng dẫn sửa chữa · 1 phút

| Bước | Làm theo | Đúng khi thấy |
|---|---|---|
| **13** | **2 — Cường** → **Tra cứu** → nhập `máy lạnh nhỏ nước xuống sàn` → **Tìm kiếm**. Thử tiếp `may lanh nho nuoc`. | **Chế độ: hybrid**; kết quả đầu là **SOP-FAC-01: Xử lý sự cố điều hòa không mát hoặc chảy nước**, có trích đoạn và nguồn. |
| **14** | Bấm **Sơ đồ quy trình**. Chỉ vào các ô hai viền: **Phân loại và xếp ưu tiên**, **Tra thẩm quyền duyệt**, **Kiểm tra chi phí thực tế (E2)**. | Sơ đồ có các bước và các hàng phân vai. |

> **Nói:** “Gõ ‘máy lạnh’ vẫn tìm được tài liệu viết ‘điều hòa’, kể cả không dấu. Tìm kiếm chạy trong máy. Quy trình có luật rõ ràng, còn người quyết định cuối cùng.”

## G. Vượt chi phí → duyệt lại → hoàn tất · 1 phút 30 giây

### 15. Cường báo sửa xong, hết 4 triệu

**2 — Cường** → **Việc của tôi** → **Đang sửa** của phiếu máy chiếu mẫu.

| Ô trên màn hình | Nhập / chọn |
|---|---|
| Kỹ thuật viên thực hiện | `Lê Văn Cường` |
| Ngày hoàn thành | Hôm nay |
| Nội dung công việc đã thực hiện | `Tháo bóng cũ, lắp bóng chính hãng mới, kiểm tra lại hình chiếu.` |
| Linh kiện thực tế thay thế | `Bóng đèn máy chiếu chính hãng` |
| Chi phí thực tế (VNĐ) | `4000000` |
| Kết quả kỹ thuật | Giữ `completed` |
| Giải trình chênh lệch chi phí | `Giá bóng chính hãng tăng so với báo giá ban đầu.` |
| Ghi chú kỹ thuật bàn giao | `Đã bàn giao, nên vệ sinh lưới lọc gió mỗi học kỳ.` |

Bấm **Hoàn thành** → phải **quay lại Chờ duyệt**, chưa nghiệm thu.

> **Nói:** “Chi phí từ 3,5 lên 4 triệu, vượt ngưỡng 10% của demo. Hệ thống yêu cầu duyệt lại.”

### 16. Hải duyệt lại 4 triệu

**5 — Hải** → **Việc của tôi** → tải lại → **Chờ duyệt** của phiếu máy chiếu mẫu.

| Ô trên màn hình | Nhập / chọn |
|---|---|
| Người duyệt | `Vũ Đức Hải` |
| Vai trò thẩm quyền | `faculty_head` |
| Hình thức ký / Số giấy ủy quyền | Giữ `direct` / để trống số giấy |
| Quyết định phê duyệt | Giữ `approved` |
| Số tiền phê duyệt (VNĐ) | `4000000` |
| Ngày phê duyệt | Hôm nay |
| Ý kiến phê duyệt / lý do | `Đồng ý duyệt lại theo chi phí thực tế 4.000.000 đ.` |

Bấm **Hoàn thành** → phải thấy **Chờ nghiệm thu**.

### 17. Giang nghiệm thu và đóng phiếu

**3 — Giang** → **Việc của tôi** → tải lại → **Chờ nghiệm thu**.

| Ô trên màn hình | Nhập / chọn |
|---|---|
| Cán bộ nghiệm thu | `Hoàng Thu Giang` |
| Vai trò người nghiệm thu | `lab_manager` |
| Ngày nghiệm thu | Hôm nay |
| Tình trạng vận hành thiết bị / Kết luận nghiệm thu | Giữ `normal` / `accepted` |
| Ý kiến nghiệm thu chi tiết | `Máy chiếu lên hình rõ, đã thử trong giờ thực hành.` |
| Xác nhận bàn giao đưa thiết bị vào sử dụng | **Tick — bắt buộc để hoàn tất** |

**Trước khi gửi:** cuộn tới **Lịch sử**, chỉ các lần xác nhận, duyệt thay, sửa, duyệt lại.
Sau đó bấm **Hoàn thành** → phải thấy **Hoàn tất**.

> **Nói:** “Trưởng khoa duyệt lại tiền thực tế, trưởng phòng kiểm tra và nhận bàn giao. Phiếu hoàn tất, vẫn giữ lịch sử từng người xử lý.”

## H. Kết luận · 30 giây

**18.** Mở lại tab **Sơ đồ quy trình**; không cần nhập thêm.

> **Nói:** “Tầng 1 là lõi dùng chung: đăng nhập, cổng kết nối, xử lý quy trình và lưu dữ liệu. Tầng 2 phục vụ người dùng, quy trình, dữ liệu và tìm kiếm thông minh — H-P-D-I. Tầng 3 là ứng dụng cụ thể như sửa chữa lab, đặt phòng; thêm gói ứng dụng mà không sửa lõi.”

## Nếu màn hình không giống hướng dẫn

| Gặp gì? | Người hỗ trợ làm gì? |
|---|---|
| Không thấy việc mới | Kiểm tra tên người góc trên phải → **Việc của tôi** → tải lại. |
| Hoa chưa thấy **Chờ duyệt** | Kiểm tra bước 7 đã ra **Chờ duyệt**, bước 8 đã ra `active`; nếu chưa, nhờ kỹ thuật. |
| Hoa bị từ chối khi duyệt | Kiểm tra `faculty_head`, `tuq` và số giấy `GĐ-UQ-DEMO/2026` đúng bảng bước 9. |
| Bị đưa về trang đăng nhập | Nhờ kỹ thuật đăng nhập lại đúng cửa sổ; phiên hết hạn sau 30 phút không thao tác. |
| Mã xác thực bị từ chối | Nhờ kỹ thuật lấy mã mới sau 30 giây. |
| Swagger trắng / lệnh ủy quyền lỗi / dịch vụ lỗi | Báo kỹ thuật, không tự sửa lệnh hoặc bấm gửi liên tục. |
| Tìm kiếm hiện `fts`, không phải `hybrid` | Nói rõ “đang tìm theo từ khóa”; nhờ kỹ thuật xử lý mô hình sau demo. |
| Không thể tiếp tục | Người trình bày nói rõ sự cố; kỹ thuật dùng phương án chạy tự động bên dưới. Không tuyên bố thao tác đã thành công. |

<a id="chuan-bi-ky-thuat"></a>

## Phụ lục — chỉ dành cho người chuẩn bị kỹ thuật

### Chuẩn bị và bàn giao trước giờ demo ít nhất 15 phút

**Chỉ làm trên máy demo. Lệnh reset xóa toàn bộ dữ liệu cũ; không chạy giữa buổi trình bày.**
Trong thư mục gốc DX-Lab, chạy lần lượt:

```bash
bash scripts/reset.sh --yes
bash scripts/download-models.sh
```

Đợi khoảng 30 giây, kiểm tra:

```bash
curl -s localhost:9080/api/health
```

Chỉ bàn giao khi `embedding_model` là `ok`. Cần Internet để Swagger tải giao diện từ `cdn.jsdelivr.net`; các phần còn lại chạy trong máy.

**Chuẩn bị cửa sổ Lệnh:** cần `curl`, `jq`, `python3`. Dán nguyên khối sau vào Terminal tại thư mục gốc; không chiếu mật khẩu hoặc khóa lên màn hình.

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

Phải hiện mã 6 số. Khi cần mã đăng nhập, gõ `otp` → Enter; dùng ngay trong 30 giây. Không dùng lại một mã cho cùng tài khoản. **Chưa chạy `uyquyen`: để đến bước 8.**

**Đăng nhập 6 cửa sổ theo bảng đầu tài liệu:** mỗi tài khoản dùng **một hồ sơ Chrome riêng**, không chỉ mở thêm cửa sổ thường/ẩn danh. Tạo hồ sơ: ảnh đại diện góc trên phải → **Thêm** → tiếp tục không cần tài khoản Google.

1. Mở `http://localhost:8000` → nhập **Username**, **Password** → **Sign In**. Mọi tài khoản demo dùng **chung một mật khẩu**.
   Hệ thống **không có mật khẩu mặc định cố định**: `scripts/up.sh` sinh ngẫu nhiên khi tạo `.env` lần đầu. Xem mật khẩu
   của máy demo bằng lệnh sau (tại thư mục gốc), không chiếu lên màn hình và không ghi vào tài liệu:

   ```bash
   grep '^DXLAB_DEMO_PASSWORD=' .env | cut -d= -f2-
   ```

   Muốn mật khẩu dễ nhớ cho buổi demo: sửa dòng `DXLAB_DEMO_PASSWORD=` trong `.env` **trước** khi chạy
   `bash scripts/reset.sh --yes` (reset nạp lại tài khoản với mật khẩu mới). Không commit `.env`.
2. Hoa, Hải, Khánh cần thêm mã 6 số ở ô **One-time code** → **Sign In**.
3. Kiểm tra đúng tên ở góc trên phải, dán nhãn cửa sổ theo bảng.
4. Trong **1 — An**, mở thêm tab `http://localhost:9080/api/docs`, không đăng nhập Swagger.

**Kiểm tra trước khi bàn giao:**

- [ ] **1 — An**, **Trạng thái hệ thống**: 7 dòng **Hoạt động**.
- [ ] **3 — Giang**, **Việc của tôi**: đúng 1 việc **Chờ xác nhận nhu cầu**.
- [ ] **6 — Khánh**, **Việc của tôi**: đúng 1 việc **Chờ duyệt**, phiếu 12.000.000 đ.
- [ ] **4 — Hoa**, **Việc của tôi**: chưa có việc.
- [ ] Cửa sổ **Lệnh** vẫn mở, lệnh `otp` dùng được.

### Xử lý sự cố kỹ thuật

| Sự cố | Cách xử lý |
|---|---|
| Swagger trắng vì mất Internet | Chạy `curl -i http://localhost:9080/api/workflows`, chỉ dòng `HTTP/1.1 401`; thay kiểm tra sức khỏe bằng `curl -s localhost:9080/api/health`. Nói rõ đang kiểm tra bằng dòng lệnh. |
| `uyquyen` lỗi hoặc `null` | Nếu vừa dùng OTP của `tk.hai`, đợi sang mã mới sau 30 giây rồi thử lại. Chỉ tiếp tục khi có `active`; còn lỗi thì kiểm tra đăng nhập/dịch vụ, không mặc định mọi lỗi đều do OTP. |
| Sai người đăng nhập / đăng xuất mà trang đứng yên | Kiểm tra hồ sơ Chrome riêng; mở `http://localhost:8000/auth/logout`, tải lại rồi đăng nhập đúng người. |
| Dịch vụ không hoạt động | Chạy `bash scripts/up.sh` (không xóa dữ liệu), chờ 1–2 phút → **Kiểm tra lại**. |
| Tìm kiếm chỉ có `fts` | Sau demo chạy `bash scripts/download-models.sh`, kiểm tra lại sức khỏe. |
| Phiếu mẫu đã dùng hết | Trước buổi demo tiếp theo, làm lại phần chuẩn bị dữ liệu; reset xong phải tải lại mô hình. |
| Giao diện không dùng được | Chạy `bash scripts/demo-e2e.sh`; thành công khi in **KỊCH BẢN E2E THÀNH CÔNG**. Nói rõ đây là chạy tự động, không phải thao tác trên giao diện. Lệnh tạo thêm phiếu `[E2E]`; reset trước buổi demo tiếp theo. |

### Giới hạn và bằng chứng chạy thử

- Bản hướng dẫn gốc ghi nhận đã chạy A–G trên **0.2.1**, tới **Hoàn tất**; H chỉ nói. Bản rút gọn giữ các thao tác đó, **không phải biên bản chạy thử mới**. Chưa tổng duyệt trên máy demo thật, chưa kiểm hai người phối hợp hay đo thời gian thực tế.
- Chưa có màn hình tạo ủy quyền; Swagger không có nút **Authorize**. Bước 8 vẫn cần lệnh đã chuẩn bị.
- Hoa không thấy phiếu 12 triệu để bấm thử vượt hạn mức. Việc bị chặn đã kiểm bằng API, **không minh họa trên giao diện**. Tình huống người sửa tự nghiệm thu bị chặn **chưa chạy thử**.
- Không trình diễn mức ưu tiên/mã lý do từng phiếu: giao diện chưa hiện. Không hứa tìm kiếm luôn đúng hoặc trả rỗng: thử `ghế gãy chân` từng ra kết quả không liên quan.
- Chưa có video dự phòng trong repo. Chỉ dùng nếu đội đã tự chuẩn bị và kiểm tra trước buổi trình bày.
