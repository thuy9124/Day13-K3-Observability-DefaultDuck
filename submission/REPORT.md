# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

* **Tên nhóm:**
* **Repository URL:**
* **Commit SHA cuối:**
* **Thành viên và vai trò:**

## 2. Kết quả kỹ thuật

* **Điểm `validate_logs.py`:**
* **Tổng số traces:**
* **Số PII leak còn lại:**
* **Link/đường dẫn dashboard:**

## 3. Logging và tracing

* **Evidence correlation ID:**
* **Evidence PII redaction:**
* **Evidence trace waterfall:**
* **Giải thích một span đáng chú ý:**

## 4. Prompt versioning

* **Prompt name:**
* **Version/label baseline:**
* **Version/label candidate:**
* **Trace ID của mỗi version:**
* **Bằng chứng đổi label hoặc rollback:**

## 5. Dashboard, SLO và alerts

* **Kết quả `validate_dashboard.py`:** `HỢP LỆ: 6/6 panel có trong dashboard contract.`
* **Evidence dashboard:** `submission/evidence/dashboard-6-panels.png` (bổ sung ảnh runtime trước khi nộp bài).
* **SLO đã chọn và lý do:**

  * **Latency P95:** `<= 3000 ms`, target `99.5%` — giới hạn thời gian chờ của phần lớn người dùng và phát hiện sớm request chậm.
  * **Error rate:** `<= 2%`, target `99.0%` — bảo đảm API trả kết quả ổn định và hạn chế request thất bại.
  * **Average quality score:** `>= 0.75`, target `95.0%` — phát hiện suy giảm chất lượng ngay cả khi API vẫn trả HTTP thành công.
  * **Daily cost:** `<= 2.5 USD`, target `100%` — kiểm soát chi phí vận hành theo contract của dashboard.
* **Alert rules và runbook:** Đã cấu hình ba symptom-based alerts `HighLatencyP95`, `HighErrorRate`, `LowQualityScore` trong `config/alert_rules.yaml`. Mỗi alert liên kết tới `docs/alerts.md`, gồm ảnh hưởng người dùng, ba bước điều tra Metrics → Traces → Logs, mitigation, owner và điều kiện escalation.

## 6. Điều tra challenge

* **Challenge ID:**
* **Triệu chứng từ metrics:**
* **Trace ID liên quan:**
* **Log line/correlation ID liên quan:**
* **Root cause:**
* **Fix action:**
* **Preventive measure:**

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên               | Phần việc                                                                     | Commit/PR                        | Điều đã học                                                                        |
| ------------------------ | ----------------------------------------------------------------------------- | -------------------------------- | ---------------------------------------------------------------------------------- |
| [Điền tên thành viên 2B] | Checkpoint 2B: dashboard contract, SLO, alert rules, runbook và Mục 5 báo cáo | [Bổ sung commit/PR sau khi push] | Thiết kế alert theo triệu chứng/SLO và điều tra sự cố theo Metrics → Traces → Logs |
