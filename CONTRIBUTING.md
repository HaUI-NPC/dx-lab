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

1. Tạo nhánh từ `main`: `feature/<mô-tả-ngắn>`, `fix/<mô-tả-ngắn>` hoặc `docs/<mô-tả-ngắn>`.
2. Thực hiện thay đổi, kèm cập nhật tài liệu nếu hành vi thay đổi.
3. Chạy kiểm tra cục bộ (xem mục dưới) và bảo đảm tất cả đều pass.
4. Ghi một mục vào `CHANGELOG.md` phần `[Unreleased]` nếu thay đổi có ảnh hưởng tới người dùng.
5. Mở Pull Request mô tả: vấn đề, cách giải quyết, cách kiểm chứng.
6. PR cần ít nhất một review chấp thuận từ thành viên khác trước khi merge.

## Yêu cầu bắt buộc với mỗi commit

### 1. Ký nhận DCO

Mọi commit phải có dòng `Signed-off-by`, xác nhận bạn có quyền hợp pháp đóng góp phần
mã đó theo [Developer Certificate of Origin 1.1](https://developercertificate.org/):

```bash
git commit -s -m "fix(workflow): chặn đóng work order khi thiếu bằng chứng"
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

Dùng dạng `<type>(<scope>): <mô tả ngắn, thức mệnh lệnh>`.

Các `type` dùng trong dự án: `feat`, `fix`, `docs`, `refactor`, `test`, `build`, `ci`, `chore`.

```text
feat(workflow): chặn đóng yêu cầu sửa chữa khi thiếu ảnh minh chứng

Yêu cầu chỉ chuyển sang ĐÃ KHẮC PHỤC khi có ít nhất một ảnh sau sửa chữa.
Kiểm tra nằm ở Core nên mọi ứng dụng tầng trên đều chịu cùng ràng buộc.

Signed-off-by: Tên Của Bạn <email@example.com>
```

## Kiểm thử

Viết test cho hành vi mà người dùng quan sát được, khi một lỗi hợp lý sẽ làm test đó fail.
Không viết test chỉ để "có test": không kiểm tra giá trị mặc định, không so khớp chuỗi
nội bộ, không assert lại cách hiện thực.

Thay đổi hành vi nghiệp vụ phải kèm test tương ứng, và mô tả cách kiểm chứng trong PR.
