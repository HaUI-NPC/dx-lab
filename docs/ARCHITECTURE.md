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

### 3.1 Sơ đồ tổng quan luồng dịch vụ

Mọi tương tác giữa các tầng tuân thủ kiến trúc phân lớp nghiêm ngặt: client (Portal, CLI, MCP) gửi request kèm Bearer token của người dùng qua API Gateway (APISIX); APISIX xác thực sơ bộ và chuyển tiếp tới Core API; Core độc lập giải mã token, kiểm soát 5 lớp phân quyền, thực thi quy trình qua SpiffWorkflow và truy vấn dữ liệu/chỉ mục.

```mermaid
sequenceDiagram
  autonumber
  actor U as Người dùng / Kỹ thuật viên
  participant P as Portal (BFF)
  participant K as Keycloak
  participant G as APISIX Gateway
  participant C as Core API
  participant D as PostgreSQL
  participant Z as zvec (Chỉ mục vector)

  U->>P: Mở portal trên trình duyệt
  P->>K: Chuyển hướng đăng nhập (Authorization Code + PKCE)
  K-->>P: Code → Đổi lấy access_token qua kênh nội bộ
  Note over P: Token lưu ở server session, trình duyệt nhận cookie phiên httpOnly
  U->>P: Thao tác nghiệp vụ (báo hỏng, xử lý việc, tra cứu)
  P->>G: Gọi /api/... kèm header Authorization: Bearer (token người dùng)
  G->>G: Kiểm tra JWT (JWKS), rate limit, gắn X-Request-Id
  G->>C: Chuyển tiếp nguyên đường dẫn /api/...
  C->>C: Tự kiểm tra JWT, xác thực danh tính & 5 lớp phân quyền (AUTHZ)
  alt Đọc / Ghi nghiệp vụ hoặc quy trình
    C->>D: Đọc / ghi instance quy trình, task, records, audit
  else Tra cứu tri thức sửa chữa (RAG)
    C->>D: Tra cứu toàn văn (FTS PostgreSQL)
    C->>Z: Tra cứu độ tương đồng vector (cosine distance)
  end
  C-->>P: JSON (dữ liệu cá nhân đã được che theo quyền)
  P-->>U: Hiển thị giao diện người dùng tiếng Việt
```

### 3.2 Luồng người dùng qua Web Portal (BFF & OIDC PKCE)

Portal hoạt động theo mô hình BFF (Backend-for-Frontend): trình duyệt không giữ access token nhằm giảm thiểu rủi ro XSS.

```mermaid
sequenceDiagram
  autonumber
  actor B as Trình duyệt (Người dùng)
  participant P as Portal BFF (FastAPI)
  participant K as Keycloak (IdP)
  participant G as APISIX
  participant C as Core API

  B->>P: GET /login
  P->>B: 302 Redirect tới Keycloak (/auth?response_type=code&code_challenge=...)
  B->>K: Người dùng nhập thông tin đăng nhập (+ OTP nếu có)
  K-->>B: 302 Redirect về Portal (/auth/callback?code=...)
  B->>P: GET /auth/callback?code=...
  P->>K: POST /token (đổi code + code_verifier lấy access_token & id_token)
  K-->>P: access_token, refresh_token, id_token
  Note over P: Lưu token vào server-side session và sinh session_id ngẫu nhiên
  P-->>B: 302 Redirect về / kèm cookie session (httpOnly, SameSite=Lax)

  B->>P: Thao tác gửi biểu mẫu (POST /report hoặc hoàn thành task)
  P->>P: Đọc access_token từ session (tự làm mới nếu gần hết hạn)
  P->>G: POST /api/workflows/... (Authorization: Bearer user_token)
  G->>G: Xác thực chữ ký JWT bằng JWKS của Keycloak, kiểm tra hạn
  G->>C: Chuyển tiếp request sang Core
  C->>C: Kiểm tra schema form, thẩm quyền người gọi, ghi nhận DB
  C-->>P: Phản hồi kết quả JSON
  P-->>B: Render trang kết quả tiếng Việt
```

### 3.3 Luồng dòng lệnh (CLI `dxlab`) và Trợ lý MCP

Cả CLI và MCP đều sử dụng trực tiếp danh tính người dùng và tương tác với Core qua APISIX, không dùng tài khoản dịch vụ:

