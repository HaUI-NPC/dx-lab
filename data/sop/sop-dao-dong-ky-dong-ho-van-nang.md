<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Hướng dẫn kiểm tra và bảo dưỡng thiết bị đo lường điện tử (SOP-LAB-01)

## 1. Mục đích và phạm vi áp dụng
- **Mục đích:** Quy định các bước kiểm tra hoạt động, hiệu chuẩn sơ bộ (Self-Calibration) và xử lý sự cố thường gặp đối với dao động ký số (Digital Oscilloscope) và đồng hồ vạn năng hiện số (DMM) trong phòng thí nghiệm Điện - Điện tử.
- **Phạm vi áp dụng:** Kỹ thuật viên phòng thí nghiệm và cán bộ phụ trách thực hành bộ môn (ví dụ: phòng A10-201).
- **Từ khóa tìm kiếm:** `dao dong ky`, `dong ho van nang`, `fluke khong len`, `que do oscilloscope`, `chuan tin hieu do`.

## 2. Dấu hiệu nhận biết sự cố
- Đồng hồ vạn năng hiện số không lên màn hình LCD hoặc màn hình hiện mờ, nhấp nháy biểu tượng cảnh báo pin yếu (`Battery Low`).
- Đo điện áp hoặc thông mạch nhưng đồng hồ không phát ra tiếng kêu bíp, kim hiển thị giá trị trôi dạt (drift) không về 0 khi chập 2 que đo.
- Màn hình dao động ký không hiển thị dạng sóng tín hiệu, đường quét bị lệch hẳn ra khỏi phạm vi khung lưới hiển thị dù đã cắm que đo vào điểm chuẩn.
- Dạng sóng đo được bị méo dạng biên độ, xung vuông mẫu bị vát góc hoặc có gai dao động (ringing) quá mức.

## 3. Nguyên nhân phổ biến
1. Pin nguồn 9V của đồng hồ vạn năng bị chai kiệt sau thời gian dài sử dụng.
2. Cầu chì bảo vệ dòng điện bên trong đồng hồ vạn năng (cầu chì nhanh 440mA hoặc 11A) bị đứt do đo quá dòng hoặc cắm nhầm thang đo điện áp vào cổng đo dòng điện.
3. Dây que đo (Probe) bị đứt ngầm dây lõi hoặc lỏng giắc cắm BNC / banana jack.
4. Đầu dò dao động ký (Oscilloscope Probe 10X) chưa được tinh chỉnh tụ bù (Probe Compensation).
5. Trục trặc thiết lập kênh đo (Input Coupling đang đặt GND thay vì DC/AC, hoặc mức kích khởi Trigger đặt sai).

## 4. Trình tự kiểm tra và xử lý sự cố

### Bước 1: Kiểm tra nguồn và que đo đồng hồ vạn năng (DMM)
1. Bật đồng hồ vạn năng sang thang đo kiểm tra pin hoặc thang đo điện trở nhỏ nhất (thang đo thông mạch bíp).
2. Chập chặt hai mũi kim đo đỏ và đen vào nhau:
   - Nếu đồng hồ phát tiếng bíp liên tục và điện trở hiển thị nhỏ hơn 0.2 Ohm: dây que đo tốt.
   - Nếu màn hình báo `OL` (Open Loop) hoặc điện trở dao động lớn: thay thế cặp que đo mới.
3. Nếu màn hình mờ hoặc báo pin yếu: mở nắp đậy phía sau lưng máy, thay viên pin 9V Alkaline chất lượng cao mới.
4. Kiểm tra cầu chì: chuyển thang đo sang Ohm, cắm que đỏ vào cổng `V/Ohm` và cắm que đen lần lượt vào cổng `mA/uA` và `A`. Nếu hiển thị `OL` nghĩa là cầu chì tương ứng đã bị đứt, cần mở nắp thay cầu chì đúng trị số và cấp an toàn (CAT III/IV).

### Bước 2: Kiểm tra và bù tụ cho que đo dao động ký (Oscilloscope)
1. Cắm đầu nối BNC của que đo vào cổng `CH1` của dao động ký, kẹp kẹp cá sấu nối mát vào chân tiếp địa (GND terminal) của máy.
2. Móc đầu đo vào chốt xung chuẩn kiểm tra tích hợp trên mặt máy (chốt xuất tín hiệu xung vuông chuẩn 1kHz / 3Vp-p).
3. Nhấn phím `Auto` hoặc `AutoSet` trên bảng điều khiển dao động ký để máy tự động bắt điểm kích hoạt Trigger và điều chỉnh thang đo `Time/Div`, `Volt/Div`.
4. Quan sát dạng sóng xung vuông trên màn hình:
   - **Xung vuông phẳng chuẩn:** Bù tụ chính xác, sẵn sàng đo đạc.
   - **Đầu xung bị vát tròn (Under-compensated):** Dùng tuốc nơ vít căn chỉnh nhựa chuyên dụng xoay nhẹ ốc vi chỉnh trên thân đầu que đo BNC theo chiều kim đồng hồ.
   - **Đầu xung bị nhô nhọn gai (Over-compensated):** Xoay ốc vi chỉnh ngược chiều kim đồng hồ cho đến khi đỉnh xung vuông trở nên vuông vắn hoàn toàn.

### Bước 3: Chạy quy trình tự cân chỉnh (Self-Calibration)
1. Ngắt kết nối tất cả các que đo khỏi các cổng vào BNC của dao động ký.
2. Bật máy chạy ổn định trong 20 phút để nhiệt độ linh kiện đạt mức cân bằng nhiệt.
3. Nhấn phím `Utility`, chọn mục `Self-Cal` hoặc `Do Calibration`. Chờ máy thực hiện đo đạc và cập nhật các hệ số hiệu chỉnh offset tự động cho tất cả các kênh (thời gian khoảng 3–5 phút).

## 5. Nghiệm thu
- Xung vuông thử nghiệm hiển thị vuông vắn, biên độ đúng 3.0V ± 2%, tần số đo được đúng 1.000 kHz.
- Đồng hồ vạn năng đo nguồn chuẩn DC 5.00V cho sai số dưới 0.1%.
