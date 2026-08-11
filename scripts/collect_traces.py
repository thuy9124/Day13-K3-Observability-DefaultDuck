"""Ghi >= 10 traces lên Langfuse và thu evidence cho CP2.

Quy trình:
  1. Chạy load test (default baseline) để tạo >= 10 request /chat -> >= 10 traces.
     Mỗi trace có metadata prompt_name/label/version + tags [lab, feature, model].
  2. Đọc danh sách trace từ Langfuse API (limit=50) và lọc các trace của buổi này.
  3. Ghi evidence: mỗi trace ghi id, prompt_name/label/version, tags, latency.

Yêu cầu:
  - Server /chat đang chạy với tracing ENABLED (LANGFUSE_* keys hợp lệ trong .env
    và server được khởi động sau khi set key).
  - Prompt v1/v2/v3 đã tồn tại (chạy scripts/prompt_versioning.py trước nếu cần).

Cách chạy:

    python scripts/collect_traces.py                # load test baseline, rồi liệt kê traces
    python scripts/collect_traces.py --count 20     # ít nhất 20 trace

Evidence đầu ra:
    submission/evidence/traces.json    — danh sách trace + prompt metadata
    submission/evidence/traces.txt     — tóm tắt dạng văn bản
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio
from langfuse import Langfuse

EVIDENCE_DIR = REPO_ROOT / "submission" / "evidence"
MIN_TRACES = 10


def _has_keys() -> bool:
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        text = env_path.read_text(encoding="utf-8")
        pub = sec = ""
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("LANGFUSE_PUBLIC_KEY="):
                pub = line.split("=", 1)[1].strip().strip('"').strip("'")
            elif line.startswith("LANGFUSE_SECRET_KEY="):
                sec = line.split("=", 1)[1].strip().strip('"').strip("'")
        return bool(pub and sec)
    return False


def main() -> None:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Ghi >= 10 traces và thu evidence")
    parser.add_argument("--count", type=int, default=12, help="Số request tối thiểu cần ghi")
    parser.add_argument("--skip-load", action="store_true", help="Không chạy load test, chỉ liệt kê traces")
    args = parser.parse_args()

    if not _has_keys():
        print("FAIL: LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY rỗng trong .env. Dán key rồi chạy lại.")
        sys.exit(1)

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    window_start = dt.datetime.now(dt.timezone.utc)

    if not args.skip_load:
        print(f"== Chạy load test để tạo >= {args.count} traces ==")
        for i in range(0, max(args.count, MIN_TRACES), 10):
            subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts" / "load_test.py"), "--concurrency", "5"],
                cwd=str(REPO_ROOT),
                check=False,
            )
            time.sleep(2)  # cho langfuse flush

    client = Langfuse()
    try:
        resp = client.api.trace.list(limit=50)
    except Exception as exc:
        print(f"FAIL: list traces API | {type(exc).__name__}: {exc}")
        sys.exit(1)

    rows = []
    for tr in getattr(resp, "data", []) or []:
        ts = getattr(tr, "timestamp", None)
        try:
            created_at = dt.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            if created_at < window_start:
                continue  # chỉ giữ trace được tạo từ lúc script chạy
        except (ValueError, TypeError):
            pass  # không parse được timestamp -> giữ lại để không sót
        metadata = getattr(tr, "metadata", None) or {}
        tags = list(getattr(tr, "tags", []) or [])
        rows.append(
            {
                "trace_id": getattr(tr, "id", None),
                "timestamp": str(getattr(tr, "timestamp", "")),
                "latency_ms": getattr(tr, "latency", None),
                "user_id": getattr(tr, "user_id", None),
                "session_id": getattr(tr, "session_id", None),
                "tags": tags,
                "prompt_name": metadata.get("prompt_name"),
                "prompt_label": metadata.get("prompt_label"),
                "prompt_version": metadata.get("prompt_version"),
                "prompt_source": metadata.get("prompt_source"),
            }
        )

    print(f"\n== Tìm thấy {len(rows)} trace (limit=50, mới nhất trước) ==")
    for r in rows[:5]:
        print(
            f"  {r['trace_id']}  prompt={r['prompt_name']}@{r['prompt_label']} "
            f"v{r['prompt_version']}  tags={r['tags']}  latency={r['latency_ms']}ms"
        )
    if len(rows) > 5:
        print(f"  ... (+{len(rows) - 5} trace nữa)")

    (EVIDENCE_DIR / "traces.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    lines = [f"Traces trên Langfuse (tổng {len(rows)}):"]
    for r in rows:
        lines.append(
            f"  {r['trace_id']}  prompt={r['prompt_name']}@{r['prompt_label']} "
            f"v{r['prompt_version']}  source={r['prompt_source']}  tags={r['tags']}  {r['latency_ms']}ms"
        )
    (EVIDENCE_DIR / "traces.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\nEvidence saved ->", EVIDENCE_DIR / "traces.json")
    print("Evidence saved ->", EVIDENCE_DIR / "traces.txt")

    if len(rows) < MIN_TRACES:
        print(f"\nCẢNH BÁO: chỉ {len(rows)} trace (< {MIN_TRACES}). Chạy thêm load test.")
        sys.exit(2)


if __name__ == "__main__":
    main()