```mermaid
sequenceDiagram
  autonumber
  actor D as Cán bộ vận hành / LLM Client
  participant CLI as dxlab CLI / MCP Server
  participant K as Keycloak
  participant G as APISIX
  participant C as Core API

  Note over CLI,K: 1. Đăng nhập lưu token (chỉ làm một lần)
  CLI->>K: POST /auth/device (Device Flow) hoặc POST /token (Direct Grant cho demo)
  K-->>CLI: Cấp access_token & refresh_token
  CLI->>CLI: Lưu vào ~/.config/dxlab/token.json (phân quyền tệp 0600)

  Note over D,C: 2. Gọi lệnh nghiệp vụ hoặc nạp gói ứng dụng
  D->>CLI: dxlab publish apps/lab-repair (hoặc MCP: bao_hong())
  CLI->>CLI: Đọc access_token từ tệp token, kiểm tra hạn dùng
  opt Trường hợp MCP gọi thao tác ghi
    CLI->>D: Hỏi xác nhận (elicit confirmation) trước khi thực thi
    D-->>CLI: Đồng ý xác nhận
  end
  CLI->>G: POST /api/definitions/... (Authorization: Bearer user_token)
  G->>G: APISIX kiểm tra JWT, áp dụng rate-limit
  G->>C: Chuyển nguyên trạng tới Core API
  C->>C: Kiểm tra quyền quản trị viên / chuyên viên theo AUTHZ
  C-->>CLI: Trả về kết quả JSON (phiên bản mới, mã phiếu, ...)
  CLI-->>D: In kết quả ra terminal / Trả phản hồi cho LLM
```

### 3.4 Luồng thực thi quy trình BPMN & Đánh giá bảng luật DMN (SpiffWorkflow Runtime)

Core nhúng bộ máy SpiffWorkflow để thực thi quy trình mà không cần dịch vụ workflow ngoài. Trạng thái và biến quy trình được lưu bền vững trong PostgreSQL:

```mermaid
sequenceDiagram
  autonumber
  actor U as Người dùng (Người báo / Kỹ thuật viên)
  participant G as APISIX
  participant C as Core API
  participant SP as SpiffWorkflow Engine
  participant DB as PostgreSQL

  U->>G: POST /api/workflows (Tạo phiếu mới kèm dữ liệu form)
  G->>C: Chuyển tiếp request có Bearer token
  C->>C: Kiểm tra tính hợp lệ dữ liệu theo JSON Schema của form
  C->>DB: Đọc định nghĩa quy trình bản active (BPMN, DMN)
  C->>SP: Khởi tạo Workflow Instance (BpmnWorkflow)
  SP->>SP: Chạy qua Start Event tới Service / Business Rule Task

  Note over SP: Đánh giá luật tự động (DMN)
  SP->>SP: Chạy triage.dmn (xác định mức ưu tiên P1/P2/P3 và hạn SLA)
  SP->>SP: Chạy routing.dmn (xác định tech_unit và tech_role tiếp nhận)
  SP->>SP: Chạy authority.dmn (nếu có chi phí: xác định thẩm quyền duyệt)

  SP->>SP: Dừng tại User Task kế tiếp (ví dụ: pending_assessment)
  C->>DB: Ghi lưu Workflow state, tạo User Task mới trong bảng tasks
  C->>DB: Ghi sự kiện Audit Log (ai tạo, thời điểm, dữ liệu phiếu)
  C-->>G: Trả về thông tin instance và mã phiếu
  G-->>U: 201 Created (JSON)
```

### 3.5 Luồng tra cứu tri thức & Tìm kiếm ngữ nghĩa (RAG Hybrid)

Hệ thống kết hợp tìm kiếm toàn văn tiếng Việt (FTS qua PostgreSQL) và tìm kiếm ngữ nghĩa (vector qua zvec), kèm bộ lọc phân quyền xem tài liệu:

