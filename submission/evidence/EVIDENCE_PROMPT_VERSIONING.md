# Evidence — Managed Prompt Versioning và Traces

Ngày thu evidence: 2026-08-11.

Tài liệu gốc của phần Prompt Versioning v2/Tracing được ghi nhận cho **khanhngo
(Member 2A)**. Các trace ID và audit API bên dưới là evidence runtime được bổ
sung khi hoàn thiện Checkpoint 2; việc bổ sung không thay đổi attribution của
phần implementation đã có.

## Managed versions

- `day13-chat` v1: labels `baseline`, `production`.
- `day13-chat` v2: label `candidate`.
- Promote đã thực hiện: `production → v2`.
- Rollback đã thực hiện và là trạng thái cuối: `production → v1`.

Prompt v1:

```text
Feature={{feature}}
Docs={{docs}}
Question={{message}}
```

Prompt v2 candidate do phần việc 2A triển khai:

```text
Feature={{feature}}
Docs={{docs}}
Question={{message}}
Answer in a clear, structured way in 3-5 sentences.
```

Hậu kiểm được đọc lại từ Langfuse Prompts API và lưu tại
[`prompt_lifecycle.json`](prompt_lifecycle.json). Danh sách version cuối nằm tại
[`prompt_versions.json`](prompt_versions.json).

## Dynamic trace metadata linkage

Khi app lấy managed prompt candidate, trace và generation có metadata:

```json
{
  "prompt_name": "day13-chat",
  "prompt_label": "candidate",
  "prompt_version": "2",
  "prompt_source": "langfuse"
}
```

Nếu Langfuse không khả dụng, app dùng local fallback và ghi rõ
`prompt_source=local-fallback`, `prompt_version=local-v2`; fallback không được
báo cáo giả thành managed prompt.

Generation nhận managed prompt object qua trường `prompt`, nhờ đó Langfuse có
thể liên kết generation với đúng prompt version.

## Traces

- 10 traces baseline/v1: [`baseline_traces.json`](baseline_traces.json).
- 10 traces candidate/v2: [`candidate_traces.json`](candidate_traces.json).
- Baseline/v1 representative: `46597bc000a191ff5c39c43a2f5a945c`.
- Candidate/v2 representative: `cdca6743b1647c8a5928037763f808f4`.

## Screenshots

Chưa có screenshot Langfuse UI do tài khoản hiện tại không có quyền truy cập
project chứa traces. Không có ảnh render hoặc ảnh mô phỏng trong evidence. File
JSON chỉ là nguồn machine-readable để đối chiếu, không được gọi là screenshot.
