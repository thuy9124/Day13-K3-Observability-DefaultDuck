# Prompt versioning cơ bản

Mục tiêu của phần này là biết một request đã dùng prompt nào và có thể rollback an toàn. Đây không phải bài tối ưu prompt hoặc A/B testing.

## Prompt contract

Tạo text prompt tên `day13-chat` trên Langfuse. Prompt phải giữ ba biến:

```text
Feature={{feature}}
Docs={{docs}}
Question={{message}}
```

App lấy prompt theo hai biến môi trường:

```dotenv
LANGFUSE_PROMPT_NAME=day13-chat
LANGFUSE_PROMPT_LABEL=production
```

Nếu Langfuse không khả dụng, app dùng template local và trace metadata ghi `prompt_source=local` hoặc `local-fallback` thay vì giả vờ đã lấy được prompt managed.

## Việc cần làm

1. Tạo version 1, gắn labels `baseline` và `production`.
2. Tạo version 2 với một thay đổi nhỏ về format hoặc độ dài câu trả lời, gắn label `candidate`.
3. Tạo version 3 (tùy chọn, mở rộng): format gọn hơn + ràng buộc độ dài câu trả lời, gắn label `candidate`.
4. Chạy cùng một input với `LANGFUSE_PROMPT_LABEL=baseline` và `candidate`.
5. Mở hai trace, kiểm tra `prompt_name`, `prompt_label`, `prompt_version` và prompt link.
6. Chuyển label `production` sang version 2, chạy lại một request.
7. Rollback `production` về version 1 và lưu ảnh evidence.

Script tự động hoàn thành bước 1–3 và 6–7 (`scripts/prompt_versioning.py`), tạo đủ
v1/v2/v3, đổi `production` sang version chứa v2 rồi rollback về version chứa v1.
Script tái dùng version đã tồn tại theo nội dung prompt nên chạy lại không nhân
đôi version. Chạy khi đã có key trong `.env`:

```bash
python scripts/prompt_versioning.py
# thử trước không ghi:
python scripts/prompt_versioning.py --dry-run
```

Prompt v1/v2/v3 — giữ đúng contract 3 biến `{{feature}} {{docs}} {{message}}`:

| Version | Nội dung khác biệt | Labels |
|---|---|---|
| v1 | Template gốc | `baseline`, `production` |
| v2 | Thêm hướng dẫn format, 3–5 câu | `candidate` |
| v3 | `Rules: answer from Docs only; max 60 words; no PII; end with a one-line summary.` | `candidate` |

Không chấm prompt nào “hay hơn”. Điểm nằm ở khả năng truy xuất version, đổi label và rollback có bằng chứng.

## Evidence

- Một ảnh danh sách hai prompt version.
- Hai trace ID chứng minh hai version/label khác nhau.
- Một ảnh trước/sau khi đổi label hoặc rollback `production`.
- Ghi các ID và đường dẫn ảnh vào `submission/REPORT.md`.