```mermaid
sequenceDiagram
  autonumber
  actor U as Người dùng (Portal / MCP)
  participant G as APISIX
  participant C as Core API
  participant DB as PostgreSQL
  participant Z as zvec Index

  U->>G: GET /api/search?q=máy+chiếu+báo+đèn+đỏ
  G->>C: Chuyển tiếp request
  C->>C: Giải mã token, lấy thông tin đơn vị và vai trò người dùng

  par Tra cứu toàn văn (FTS)
    C->>DB: SELECT documents qua to_tsvector('simple', dxlab_unaccent(:q))
    DB-->>C: Danh sách tài liệu khớp từ khóa + rank điểm số
  and Tra cứu vector (Semantic Embedding)
    C->>C: Sinh vector biểu diễn của câu hỏi qua mô hình cục bộ
    C->>Z: Query k-nearest vectors trong collection chunks (khoảng cách cosine)
    Z-->>C: Danh sách chunk_index và điểm khoảng cách
  end

  C->>C: Kết hợp điểm (Hybrid scoring), loại trùng lặp
  C->>DB: Lọc tài liệu theo quyền truy cập của người dùng (AUTHZ mục 7)
  C-->>G: 200 OK (Danh sách hướng dẫn SOP kèm trích dẫn văn bản nguồn và điểm số)
  G-->>U: Hiển thị kết quả tra cứu có dẫn chứng
```

### 3.6 Luật và ràng buộc kiến trúc của luồng gọi

1. **Mọi lời gọi tới core đi qua APISIX:** Cổng của core không bind ra máy chủ (chỉ bind trong mạng nội bộ Compose). APISIX là điểm vào duy nhất (`127.0.0.1:9080`).
2. **Chỉ dùng token của chính người dùng:** Không sử dụng tài khoản dịch vụ (service account) để gọi thay nghiệp vụ người dùng; seed dữ liệu cũng đăng nhập bằng tài khoản demo. Nhờ vậy portal, MCP và CLI bị giới hạn đúng quyền của người đang thao tác.
3. **APISIX chặn sớm, core quyết định độc lập (Defense-in-depth):** APISIX từ chối token sai hoặc thiếu chữ ký; Core vẫn tự kiểm tra chữ ký, `iss`, `aud`, `exp` qua JWKS và thực thi đầy đủ 5 lớp phân quyền (`docs/AUTHZ.md`). Core không tin cậy header do client hoặc gateway thêm vào, ngoại trừ `X-Request-Id` phục vụ tracing.
4. **Portal và MCP chỉ là tầng hiển thị:** Ẩn nút theo vai trò để tối ưu trải nghiệm, nhưng quyết định cho phép hay từ chối luôn do Core kiểm soát tại thời điểm gọi API.
5. **Độc quyền truy cập tài nguyên dữ liệu:** Chỉ duy nhất Core API có quyền đọc/ghi cơ sở dữ liệu PostgreSQL, volume tài liệu và thư mục chỉ mục vector `zvec`.

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
| `/api/health` | Trạng thái core, database, chỉ mục và cache mô hình; không cần token | CORE-01, CORE-08 |
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

`/api/health` trả `search_index: "ok" | "error"` và `embedding_model: "ok" | "missing"`. Thiếu cache mô hình
không làm Core dừng: tìm kiếm chuyển sang FTS; Core không tự tải mô hình khi xử lý yêu cầu.
`scripts/download-models.sh` là bước tải có chủ đích của người vận hành.

Danh mục dùng `GET/PUT /api/records/{app_id}/{record_type}/{key}`; khi duyệt một phiên bản ứng dụng, Core đăng ký
JSON Schema từ `records/<record_type>-record.json`. Bản ghi có `data`, `source`, `license`, `source_ref` và thông tin
người/thời điểm tạo, sửa. Ban CSVC và người thiết kế quy trình được ghi danh mục; người đã đăng nhập được đọc.

Tài liệu dùng `POST /api/documents` dạng multipart (`file`, `app_id`, `kind`, `title`, `source`, `license`;
`source_ref` và `workflow_id` tùy chọn), tối đa 20 MB/tệp; `GET /api/documents/{id}` đọc metadata và
`GET /api/documents/{id}/content` tải byte gốc. Tệp được lưu theo SHA-256, không dùng tên tải lên làm đường dẫn.
SOP/tài liệu chung do Ban CSVC hoặc người thiết kế quy trình nạp; báo giá cho phép kỹ thuật viên nạp thêm.
Tài liệu gắn phiếu và kết quả tìm kiếm phải qua kiểm quyền của người gọi, không dùng token quản trị.

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
    records/                  <record_type>-record.json: schema danh mục của ứng dụng
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
| Dữ liệu khởi tạo | `data_defaults` trong `process_model.json`; chỉ người được nạp quy trình thay đổi được, không lấy từ output do client gửi |
| Liên kết danh mục | `record_bindings` trong `process_model.json`: mỗi mục có `type`, `key_field`, `fields` (trường nguồn → trường runtime); `app_id` tùy chọn chỉ rõ danh mục dùng chung |

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
