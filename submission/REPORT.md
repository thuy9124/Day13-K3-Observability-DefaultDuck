# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: DefaultDuck
- Repository URL: https://github.com/thuy9124/Day13-K3-Observability-DefaultDuck
- Commit SHA cuối: cập nhật sau khi commit bài nộp
- Phân vai đã có trong report trước:
  - Thành viên 1: Logging & PII Scrubbing, Middleware Correlation ID.
  - Thành viên 2: Tracing, Prompt Management & Dashboard Validator.

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100.
- Langfuse traces đã xác minh qua API: 20 traces (10 baseline/v1 và 10 candidate/v2).
- Số PII leak còn lại: 0.
- Dashboard contract: `HỢP LỆ: 6/6 panel có trong dashboard contract`.
- Dashboard runtime và ảnh chụp UI: cần bổ sung trước khi nộp.

## 3. Logging và tracing

- Evidence correlation ID: header `x-request-id` và trường `correlation_id` dạng `req-xxxxxxxx` được truyền qua các log record trong `data/logs.jsonl`.
- Evidence PII redaction: email, số điện thoại, CCCD, số thẻ tín dụng, hộ chiếu và địa chỉ được xử lý bởi `scrub_event` trước khi ghi log.
- Trace metadata: `prompt_name`, `prompt_label`, `prompt_version`, `prompt_source`, user/session và tags feature/model.
- Generation span có `usage_details` (prompt/completion tokens), `cost_details` và liên kết managed prompt.
- Danh sách trace API: [`evidence/baseline_traces.json`](evidence/baseline_traces.json) và [`evidence/candidate_traces.json`](evidence/candidate_traces.json).
- Trace waterfall thật trên Langfuse UI: chưa có do tài khoản hiện tại không có quyền truy cập project chứa traces.

## 4. Prompt versioning — Checkpoint 2

- Managed prompt: `day13-chat`.
- Baseline: Langfuse version 1, labels `baseline` và `production`.
- Candidate: Langfuse version 2, label `candidate`.
- Promote thực tế: `production` đã được chuyển sang version 2 và hậu kiểm qua Prompts API trả về version 2.
- Rollback thực tế: `production` đã được chuyển lại version 1 và hậu kiểm qua Prompts API trả về version 1.
- Audit machine-readable: [`evidence/prompt_lifecycle.json`](evidence/prompt_lifecycle.json) và [`evidence/prompt_versions.json`](evidence/prompt_versions.json).

| Label/version | Trace ID | Link trực tiếp |
|---|---|---|
| `baseline` / v1 | `46597bc000a191ff5c39c43a2f5a945c` | [Mở trace baseline/v1](https://cloud.langfuse.com/project/cmso6msot04syad0ducpc4wnw/traces/46597bc000a191ff5c39c43a2f5a945c) |
| `candidate` / v2 | `cdca6743b1647c8a5928037763f808f4` | [Mở trace candidate/v2](https://cloud.langfuse.com/project/cmso6msot04syad0ducpc4wnw/traces/cdca6743b1647c8a5928037763f808f4) |

Các link trên yêu cầu tài khoản là thành viên của project Langfuse tương ứng hoặc
trace đã được chủ project đặt public.

Evidence ảnh Langfuse UI hiện chưa có do tài khoản chụp ảnh chưa được cấp quyền
vào project chứa traces. Không sử dụng ảnh render hoặc ảnh mô phỏng thay thế.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract`.
- Ảnh chụp terminal validator thật: [`evidence/dashboard-validator.png`](evidence/dashboard-validator.png).
- Sáu panel theo contract: Latency P50/P95/P99, Request traffic, Error rate/breakdown, Cost over time, Input/output tokens và Quality proxy.
- SLO đã chọn và lý do:
  - Latency P95 ≤ 3000 ms, target 99.5% — giới hạn thời gian chờ của phần lớn người dùng.
  - Error rate ≤ 2%, target 99.0% — bảo đảm API ổn định.
  - Average quality score ≥ 0.75, target 95.0% — phát hiện suy giảm chất lượng khi HTTP vẫn thành công.
  - Daily cost ≤ 2.5 USD, target 100% — kiểm soát chi phí vận hành.
- Alert rules và runbook: ba symptom-based alerts `HighLatencyP95`, `HighErrorRate`, `LowQualityScore` trong `config/alert_rules.yaml`, liên kết tới `docs/alerts.md`.
- Evidence dashboard runtime: chưa có file ảnh thật; cần bổ sung tên panel, time range, đơn vị và threshold/SLO line.

## 6. Điều tra challenge

Nội dung dưới đây được giữ lại từ report của nhóm trước lần hoàn thiện Checkpoint 2 và cần được nhóm đối chiếu với challenge chính thức trước khi nộp:

- Challenge ID: `day13-k3`.
- Triệu chứng từ metrics: Latency p95 tăng đột biến trên panel Latency Percentiles.
- Trace ID liên quan: tra cứu span RAG retrieval và FakeLLM generation trong Langfuse/Logs.
- Log line/correlation ID liên quan: lọc log theo `latency_ms > 3000` với `event == "response_sent"`.
- Root cause: tắc nghẽn hoặc độ trễ gia tăng từ bước RAG document retrieval đối với tính năng cụ thể.
- Fix action: tối ưu truy vấn RAG, thêm cache kết quả và thiết lập timeout.
- Preventive measure: bổ sung cảnh báo `HighLatencyP95` để phát hiện trước khi ảnh hưởng SLO.

## 7. Đóng góp cá nhân

Các dòng của thành viên đã có trong report cũ được giữ nguyên; cần thay nhánh/commit bằng link commit hoặc PR thật trước khi nộp.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Dương Minh Quân — `2A202601903` | Xác minh và hoàn thiện Checkpoint 2: managed prompt lifecycle, traces thật, audit và tài liệu evidence | `63fa173` | Xác minh prompt label/version qua trace và rollback bằng hậu kiểm API |
| khanhngo (Member 2A) | Tracing Integration, Prompt Versioning & Evidence Documentation | `khanhngo` | Quản lý prompt lifecycle, metadata trace và zero-downtime rollback |
| DefaultDuck (Member 2B) | Logging, PII Redaction, Correlation ID, Alert Rules, Dashboard Contract | `936e28c` | Xây dựng hệ thống observability cho AI application |
