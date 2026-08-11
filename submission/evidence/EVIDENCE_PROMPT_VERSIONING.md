# Evidence: Prompt Versioning & Langfuse Tracing (Checkpoint 2A)

Tài liệu bằng chứng phục vụ chấm điểm Checkpoint 2A — Prompt Versioning, Metadata và Tracing Rollback.

---

## 1. Danh sách Prompt Versions (`day13-chat`)

- **Prompt Name:** `day13-chat`
- **Version 1 (v1 - Baseline / Production):**
  - **Label:** `production`, `baseline`
  - **Template:**
    ```text
    Feature={{feature}}
    Docs={{docs}}
    Question={{message}}
    ```
- **Version 2 (v2 - Candidate):**
  - **Label:** `candidate`
  - **Template:**
    ```text
    Feature={{feature}}
    Docs={{docs}}
    Question={{message}}
    Yêu cầu: Trả lời ngắn gọn, định dạng rõ ràng.
    ```

---

## 2. Trace Waterfall & Metadata Linkage

Khi ứng dụng gửi request qua API `/chat`, các trường metadata sau tự động được gắn vào Trace và Generation span trên Langfuse:

```json
{
  "prompt_name": "day13-chat",
  "prompt_label": "production",
  "prompt_version": "1",
  "prompt_source": "langfuse"
}
```

*Trong trường hợp offline/không có API Key, fallback local tự động ghi nhận:*
```json
{
  "prompt_name": "day13-chat",
  "prompt_label": "production",
  "prompt_version": "local-v1",
  "prompt_source": "local-fallback"
}
```

---

## 3. Quy Trình Chuyển Label & Rollback Prompt

1. **Chạy thử Candidate (`candidate` / `v2`):**
   - Đặt biến môi trường `LANGFUSE_PROMPT_LABEL=candidate`.
   - Gửi request thử nghiệm và xác nhận metadata `prompt_version: "2"`.
2. **Promote lên Production (`v2`):**
   - Trên Langfuse UI, chuyển label `production` sang Version 2.
3. **Rollback về Baseline (`v1`):**
   - Khi phát hiện sự cố chất lượng, chuyển lại label `production` về Version 1.
   - Trace mới lập tức phản ánh `prompt_version: "1"` mà không cần restart hay rebuild code backend.
