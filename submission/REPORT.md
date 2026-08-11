# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: DefaultDuck
- Repository URL: https://github.com/thuy9124/Day13-K3-Observability-DefaultDuck
- Commit SHA kỹ thuật/evidence: `48ea56f`
- Thành viên/đóng góp đã xác định trong Git: xem Mục 7.

## 2. Kết quả kỹ thuật

- `validate_logs.py`: **100/100** — [`evidence/checkpoint1-validation.txt`](evidence/checkpoint1-validation.txt).
- Langfuse: 4 managed prompt versions; 10 trace baseline/v1 và 10 trace v4.
- PII leak trong log: **0**.
- Tests: **26 passed**.
- Dashboard contract: **HỢP LỆ 6/6 panel**.
- Dashboard runtime: [`evidence/dashboard-runtime.png`](evidence/dashboard-runtime.png).

## 3. Logging và tracing

- Correlation ID đúng dạng `req-[0-9a-f]{8}`, xuất hiện trong response header,
  response body, JSON log và Langfuse trace metadata.
- API log có `user_id_hash`, `session_id`, `feature`, `model`, `env`.
- PII được scrub đệ quy trước khi ghi log; raw email, điện thoại và thẻ thử
  nghiệm không còn trong `data/logs.jsonl`.
- Trace có generation `run` và span con `rag.retrieve`; generation chứa token,
  cost và managed prompt link.
- Health evidence: [`evidence/health.json`](evidence/health.json).

## 4. Prompt versioning — Checkpoint 2

- Prompt name: `day13-chat`.
- Baseline: version 1, labels `baseline`, `production`.
- Teammate candidates: version 2 `candidate-v2`; version 3 `candidate-v3`.
- Candidate v4: version 4, labels `candidate`, `candidate-v4`, `latest`.
- V4 trace đại diện: `c48d441070e024fa403706e88c42c59e`.
- Baseline trace đại diện: `cfc841269263ccc4923639dfdbf70bbf`.
- Promote: `production → v4`; rollback cuối: `production → v1`.
- Evidence: [`evidence/EVIDENCE_PROMPT_VERSIONING.md`](evidence/EVIDENCE_PROMPT_VERSIONING.md),
  [`evidence/prompt_versions.json`](evidence/prompt_versions.json) và
  [`evidence/prompt_lifecycle.json`](evidence/prompt_lifecycle.json). Trạng thái
  cuối được hậu kiểm tại [`evidence/langfuse-final-state.json`](evidence/langfuse-final-state.json).

Do FakeLLM trả output gần cố định, nhóm không tuyên bố v4 tốt hơn về chất lượng
ngữ nghĩa. So sánh tập trung vào traceability, version/label, token overhead và
rollback an toàn.

## 5. Dashboard, SLO và alerts

- Dashboard có đủ latency P50/P95/P99, traffic, error, cost, token và quality.
- Nguồn chuẩn: `data/logs.jsonl`; time range 60 phút; refresh 30 giây.
- SLO: latency P95 ≤ 3000 ms; error rate ≤ 2%; daily cost ≤ 2.5 USD; quality
  average ≥ 0.75.
- Alerts: `HighLatencyP95`, `HighErrorRate`, `LowQualityScore` với runbook tại
  `docs/alerts.md`.
- Evidence runtime: [`evidence/dashboard-runtime.png`](evidence/dashboard-runtime.png)
  và source HTML [`evidence/dashboard-runtime.html`](evidence/dashboard-runtime.html).

## 6. Điều tra challenge — Checkpoint 3

- Challenge ID: `day13-k3-observability-v1`.
- Incident/feature: `rag_slow` / `refund`.
- Ngưỡng challenge: 2000 ms.
- Metrics: P50 2651 ms, P95/P99 5209 ms, error rate 0%.
- Trace: `170fd58c40f889d6a438d6ef497c909b`.
- Correlation ID/log: `req-1e041367`, `response_sent`, latency 2651 ms.
- Span bất thường: `rag.retrieve`, observation `e7e482feaf8c9b8b`, khoảng 2504 ms.
- Root cause: incident chèn độ trễ 2.5 giây vào retrieval; span RAG chiếm gần
  toàn bộ latency bất thường.
- Fix: tắt incident; trong production áp dụng timeout, cache refund policy và
  fallback an toàn khi vector store chậm.
- Prevention: alert theo threshold, latency budget riêng cho retrieval và diễn
  tập fallback/rollback.
- Audit đầy đủ: [`evidence/challenge-investigation.json`](evidence/challenge-investigation.json).

## 7. Phân công và đóng góp cá nhân

| Thành viên | MSSV | Phần việc phụ trách | Commit/evidence | Kết quả bàn giao |
|---|---|---|---|---|
| Lê Thị Thuý | `2A202601381` | **Checkpoint 1:** structured JSON logging, correlation ID, PII scrubbing và metrics nền tảng | `936e28c` | Log có đủ trường bắt buộc; request ID xuyên suốt header/body/log; dữ liệu nhạy cảm được che |
| Phí Đình Hoàng Anh | `2A202601853` | **Checkpoint 2:** thiết kế và triển khai prompt candidate V3; cập nhật luồng prompt versioning/trace collection | `5f14ea2` | Prompt `day13-chat` V3 với label `candidate-v3`, sẵn sàng so sánh với các phiên bản khác |
| Ngô Việt Anh | `2A202601579` | **Tích hợp & Checkpoint 3:** tối ưu prompt V4, hardening observability, dựng dashboard runtime, chạy challenge và điều tra root cause | `48ea56f`, `7c428ef` | V4 có trace/evidence; hoàn thiện kiểm thử; xác định `rag.retrieve` là nguyên nhân latency và lập hướng khắc phục |
| Ngô Đình Khánh | `2A202601625` | **Checkpoint 2:** xây dựng prompt candidate V2; bổ sung Langfuse tracing, prompt metadata và tài liệu rollback | `84360ce`, `6bd73a7` | Prompt V2 có version/label rõ ràng; trace liên kết được với managed prompt |
| Trần Thị Kiều Oanh | `2A202601417` | **Dashboard & vận hành:** định nghĩa dashboard contract, 6 panels, SLO, alert rules và runbook | `fda8021` | Dashboard hợp lệ 6/6; có ngưỡng latency/error/quality và hướng xử lý cảnh báo |
| Dương Minh Quân | `2A202601903` | **Checkpoint 2 automation:** tự động hoá prompt lifecycle, thu baseline/candidate traces và chuẩn bị evidence kiểm chứng | `63fa173`, `0be20cd` | Có scripts tạo/promote/rollback prompt; evidence API và trace phục vụ đối chiếu phiên bản |
