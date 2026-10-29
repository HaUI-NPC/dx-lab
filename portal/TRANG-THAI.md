<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Dashboard và trạng thái hệ thống

Sau khi đăng nhập, chọn **Dashboard** để xem số phiếu theo trạng thái, đơn vị, quá hạn và chi phí tổng hợp từ core. Không cần đăng nhập để mở `/status`: trang này kiểm tra portal, Keycloak, APISIX, core, PostgreSQL, chỉ mục tìm kiếm và mô hình embedding; tự cập nhật mỗi 15 giây hoặc khi chọn **Kiểm tra lại**.

Nếu APISIX không phản hồi, trạng thái core và các thành phần phía sau cổng được ghi là chưa xác định, không đoán rằng chúng đã dừng. Mô hình embedding chưa có là cảnh báo: tìm kiếm vẫn dùng từ khóa.
