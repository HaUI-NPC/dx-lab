<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Hướng dẫn xử lý sự cố mất kết nối mạng LAN phòng máy (SOP-NET-01)

## 1. Mục đích và phạm vi áp dụng
- **Mục đích:** Hướng dẫn quy trình xác định vùng sự cố và xử lý lỗi mạng cục bộ (LAN Ethernet) và mạng Wi-Fi tại các phòng thực hành công nghệ thông tin.
- **Phạm vi áp dụng:** Kỹ thuật viên mạng thuộc Trung tâm CNTT và quản lý phòng lab.
- **Từ khóa tìm kiếm:** `mat mang`, `mất mạng lan`, `không vào được mạng`, `mat ket noi internet`, `cham cham vang`, `network disconnected`.

## 2. Dấu hiệu nhận biết sự cố
- Biểu tượng mạng trên thanh tác vụ máy tính hiện quả địa cầu hoặc dấu chấm than màu vàng (No Internet access).
- Trình duyệt báo lỗi `DNS_PROBE_FINISHED_NO_INTERNET` hoặc `ERR_CONNECTION_TIMED_OUT`.
- Đèn cổng mạng RJ45 phía sau thùng máy không sáng hoặc chỉ nhấp nháy đèn cam mà không có đèn xanh.
- Toàn bộ máy tính trong một dãy bàn hoặc cả phòng học đồng loạt mất kết nối mạng nội bộ.

## 3. Nguyên nhân phổ biến
1. Đầu bấm hạt mạng RJ45 bị gãy lẫy nhựa, oxy hóa chân đồng hoặc dây cáp Cat6 bị dập đứt ngầm.
2. Cổng mạng trên Switch tầng/phòng bị treo hoặc nhảy cổng bảo vệ (Port Security / Loop Protection).
3. Máy tính bị xung đột địa chỉ IP tĩnh hoặc dịch vụ DHCP Server không cấp phát được dải địa chỉ IP mới.
4. Cấu hình DNS Server sai hoặc máy chủ phân giải tên miền nội bộ gặp sự cố.
5. Thiết bị mạng trung tâm (Switch/Router) bị ngắt nguồn đột ngột do nhảy aptomat tủ rack.

## 4. Trình tự xử lý sự cố

### Bước 1: Kiểm tra kết nối vật lý và đèn trạng thái
1. Kiểm tra đầu cáp mạng cắm vào máy tính: rút ra và cắm lại thật chặt nghe tiếng "tách" của lẫy khóa.
2. Quan sát đèn LED báo link tại cổng mạng:
   - Đèn xanh lá sáng đứng: liên kết vật lý tốt (Link Up).
   - Đèn cam/vàng nhấp nháy: đang truyền nhận gói tin (Activity).
   - Không sáng đèn: mất liên kết vật lý (dây đứt, đầu cáp hỏng, hoặc cổng Switch không có điện).
3. Thử dùng dây mạng dự phòng cắm vào máy tính khác hoặc sử dụng máy đo kiểm tra cáp mạng (Network Cable Tester).

### Bước 2: Kiểm tra cấu hình mạng logic trên máy trạm
1. Mở cửa sổ dòng lệnh (Terminal / Command Prompt).
2. Chạy lệnh kiểm tra địa chỉ IP:
   - Linux: `ip addr show` hoặc `ifconfig`
   - Windows: `ipconfig /all`
3. Nếu máy nhận dải IP `169.254.x.x` (APIPA): chứng tỏ máy không xin được IP từ DHCP Server.
4. Thực hiện làm mới cấu hình DHCP:
   - Windows: `ipconfig /release` sau đó `ipconfig /renew`.
   - Linux: `sudo dhclient -r` sau đó `sudo dhclient`.

### Bước 3: Chẩn đoán bằng lệnh Ping phân đoạn
1. Kiểm tra card mạng nội bộ: `ping 127.0.0.1`.
2. Kiểm tra kết nối tới Gateway mặc định: `ping <IP_DEFAULT_GATEWAY>` (ví dụ: `192.168.1.1` hoặc `10.10.x.1`).
3. Kiểm tra kết nối mạng diện rộng qua IP công cộng: `ping 8.8.8.8` hoặc `ping 1.1.1.1`.
4. Kiểm tra máy chủ DNS: `ping google.com` hoặc dùng lệnh `nslookup haui.edu.vn`.

### Bước 4: Kiểm tra thiết bị mạng tủ Rack phòng máy
1. Mở tủ mạng treo tường của phòng thực hành, kiểm tra nguồn điện cấp cho Switch.
2. Kiểm tra đèn báo của cổng Uplink kết nối về phòng máy chủ trung tâm.
3. Nếu cổng mạng bị khóa do vòng lặp (Loop detection): ngắt kết nối các dây nối vòng giữa các switch bàn và khởi động lại switch bằng công tắc nguồn.

## 5. Nghiệm thu
- Lệnh ping ra Gateway và Internet có độ trễ dưới 5ms, tỉ lệ mất gói (Packet Loss) là 0%.
- Truy cập thành công cổng thông tin đào tạo và hệ thống DX-Lab nội bộ.
