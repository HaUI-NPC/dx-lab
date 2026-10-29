<!-- SPDX-FileCopyrightText: 2026 DX-Lab contributors -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# DX-Lab MCP

Chạy `dxlab login` trước để lưu token của chính người dùng. Khởi động máy chủ stdio bằng `uv run --package dxlab-mcp dxlab-mcp`; cấu hình lệnh này trong MCP Inspector hoặc MCP host. `DXLAB_TOKEN_FILE` đổi vị trí tệp token (mặc định `~/.config/dxlab/token.json`, chỉ chủ sở hữu được phép đọc/ghi); `DXLAB_API_URL` đổi địa chỉ gateway (mặc định `http://localhost:9080/api`). Token hết hạn: chạy `dxlab login` lại. Không cung cấp token dịch vụ hoặc địa chỉ core trực tiếp.

Các tool `bao_hong`, `viec_cua_toi`, `tra_cuu_phieu`, `tim_huong_dan`, `hoan_thanh_viec` gọi API gateway với quyền của người đăng nhập. Tool ghi hiển thị toàn bộ dữ liệu và yêu cầu người dùng xác nhận qua MCP elicitation trước khi gửi; host không hỗ trợ elicitation sẽ không thể thực hiện ghi. Dữ liệu `bao_hong` và `hoan_thanh_viec` phải tuân theo schema form của core. Core vẫn kiểm tra quyền, che dữ liệu cá nhân và không kiêm nhiệm; thao tác không có xác thực bổ sung từng lần.
