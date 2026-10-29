<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Hướng dẫn đóng góp

Cảm ơn bạn quan tâm tới DX-Lab. Tài liệu này mô tả quy trình đóng góp và các
yêu cầu bắt buộc để một thay đổi được chấp nhận.

## Kênh trao đổi

| Mục đích | Kênh |
|---|---|
| Báo lỗi, đề xuất tính năng | Issue tracker công khai của repo |
| Thảo luận thiết kế trước khi code | Mở issue mô tả vấn đề trước, đừng gửi thẳng PR lớn |
| Báo lỗ hổng bảo mật | Theo [`SECURITY.md`](SECURITY.md), **không** mở issue công khai |

## Chuẩn bị môi trường

```bash
git clone https://github.com/HaUI-NPC/dx-lab.git
cd dx-lab
uv sync --all-packages
```

Repo là một [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/) gồm hai gói:

| Thư mục | Gói | Tầng | Ràng buộc |
|---|---|---|---|
| `core/` | `dxlab-core` | Tầng 1 – Open-Core headless | Không phục vụ UI; không import `dxlab_portal` hay thư viện UI |
| `portal/` | `dxlab-portal` | Tầng 2/3 – H-P-D-I và ứng dụng | Không import `dxlab_core`; chỉ gọi Core qua API Gateway |

Module nghiệp vụ mới (một quy trình, một ứng dụng) phải dùng dịch vụ sẵn có của Core.
Chỉ sửa `core/` khi cần một năng lực nền tảng dùng chung cho mọi ứng dụng.

## Quy trình gửi thay đổi

Mọi thay đổi vào `main` đều đi qua Pull Request, kể cả của maintainer. Không ai đẩy thẳng `main`.

