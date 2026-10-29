<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Realm Keycloak `dxlab`

`realm.json` là realm duy nhất của DX-Lab. Compose mount cả thư mục này vào `/opt/keycloak/data/import` và Keycloak
(`start-dev --import-realm`) nạp realm lúc khởi động ([`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) mục 4).
Luật phân quyền mà realm thể hiện nằm ở [`docs/AUTHZ.md`](../../docs/AUTHZ.md) mục 2, 3, 10, 11.

## Nội dung

| Phần | Chi tiết |
|---|---|
| Cây nhóm | Cây đơn vị `/haui/...` theo AUTHZ mục 2. Thuộc tính nhóm `display_name` là tên hiển thị tiếng Việt của đơn vị hoặc vai trò |
| Nhóm vai trò | Nhóm con mang tên khóa vai trò (AUTHZ mục 3) dưới đúng đơn vị, ví dụ `/haui/sict/khmt/lab-a1-305/lab_manager`. `reporter` không có nhóm |
| `dxlab-portal` | Confidential, authorization code + PKCE (S256 bắt buộc). Secret `${DXLAB_PORTAL_CLIENT_SECRET}`. Redirect `${DXLAB_PORTAL_PUBLIC_URL}/auth/callback` và `http://localhost:8001/auth/callback` (portal chạy dev) |
| `dxlab-cli` | Public, bật device authorization grant. Direct access grant bật **chỉ để** `seed.sh`, `demo-e2e.sh` lấy token bằng tài khoản demo |
| Token (cả hai client) | `aud` chứa `dxlab-core`; claim `groups` là đường dẫn nhóm đầy đủ; `preferred_username`, `name` |
| Tài khoản demo | 17 tài khoản AUTHZ mục 11, mật khẩu `${DXLAB_DEMO_PASSWORD}`, email dạng `<tên>@dx-lab.example`, mỗi người thuộc nhóm vai trò đúng bảng |
| OTP | Realm role `otp-required` gán cho nhóm vai trò `faculty_head`, `faculty_deputy`, `school_head`, `vice_president`, `president`, `process_admin`, `rule_admin`, `process_owner`, `internal_auditor`, `system_admin` (AUTHZ mục 10). Luồng `browser` (kể cả device flow) và `direct grant` (client `dxlab-cli`) đòi OTP khi người dùng có realm role này; người chưa cài OTP bị ép cài ở lần đăng nhập trình duyệt đầu |
| Phiên | `ssoSessionIdleTimeout` = 1800 giây (30 phút không thao tác) |

Người dùng không thuộc nhóm nào (ví dụ người chỉ có vai trò `reporter`) nhận token **không có** claim `groups`
(Keycloak bỏ claim rỗng); core coi thiếu claim như danh sách rỗng.

## Biến thay lúc import

Keycloak thay `${TÊN}` trong `realm.json` bằng biến môi trường cùng tên của container. Compose truyền các biến sau từ `.env`:
`DXLAB_PORTAL_PUBLIC_URL`, `DXLAB_PORTAL_CLIENT_SECRET`, `DXLAB_DEMO_PASSWORD`, `DXLAB_DEMO_OTP_SECRET`. Không ghi giá trị thật
vào tệp này.

## OTP của tài khoản demo

Mười tài khoản có OTP được nạp sẵn một credential TOTP (SHA1, 6 chữ số, chu kỳ 30 giây) với secret `${DXLAB_DEMO_OTP_SECRET}`,
để script demo đăng nhập không tương tác. **Khóa TOTP là các byte UTF-8 của chuỗi secret** (Keycloak lưu secret dạng chuỗi,
không phải base32): tính mã bằng `HMAC-SHA1(secret.encode(), bộ_đếm_30s)`. Direct grant gửi mã ở tham số `totp`:

```bash
curl -s http://localhost:8180/realms/dxlab/protocol/openid-connect/token \
  -d client_id=dxlab-cli -d grant_type=password -d username=tk.hai \
  -d password="$DXLAB_DEMO_PASSWORD" -d totp="$(mã_totp)"
```

Người dùng có OTP mà gọi direct grant thiếu hoặc sai `totp` nhận `400 invalid_grant`. Keycloak **từ chối dùng lại một mã**
trong cùng chu kỳ 30 giây (đã kiểm: hai lần direct grant liên tiếp cùng mã, lần hai `400`): script cần lấy token một lần rồi dùng
lại, hoặc đợi sang chu kỳ kế tiếp trước khi lấy token lần nữa cho cùng tài khoản.

## Thời hạn phiên

Keycloak đặt thời hạn không thao tác theo **realm**, không theo từng người dùng, nên 30 phút áp cho mọi tài khoản (chặt hơn
AUTHZ mục 10, vốn chỉ đòi cho tài khoản có OTP).

## Sửa realm

Keycloak chỉ nạp `realm.json` khi realm `dxlab` chưa có trong volume `keycloak-data`. Sửa tệp xong phải xóa volume:

```bash
docker compose -p dxlab down -v && scripts/up.sh
```

Thay đổi làm trực tiếp trên trang quản trị `/admin` không ghi ngược vào `realm.json`.
