<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Hướng dẫn xử lý sự cố trạm hàn nhiệt không gia nhiệt hoặc hỏng mũi hàn (SOP-LAB-02)

## 1. Mục đích và phạm vi áp dụng
- **Mục đích:** Hướng dẫn quy trình kiểm tra điện trở may-so gia nhiệt (Heating Element), cảm biến nhiệt độ (Thermocouple) và kỹ thuật bảo dưỡng, thay thế mũi mỏ hàn cho trạm hàn điện tử tại phòng thực hành mạch điện tử.
- **Phạm vi áp dụng:** Kỹ thuật viên phụ trách phòng thí nghiệm và sinh viên thực hành hàn mạch PCB.
- **Từ khóa tìm kiếm:** `tram han khong nong`, `mo han khong nong`, `mui han bi oxy hoa`, `loi e-01 tram han`, `hakko fx-888d error`.

## 2. Dấu hiệu nhận biết sự cố
- Bật công tắc trạm hàn nhưng màn hình LED nhấp nháy báo mã lỗi cảm biến (ví dụ: mã `S-E` hoặc `H-E` - Sensor Error / Heater Error).
- Màn hình hiển thị nhiệt độ cài đặt (ví dụ 350°C) nhưng đầu mũi hàn thực tế hoàn toàn nguội lạnh.
- Mũi hàn bị cháy đen, xỉ thiếc bám quanh mũi hàn không tan chảy dù trạm hàn báo đủ nhiệt độ.
- Tay hàn rung giật hoặc phát sinh điện rò ra vỏ kim loại khi chạm vào linh kiện nhạy cảm tĩnh điện (ESD).

## 3. Nguyên nhân phổ biến
1. Dây cáp tay hàn bị đứt ngầm các đường tín hiệu do gập xoắn nhiều lần gần đầu nối giắc 5 chân/8 chân.
2. Lõi gia nhiệt gốm (Ceramic Heater) bên trong tay hàn bị nứt vỡ do va đập cơ học hoặc bị đứt cuộn dây may-so phát nhiệt.
3. Cảm biến nhiệt độ ngắt mạch hoặc đoản mạch.
4. Mũi mỏ hàn (Soldering Tip) bị oxy hóa nghiêm trọng do để nhiệt độ quá cao trong thời gian dài mà không mạ thiếc bảo vệ.
5. Ống kim loại giữ mũi hàn bị lỏng ren hoặc bám cặn rỉ sét ngăn cản sự truyền nhiệt từ lõi gốm sang mũi hàn.

## 4. Trình tự kiểm tra và xử lý sự cố

### Bước 1: Kiểm tra an toàn và kết nối giắc cắm
1. Tắt công tắc nguồn trạm hàn và rút phích cắm điện AC 220V.
2. Kiểm tra giắc cắm nối tay hàn với thân máy chính: vặn vòng ren khóa chắc chắn, đảm bảo các chân kim tiếp xúc không bị cong gập hoặc rỉ sét.
3. Nếu máy tiếp tục báo lỗi, tắt nguồn, rút phích cắm và đợi tay hàn nguội hoàn toàn trước khi tháo hoặc đo.

### Bước 2: Đo kiểm tra lõi gia nhiệt và cảm biến nhiệt
1. Rút giắc cắm tay hàn khỏi thân máy.
2. Sử dụng đồng hồ vạn năng chuyển sang thang đo điện trở Ohm.
3. Chỉ người đã được hướng dẫn mới thực hiện đo và tháo lắp. Đối chiếu sơ đồ chân, phương pháp đo và giới hạn điện trở với tài liệu chính thức của đúng mẫu thiết bị; không dùng trị số của mẫu khác để kết luận an toàn.
4. Nếu nghi ngờ hỏng lõi sưởi, cảm biến hoặc tiếp địa, ngừng sử dụng và chuyển cho kỹ thuật viên có chuyên môn.

### Bước 3: Thay thế lõi may-so gia nhiệt bị hỏng
Chỉ thực hiện sau khi ngắt điện, rút phích cắm và để tay hàn nguội hoàn toàn; thao tác hàn, tháo linh kiện có nguy cơ bỏng và chỉ dành cho người đã được hướng dẫn.
1. Tháo nắp vặn ren kim loại chụp ngoài mũi hàn, nhẹ nhàng rút mũi hàn ra ngoài.
2. Vặn rời khớp nối thân nhựa tay cầm, rút nhẹ bo mạch nhỏ và cụm lõi sưởi gốm ra ngoài.
3. Dùng mỏ hàn chì nhả mối hàn của 4 chân lõi gốm cũ trên bo mạch tay cầm.
4. Lắp lõi gốm mới cùng chủng loại, căn chỉnh chiều dài đầu gốm thò ra đúng tiêu chuẩn (thường 22–24mm) để chạm khít vào đáy mũi hàn. Hàn chắc chắn 4 chân linh kiện vào bo mạch.
5. Lắp lại vỏ bảo vệ và siết chặt ốc giữ.

### Bước 4: Làm sạch và phục hồi mũi hàn bị oxy hóa
1. Cắm lại tay hàn và bật máy ở nhiệt độ 250°C.
2. Khi mũi hàn vừa ấm, nhúng mũi hàn vào bột phục hồi mũi hàn chuyên dụng (Tip Refresher) chứa hợp chất làm sạch và thiếc hoạt tính trong 2–3 giây.
3. Dùng bùi nhùi đồng hoặc miếng xốp ẩm chuyên dụng miết nhẹ để làm bong lớp oxit đen.
4. Ngay lập tức quấn một lớp thiếc hàn có nhựa thông mới phủ đều quanh chóp mũi hàn để tạo lớp mạ bóng bảo vệ chống tái oxy hóa.

## 5. Nghiệm thu
- Màn hình trạm hàn đạt nhiệt độ cài đặt 350°C trong vòng 30 giây kể từ khi bật nguồn.
- Mũi hàn bám thiếc sáng bóng, thiếc tan chảy đều mịn ngay khi chạm vào mũi hàn.
- Kiểm tra an toàn điện và tiếp địa theo tài liệu chính thức của đúng mẫu, bằng thiết bị đo phù hợp; không đưa vào sử dụng nếu chưa đạt.
