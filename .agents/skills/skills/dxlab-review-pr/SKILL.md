---
name: dxlab-review-pr
description: "Dùng khi mentor hoặc thành viên review một pull request của dx-lab: checklist phạm vi, ranh giới tầng, dependency, bằng chứng, bảo mật, test có giá trị."
---

# Review PR

> Phiên bản 1.0 · 30/10/2026 · bộ skill riêng của DX-Lab, không commit (D-19).

## Checklist
1. **Phạm vi:** `gh pr diff <n> --name-only` khớp "Phạm vi tệp" của issue; không đụng tệp hợp đồng.
2. **Base và xếp chồng:** base là `main`, hoặc tối đa 2 tầng có lý do. Chuỗi sâu hơn: đề nghị gộp.
3. **Ranh giới tầng:** core không HTML, không biết tên ứng dụng, không gọi LLM; portal/CLI/MCP chỉ gọi `/api` bằng token người dùng.
4. **Dependency:** thư viện, image, mô hình mới có trong ARCHITECTURE mục 8 và `docs/DEPENDENCIES.md`.
5. **Bằng chứng:** lệnh và kết quả thật; phân biệt chạy thật với server giả. Nghi ngờ thì tự chạy lại.
6. **Quyền và dữ liệu cá nhân:** route nghiệp vụ dùng `CurrentPrincipal`; trường `x-personal-data` không lộ cho vai trò không được xem; audit không chứa dữ liệu cá nhân.
7. **Test:** bắt được lỗi thật, không test câu chữ; sửa lỗi có test đỏ khi bỏ bản sửa.
8. **Bảo mật:** không secret, `.env`, token trong diff hay log.
9. **REUSE, DCO:** CI xanh.

## Cách review
- Tái hiện lỗi bằng API hoặc test trước khi kết luận; ghi vị trí (`tệp:dòng`), cách tái hiện, thực tế, đề nghị.
- Phân mức: lỗi chặn merge, nên sửa, góp ý.
- Approve chỉ khi đã đọc diff. Merge: chỉ mentor, kiểu rebase.
