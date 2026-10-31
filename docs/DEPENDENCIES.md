<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Danh mục thành phần phụ thuộc (Dependencies) — DX-Lab

Tài liệu này là bảng kê khai chi tiết các thành phần phần mềm bên thứ ba (Software Bill of Materials - SBOM) của dự án **DX-Lab**, phục vụ đánh giá tính minh bạch và tuân thủ nguồn mở theo tiêu chí PoF của cuộc thi Olympic Tin học Sinh viên (khối Phần mềm nguồn mở OLP 2026, chủ đề DX-OS Open-Core).

## 1. Nguyên tắc tuân thủ nguồn mở (OSS Compliance)

- **100% Giấy phép nguồn mở được OSI phê duyệt:** Mọi thành phần phụ thuộc (trực tiếp và gián tiếp) đều sử dụng giấy phép nguồn mở chuẩn quốc tế (Apache-2.0, MIT, BSD, LGPL-3.0, PostgreSQL License, PSF-2.0...).
- **Không nhúng mã nguồn bên thứ ba thủ công:** Không commit thư mục `.venv/`, artifact build, thư viện copy tay. Các thư viện được quản lý tập trung và tải tự động qua chỉ mục công khai PyPI thông qua `uv.lock`.
- **Ghim phiên bản và mã băm bất biến:**
  - Container image được ghim bằng digest SHA-256 (`@sha256:...`) trong `deploy/compose.yaml` và các Dockerfile.
  - Các gói Python được cố định phiên bản và mã hash toàn vẹn trong `uv.lock`.
- **Minh bạch thành phần đóng gói sẵn (Bundling):** Mọi thành phần được nhúng sẵn trong thư viện đều được kê khai theo chuẩn Fedora.

---

## 2. Container Images (Compose & Dockerfile)

Toàn bộ image môi trường sản phẩm được ghim bằng digest bất biến tại `deploy/compose.yaml`, `core/Dockerfile` và `portal/Dockerfile`:

