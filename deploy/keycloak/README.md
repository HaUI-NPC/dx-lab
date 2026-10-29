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

Người dùng không thuộc nhóm nào (ví dụ người chỉ có vai trò `reporter`) nhận token **không có** claim `groups`
(Keycloak bỏ claim rỗng); core coi thiếu claim như danh sách rỗng.

## Biến thay lúc import

Keycloak thay `${TÊN}` trong `realm.json` bằng biến môi trường cùng tên của container. Compose truyền các biến sau từ `.env`:
`DXLAB_PORTAL_PUBLIC_URL`, `DXLAB_PORTAL_CLIENT_SECRET`. Không ghi giá trị thật vào tệp này.

## Sửa realm

Keycloak chỉ nạp `realm.json` khi realm `dxlab` chưa có trong volume `keycloak-data`. Sửa tệp xong phải xóa volume:

```bash
docker compose -p dxlab down -v && scripts/up.sh
```

Thay đổi làm trực tiếp trên trang quản trị `/admin` không ghi ngược vào `realm.json`.
