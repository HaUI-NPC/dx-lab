<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Hướng dẫn xử lý sự cố máy chiếu không nhận tín hiệu hoặc mờ hình (SOP-IT-02)

## 1. Mục đích và phạm vi áp dụng
- **Mục đích:** Hướng dẫn quy trình chuẩn kiểm tra, cân chỉnh và khắc phục sự cố máy chiếu treo trần hoặc máy chiếu để bàn tại các giảng đường, phòng thực hành.
- **Phạm vi áp dụng:** Cán bộ kỹ thuật Trung tâm CNTT và giảng viên giảng dạy tại các phòng học.
- **Từ khóa tìm kiếm:** `may chieu khong len`, `may chieu mo hinh`, `khong nhan hdmi`, `khong nhan vga`, `may chieu bao den do`.

## 2. Dấu hiệu nhận biết sự cố
- Máy chiếu đã bật, quạt làm mát hoạt động nhưng màn chiếu chỉ báo dòng chữ "No Signal" hoặc "Searching signal".
- Hình ảnh chiếu lên màn bị nhòe, mờ, sai lệch màu sắc (bị ngả vàng, ngả tím hoặc xuất hiện sọc màu).
- Đèn báo trạng thái trên thân máy chiếu nhấp nháy đỏ hoặc cam liên tục (đèn LAMP hoặc TEMP báo lỗi).
- Máy tự động tắt nguồn chỉ sau 1–2 phút hoạt động kèm tiếng quạt gió rít to.

## 3. Nguyên nhân phổ biến
1. Cáp truyền tín hiệu HDMI hoặc VGA bị lỏng, gãy chân cắm hoặc đứt ngầm do co kéo thường xuyên.
2. Máy tính nguồn phát chưa bật chế độ xuất màn hình ngoài (chế độ Duplicate hoặc Extend).
3. Độ phân giải hoặc tần số quét màn hình trên máy tính vượt quá ngưỡng hỗ trợ của máy chiếu.
4. Tấm lọc bụi (Air Filter) bị bám bụi dày đặc làm máy quá nhiệt, kích hoạt rơ-le nhiệt tự ngắt bảo vệ bóng đèn.
5. Bóng đèn máy chiếu đã hết tuổi thọ hoạt động (quá số giờ quy định) hoặc bị cháy bóng.

## 4. Trình tự xử lý sự cố

### Bước 1: Kiểm tra kết nối và nguồn phát máy tính
1. Kiểm tra hai đầu giắc cắm cáp HDMI/VGA tại máy tính giảng viên và ổ cắm âm tường / thân máy chiếu; cắm chặt và siết ốc cố định (đối với cáp VGA).
2. Trên máy tính Windows, nhấn tổ hợp phím `Windows + P`, chọn chế độ hiển thị `Duplicate` (Nhân đôi màn hình) hoặc `Extend`.
3. Kiểm tra độ phân giải hiển thị trên máy tính: đặt về độ phân giải chuẩn của máy chiếu (ví dụ: 1024x768 hoặc 1920x1080, tần số quét 60Hz).

### Bước 2: Chọn đúng cổng vào (Input Source)
1. Sử dụng điều khiển từ xa hoặc cụm phím trên máy chiếu, nhấn phím `Source` hoặc `Input`.
2. Chọn đúng cổng tín hiệu đang kết nối vật lý (ví dụ: `HDMI 1`, `HDMI 2` hoặc `Computer 1/VGA`).
3. Chờ 5–10 giây để máy chiếu đồng bộ tần số nhận diện tín hiệu.

### Bước 3: Khắc phục lỗi nhiệt độ (Đèn TEMP báo đỏ)
1. Tắt máy chiếu bằng điều khiển, để quạt làm mát chạy cho đến khi máy chuyển hẳn sang chế độ chờ (đèn Power chuyển đỏ ổn định). Rút nguồn điện.
2. Tháo nắp khay lọc bụi bên hông máy chiếu, lấy tấm lưới lọc ra ngoài.
3. Dùng chổi mềm và bình khí nén vệ sinh sạch lớp bụi bám trên lưới lọc. Lắp lại đúng khớp.
4. Bật lại máy chiếu và theo dõi hoạt động trong 10 phút.

### Bước 4: Điều chỉnh độ nét hình ảnh
1. Xoay vòng xoay Focus (Lấy nét) trên cụm ống kính quang học để đạt độ sắc nét chữ trên màn hình.
2. Xoay vòng Zoom để kích thước khung hình vừa vặn với màn chiếu.
3. Vào Menu máy chiếu, chọn chức năng `Keystone` để cân chỉnh vuông góc cạnh viền màn chiếu.

## 5. Nghiệm thu và bàn giao
- Hình ảnh hiển thị rõ nét, màu sắc trung thực, không rung giật hay chớp tắt.
- Máy chiếu hoạt động liên tục 15 phút không báo lỗi nhiệt độ.
