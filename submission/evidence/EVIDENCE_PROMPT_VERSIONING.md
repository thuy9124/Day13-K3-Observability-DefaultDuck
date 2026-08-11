# Evidence: Prompt Versioning (v2 Candidate) & Langfuse Tracing (Checkpoint 2A)

Tài liệu bằng chứng thuộc phần làm việc của **khanhngo** (Nửa 2A) — Xây dựng và triển khai Prompt Version 2 (Candidate), tích hợp Metadata Tracing và quy trình Rollback.

---

## 1. Danh sách Prompt Versions (`day13-chat`)

- **Prompt Name:** `day13-chat`
- **Version 1 (v1 - Baseline):** *(Được thực hiện bởi thành viên khác trong nhóm)*
  - **Label:** `baseline`
  - **Template:**
    ```text
    Feature={{feature}}
    Docs={{docs}}
    Question={{message}}
    ```
- **Version 2 (v2 - Candidate / Chỉnh sửa bởi khanhngo):**
  - **Label:** `candidate` (hoặc `v2` / `staging`)
  - **Template:**
    ```text
    Feature={{feature}}
    Docs={{docs}}
    Question={{message}}
    Yêu cầu: Trả lời ngắn gọn, có cấu trúc và đúng trọng tâm từ Docs.
    ```

---

## 2. Dynamic Trace Metadata Linkage (Prompt v2)

Khi ứng dụng chạy với `LANGFUSE_PROMPT_LABEL=candidate` (Prompt v2), các trường metadata sau tự động được gắn kết vào Trace và Generation span:

```json
{
  "prompt_name": "day13-chat",
  "prompt_label": "candidate",
  "prompt_version": "2",
  "prompt_source": "langfuse"
}
```

*Khi chạy ở chế độ Local / Fallback (`LANGFUSE_PROMPT_LABEL=candidate`):*
```json
{
  "prompt_name": "day13-chat",
  "prompt_label": "candidate",
  "prompt_version": "local-v2",
  "prompt_source": "local-fallback"
}
```

---

## 3. Quy Trình Promote Prompt v2 & Rollback v1

1. **Triển khai Prompt v2 Candidate:**
   - Cấu hình `LANGFUSE_PROMPT_LABEL=candidate`.
   - Hệ thống tự động biên dịch template v2 kèm các yêu cầu về định dạng và câu trả lời.
2. **Promote Prompt v2 thành Production:**
   - Gắn nhãn `production` cho Version 2 trên Langfuse UI (hoặc cấu hình môi trường).
3. **Rollback về Prompt v1:**
   - Trong trường hợp cần khôi phục, đổi lại nhãn `production` về Version 1.
   - Traces cập nhật tức thì về `prompt_version: "1"` mà không gián đoạn dịch vụ.

