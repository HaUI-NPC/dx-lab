<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Spiff Editor cho `apps/`

Công cụ soạn BPMN/DMN (SpiffArena) chạy cục bộ trên máy người thiết kế quy trình. Không thuộc compose sản phẩm
(`deploy/compose.yaml`) và không nói chuyện với core: tệp ghi xuống `apps/` rồi đi tiếp bằng git và `dxlab publish`
(xem [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) mục 7).

## Chạy

Từ **gốc repo**:

```bash
docker compose -f tools/spiff-editor/compose.yaml up -d --wait
```

Mở <http://127.0.0.1:8600> → **Processes** → nhóm *Ứng dụng DX-Lab* → *lab-repair*. Dừng:

```bash
docker compose -f tools/spiff-editor/compose.yaml down
```

Nếu thư mục repo là **git worktree** (`.git` là tệp, không phải thư mục), thêm một biến trước lệnh `up`; không có biến
này backend của editor không thấy repo và thoát vì không chạy được `git init`:

```bash
export SPIFF_EDITOR_GIT_COMMON_DIR="$(git rev-parse --path-format=absolute --git-common-dir)"
```

## Thiết kế và các ràng buộc

| Điều | Cách làm |
|---|---|
| Image | 3 image SpiffArena ghim digest (`spiffworkflow-backend`, `spiffworkflow-frontend`, `connector-proxy-demo`) |
| Mạng | Cổng chỉ bind `127.0.0.1`: giao diện `8600`, API `8601` (đổi bằng `SPIFF_EDITOR_FRONTEND_PORT`, `SPIFF_EDITOR_BACKEND_PORT`, giữ trong dải 8600–8609). Máy khác trong mạng không vào được |
| Xác thực | Tắt (một người, một máy). Vì vậy **không** đổi địa chỉ bind sang `0.0.0.0` |
| Thư mục làm việc | Mount **gốc repo** tại `/app/process_models`, không phải `apps/`: nếu thư mục không thuộc repo git, script khởi động của editor chạy `git init` và sinh `.git` lồng |
| Lưu | Editor **không** tự commit (`SPIFFWORKFLOW_BACKEND_GIT_COMMIT_ON_SAVE=false`); commit bằng git như thường |
| Dữ liệu của editor | SQLite trên tmpfs, mất khi dừng container; nguồn sự thật duy nhất là các tệp trong `apps/` |

## Quy tắc khi soạn

1. Dựng pool và **từng lane** ngay trong editor; kéo một bước ra khỏi lane làm bước đó mất vai trò, validator của core
   (`dxlab validate apps/`) sẽ từ chối.
2. Lưu qua giao diện một lần rồi mới commit: editor viết lại `process_model.json` và định dạng lại XML, commit trước
   sẽ làm diff nhiễu.
3. Không dùng script task, pre/post script hay điều kiện ngoài so sánh, `and`/`or`/`not` (ARCHITECTURE mục 7).
