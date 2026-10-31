---
name: dxlab-core-service
description: "Dùng khi sửa hoặc thêm mã trong core/ của dx-lab (FastAPI, SQLAlchemy, Alembic, SpiffWorkflow) hoặc CLI dxlab: route mới, service, migration, phân quyền, audit."
---

# Mã core và CLI

> Phiên bản 1.0 · 30/10/2026 · bộ skill riêng của DX-Lab, không commit (D-19).

Hợp đồng: `docs/ARCHITECTURE.md` mục 2 (ranh giới import), 6 (API); `CONTRIBUTING.md` "Đặt tên API", "Định dạng lỗi"; `docs/AUTHZ.md`.

## Mẫu phải theo (xem code trên `main`)
- Route: `APIRouter(prefix="/<tài-nguyên>")`, đăng ký trong `app.py`; mỗi route có `response_model` và `summary` tiếng Việt; danh sách trả `Page[T]` (`{"items","total"}`, `limit`/`offset`).
- Phiên DB: `DbSession` (commit trước khi trả phản hồi). Người gọi: `CurrentPrincipal` (đã chặn `system_admin`, SoD-4), `require_role(...)`.
- Lỗi: `ApiError(status, code, message_vi, details)`, mã trong `CONTRIBUTING.md`; 422 có `details.errors = [{"path","message"}]`.
- Audit: `audit.service.record(...)` cùng transaction; không ghi dữ liệu cá nhân vào `details`.
- Migration Alembic mới, nối tiếp head (`down_revision`); không sửa migration đã merge. Cột sinh sẵn không đổi công thức được: phải tạo lại.

## Luật nghiệp vụ
- **Core không biết tên ứng dụng** (`lab-repair`), không có con số nghiệp vụ (hạn mức, SLA): chúng ở DMN và `process_model.json` (`data_defaults`, `record_bindings`).
- Quyền nghiệp vụ kiểm ở core theo 5 lớp, mặc định từ chối; trường `x-personal-data` bị che theo vai trò (AUTHZ mục 8).
- Không gọi LLM từ core (D-18). CLI và MCP là client qua gateway, không import `dxlab_core` nội bộ ngoài CLI có sẵn.

## Kiểm chứng
- Test PostgreSQL thật (`DXLAB_TEST_DATABASE_URL`, xem `core/tests/conftest.py`). Test kiểm hành vi qua HTTP (`TestClient`), không kiểm chuỗi nội bộ.
- Sửa lỗi: test phải đỏ khi bỏ bản sửa.
- Thêm một lượt chạy thật: uvicorn + PostgreSQL + token Keycloak của tài khoản demo, dán kết quả.
