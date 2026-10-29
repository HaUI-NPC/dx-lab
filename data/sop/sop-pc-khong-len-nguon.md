<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Hướng dẫn kiểm tra và khắc phục sự cố máy tính không lên nguồn (SOP-IT-01)

## 1. Mục đích và phạm vi áp dụng
- **Mục đích:** Quy định trình tự các bước chẩn đoán, kiểm tra an toàn và xử lý nhanh sự cố máy tính để bàn (PC), máy trạm không lên nguồn hoặc tự sập nguồn trong phòng thực hành máy tính.
- **Phạm vi áp dụng:** Áp dụng cho giảng viên, sinh viên và cán bộ kỹ thuật Trung tâm CNTT phụ trách các phòng máy tính (ví dụ: A1-305, A1-306).
- **Từ khóa tìm kiếm:** `may tinh khong len`, `máy tính không lên`, `khong len nguon`, `mất nguồn PC`, `bat may khong len`, `treo may`.

## 2. Dấu hiệu nhận biết sự cố
- Bấm nút nguồn (Power) trên thùng máy nhưng đèn LED không sáng, quạt nguồn và quạt CPU không quay.
- Quạt quay giật một lần rồi tắt hẳn, máy tính không phát ra tiếng bíp POST.
- Đèn bo mạch chủ (Mainboard) sáng nhưng nhấn nút nguồn thùng máy không có phản hồi.
- Máy tính đang chạy tự động sập nguồn đột ngột và không bật lại được ngay.

## 3. Nguyên nhân phổ biến
1. Cáp nguồn AC bị lỏng, ổ cắm bàn thực hành bị ngắt aptomat hoặc lỏng chân cắm.
2. Công tắc phụ phía sau bộ nguồn (PSU) đang ở vị trí TẮT (O).
3. Nút bấm nguồn (Power SW) trên vỏ case bị kẹt, lỏng dây nối vào chân cắm Front Panel của bo mạch chủ.
4. Bộ nguồn máy tính (PSU) bị quá tải, nổ tụ hoặc chập mạch bảo vệ nguồn.
5. Xung đột tiếp xúc linh kiện: thanh RAM hoặc card màn hình bị bám bụi, lỏng chân cắm sau thời gian dài sử dụng.

## 4. Trình tự xử lý sự cố

### Bước 1: Kiểm tra an toàn nguồn điện ngoài
1. Kiểm tra ổ cắm điện tại bàn học xem có điện hay không (thử cắm thiết bị khác hoặc quan sát đèn báo ổ cắm).
2. Rút cáp nguồn PC cắm chặt lại vào cả hai đầu: chân cắm ổ điện và chân cắm phía sau bộ nguồn.
3. Đảm bảo công tắc phụ I/O trên PSU (nếu có) được bật về vị trí BẬT (I).

### Bước 2: Kiểm tra nút nguồn và dây kích nguồn
1. Kiểm tra nút bấm phía trước vỏ case có độ nảy đàn hồi tốt không, có bị kẹt lún vào trong hay không.
2. Mở nắp hông case, kiểm tra cặp chân cắm `POWER SW` từ mặt trước vào cụm chân điều khiển bo mạch chủ (Front Panel Header).
3. Nếu nghi ngờ hỏng nút bấm: dùng tuốc nơ vít cách điện chạm nhẹ vào 2 chân `POWER SW` trên mainboard để kích nguồn trực tiếp.

### Bước 3: Kiểm tra và xả tĩnh điện linh kiện
1. Rút hoàn toàn dây nguồn khỏi máy tính.
2. Nhấn và giữ nút nguồn phía trước trong 15–20 giây để xả hết điện áp dư tích tụ trong tụ điện.
3. Tháo các thanh RAM, dùng chổi lông mềm quét bụi khe cắm và dùng tẩy cao su làm sạch chân tiếp xúc mạ vàng của RAM. Cắm lại chặt vào đúng rãnh lẫy khóa.
4. Cắm lại dây nguồn và thử khởi động lại.

### Bước 4: Kiểm tra bộ nguồn (PSU) độc lập
1. Nếu quạt nguồn hoàn toàn không quay khi kích nguồn: rút cáp 24-pin nối mainboard.
2. Dùng đoạn dây kim loại hoặc kẹp giấy cắm nối tắt chân màu xanh lá (PS_ON) với một chân màu đen (GND bất kỳ).
3. Cắm điện: nếu quạt nguồn không quay, xác định bộ nguồn đã hỏng, cần lập đề xuất thay thế.

## 5. Nghiệm thu và báo cáo
- Máy tính khởi động ổn định vào màn hình BIOS/Hệ điều hành, quạt tản nhiệt quay êm, nhiệt độ CPU dưới 60 độ C.
- Ghi nhận kết quả vào phiếu sửa chữa trên hệ thống DX-Lab kèm mã linh kiện thay thế (nếu có).
