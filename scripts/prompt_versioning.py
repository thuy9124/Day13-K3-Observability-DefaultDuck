"""Thiết lập prompt versioning v1/v2 và giữ v3 mở rộng trên Langfuse.

Quy trình theo docs/PROMPT_VERSIONING.md:

  1. Tạo v1 (template gốc), gắn label `baseline` + `production`.
  2. Tạo v2 (thêm dòng hướng dẫn), gắn label `candidate`.
  3. Giữ v3 mở rộng với label `experimental` khi cần tạo mới.
  4. Kiểm tra các version qua API GET /prompts.
  5. Chuyển label `production` sang v2 (đổi label).
  6. Rollback `production` về v1.

Idempotent: chạy lại không tạo trùng — nếu version 1/2 đã tồn tại thì dùng lại,
chỉ tạo version mới khi thiếu. An toàn với lỗi mạng: mỗi bước in OK/FAIL riêng.

Cách chạy (đã có LANGFUSE_PUBLIC_KEY/SECRET_KEY trong .env):

    python scripts/prompt_versioning.py
    # hoặc chạy thử không ghi:
    python scripts/prompt_versioning.py --dry-run

Evidence đầu ra (khi không --dry-run):
    submission/evidence/prompt_versions.json   — danh sách version + label
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio
from langfuse import Langfuse

# Prompt contract theo docs/PROMPT_VERSIONING.md — giữ đúng 3 biến {{feature}}, {{docs}}, {{message}}.
PROMPT_V1 = "Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}"

# v2: thêm hướng dẫn trả lời (format/độ dài thay đổi nhẹ).
PROMPT_V2 = (
    "Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}\n"
    "Answer in a clear, structured way in 3-5 sentences."
)

# v3: format gọn hơn + ràng buộc độ dài câu trả lời.
PROMPT_V3 = (
    "Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}\n"
    "Rules: answer from Docs only; max 60 words; no PII; end with a one-line summary."
)

PROMPT_NAME = "day13-chat"

EVIDENCE_DIR = REPO_ROOT / "submission" / "evidence"

# CLI scripts are normally started with ``python ...`` (not ``uvicorn --env-file``),
# therefore the SDK would not otherwise receive the Langfuse credentials/host.
load_dotenv(REPO_ROOT / ".env")


def _redact_env_key(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        env_path = REPO_ROOT / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith(name + "="):
                    value = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not value:
        return ""
    # Chỉ hiển thị 4 ký tự đầu + 4 cuối để xác nhận đã có key, không lộ toàn bộ.
    return f"{value[:4]}…{value[-4:]} (len={len(value)})"


def main() -> None:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Setup prompt v1/v2/v3 + đổi label + rollback trên Langfuse")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ in kế hoạch, không gọi API")
    parser.add_argument(
        "--stop-after-promote",
        action="store_true",
        help="Dừng với production ở v2 để chụp UI; chạy lại không cờ để rollback về v1",
    )
    args = parser.parse_args()

    pub = _redact_env_key("LANGFUSE_PUBLIC_KEY")
    sec = _redact_env_key("LANGFUSE_SECRET_KEY")
    if not pub or not sec:
        print("FAIL: LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY rỗng trong .env. Dán key rồi chạy lại.")
        sys.exit(1)
    print(f"Langfuse keys: public={pub} secret={sec}")

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    client = Langfuse()

    def log(ok: bool, step: str, detail: str = "") -> None:
        prefix = "OK  " if ok else "FAIL"
        print(f"{prefix} | {step}" + (f" | {detail}" if detail else ""))

    # -- 1..3. Tạo/đảm bảo tồn tại các version --------------------------------
    versions: list[dict] = []
    plan = [
        (1, PROMPT_V1, ["baseline", "production"]),
        (2, PROMPT_V2, ["candidate"]),
        (3, PROMPT_V3, ["experimental"]),
    ]

    # Đọc các version đã có trên server theo nội dung prompt để tái dùng
    # (Langfuse create_prompt luôn tạo version MỚI — chạy lại sẽ nhân đôi nếu
    # không check trước). Dùng content làm key để chạy lại là no-op.
    existing_by_content: dict[str, dict] = {}
    try:
        resp = client.api.prompts.list(name=PROMPT_NAME)
        for meta in getattr(resp, "data", []) or []:
            for ver in getattr(meta, "versions", []) or []:
                try:
                    detail = client.api.prompts.get(PROMPT_NAME, version=ver)
                    content = getattr(detail, "prompt", None)
                    if content:
                        existing_by_content[content] = {
                            "name": PROMPT_NAME,
                            "version": getattr(detail, "version", ver),
                            "labels": list(getattr(detail, "labels", []) or []),
                            "prompt": content,
                            "commit_message": getattr(detail, "commit_message", None),
                        }
                except Exception:
                    pass  # version vừa bị xoá — bỏ qua
        log(True, "list existing prompts", f"{len(existing_by_content)} version đã tồn tại")
    except Exception as exc:
        log(False, "list existing prompts", f"{type(exc).__name__}: {exc} (tiếp tục tạo mới)")

    for ver, text, labels in plan:
        if args.dry_run:
            print(f"DRY  | would create v{ver} labels={labels}")
            continue
        if text in existing_by_content:
            hit = existing_by_content[text]
            log(True, f"reuse v{hit['version']}", f"content khớp labels={hit['labels']}")
            versions.append(hit)
            continue
        try:
            created = client.create_prompt(
                name=PROMPT_NAME,
                prompt=text,
                labels=labels,
                type="text",
                commit_message=f"day13 v{ver}",
            )
            log(True, f"create_prompt v{ver}", f"labels={labels} version={created.version}")
            versions.append(
                {
                    "name": PROMPT_NAME,
                    "version": created.version,
                    "labels": list(created.labels),
                    "prompt": text,
                    "commit_message": created.commit_message,
                }
            )
        except Exception as exc:
            log(False, f"create_prompt v{ver}", f"{type(exc).__name__}: {exc}")

    if args.dry_run:
        print("DRY  | đổi label production -> v2")
        if not args.stop_after_promote:
            print("DRY  | rollback production -> v1")
        print("Dry-run xong. Bật --dry-run off (mặc định) khi có backend.")
        return

    # -- 4. Lấy toàn bộ version từ server để làm evidence ----------------------
    try:
        resp = client.api.prompts.list(name=PROMPT_NAME)
        items: list[dict] = []
        for meta in getattr(resp, "data", []) or []:
            for ver in getattr(meta, "versions", []) or []:
                try:
                    detail = client.api.prompts.get(PROMPT_NAME, version=ver)
                    items.append(
                        {
                            "name": PROMPT_NAME,
                            "version": getattr(detail, "version", ver),
                            "labels": list(getattr(detail, "labels", []) or []),
                            "prompt": getattr(detail, "prompt", None),
                            "commit_message": getattr(detail, "commit_message", None),
                        }
                    )
                except Exception as exc:  # version có thể vừa bị xoá
                    log(False, f"get prompt v{ver}", f"{type(exc).__name__}: {exc}")
        versions.extend(items)
        log(True, "list prompts API", f"{len(items)} version")
    except Exception as exc:
        log(False, "list prompts API", f"{type(exc).__name__}: {exc}")

    # -- 5. Đổi label production sang version chứa v2 ---------------------------
    # Target theo version thực tế giữ nội dung v2 (sau content-reuse số version
    # có thể không còn là 1/2 nếu chạy nhiều lần).
    v2_ver = existing_by_content.get(PROMPT_V2, {}).get("version")
    v1_ver = existing_by_content.get(PROMPT_V1, {}).get("version")
    if not v1_ver or not v2_ver:
        v1_ver = next((v.get("version") for v in versions if v.get("prompt") == PROMPT_V1), v1_ver)
        v2_ver = next((v.get("version") for v in versions if v.get("prompt") == PROMPT_V2), v2_ver)

    lifecycle: dict[str, object] = {
        "prompt_name": PROMPT_NAME,
        "baseline_version": v1_ver,
        "candidate_version": v2_ver,
    }
    if v2_ver is not None:
        try:
            # Explicitly move candidate away from any stale optional version.
            client.update_prompt(name=PROMPT_NAME, version=v2_ver, new_labels=["candidate"])
            candidate = client.api.prompts.get(PROMPT_NAME, label="candidate")
            candidate_ver = getattr(candidate, "version", None)
            lifecycle["candidate_version_after_normalize"] = candidate_ver
            if candidate_ver != v2_ver:
                raise RuntimeError(f"hậu kiểm candidate=v{candidate_ver}, mong đợi v{v2_ver}")

            client.update_prompt(
                name=PROMPT_NAME, version=v2_ver, new_labels=["candidate", "production"]
            )
            promoted = client.api.prompts.get(PROMPT_NAME, label="production")
            promoted_ver = getattr(promoted, "version", None)
            lifecycle["after_promote_production_version"] = promoted_ver
            if promoted_ver != v2_ver:
                raise RuntimeError(f"hậu kiểm production=v{promoted_ver}, mong đợi v{v2_ver}")
            log(True, f"update_prompt v{v2_ver} -> production", "đã hậu kiểm production trỏ tới v2")
        except Exception as exc:
            log(False, f"update_prompt v{v2_ver} -> production", f"{type(exc).__name__}: {exc}")
    else:
        log(False, "update_prompt v2 -> production", "không tìm thấy version chứa v2")

    # -- 6. Rollback production về version chứa v1 ------------------------------
    if args.stop_after_promote:
        log(True, "stop after promote", "giữ production ở v2 để chụp evidence UI")
    elif v1_ver is not None:
        try:
            client.update_prompt(
                name=PROMPT_NAME, version=v1_ver, new_labels=["baseline", "production"]
            )
            rolled_back = client.api.prompts.get(PROMPT_NAME, label="production")
            rollback_ver = getattr(rolled_back, "version", None)
            lifecycle["after_rollback_production_version"] = rollback_ver
            if rollback_ver != v1_ver:
                raise RuntimeError(f"hậu kiểm production=v{rollback_ver}, mong đợi v{v1_ver}")
            log(True, f"update_prompt v{v1_ver} -> production (rollback)", "đã hậu kiểm production trở về v1")
        except Exception as exc:
            log(False, f"update_prompt v{v1_ver} -> production (rollback)", f"{type(exc).__name__}: {exc}")
    elif not args.stop_after_promote:
        log(False, "update_prompt v1 -> production (rollback)", "không tìm thấy version chứa v1")

    # Refresh after lifecycle operations so evidence represents the final server
    # state rather than the snapshot taken before promote/rollback.
    try:
        final_items: list[dict] = []
        resp = client.api.prompts.list(name=PROMPT_NAME)
        for meta in getattr(resp, "data", []) or []:
            for ver in getattr(meta, "versions", []) or []:
                detail = client.api.prompts.get(PROMPT_NAME, version=ver)
                final_items.append(
                    {
                        "name": PROMPT_NAME,
                        "version": getattr(detail, "version", ver),
                        "labels": list(getattr(detail, "labels", []) or []),
                        "prompt": getattr(detail, "prompt", None),
                        "commit_message": getattr(detail, "commit_message", None),
                    }
                )
        versions.extend(final_items)
    except Exception as exc:
        log(False, "refresh final prompt state", f"{type(exc).__name__}: {exc}")

    # -- Ghi evidence -----------------------------------------------------------
    # De-dup theo (name, version) giữ thứ tự version tăng dần.
    seen: dict[tuple, dict] = {}
    for it in versions:
        seen[(it.get("name"), it.get("version"))] = it
    unique = sorted(seen.values(), key=lambda x: (x.get("name", ""), x.get("version", 0)))

    # Chỉ ghi evidence khi server thật sự trả về version. Nếu rỗng (VD lỗi mạng/
    # key sai) thì không tạo file rỗng gây hiểu lầm là đã có version.
    if not unique:
        print("\nFAIL: Không lấy được version nào từ Langfuse — KHÔNG ghi evidence. Kiểm tra key/mạng.")
        sys.exit(1)

    (EVIDENCE_DIR / "prompt_versions.json").write_text(
        json.dumps(unique, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (EVIDENCE_DIR / "prompt_lifecycle.json").write_text(
        json.dumps(lifecycle, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    lines = [f"{PROMPT_NAME} — các version trên Langfuse:"]
    for it in unique:
        lines.append(
            f"  v{it.get('version')}  labels={it.get('labels')}  "
            f"commit={it.get('commit_message')!r}  source={(it.get('prompt') or '')[:60]!r}..."
        )
    if args.stop_after_promote:
        lines.append(f"production → v{v2_ver} (đang giữ trạng thái promoted để chụp UI).")
    else:
        lines.append(
            f"production → v{v1_ver} (rollback) sau khi đổi sang v{v2_ver}; "
            "chạy load_test để ghi trace."
        )
    print("\nEvidence saved ->", EVIDENCE_DIR / "prompt_versions.json")
    for line in lines:
        print("  " + line)


if __name__ == "__main__":
    main()
