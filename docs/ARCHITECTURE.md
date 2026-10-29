<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Kiến trúc DX-Lab

Tài liệu này là **hợp đồng kỹ thuật chung** của dự án: ranh giới giữa các tầng, đường đi của mỗi lời gọi, dịch vụ
và cổng, biến cấu hình, định dạng gói ứng dụng, danh sách thư viện và image được phép dùng. Mọi task trỏ tới đây;
quy ước viết mã, đặt tên API và định dạng lỗi nằm ở mục [Quy ước](../CONTRIBUTING.md#quy-ước) của `CONTRIBUTING.md`,
luật phân quyền nằm ở [`AUTHZ.md`](AUTHZ.md).

Muốn làm khác điều ghi ở đây (thêm thư viện, đổi cổng, đổi tên biến, gọi tắt qua tầng khác): dừng, comment trên
issue và gắn nhãn `needs-mentor`. Hợp đồng chỉ đổi bằng PR riêng do maintainer chính duyệt.

## 1. Ba tầng

```mermaid
flowchart TB
  subgraph T3["Tầng 3 – ứng dụng: apps/, data/"]
    LR["lab-repair: BPMN + DMN + JSON Schema + hướng dẫn"]
    RB["room-booking: chỉ BPMN + DMN + JSON Schema"]
  end
  subgraph T2["Tầng 2 – H-P-D-I: portal/, mcp/"]
    POR["portal: Prefab + BFF đăng nhập"]
    MCP["mcp: MCP server FastMCP (stdio)"]
    CLI["dxlab CLI: login, validate, publish"]
  end
  subgraph T1["Tầng 1 – Open-Core headless: deploy/, core/"]
    GW["APISIX standalone"]
    KC["Keycloak"]
    CORE["Core API (FastAPI + SpiffWorkflow)"]
    PG[("PostgreSQL")]
    VOL[("Volume: tài liệu, chỉ mục zvec, mô hình")]
  end
  LR -. "dxlab publish" .-> GW
  RB -. "dxlab publish" .-> GW
  POR -->|"Bearer token người dùng"| GW
  MCP -->|"Bearer token người dùng"| GW
  CLI -->|"Bearer token người dùng"| GW
  POR -. "OIDC" .-> KC
  CLI -. "device flow" .-> KC
  GW --> CORE
  CORE -. "JWKS" .-> KC
  CORE --> PG
  CORE --> VOL
```

| Tầng | Thư mục | Có gì | Không bao giờ |
|---|---|---|---|
| 1 | `deploy/`, `core/` | Keycloak, APISIX, Core API, PostgreSQL; CLI `dxlab` nằm trong gói `dxlab-core` | Core trả HTML, template, tệp tĩnh giao diện; core biết tên ứng dụng cụ thể; core gọi LLM |
| 2 | `portal/`, `mcp/` | Giao diện H-P-D-I, BFF đăng nhập, MCP server | Import `dxlab_core`; đọc PostgreSQL; tự quyết quyền thay core |
| 3 | `apps/<app>/`, `data/` | Quy trình BPMN, bảng luật DMN, form JSON Schema, hướng dẫn, dữ liệu mẫu | Chứa mã Python hay script chạy trong core |

Core không biết ứng dụng nào đang gọi. Thêm ứng dụng mới = nạp một gói tệp qua `/api/definitions`, không sửa
`core/` và không sửa `portal/`.

## 2. Ranh giới import

Mỗi tầng là một gói Python riêng trong uv workspace; ranh giới được kiểm bằng khai báo phụ thuộc, không chỉ bằng
quy ước.

| Gói | Thư mục | Được import | Cấm import |
|---|---|---|---|
| `dxlab-core` | `core/` | Thư viện trong mục 8 cho core | `dxlab_portal`, `dxlab_mcp`, `prefab_ui`, `authlib`, `fastmcp` |
| `dxlab-portal` | `portal/` | Thư viện trong mục 8 cho portal | `dxlab_core`, `dxlab_mcp`, `SpiffWorkflow`, `sqlalchemy` |
| `dxlab-mcp` | `mcp/` (INT-02) | Thư viện trong mục 8 cho MCP | `dxlab_core`, `dxlab_portal` |

- Không có gói "chung" giữa portal và MCP. Hai bên trao đổi với core bằng HTTP theo OpenAPI của core.
- Lệnh `dxlab validate` chạy cục bộ và dùng **chính** validator của `/api/definitions` (cùng gói `dxlab-core`), để CI
  và core không lệch nhau. `dxlab login` và `dxlab publish` đi qua APISIX như mọi client khác.
- `apps/` chỉ chứa tệp dữ liệu (`.bpmn`, `.dmn`, `.json`, `.md`). Validator của core từ chối gói có script.

## 3. Luồng gọi

```mermaid
sequenceDiagram
  autonumber
  actor U as Người dùng
  participant P as Portal (BFF)
  participant K as Keycloak
  participant G as APISIX
  participant C as Core
  participant D as PostgreSQL
  U->>P: Mở portal
  P->>K: Chuyển hướng đăng nhập (authorization code + PKCE)
  K-->>P: Code → đổi lấy token qua kênh nội bộ
  Note over P: Token giữ phía server, trình duyệt chỉ có cookie phiên httpOnly
  U->>P: Thao tác (ví dụ báo hỏng)
  P->>G: /api/... kèm header Authorization: Bearer (token của người dùng)
  G->>G: Kiểm chữ ký, hạn, issuer của JWT, giới hạn tần suất, gắn X-Request-Id
  G->>C: Chuyển nguyên đường dẫn /api/...
  C->>C: Kiểm lại JWT + 5 lớp phân quyền (AUTHZ.md)
  C->>D: Đọc / ghi
  C-->>P: JSON (dữ liệu cá nhân đã che theo quyền)
  P-->>U: Trang tiếng Việt
```

Luật của luồng gọi:

1. **Mọi lời gọi tới core đi qua APISIX.** Cổng của core không mở ra máy chủ.
2. **Chỉ dùng token của chính người dùng.** Không có tài khoản dịch vụ gọi nghiệp vụ thay người dùng; seed dữ liệu
   cũng đăng nhập bằng tài khoản demo. Nhờ vậy portal, MCP và CLI không làm được gì hơn người đang dùng.
3. **APISIX chặn sớm, core quyết định.** APISIX từ chối token sai hoặc thiếu; core vẫn tự kiểm chữ ký, `iss`, `aud`,
   `exp` và mọi lớp phân quyền. Core không tin header nào do client hay gateway thêm, trừ `X-Request-Id` dùng để log.
4. **Portal và MCP chỉ hiển thị.** Ẩn nút theo vai trò để dễ dùng là được, nhưng quyết định cho hay không luôn do core.
5. Đọc PostgreSQL, volume tài liệu, chỉ mục tìm kiếm: chỉ core.

## 4. Dịch vụ, cổng, URL

Compose sản phẩm nằm ở `deploy/compose.yaml`, tên project `dxlab`, khởi động bằng `scripts/up.sh`
(`docker compose --env-file .env -f deploy/compose.yaml up -d --wait`). Mọi cổng ra máy chủ chỉ bind `127.0.0.1`.

| Service | Image / build | Cổng trong mạng compose | Cổng trên máy chủ | Healthcheck |
|---|---|---|---|---|
| `postgres` | `postgres:17.11-alpine` | 5432 | không mở | `pg_isready` |
| `keycloak` | `quay.io/keycloak/keycloak:26.8.1` | 8080 | `127.0.0.1:8180` | `/health/ready` ở cổng quản trị 9000 |
| `apisix` | `apache/apisix:3.19.0-debian` | 9080 | `127.0.0.1:9080` | gọi `/api/health` qua chính gateway |
| `core` | `core/Dockerfile` | 8000 | không mở | `GET /api/health` |
| `portal` | `portal/Dockerfile` | 8000 | `127.0.0.1:8000` | `GET /healthz` |

Image ghim theo digest trong compose (`image: <tên>:<tag>@sha256:…`); tag trong bảng là để người đọc biết phiên bản.

URL trên máy chạy compose:

| Dùng cho | URL |
|---|---|
| Portal | `http://localhost:8000` |
| API qua gateway (CLI, MCP, `curl`, `demo-e2e.sh`) | `http://localhost:9080/api` |
| Swagger UI, OpenAPI | `http://localhost:9080/api/docs`, `http://localhost:9080/api/openapi.json` |
| Keycloak (realm `dxlab`, trang quản trị `/admin`) | `http://localhost:8180` |

Route của APISIX (`deploy/apisix/apisix.yaml`, chế độ standalone, không etcd):

| Đường dẫn | Token | Plugin |
|---|---|---|
| `GET /api/health`, `GET /api/openapi.json`, `GET /api/docs*` | Không cần | `request-id` |
| Mọi đường dẫn khác dưới `/api/` | Bắt buộc `Authorization: Bearer` | kiểm JWT bằng JWKS của Keycloak, `limit-count`, `request-id` |

APISIX **không viết lại đường dẫn**: core nhận nguyên `/api/...`, và mọi route của core nằm dưới tiền tố `/api`.

### Issuer của Keycloak: URL công khai và URL nội bộ

Trình duyệt và CLI gọi Keycloak ở `http://localhost:8180`, còn container gọi `http://keycloak:8080`. Token chỉ có một
`iss`, nên:

- Keycloak chạy với `KC_HOSTNAME=${DXLAB_KEYCLOAK_PUBLIC_URL}` và `KC_HOSTNAME_BACKCHANNEL_DYNAMIC=true`: `iss` luôn là
  URL công khai, còn endpoint kênh nội bộ (token, JWKS, userinfo) trả theo địa chỉ container đã gọi.
- Tiến trình trong compose (core, portal, APISIX) gọi Keycloak bằng `DXLAB_OIDC_INTERNAL_URL` và so `iss` với
  `DXLAB_OIDC_ISSUER` (URL công khai). CLI và MCP chạy trên máy người dùng nên chỉ cần `DXLAB_OIDC_ISSUER`.
- Realm: `dxlab`. Client: `dxlab-portal` (confidential, authorization code + PKCE, redirect
  `${DXLAB_PORTAL_PUBLIC_URL}/auth/callback`), `dxlab-cli` (public, device authorization grant). Token của cả hai
  client mang `aud` chứa `dxlab-core` và claim `groups` là đường dẫn nhóm đầy đủ ([`AUTHZ.md`](AUTHZ.md) mục 2).
- Keycloak chạy `start-dev --import-realm`, dữ liệu trên volume. Đây là cấu hình demo một máy; triển khai thật dùng
  `start` với TLS và database riêng.

## 5. Cấu hình

- Mọi cấu hình qua **biến môi trường**. Đổi môi trường không phải sửa mã.
- `.env.example` ở gốc repo liệt kê biến người vận hành đặt. `.env` không commit. `scripts/up.sh` tạo `.env` từ
  `.env.example` nếu chưa có và sinh ngẫu nhiên mọi secret đang để trống.
- Biến của DX-Lab có tiền tố `DXLAB_`. Biến của image bên thứ ba giữ tên gốc (`POSTGRES_*`, `KC_*`).
- Secret không có giá trị mặc định trong mã. Thiếu biến bắt buộc thì tiến trình dừng ngay lúc khởi động, báo đúng tên
  biến, không chạy tiếp với giá trị đoán.
- Không in giá trị secret ra log, kể cả khi báo thiếu.

Biến đặt trong `.env`:

| Biến | Ai dùng | Ví dụ / mặc định | Ghi chú |
|---|---|---|---|
| `DXLAB_PORTAL_PUBLIC_URL` | portal, Keycloak (redirect) | `http://localhost:8000` | |
| `DXLAB_KEYCLOAK_PUBLIC_URL` | Keycloak (`KC_HOSTNAME`), compose suy ra issuer | `http://localhost:8180` | |
| `POSTGRES_DB`, `POSTGRES_USER` | postgres, compose suy ra URL database | `dxlab` | |
| `POSTGRES_PASSWORD` | postgres, compose suy ra URL database | (secret) | |
| `KC_BOOTSTRAP_ADMIN_USERNAME`, `KC_BOOTSTRAP_ADMIN_PASSWORD` | Keycloak | `admin` / (secret) | Chỉ để vào trang quản trị |
| `DXLAB_PORTAL_CLIENT_SECRET` | Keycloak (realm import), portal | (secret) | Secret của client `dxlab-portal` |
| `DXLAB_DEMO_PASSWORD` | Keycloak (realm import) | (secret) | Mật khẩu chung của tài khoản demo, chỉ dùng cho demo |
| `DXLAB_DEMO_OTP_SECRET` | Keycloak (realm import), script demo | (secret) | Khóa OTP chung nạp sẵn cho tài khoản demo phải xác thực hai bước, chỉ dùng cho demo |
| `DXLAB_PORTAL_SESSION_SECRET` | portal | (secret) | Ký cookie phiên |
| `DXLAB_LOG_LEVEL` | core, portal | `INFO` | |
| `DXLAB_EMBEDDING_MODEL` | core | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Thiếu mô hình thì `/api/search` chỉ dùng FTS |

Biến compose tự đặt cho từng tiến trình (không ghi trong `.env`):

| Biến | Tiến trình | Giá trị trong compose | Chạy ngoài compose |
|---|---|---|---|
| `DXLAB_DATABASE_URL` | core | `postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}` | Bắt buộc tự đặt |
| `DXLAB_OIDC_ISSUER` | core, portal, CLI, MCP | `${DXLAB_KEYCLOAK_PUBLIC_URL}/realms/dxlab` | Mặc định `http://localhost:8180/realms/dxlab` |
| `DXLAB_OIDC_INTERNAL_URL` | core, portal | `http://keycloak:8080/realms/dxlab` | Không đặt thì dùng `DXLAB_OIDC_ISSUER` |
| `DXLAB_OIDC_AUDIENCE` | core | `dxlab-core` | Mặc định `dxlab-core` |
| `DXLAB_PORTAL_CLIENT_ID` | portal | `dxlab-portal` | Mặc định `dxlab-portal` |
| `DXLAB_CLI_CLIENT_ID` | CLI, MCP | — | Mặc định `dxlab-cli` |
| `DXLAB_API_URL` | portal, CLI, MCP | `http://apisix:9080/api` (portal) | Mặc định `http://localhost:9080/api` |
| `DXLAB_DOCUMENTS_DIR` | core | `/data/documents` (volume `core-data`) | Bắt buộc tự đặt |
| `DXLAB_SEARCH_INDEX_DIR` | core | `/data/search` (volume `core-data`) | Bắt buộc tự đặt |
| `DXLAB_MODEL_CACHE_DIR` | core | `/models` (volume `models`) | Không đặt thì chỉ dùng FTS |
| `DXLAB_TOKEN_FILE` | CLI, MCP | — | Mặc định `~/.config/dxlab/token.json` |

Volume: `pgdata` (PostgreSQL), `keycloak-data`, `core-data` (tài liệu tải lên, chỉ mục zvec), `models` (cache mô hình
embedding, nạp bằng `scripts/download-models.sh` để chạy offline).

## 6. Core API

OpenAPI do FastAPI sinh là mô tả chính thức; bảng dưới chỉ để biết nhóm tài nguyên nào thuộc task nào.

| Đường dẫn | Việc | Task |
|---|---|---|
| `/api/health` | Trạng thái core và kết nối database; không cần token | CORE-01 |
| `/api/me` | Người đang gọi: tên, đơn vị, vai trò tách từ token | CORE-02 |
| `/api/definitions` | Nạp gói ứng dụng, kiểm tra, phiên bản, duyệt áp dụng | CORE-03 |
| `/api/workflows` | Tạo và xem một lượt chạy quy trình (ví dụ một phiếu báo hỏng); trạng thái = id bước BPMN | CORE-04a |
| `/api/tasks` | Hộp việc theo vai trò và phạm vi; hoàn thành một bước | CORE-04b |
| `/api/audit` | Lịch sử: ai làm gì, lúc nào, theo căn cứ nào | CORE-04b, CORE-05 |
| `/api/records`, `/api/documents` | Danh mục theo JSON Schema của ứng dụng; tài liệu, báo giá; provenance | CORE-06 |
| `/api/stats` | Số liệu tổng hợp cho dashboard, không tên người | CORE-07 |
| `/api/search` | Tìm kiếm hybrid FTS + zvec, có trích dẫn, lọc theo quyền xem | CORE-08 |
| `/api/delegations` | Ủy quyền có thời hạn (TUQ.) | CORE-05b |

Core chạy migration Alembic khi khởi động. Chỉ core có quyền vào database; dữ liệu mẫu nạp qua API, không ghi thẳng
vào bảng.

## 7. Gói ứng dụng (Tầng 3)

Cấu trúc dùng chung cho Spiff Editor (công cụ soạn) và core (nơi nạp):

```text
apps/
  process_group.json          nhóm "Ứng dụng DX-Lab" cho Spiff Editor
  <app>/                      tên thư mục = mã ứng dụng (app_id): chữ thường, số, gạch ngang
    process_model.json        display_name, primary_file_name, primary_process_id
    <app>.bpmn                quy trình chính: pool + lane
    <tên>.dmn                 bảng luật
    <bước>-schema.json        form của bước (JSON Schema)
    <bước>-uischema.json      bố cục form
    docs/                     hướng dẫn sửa chữa, SOP (Markdown)
    eval/                     bộ đánh giá luật và tìm kiếm
```

Quy ước bên trong tệp (dạng Spiff, để editor giữ nguyên khi lưu):

| Chỗ | Quy ước |
|---|---|
| User task | Bắt buộc nằm trong một lane; tên lane = khóa vai trò ở [`AUTHZ.md`](AUTHZ.md) mục 3 (`reporter`, `technician`, `lab_manager`, `approver`…) |
| Form của user task | `spiffworkflow:property` `formJsonSchemaFilename` và `formUiSchemaFilename`, trỏ tới tệp có trong gói |
| Không kiêm nhiệm | `spiffworkflow:property name="dxlabExcludeActorsOf" value="<id bước>,<id bước>"` |
| Business rule task | `spiffworkflow:calledDecisionId` trỏ tới một bảng luật có trong gói |
| Điều kiện ở gateway | Chỉ so sánh, `and`/`or`/`not`, tên biến, hằng số |
| Trường dữ liệu cá nhân | `"x-personal-data": true` trên thuộc tính trong `*-schema.json` |
| Con số nghiệp vụ (hạn mức, SLA, ngưỡng) | Chỉ nằm trong `.dmn`; BPMN đọc kết quả của bảng luật |
| Trạng thái hiển thị | Id của bước BPMN đang chờ, hoặc id của điểm kết thúc |

Validator của core (dùng chung cho `/api/definitions` và `dxlab validate`) từ chối gói có `scriptTask`, pre/post
script, điều kiện ngoài dạng trên, user task không có lane hay lane không phải vai trò đã biết, form tham chiếu không
có trong gói, bảng luật mới đổi tên cột kết quả mà quy trình đang đọc. Quyền nạp theo loại tệp ở
[`AUTHZ.md`](AUTHZ.md) mục 4.

Spiff Editor chỉ là công cụ soạn chạy trên máy người thiết kế quy trình (`tools/spiff-editor/`, chỉ bind
`127.0.0.1`), không thuộc compose sản phẩm và không nói chuyện với core. Đường từ tệp tới core duy nhất là
`dxlab publish`.

## 8. Thư viện, image, mô hình được phép

Thêm bất kỳ thứ gì ngoài bảng này: gắn nhãn `needs-mentor` và chờ. Khi được duyệt, ghi tên, phiên bản, giấy phép,
nguồn vào `docs/DEPENDENCIES.md` trong cùng PR. Gói pre-1.0 ghim `==`; gói khác ghi `>=` và để `uv.lock` ghim bản cụ thể.

Gói Python:

| Gói | Giấy phép | Dùng ở | Ràng buộc |
|---|---|---|---|
| `fastapi`, `uvicorn` | MIT, BSD-3-Clause | core, portal | |
| `pydantic-settings` | MIT | core, portal | Đọc biến môi trường |
| `sqlalchemy`, `alembic` | MIT | core | |
| `psycopg[binary]` | LGPL-3.0-only | core | Dùng nguyên bản, không sửa |
| `SpiffWorkflow` | LGPL-3.0 | core | `>=3.2`; dùng nguyên bản, không sửa |
| `jsonschema` | MIT | core | |
| `pyjwt[crypto]` | MIT | core | Kiểm JWT bằng `PyJWKClient` |
| `python-multipart` | Apache-2.0 | core | Nhận tệp tải lên |
| `httpx` | BSD-3-Clause | core (CLI), portal, MCP | |
| `zvec` | Apache-2.0 | core | `==0.8.0` (CORE-08) |
| `fastembed` | Apache-2.0 | core | CORE-08 |
| `prefab-ui` | Apache-2.0 | portal | `==0.21.1`, dùng renderer đóng gói sẵn |
| `authlib`, `itsdangerous` | BSD-3-Clause | portal | BFF đăng nhập OIDC, cookie phiên |
| `fastmcp` | Apache-2.0 | MCP | INT-02 |
| `pytest` | MIT | dev | |

Image container:

| Image | Giấy phép | Dùng ở |
|---|---|---|
| `postgres:17.11-alpine` | PostgreSQL License | compose sản phẩm |
| `quay.io/keycloak/keycloak:26.8.1` | Apache-2.0 | compose sản phẩm |
| `apache/apisix:3.19.0-debian` | Apache-2.0 | compose sản phẩm |
| `python:3.12-slim-bookworm` | PSF-2.0 (Python), giấy phép gói Debian | image nền của core, portal |
| `ghcr.io/astral-sh/uv` (tag phiên bản cụ thể) | Apache-2.0 / MIT | chỉ ở bước build của Dockerfile |
| `ghcr.io/sartography/spiffworkflow-backend`, `-frontend`, `connector-proxy-demo` | LGPL-2.1 | chỉ `tools/spiff-editor/`, không phân phối kèm |

Mô hình: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (Apache-2.0) chạy qua fastembed; không commit
tệp mô hình vào repo.

Công cụ CI và phát hành: `actions/checkout`, `astral-sh/setup-uv`, `fsfe/reuse-action`, gitleaks, syft. Action bên thứ
ba ghim theo commit SHA.

**Không dùng:** bpmn-js, dmn-js (giấy phép không phải OSI); n8n, Directus, Open WebUI (không phải giấy phép OSI);
bước build Node.js cho portal; Redis, message broker, MinIO, Grafana, Prometheus; LLM hay Ollama trong compose sản phẩm.
