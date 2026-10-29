<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Đặt phòng thực hành

Gói dữ liệu `room-booking` dùng danh mục phòng `room` của ứng dụng `lab-repair` qua
`record_bindings` trong `process_model.json`. Cần công bố schema bản ghi phòng của
`lab-repair` và nạp danh mục phòng trước khi tạo phiếu; mã `room_id` phải có trong danh mục.
Core đọc đường dẫn tổ chức `org_path` của phòng thành `room_unit` để định phạm vi quản lý.

Người đề nghị tự kiểm tra lịch và khai báo `schedule_conflict`; ứng dụng không tự kiểm
tra lịch hay ngăn đặt trùng. Quyết định duyệt hoặc từ chối đều yêu cầu ghi lý do, bao gồm
trường hợp có xung đột. Dữ liệu ứng dụng không thay đổi mã nguồn core.