| Image | Phiên bản / Digest | Giấy phép | Nguồn cung cấp | Vai trò trong hệ thống |
|---|---|---|---|---|
| `postgres` | `17.11-alpine@sha256:266d3c257594e195b309ae9d1805e54c788f1d7b375f56bf6c367aac6c917e7b` | PostgreSQL License | [Docker Hub](https://hub.docker.com/_/postgres) | Hệ quản trị cơ sở dữ liệu chính: lưu trữ thực thể quy trình, task, danh mục, audit log và tìm kiếm toàn văn FTS |
| `keycloak` | `quay.io/keycloak/keycloak:26.8.1@sha256:a78d6b79572168cb25886b80a8b5b8d4ed4390743e3eecb810538683e209dd6b` | Apache-2.0 | [Quay.io](https://quay.io/repository/keycloak/keycloak) | Máy chủ Identity Provider (IdP): quản lý xác thực tập trung SSO, OIDC PKCE, Device Authorization Flow và cấp phát JWT |
| `apisix` | `apache/apisix:3.19.0-debian@sha256:9a7e45dc943fbf10ec916d1232bae4cda9302ae28a4696cfb83c2da01d261141` | Apache-2.0 | [Docker Hub](https://hub.docker.com/r/apache/apisix) | API Gateway duy nhất tiếp nhận request từ bên ngoài vào Core; kiểm tra JWT, rate-limit, gắn `X-Request-Id` |
| `python` (base) | `python:3.12-slim-bookworm@sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337` | PSF-2.0 | [Docker Hub](https://hub.docker.com/_/python) | Image nền chạy ứng dụng Core API (`core/Dockerfile`) và Web Portal (`portal/Dockerfile`) |
| `uv` (builder) | `ghcr.io/astral-sh/uv:0.13.6@sha256:af22a52f5eafef3d78e551599d405c02df61919d18028f0cea8eda93bc9986d0` | Apache-2.0 / MIT | [GHCR](https://github.com/astral-sh/uv) | Trình quản lý gói và dựng môi trường ảo trong bước trung gian của Dockerfile |

---

## 3. Mô hình Trí tuệ nhân tạo (AI Models)

| Tên mô hình | Định dạng / Kích thước | Giấy phép | Nguồn cung cấp | Vai trò trong hệ thống |
|---|---|---|---|---|
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | ONNX (384 chiều, ~470 MB) | Apache-2.0 | [Hugging Face](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2) | Sinh vector embedding đa ngữ (bao gồm tiếng Việt) cho văn bản SOP và câu hỏi; nạp offline qua `scripts/download-models.sh` phục vụ `/api/search` qua `fastembed` |

---

## 4. Khai báo thành phần đóng gói sẵn (Bundling Declarations)

Theo tiêu chí I.5 (thể lệ OLP và quy ước Fedora Project):

| Tên thành phần | Khai báo chuẩn Fedora | Giấy phép | Nguồn gốc | Lý do đóng gói sẵn |
|---|---|---|---|---|
| Prefab Web Renderer | `bundled(prefab-renderer) = 0.21.1` | Apache-2.0 | [PrefectHQ/prefab](https://github.com/PrefectHQ/prefab) | Tệp giao diện JavaScript/CSS được đóng gói sẵn trong package wheel của `prefab-ui==0.21.1` để render giao diện Web Portal trực tiếp từ server, không yêu cầu cài đặt Node.js hay tải thêm tài nguyên CDN ngoài lúc chạy |

---

## 5. Danh mục toàn bộ các gói thư viện Python (từ `uv.lock`)

Danh sách đầy đủ 111 gói Python trong tệp `uv.lock` được sử dụng bởi các thành phần Core API, Web Portal, MCP Server, CLI và công cụ kiểm thử:

| Tên gói | Phiên bản | Giấy phép | Nguồn | Vai trò |
|---|---|---|---|---|
| `aiofile` | `3.12.3` | Apache-2.0 | [aiofile](https://pypi.org/project/aiofile/3.12.3/) | Core API / Workflow / Dữ liệu |
| `alembic` | `1.20.1` | MIT | [alembic](https://pypi.org/project/alembic/1.20.1/) | Core API / Workflow / Dữ liệu |
| `annotated-doc` | `0.0.5` | MIT | [annotated-doc](https://pypi.org/project/annotated-doc/0.0.5/) | Thư viện phụ thuộc gián tiếp |
| `annotated-types` | `0.8.0` | MIT | [annotated-types](https://pypi.org/project/annotated-types/0.8.0/) | Thư viện phụ thuộc gián tiếp |
| `anyio` | `4.15.1` | MIT | [anyio](https://pypi.org/project/anyio/4.15.1/) | Thư viện phụ thuộc gián tiếp |
| `attrs` | `26.1.0` | MIT | [attrs](https://pypi.org/project/attrs/26.1.0/) | Core API / Workflow / Dữ liệu |
| `authlib` | `1.9.1` | BSD-3-Clause | [authlib](https://pypi.org/project/authlib/1.9.1/) | Web Portal / BFF / Giao diện |
| `beartype` | `0.23.1` | MIT | [beartype](https://pypi.org/project/beartype/0.23.1/) | Thư viện phụ thuộc gián tiếp |
| `cachetools` | `7.2.7` | MIT | [cachetools](https://pypi.org/project/cachetools/7.2.7/) | Thư viện phụ thuộc gián tiếp |
| `caio` | `0.12.10` | Apache-2.0 | [caio](https://pypi.org/project/caio/0.12.10/) | Core API / Workflow / Dữ liệu |
| `certifi` | `2026.10.23` | MPL-2.0 | [certifi](https://pypi.org/project/certifi/2026.10.23/) | Thư viện phụ thuộc gián tiếp |
| `cffi` | `2.1.1` | MIT-0 | [cffi](https://pypi.org/project/cffi/2.1.1/) | Core API / Workflow / Dữ liệu |
| `charset-normalizer` | `3.5.2` | MIT | [charset-normalizer](https://pypi.org/project/charset-normalizer/3.5.2/) | Thư viện phụ thuộc gián tiếp |
| `click` | `8.5.0` | BSD-3-Clause | [click](https://pypi.org/project/click/8.5.0/) | Thư viện phụ thuộc gián tiếp |
| `colorama` | `0.4.6` | BSD-3-Clause | [colorama](https://pypi.org/project/colorama/0.4.6/) | Thư viện phụ thuộc gián tiếp |
| `cryptography` | `50.0.2` | Apache-2.0 OR BSD-3-Clause | [cryptography](https://pypi.org/project/cryptography/50.0.2/) | Core API / Workflow / Dữ liệu |
| `cyclopts` | `5.3.1` | Apache-2.0 | [cyclopts](https://pypi.org/project/cyclopts/5.3.1/) | MCP Server / Trợ lý AI |
| `dnspython` | `2.9.1` | ISC | [dnspython](https://pypi.org/project/dnspython/2.9.1/) | Thư viện phụ thuộc gián tiếp |
| `docstring-parser` | `0.18.0` | MIT | [docstring-parser](https://pypi.org/project/docstring-parser/0.18.0/) | MCP Server / Trợ lý AI |
| `dx-lab` | `0.2.0` | Apache-2.0 | [dx-lab](https://github.com/HaUI-NPC/dx-lab) | Thư viện phụ thuộc gián tiếp |
| `dxlab-core` | `0.2.0` | Apache-2.0 | [dxlab-core](https://github.com/HaUI-NPC/dx-lab) | Core API / Workflow / Dữ liệu |
| `dxlab-mcp` | `0.2.0` | Apache-2.0 | [dxlab-mcp](https://github.com/HaUI-NPC/dx-lab) | MCP Server / Trợ lý AI |
| `dxlab-portal` | `0.2.0` | Apache-2.0 | [dxlab-portal](https://github.com/HaUI-NPC/dx-lab) | Web Portal / BFF / Giao diện |
| `email-validator` | `2.3.0` | Unlicense | [email-validator](https://pypi.org/project/email-validator/2.3.0/) | Thư viện phụ thuộc gián tiếp |
| `exceptiongroup` | `1.3.1` | MIT | [exceptiongroup](https://pypi.org/project/exceptiongroup/1.3.1/) | Kiểm thử / Phát triển |
| `fastapi` | `0.162.0` | MIT | [fastapi](https://pypi.org/project/fastapi/0.162.0/) | Core API / Workflow / Dữ liệu |
| `fastembed` | `0.9.1` | Apache-2.0 | [fastembed](https://pypi.org/project/fastembed/0.9.1/) | Core API / Workflow / Dữ liệu |
| `fastmcp` | `3.4.11` | Apache-2.0 | [fastmcp](https://pypi.org/project/fastmcp/3.4.11/) | MCP Server / Trợ lý AI |
| `fastmcp-slim` | `3.4.11` | Apache-2.0 | [fastmcp-slim](https://pypi.org/project/fastmcp-slim/3.4.11/) | MCP Server / Trợ lý AI |
| `filelock` | `4.2.4` | MIT | [filelock](https://pypi.org/project/filelock/4.2.4/) | Thư viện phụ thuộc gián tiếp |
| `flatbuffers` | `25.12.19` | Apache-2.0 | [flatbuffers](https://pypi.org/project/flatbuffers/25.12.19/) | Thư viện phụ thuộc gián tiếp |
| `fsspec` | `2026.9.0` | BSD-3-Clause | [fsspec](https://pypi.org/project/fsspec/2026.9.0/) | Thư viện phụ thuộc gián tiếp |
| `griffelib` | `2.4.1` | ISC | [griffelib](https://pypi.org/project/griffelib/2.4.1/) | Thư viện phụ thuộc gián tiếp |
| `h11` | `0.16.0` | MIT | [h11](https://pypi.org/project/h11/0.16.0/) | Thư viện phụ thuộc gián tiếp |
| `hf-xet` | `1.7.1` | Apache-2.0 | [hf-xet](https://pypi.org/project/hf-xet/1.7.1/) | Thư viện phụ thuộc gián tiếp |
| `httpcore` | `1.0.9` | BSD-3-Clause | [httpcore](https://pypi.org/project/httpcore/1.0.9/) | Thư viện phụ thuộc gián tiếp |
| `httpx` | `0.28.1` | BSD-3-Clause | [httpx](https://pypi.org/project/httpx/0.28.1/) | Thư viện phụ thuộc gián tiếp |
| `httpx-sse` | `0.4.3` | MIT | [httpx-sse](https://pypi.org/project/httpx-sse/0.4.3/) | MCP Server / Trợ lý AI |
| `huggingface-hub` | `1.33.0` | Apache-2.0 | [huggingface-hub](https://pypi.org/project/huggingface-hub/1.33.0/) | Core API / Workflow / Dữ liệu |
| `idna` | `3.20` | BSD-3-Clause | [idna](https://pypi.org/project/idna/3.20/) | Thư viện phụ thuộc gián tiếp |
| `iniconfig` | `2.3.1` | MIT | [iniconfig](https://pypi.org/project/iniconfig/2.3.1/) | Kiểm thử / Phát triển |
| `itsdangerous` | `2.2.0` | BSD-3-Clause | [itsdangerous](https://pypi.org/project/itsdangerous/2.2.0/) | Web Portal / BFF / Giao diện |
| `jaraco-classes` | `3.4.0` | MIT | [jaraco-classes](https://pypi.org/project/jaraco-classes/3.4.0/) | Thư viện phụ thuộc gián tiếp |
| `jaraco-context` | `6.1.2` | MIT | [jaraco-context](https://pypi.org/project/jaraco-context/6.1.2/) | Thư viện phụ thuộc gián tiếp |
| `jaraco-functools` | `4.6.0` | MIT | [jaraco-functools](https://pypi.org/project/jaraco-functools/4.6.0/) | Thư viện phụ thuộc gián tiếp |
| `jeepney` | `0.9.0` | MIT | [jeepney](https://pypi.org/project/jeepney/0.9.0/) | Thư viện phụ thuộc gián tiếp |
| `joserfc` | `1.7.7` | BSD-3-Clause | [joserfc](https://pypi.org/project/joserfc/1.7.7/) | Web Portal / BFF / Giao diện |
| `jsonref` | `1.1.0` | MIT | [jsonref](https://pypi.org/project/jsonref/1.1.0/) | Thư viện phụ thuộc gián tiếp |
| `jsonschema` | `4.26.0` | MIT | [jsonschema](https://pypi.org/project/jsonschema/4.26.0/) | Core API / Workflow / Dữ liệu |
| `jsonschema-path` | `0.5.0` | Apache-2.0 | [jsonschema-path](https://pypi.org/project/jsonschema-path/0.5.0/) | Thư viện phụ thuộc gián tiếp |
| `jsonschema-specifications` | `2025.9.1` | MIT | [jsonschema-specifications](https://pypi.org/project/jsonschema-specifications/2025.9.1/) | Thư viện phụ thuộc gián tiếp |
| `keyring` | `25.7.0` | MIT | [keyring](https://pypi.org/project/keyring/25.7.0/) | Thư viện phụ thuộc gián tiếp |
| `loguru` | `0.7.3` | MIT | [loguru](https://pypi.org/project/loguru/0.7.3/) | Thư viện phụ thuộc gián tiếp |
| `lxml` | `6.1.3` | BSD-3-Clause | [lxml](https://pypi.org/project/lxml/6.1.3/) | Core API / Workflow / Dữ liệu |
| `mako` | `1.4.3` | MIT | [mako](https://pypi.org/project/mako/1.4.3/) | Core API / Workflow / Dữ liệu |
| `markdown-it-py` | `4.2.0` | MIT | [markdown-it-py](https://pypi.org/project/markdown-it-py/4.2.0/) | Thư viện phụ thuộc gián tiếp |
| `markupsafe` | `3.0.4` | BSD-3-Clause | [markupsafe](https://pypi.org/project/markupsafe/3.0.4/) | Thư viện phụ thuộc gián tiếp |
| `mcp` | `1.30.0` | MIT | [mcp](https://pypi.org/project/mcp/1.30.0/) | MCP Server / Trợ lý AI |
| `mdurl` | `0.1.2` | MIT | [mdurl](https://pypi.org/project/mdurl/0.1.2/) | Thư viện phụ thuộc gián tiếp |
| `mmh3` | `5.3.1` | MIT | [mmh3](https://pypi.org/project/mmh3/5.3.1/) | Thư viện phụ thuộc gián tiếp |
| `more-itertools` | `11.2.1` | MIT | [more-itertools](https://pypi.org/project/more-itertools/11.2.1/) | Thư viện phụ thuộc gián tiếp |
| `numpy` | `2.5.4` | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | [numpy](https://pypi.org/project/numpy/2.5.4/) | Core API / Workflow / Dữ liệu |
| `onnxruntime` | `1.31.1` | MIT | [onnxruntime](https://pypi.org/project/onnxruntime/1.31.1/) | Core API / Workflow / Dữ liệu |
| `openapi-pydantic` | `0.6.0` | MIT | [openapi-pydantic](https://pypi.org/project/openapi-pydantic/0.6.0/) | Thư viện phụ thuộc gián tiếp |
| `opentelemetry-api` | `1.45.1` | Apache-2.0 | [opentelemetry-api](https://pypi.org/project/opentelemetry-api/1.45.1/) | Thư viện phụ thuộc gián tiếp |
| `packaging` | `26.3` | Apache-2.0 OR BSD-2-Clause | [packaging](https://pypi.org/project/packaging/26.3/) | Kiểm thử / Phát triển |
| `pathable` | `0.6.0` | Apache-2.0 | [pathable](https://pypi.org/project/pathable/0.6.0/) | Thư viện phụ thuộc gián tiếp |
| `pillow` | `13.0.0` | MIT-CMU | [pillow](https://pypi.org/project/pillow/13.0.0/) | Thư viện phụ thuộc gián tiếp |
| `platformdirs` | `4.14.0` | MIT | [platformdirs](https://pypi.org/project/platformdirs/4.14.0/) | Thư viện phụ thuộc gián tiếp |
| `pluggy` | `1.7.0` | MIT | [pluggy](https://pypi.org/project/pluggy/1.7.0/) | Kiểm thử / Phát triển |
| `prefab-ui` | `0.21.1` | Apache-2.0 | [prefab-ui](https://pypi.org/project/prefab-ui/0.21.1/) | Web Portal / BFF / Giao diện |
| `protobuf` | `7.36.2` | BSD-3-Clause | [protobuf](https://pypi.org/project/protobuf/7.36.2/) | Thư viện phụ thuộc gián tiếp |
| `psycopg` | `3.3.6` | LGPL-3.0-only | [psycopg](https://pypi.org/project/psycopg/3.3.6/) | Core API / Workflow / Dữ liệu |
| `psycopg-binary` | `3.3.6` | LGPL-3.0-only | [psycopg-binary](https://pypi.org/project/psycopg-binary/3.3.6/) | Core API / Workflow / Dữ liệu |
| `py-key-value-aio` | `0.4.6` | Apache-2.0 | [py-key-value-aio](https://pypi.org/project/py-key-value-aio/0.4.6/) | Thư viện phụ thuộc gián tiếp |
| `py-rust-stemmers` | `0.1.8` | OSI-Approved | [py-rust-stemmers](https://pypi.org/project/py-rust-stemmers/0.1.8/) | Thư viện phụ thuộc gián tiếp |
| `pycparser` | `3.12` | BSD-3-Clause | [pycparser](https://pypi.org/project/pycparser/3.12/) | Core API / Workflow / Dữ liệu |
| `pydantic` | `2.14.1` | MIT | [pydantic](https://pypi.org/project/pydantic/2.14.1/) | Core API / Workflow / Dữ liệu |
| `pydantic-core` | `2.50.1` | MIT | [pydantic-core](https://pypi.org/project/pydantic-core/2.50.1/) | Core API / Workflow / Dữ liệu |
| `pydantic-settings` | `2.16.2` | MIT | [pydantic-settings](https://pypi.org/project/pydantic-settings/2.16.2/) | Core API / Workflow / Dữ liệu |
| `pygments` | `2.21.0` | BSD-2-Clause | [pygments](https://pypi.org/project/pygments/2.21.0/) | Thư viện phụ thuộc gián tiếp |
| `pyjwt` | `2.15.1` | MIT | [pyjwt](https://pypi.org/project/pyjwt/2.15.1/) | Core API / Workflow / Dữ liệu |
| `pyperclip` | `1.11.0` | BSD-3-Clause | [pyperclip](https://pypi.org/project/pyperclip/1.11.0/) | Thư viện phụ thuộc gián tiếp |
| `pytest` | `9.1.1` | MIT | [pytest](https://pypi.org/project/pytest/9.1.1/) | Kiểm thử / Phát triển |
| `python-dotenv` | `1.2.4` | BSD-3-Clause | [python-dotenv](https://pypi.org/project/python-dotenv/1.2.4/) | Thư viện phụ thuộc gián tiếp |
| `python-multipart` | `0.0.32` | Apache-2.0 | [python-multipart](https://pypi.org/project/python-multipart/0.0.32/) | Core API / Workflow / Dữ liệu |
| `pywin32` | `312` | PSF-2.0 | [pywin32](https://pypi.org/project/pywin32/312/) | Thư viện phụ thuộc gián tiếp |
| `pywin32-ctypes` | `0.2.3` | BSD-3-Clause | [pywin32-ctypes](https://pypi.org/project/pywin32-ctypes/0.2.3/) | Thư viện phụ thuộc gián tiếp |
| `pyyaml` | `6.0.3` | MIT | [pyyaml](https://pypi.org/project/pyyaml/6.0.3/) | Thư viện phụ thuộc gián tiếp |
| `referencing` | `0.37.0` | MIT | [referencing](https://pypi.org/project/referencing/0.37.0/) | Core API / Workflow / Dữ liệu |
| `requests` | `2.34.2` | Apache-2.0 | [requests](https://pypi.org/project/requests/2.34.2/) | Thư viện phụ thuộc gián tiếp |
| `rich` | `15.0.0` | MIT | [rich](https://pypi.org/project/rich/15.0.0/) | Thư viện phụ thuộc gián tiếp |
| `rich-rst` | `2.2.0` | MIT | [rich-rst](https://pypi.org/project/rich-rst/2.2.0/) | Thư viện phụ thuộc gián tiếp |
| `rpds-py` | `2026.9.1` | MIT | [rpds-py](https://pypi.org/project/rpds-py/2026.9.1/) | Core API / Workflow / Dữ liệu |
| `secretstorage` | `3.5.0` | BSD-3-Clause | [secretstorage](https://pypi.org/project/secretstorage/3.5.0/) | Thư viện phụ thuộc gián tiếp |
| `spiffworkflow` | `3.2.0` | LGPL-3.0-only | [spiffworkflow](https://pypi.org/project/spiffworkflow/3.2.0/) | Core API / Workflow / Dữ liệu |
| `sqlalchemy` | `2.1.6` | MIT | [sqlalchemy](https://pypi.org/project/sqlalchemy/2.1.6/) | Core API / Workflow / Dữ liệu |
| `sse-starlette` | `3.6.0` | BSD-3-Clause | [sse-starlette](https://pypi.org/project/sse-starlette/3.6.0/) | MCP Server / Trợ lý AI |
| `starlette` | `1.10.0` | BSD-3-Clause | [starlette](https://pypi.org/project/starlette/1.10.0/) | Core API / Workflow / Dữ liệu |
| `tokenizers` | `0.23.3` | Apache-2.0 | [tokenizers](https://pypi.org/project/tokenizers/0.23.3/) | Core API / Workflow / Dữ liệu |
| `tqdm` | `4.70.1` | MIT | [tqdm](https://pypi.org/project/tqdm/4.70.1/) | Thư viện phụ thuộc gián tiếp |
| `typing-extensions` | `4.16.0` | PSF-2.0 | [typing-extensions](https://pypi.org/project/typing-extensions/4.16.0/) | Thư viện phụ thuộc gián tiếp |
| `typing-inspection` | `0.4.4` | MIT | [typing-inspection](https://pypi.org/project/typing-inspection/0.4.4/) | Thư viện phụ thuộc gián tiếp |
| `tzdata` | `2026.5` | Apache-2.0 | [tzdata](https://pypi.org/project/tzdata/2026.5/) | Thư viện phụ thuộc gián tiếp |
| `uncalled-for` | `0.4.1` | MIT | [uncalled-for](https://pypi.org/project/uncalled-for/0.4.1/) | Thư viện phụ thuộc gián tiếp |
| `urllib3` | `2.8.0` | MIT | [urllib3](https://pypi.org/project/urllib3/2.8.0/) | Thư viện phụ thuộc gián tiếp |
| `uvicorn` | `0.54.0` | BSD-3-Clause | [uvicorn](https://pypi.org/project/uvicorn/0.54.0/) | Core API / Workflow / Dữ liệu |
| `watchfiles` | `1.3.0` | MIT | [watchfiles](https://pypi.org/project/watchfiles/1.3.0/) | Thư viện phụ thuộc gián tiếp |
| `websockets` | `17.3` | BSD-3-Clause | [websockets](https://pypi.org/project/websockets/17.3/) | MCP Server / Trợ lý AI |
| `win32-setctime` | `1.2.1` | MIT | [win32-setctime](https://pypi.org/project/win32-setctime/1.2.1/) | Thư viện phụ thuộc gián tiếp |
| `zvec` | `0.8.0` | Apache-2.0 | [zvec](https://pypi.org/project/zvec/0.8.0/) | Core API / Workflow / Dữ liệu |

