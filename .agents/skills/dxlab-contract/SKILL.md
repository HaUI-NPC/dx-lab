---
name: dxlab-contract
description: "Dùng cho MỌI việc trong repo dx-lab (HaUI-NPC/dx-lab): đọc code, sửa code, viết tài liệu, mở PR. Chỉ dẫn tới hợp đồng chung trên main (ARCHITECTURE, AUTHZ, CONTRIBUTING, .env.example), danh sách tệp không được sửa, khi nào phải dừng và hỏi mentor, luật bảo mật."
---

# DX-Lab: hợp đồng chung

> Phiên bản 1.0 · 30/10/2026 · bộ skill riêng của DX-Lab, không commit (D-19).

Skill nền, luôn áp dụng. **Không chép hợp đồng vào đây** (D-22): đọc bản trên `main`, vì mentor sửa ở đó.

## Đọc trước khi làm bất cứ gì

| Cần biết | Đọc |
|---|---|
| 3 tầng, ranh giới import, cổng, URL, biến môi trường, API core, gói ứng dụng, thư viện được phép | `docs/ARCHITECTURE.md` (mục 1–8) |
| Cây tổ chức, vai trò, 5 lớp phân quyền, hạn mức, SoD, tài khoản demo, 14 kịch bản | `docs/AUTHZ.md` |
| Nhánh, commit, DCO, REUSE, cấu trúc thư mục, đặt tên API, **định dạng lỗi**, tiếng Việt, kiểm thử | `CONTRIBUTING.md` |
| Biến cấu hình | `.env.example` |
| API thật | `GET /api/openapi.json` của core đang chạy (OpenAPI là mô tả chính thức) |
| Mẫu code | `core/src/dxlab_core/` trên `main` (router, service, errors, audit), `apps/lab-repair/` |
| Việc của bạn | Body issue: **Phạm vi tệp**, **Không làm**, **Phụ thuộc**, **Xong khi**, **Cách kiểm chứng** |

Issue là hợp đồng của việc. Phần nào issue và tài liệu trên `main` mâu thuẫn: dừng, hỏi trên issue.

## Không bao giờ sửa (trừ khi issue ghi rõ cho phép)
`docs/ARCHITECTURE.md`, `docs/AUTHZ.md`, `CONTRIBUTING.md`, `.env.example`, `REUSE.toml`, `LICENSE`, `LICENSES/`,
`.github/workflows/`, `CHANGELOG.md` (REL-02 tổng hợp), tệp `.bpmn` / `.dmn` (chỉ mentor, D-10).
`uv.lock`: chỉ khi PR thêm hoặc đổi dependency, và chỉ sinh bằng `uv lock`, không sửa tay.

## Dừng và hỏi mentor (comment trên issue, gắn nhãn `needs-mentor`)
- Cần thêm thư viện, image, mô hình không có trong `docs/ARCHITECTURE.md` mục 8 (dùng skill `dxlab-dependency`).
- Cần đổi hợp đồng API (tên route, trường JSON, mã lỗi) hoặc tệp ở danh sách trên.
- Issue mơ hồ, phụ thuộc chưa đóng, hoặc "Xong khi" không kiểm chứng được.
- Thấy lỗi bảo mật hay lộ dữ liệu cá nhân ở chỗ khác: tạo issue (skill `dxlab-report-issue`), không tự sửa lan.

## Bảo mật
- Không đọc, in, dán, commit `.env`, token, mật khẩu demo, khóa OTP. Chỉ nói tên biến, không nói giá trị.
- Không tắt xác thực, không dùng token quản trị "để thử", không gọi thẳng database: dữ liệu vào qua API.
- Dữ liệu mẫu là dữ liệu giả; không đưa dữ liệu cá nhân thật vào repo công khai.
- Quyền nghiệp vụ luôn kiểm ở core; portal, CLI, MCP chỉ là client dùng token của người dùng.

## Bài học của dự án (đừng lặp lại)
- **Không xếp chồng PR quá 2 tầng.** Repo chỉ cho merge kiểu rebase: merge PR dưới tạo SHA mới, mọi PR phía trên xung đột và phải force-push, mất approve. Phụ thuộc dài thì đợi merge rồi mở PR kế, hoặc gộp thành một PR nhỏ.
- **Đẩy thêm commit sau khi đã được approve sẽ mất approve** (`dismiss_stale_reviews` đang bật). Gom sửa lại trước khi xin approve.
- **"Đã test" phải là đã chạy thật**: dán lệnh và kết quả. Server giả lập chỉ để phát triển, không phải bằng chứng.
- Lỗi thường chỉ lộ ra khi chạy với PostgreSQL và Keycloak thật (ví dụ JSONB sắp xếp lại khóa làm mất dữ liệu task); test bằng SQLite hay mock không bắt được.
