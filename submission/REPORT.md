# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: DefaultDuck
- Repository URL: https://github.com/thuy9124/Day13-K3-Observability-DefaultDuck
- Commit SHA cuối: 936e28c7cb18911904fe8ae759fb518cc84e9581
- Thành viên và vai trò:
  - Thành viên 1: Logging & PII Scrubbing, Middleware Correlation ID
  - Thành viên 2: Tracing, Prompt Management & Dashboard Validator

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100 (Đã hoàn thành 100% tiêu chí)
- Tổng số traces: 10+ traces
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard: `config/dashboard.yaml` (6/6 panel hợp lệ)

## 3. Logging và tracing

- Evidence correlation ID: Header `x-request-id` và trường `correlation_id` chuẩn dạng `req-xxxxxx` tự động được sinh và truyền qua các log record trong `data/logs.jsonl`.
- Evidence PII redaction: Tất cả thông tin Email, Số điện thoại Việt Nam, CCCD, Số thẻ tín dụng, Hộ chiếu, Địa chỉ Việt Nam đều được tự động thay thế bằng nhãn `[REDACTED_...]` qua `scrub_event`.
- Evidence trace waterfall: Dữ liệu trace bao gồm metadata `user_id_hash`, `session_id`, `feature`, `model`, `prompt_name`, `prompt_version`, `prompt_label`.
- Giải thích một span đáng chú ý: Span `generation` chứa chi tiết `usage_details` (prompt_tokens, completion_tokens), `cost_details` và `quality_score`.

## 4. Prompt versioning

- Prompt name: `day13-chat`
- Version/label baseline: `production` (v1 - `local-v1` / Langfuse Managed Prompt)
- Version/label candidate: `candidate` (v2 - `Yêu cầu: Trả lời ngắn gọn, định dạng rõ ràng.`)
- Trace ID của mỗi version: Gắn kết tự động thông qua metadata (`prompt_version`, `prompt_label`, `prompt_name`).
- Bằng chứng đổi label hoặc rollback: Xem chi tiết tài liệu bằng chứng tại `submission/evidence/EVIDENCE_PROMPT_VERSIONING.md`.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract.`
- Evidence dashboard: Đáp ứng đầy đủ 6 panel: Latency (p50, p95, p99), Request traffic (rate per minute), Error rate & breakdown, Cost over time, Input & output tokens, Quality proxy.
- SLO đã chọn và lý do:
  - Latency P95 <= 3000ms: Đảm bảo trải nghiệm phản hồi tức thì cho người dùng AI Chat.
  - Error rate <= 2%: Duy trì độ tin cậy và sẵn sàng của API.
  - Daily cost <= 2.5 USD: Kiểm soát ngân sách LLM token.
  - Quality score avg >= 0.75: Đảm bảo câu trả lời AI hữu ích và đúng trọng tâm.
- Alert rules và runbook: Được định nghĩa trong `config/alert_rules.yaml` và hướng dẫn xử lý tại `docs/alerts.md`.

## 6. Điều tra challenge

- Challenge ID: `day13-k3`
- Triệu chứng từ metrics: Latency p95 tăng đột biến trên panel Latency Percentiles.
- Trace ID liên quan: Tra cứu span RAG retrieval và FakeLLM generation trong Langfuse/Logs.
- Log line/correlation ID liên quan: Lọc log theo `latency_ms > 3000` với `event == "response_sent"`.
- Root cause: Tắc nghẽn hoặc độ trễ gia tăng từ bước RAG document retrieval đối với tính năng cụ thể.
- Fix action: Tối ưu hóa truy vấn RAG, thêm cache kết quả tìm kiếm và thiết lập timeout.
- Preventive measure: Bổ sung cảnh báo `HighLatencyP95` để chủ động phát hiện trước khi ảnh hưởng SLO.

## 7. Đóng góp cá nhân

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| DefaultDuck (Member 2A) | Tracing Integration, Prompt Versioning & Evidence Documentation | `feat/tracing-prompt-versioning-2a` | Quản lý prompt lifecycle, metadata trace & zero-downtime rollback |
| DefaultDuck (Member 2B) | Logging, PII Redaction, Correlation ID, Alert Rules, Dashboard Contract | `936e28c` | Xây dựng hệ thống Observability chuẩn cho AI Application |


