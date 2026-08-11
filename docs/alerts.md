# Alert Rules và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## HighLatencyP95

* **Tên:** `HighLatencyP95`
* **Severity:** Warning
* **SLI/SLO liên quan:** `latency_p95_ms <= 3000 ms`
* **Điều kiện và thời gian duy trì:** Kích hoạt khi P95 latency lớn hơn 3000 ms liên tục trong 5 phút.
* **Ảnh hưởng tới người dùng:** Phần lớn yêu cầu vẫn hoàn thành nhưng người dùng phải chờ lâu, dễ timeout hoặc gửi lại yêu cầu.
* **Ba bước kiểm tra đầu tiên:**

  1. Mở panel `latency`, xác nhận thời điểm P95 vượt 3000 ms và so sánh với P50/P99.
  2. Từ khoảng thời gian bất thường, mở các trace chậm và xác định span chiếm nhiều thời gian nhất.
  3. Dùng `trace_id` hoặc `correlation_id` tra log, kiểm tra `latency_ms`, `error_type`, lưu lượng và dependency liên quan.
* **Mitigation tạm thời:** Giảm concurrency hoặc rate limit, tạm chuyển về prompt/model ổn định và vô hiệu hóa dependency tùy chọn đang chậm. Theo dõi lại P95 ít nhất 10 phút.
* **Owner:** AI Platform On-call
* **Escalation:** Chuyển mức Critical nếu P95 lớn hơn 6000 ms trong 10 phút hoặc tỷ lệ timeout vượt 2%.

## HighErrorRate

* **Tên:** `HighErrorRate`
* **Severity:** Critical
* **SLI/SLO liên quan:** `error_rate_pct <= 2%`
* **Điều kiện và thời gian duy trì:** Kích hoạt khi error rate lớn hơn 2% liên tục trong 5 phút.
* **Ảnh hưởng tới người dùng:** Một phần yêu cầu thất bại, người dùng không nhận được câu trả lời hoặc phải thử lại.
* **Ba bước kiểm tra đầu tiên:**

  1. Mở panel `errors`, xác nhận error rate và nhóm lỗi phổ biến theo `error_type`.
  2. Chọn trace thất bại trong đúng time range, xác định span đầu tiên có trạng thái lỗi.
  3. Tra log bằng `trace_id` hoặc `correlation_id`, kiểm tra status, thông báo lỗi, prompt version và dependency liên quan.
* **Mitigation tạm thời:** Rollback thay đổi mới nhất nếu lỗi xuất hiện sau triển khai; tạm dùng fallback cho dependency lỗi và giảm tải nếu có dấu hiệu quá tải. Xác nhận error rate về dưới 2%.
* **Owner:** AI Platform On-call
* **Escalation:** Báo ngay cho Incident Commander khi lỗi vượt 5% trong 5 phút hoặc endpoint chính không sử dụng được.

## LowQualityScore

* **Tên:** `LowQualityScore`
* **Severity:** Warning
* **SLI/SLO liên quan:** `quality_score_avg >= 0.75`
* **Điều kiện và thời gian duy trì:** Kích hoạt khi quality score trung bình nhỏ hơn 0.75 liên tục trong 15 phút.
* **Ảnh hưởng tới người dùng:** Câu trả lời có thể thiếu chính xác, ít liên quan hoặc không đáp ứng yêu cầu dù API vẫn trả về thành công.
* **Ba bước kiểm tra đầu tiên:**

  1. Mở panel `quality`, xác nhận thời điểm score giảm và phạm vi request bị ảnh hưởng.
  2. So sánh trace theo `prompt_name`, `prompt_label` và `prompt_version` để xác định phiên bản có chất lượng thấp.
  3. Đọc input/output đã redaction trong log của các trace điểm thấp, kiểm tra dữ liệu đầu vào và quality proxy.
* **Mitigation tạm thời:** Chuyển label về prompt baseline đã được xác nhận, tạm dừng candidate kém chất lượng và chạy lại bộ input đánh giá. Theo dõi score ít nhất 15 phút.
* **Owner:** AI Quality Owner
* **Escalation:** Chuyển mức Critical nếu quality score dưới 0.60 trong 15 phút hoặc phát hiện câu trả lời gây hại/sai nghiêm trọng.
