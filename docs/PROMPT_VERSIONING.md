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
2. Tạo version 2 với một thay đổi nhỏ về format hoặc độ dài câu trả lời, gắn label `candidate-v2`.
3. Giữ version 3 mở rộng với label riêng `candidate-v3`.
4. Version 4 dùng labels `candidate` và `candidate-v4`, giữ grounding/privacy/output contract rõ ràng.
5. Chạy cùng một input với `LANGFUSE_PROMPT_LABEL=baseline` và `candidate-v4`.
6. Mở hai trace, kiểm tra `prompt_name`, `prompt_label`, `prompt_version` và prompt link.
7. Chuyển label `production` sang candidate cần kiểm chứng (v4 trong bài nộp này), chạy lại một request.
8. Rollback `production` về version 1 và lưu ảnh evidence.

Script tự động tạo/chuẩn hóa v1–v4, đổi `production` sang version chứa v4 rồi
rollback về version chứa v1.
Script tái dùng version đã tồn tại theo nội dung prompt nên chạy lại không nhân
đôi version. Chạy khi đã có key trong `.env`:

```bash
python scripts/prompt_versioning.py
# thử trước không ghi:
python scripts/prompt_versioning.py --dry-run
```

Prompt v1–v4 — giữ đúng contract 3 biến `{{feature}} {{docs}} {{message}}`:

| Version | Nội dung khác biệt | Labels |
|---|---|---|
| v1 | Template gốc | `baseline`, `production` |
| v2 | Thêm hướng dẫn format, 3–5 câu | `candidate-v2` |
| v3 | Ràng buộc Docs-only, tối đa 60 từ, không PII | `candidate-v3` |
| v4 | Grounding, context thiếu, privacy, output contract | `candidate`, `candidate-v4` |

Không chấm prompt nào “hay hơn”. Điểm nằm ở khả năng truy xuất version, đổi label và rollback có bằng chứng.

## Evidence

- Một ảnh danh sách hai prompt version.
- Hai trace ID chứng minh hai version/label khác nhau.
- Một ảnh trước/sau khi đổi label hoặc rollback `production`.
- Ghi các ID và đường dẫn ảnh vào `submission/REPORT.md`.
