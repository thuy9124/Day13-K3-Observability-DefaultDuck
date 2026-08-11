# Evidence — Managed Prompt Versioning và Traces

Ngày thu evidence: 2026-08-11. Nguồn là Langfuse Prompts/Traces API của project
đang cấu hình trong `.env`; secret không được lưu trong evidence.

## Managed versions

- `day13-chat` v1: `baseline`, `production`.
- `day13-chat` v2: `candidate-v2`.
- `day13-chat` v3: `candidate-v3`.
- `day13-chat` v4: `candidate`, `candidate-v4`, `latest`.

V4 bổ sung grounding, xử lý context thiếu, privacy rule, giới hạn 80 từ và output
contract `Answer`/`Evidence`. Ba biến bắt buộc `{{feature}}`, `{{docs}}`,
`{{message}}` vẫn được giữ nguyên.

Audit lifecycle tại [`prompt_lifecycle.json`](prompt_lifecycle.json):

1. `production` được promote từ v1 sang v4.
2. Trace v4 được tạo với `prompt_label=candidate-v4`, `prompt_version=4`.
3. `production` được rollback về v1 và hậu kiểm qua API.

## Trace evidence

- 10 trace baseline/v1: [`baseline_current_traces.json`](baseline_current_traces.json).
- 10 trace candidate-v4/v4: [`v4_traces.json`](v4_traces.json).
- Baseline đại diện: `cfc841269263ccc4923639dfdbf70bbf`.
- V4 đại diện: `c48d441070e024fa403706e88c42c59e`.

Trace metadata có `prompt_name`, `prompt_label`, `prompt_version`,
`prompt_source=langfuse`, user hash, session, feature/model và tags. Generation
được liên kết với managed prompt object. Input dùng để thu evidence đã được
redact PII trước khi gửi.

Danh sách version cuối nằm tại [`prompt_versions.json`](prompt_versions.json).
Ảnh Langfuse UI vẫn nên được thành viên đăng nhập project chụp thêm nếu giảng
viên bắt buộc screenshot thay vì audit API machine-readable.