1. Mỗi thay đổi gắn với một issue. Việc mới hoặc lỗi chưa có issue → mở issue trước. Tiến độ theo dõi trên
   [bảng việc](https://github.com/orgs/HaUI-NPC/projects/1): bắt đầu làm thì chuyển thẻ sang *Đang làm*; chờ
   issue khác hoặc chờ quyết định thì chuyển *Bị chặn*, comment lý do và gắn nhãn `blocked` hoặc `needs-mentor`.
2. Tạo nhánh từ `main` mới nhất, đặt tên `<type>/<MÃ-VIỆC>-<mô-tả-ngắn>`, ví dụ `feat/CORE-03-definitions`,
   `fix/POR-02-loi-form`. `type` lấy theo [quy ước commit](#quy-ước-commit-message).
3. Chỉ sửa trong phạm vi issue. Thấy việc khác cần làm → mở issue mới, không gộp vào PR đang làm. Cần làm khác
   hợp đồng chung ([`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/AUTHZ.md`](docs/AUTHZ.md),
   [`.env.example`](.env.example), mục [Quy ước](#quy-ước)) → dừng, comment trên issue, gắn nhãn `needs-mentor`.
4. Chạy kiểm tra cục bộ (xem mục dưới) và bảo đảm tất cả đều pass.
5. Ghi một mục vào `CHANGELOG.md` phần `[Unreleased]` nếu thay đổi có ảnh hưởng tới người dùng.
6. Mở PR theo mẫu (tự hiện khi tạo PR): issue được đóng (`Closes #…`), thay đổi gì, **lệnh đã chạy để kiểm chứng
   và kết quả thật**, ảnh chụp nếu có giao diện. Mở ở dạng *draft*; CI xanh mới chuyển sang *ready for review* và
   chuyển thẻ sang *Chờ review*.
7. Cần ít nhất một review chấp thuận của người khác tác giả. **Chỉ maintainer chính được merge** vào `main`
   (xem [`MAINTAINERS.md`](MAINTAINERS.md)); dự án chỉ dùng kiểu gộp *rebase* để giữ nguyên từng commit.

## Yêu cầu bắt buộc với mỗi commit

### 1. Ký nhận DCO

Mọi commit phải có dòng `Signed-off-by`, xác nhận bạn có quyền hợp pháp đóng góp phần
mã đó theo [Developer Certificate of Origin 1.1](https://developercertificate.org/):

```bash
git commit -s -m "fix(core): từ chối nghiệm thu khi người làm là người đã sửa (CORE-04b)"
```

Lệnh `-s` tự thêm:

```text
Signed-off-by: Tên Của Bạn <email@example.com>
```

Đây là **khẳng định quyền đóng góp**, không phải chuyển nhượng bản quyền — dự án không
yêu cầu ký CLA. Bạn giữ bản quyền phần đóng góp của mình; phần đóng góp được cấp phép
theo Apache-2.0 như phần còn lại của mã nguồn.

Yêu cầu này theo control `OSPS-LE-01.01` của
[OpenSSF Security Baseline](https://baseline.openssf.org/versions/2025-02-25).

### 2. Khai báo giấy phép cho mọi tệp

Repo tuân thủ [REUSE 3.3](https://reuse.software/spec-3.3/). Mọi tệp mới đều phải có
thông tin bản quyền và giấy phép.

Tệp mã (có thể chứa comment) — đặt header ở đầu tệp:

```python
# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0
```

Tài liệu Markdown:

```markdown
<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->
```

Tệp không chứa được comment (JSON, ảnh, dữ liệu nhị phân): khai báo trong [`REUSE.toml`](REUSE.toml),
hoặc tạo tệp `.license` đi kèm.

Quy ước giấy phép:

| Loại tệp | `SPDX-License-Identifier` |
|---|---|
| Mã nguồn, script, cấu hình build | `Apache-2.0` |
| Tài liệu, README, changelog | `CC-BY-4.0` |
| Dữ liệu bên thứ ba | Giữ nguyên giấy phép gốc của nguồn |

Khi dùng giấy phép mới chưa có trong `LICENSES/`, thêm toàn văn giấy phép đó vào cùng PR.
Lấy bản chuẩn tại [SPDX license-list-data](https://github.com/spdx/license-list-data/tree/main/text).

### 3. Không đóng gói kèm mã bên thứ ba

Không commit `.venv/`, `node_modules/`, mã nguồn thư viện đã copy vào repo, hay bản
build sinh tự động. Khai báo phụ thuộc qua `pyproject.toml` của gói tương ứng để trình
quản lý gói tự tải.

Nếu một thư viện bắt buộc phải đóng gói kèm (upstream không hỗ trợ dùng thư viện hệ thống),
phải nêu rõ tên, phiên bản và lý do trong PR, đồng thời ghi vào bảng kê thành phần.
Không sửa mã nguồn của thư viện bên thứ ba rồi giữ im lặng: gửi patch lên upstream và
ghi lại patch đã áp dụng.

Dữ liệu và công cụ có điều khoản cấm phân phối lại tuyệt đối không được commit.

## Kiểm tra trước khi gửi PR

```bash
uvx reuse lint                     # mọi tệp phải có bản quyền + giấy phép
uv build --all-packages            # mọi gói build được từ mã nguồn
uv run --all-packages pytest       # khi gói có thư mục tests/
```

CI chạy `reuse lint`, build từng gói rồi cài vào môi trường sạch và import từ thư mục
nằm ngoài repo. PR có kiểm tra fail sẽ không được merge.

## Quy ước commit message

Dùng dạng `<type>(<scope>): <mô tả ngắn, thức mệnh lệnh> (<MÃ-VIỆC>)`. `MÃ-VIỆC` là mã trong tiêu đề issue,
ví dụ `CORE-03`; bỏ trống nếu thay đổi không thuộc việc nào đã lên kế hoạch.

Các `type` dùng trong dự án: `feat`, `fix`, `docs`, `refactor`, `test`, `build`, `ci`, `chore`.
`scope` là thư mục hoặc mảng bị ảnh hưởng: `core`, `portal`, `mcp`, `apps`, `deploy`, `docs`, `ci`.

```text
fix(core): từ chối nghiệm thu khi người làm là người đã sửa (CORE-04b)

Bước nghiệm thu khai báo `dxlabExcludeActorsOf = repair`; Core so người hoàn thành bước
với người đã làm bước sửa và trả 403 nếu trùng. Kiểm tra nằm ở Core nên mọi ứng dụng
tầng trên đều chịu cùng ràng buộc.

Signed-off-by: Tên Của Bạn <email@example.com>
```

## Quy ước

Phần này cùng [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) là hợp đồng chung của dự án; đổi nó bằng PR riêng do
maintainer chính duyệt.

### Cấu trúc thư mục

```text
apps/      Gói ứng dụng Tầng 3: BPMN, DMN, JSON Schema, hướng dẫn (docs/ARCHITECTURE.md mục 7)
core/      Gói dxlab-core: Core API headless và CLI dxlab (Tầng 1)
portal/    Gói dxlab-portal: giao diện H-P-D-I và BFF đăng nhập (Tầng 2)
mcp/       Gói dxlab-mcp: MCP server (Tầng 2)
deploy/    compose.yaml, keycloak/realm.json, apisix/ (cấu hình standalone)
data/      Dữ liệu mẫu do đội tạo; nguồn, giấy phép của từng tệp ghi ở DATA_SOURCES.yml (gốc repo)
scripts/   up.sh, seed.sh, reset.sh, demo-e2e.sh, download-models.sh
tools/     Công cụ phát triển, không thuộc sản phẩm (spiff-editor/)
docs/      Tài liệu
```

Bên trong `core/`, mỗi mảng nghiệp vụ là một thư mục con cùng khuôn; CORE-01 tạo khung và mảng `health` làm mẫu:

```text
core/src/dxlab_core/
  app.py         tạo ứng dụng FastAPI, gắn router và handler lỗi
  config.py      đọc biến môi trường DXLAB_*
  errors.py      ApiError và handler trả định dạng lỗi chung
  db/            engine, session, Base; migrations/ của Alembic
  auth/          xác thực JWT, Principal, dependency kiểm quyền (CORE-02)
  audit/         ghi audit dùng chung
  <mảng>/        health, definitions, workflows, tasks, records, documents, search, stats, delegations
    router.py    chỉ lo HTTP: nhận, kiểm đầu vào, gọi service, trả schema
    service.py   nghiệp vụ; không import FastAPI
    models.py    bảng SQLAlchemy của mảng
    schemas.py   model Pydantic vào / ra
  cli/           lệnh dxlab (CLI-01)
core/tests/      pytest, mỗi mảng một tệp test_<mảng>.py
```

`portal/src/dxlab_portal/` có `bff/` (đăng nhập, phiên, gọi API kèm token) và `pages/` (mỗi tab một module);
POR-01 chốt chi tiết, các task portal sau theo khung đó.

### Đặt tên API

- Mọi route của core nằm dưới `/api`. Tài nguyên là danh từ số nhiều, chữ thường, nhiều từ thì nối bằng gạch ngang:
  `/api/definitions`, `/api/workflows/{workflow_id}`.
- Hành động không phải đọc / tạo / sửa / xóa: `POST /api/<tài-nguyên>/{id}/<động-từ>`, ví dụ
  `/api/definitions/{definition_id}/activate`, `/api/tasks/{task_id}/complete`.
- Tham số và trường JSON dùng `snake_case`. Id do core tạo là UUID; khóa nghiệp vụ giữ nguyên (mã ứng dụng, khóa
  vai trò, đường dẫn đơn vị, id bước BPMN).
- Danh sách nhận `limit` (mặc định 50, tối đa 200) và `offset`, trả `{"items": [...], "total": <số>}`.
- Thời gian: ISO 8601, UTC, ví dụ `2026-10-29T08:30:00Z`. Portal hiển thị giờ Việt Nam dạng `29/10/2026 15:30`.
- Tiền: số nguyên, đơn vị đồng; không dùng số thực.
- Mỗi route khai báo `response_model` và `summary` tiếng Việt để Swagger UI đọc được.
- Mã thành công: `200` đọc và hành động, `201` tạo mới, `204` xóa.

### Định dạng lỗi

Mọi lỗi của core, kể cả lỗi kiểm tra đầu vào của FastAPI, trả cùng một dạng:

```json
{
  "error": {
    "code": "FORBIDDEN_SCOPE",
    "message": "Phiếu thuộc phòng ngoài phạm vi đơn vị của bạn.",
    "details": {"layer": 2},
    "request_id": "8d0b6c1e-4f5a-4a51-9a59-1c1f2f5e7a10"
  }
}
```

| HTTP | `code` | Khi nào |
|---|---|---|
| 401 | `UNAUTHENTICATED` | Thiếu token, token sai chữ ký, sai `iss` / `aud`, hết hạn |
| 403 | `FORBIDDEN_ROLE`, `FORBIDDEN_SCOPE`, `FORBIDDEN_AUTHORITY`, `FORBIDDEN_SOD`, `FORBIDDEN_PERSONAL_DATA` | Bị chặn ở lớp 1 … 5 của [`docs/AUTHZ.md`](docs/AUTHZ.md); `details.layer` ghi số lớp |
| 403 | `FORBIDDEN_ORIGIN` | Portal từ chối yêu cầu ghi từ origin khác |
| 404 | `NOT_FOUND` | Không có đối tượng |
| 409 | `CONFLICT` | Đối tượng đã đổi từ lúc đọc (khóa phiên bản), bước đã được người khác hoàn thành |
| 422 | `VALIDATION_FAILED` | Dữ liệu sai model hoặc sai JSON Schema; `details.errors` là danh sách `{"path", "message"}` |
| 422 | `DEFINITION_REJECTED` | Validator từ chối gói ứng dụng; `details.errors` là danh sách `{"file", "element", "message"}` |
| 429 | `RATE_LIMITED` | Vượt giới hạn tần suất; do APISIX trả |
| 500 | `INTERNAL` | Lỗi không lường trước; chi tiết chỉ nằm trong log, tra theo `request_id` |
| 502, 504 | `INTERNAL` | Portal không kết nối được Core hoặc hết thời gian chờ; không tiết lộ địa chỉ nội bộ |

Lỗi do APISIX tự trả trước khi tới core (401 thiếu / sai token, 429) có thân phản hồi của gateway, không theo dạng
trên: client dựa vào mã HTTP cho hai trường hợp này.

- Client dựa vào `code`, không dựa vào `message`. Thêm mã lỗi mới thì thêm dòng vào bảng này trong cùng PR.
- `message` là tiếng Việt có dấu, viết cho người dùng cuối; không chứa stack trace, câu SQL, token, dữ liệu cá nhân.
- `request_id` lấy từ header `X-Request-Id` do APISIX gắn; không có thì core tự tạo, và trả lại trong header phản hồi.

### Tiếng Việt và cách đặt tên

| Thứ | Viết bằng |
|---|---|
| Giao diện, `message` của lỗi, tài liệu, `summary` của API, comment và docstring, mô tả commit / PR / issue | Tiếng Việt có dấu |
| Tên module, hàm, biến, route, trường JSON, khóa vai trò, mã lỗi, id bước BPMN, biến DMN | Tiếng Anh, ASCII, `snake_case` (mã lỗi `UPPER_SNAKE`) |
| Tên tool MCP | Tiếng Việt không dấu, `snake_case` (ví dụ `bao_hong`), vì người dùng đọc trực tiếp |
| Log | Tiếng Anh ngắn, dạng `key=value`; không chứa token, secret, dữ liệu cá nhân |
| Tên tệp | ASCII: `snake_case` cho Python, `kebab-case` cho tài liệu và tệp của ứng dụng |

- Tên hiển thị của đơn vị, vai trò, bước quy trình không viết cứng trong mã; lấy từ Keycloak, BPMN, JSON Schema.
- Căn cứ có mã bắt đầu bằng `GĐ-` luôn hiện kèm chữ "(giả định)".
- Tệp mã hóa UTF-8, xuống dòng LF.

### Kiểm thử

Viết test cho hành vi mà người dùng quan sát được, khi một lỗi hợp lý sẽ làm test đó fail.
Không viết test chỉ để "có test": không kiểm tra giá trị mặc định, không so khớp chuỗi
nội bộ, không assert lại cách hiện thực.

Thay đổi hành vi nghiệp vụ phải kèm test tương ứng, và mô tả cách kiểm chứng trong PR.
