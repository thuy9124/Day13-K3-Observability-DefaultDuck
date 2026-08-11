from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


DEFAULT_PROMPT_TEMPLATE = "Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}"
DEFAULT_PROMPT_V2_TEMPLATE = (
    "Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}\n"
    "Yêu cầu: Trả lời ngắn gọn, có cấu trúc và đúng trọng tâm từ Docs."
)
DEFAULT_PROMPT_V3_TEMPLATE = (
    "Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}\n"
    "Rules: answer from Docs only; max 60 words; no PII; end with a one-line summary."
)
DEFAULT_PROMPT_V4_TEMPLATE = (
    "You are a grounded support assistant.\n"
    "Feature={{feature}}\nContext={{docs}}\nUser question={{message}}\n"
    "Rules:\n"
    "1. Use only facts supported by Context; never invent missing details.\n"
    "2. If Context is insufficient, say so and ask one focused follow-up question.\n"
    "3. Do not repeat or expose personal data from the question.\n"
    "4. Answer directly in at most 80 words.\n"
    "Output exactly two sections: Answer and Evidence."
)


@dataclass(frozen=True)
class ResolvedPrompt:
    text: str
    name: str
    label: str
    version: str
    source: str
    managed_prompt: Any | None = None
    fetch_error: str | None = None


def _compile_local_prompt(
    *, feature: str, docs: list[str], message: str, template: str = DEFAULT_PROMPT_TEMPLATE
) -> str:
    return (
        template.replace("{{feature}}", feature)
        .replace("{{docs}}", "\n".join(docs))
        .replace("{{message}}", message)
    )


def resolve_prompt(
    client: Any,
    *,
    feature: str,
    docs: list[str],
    message: str,
    enabled: bool,
) -> ResolvedPrompt:
    name = os.getenv("LANGFUSE_PROMPT_NAME", "day13-chat")
    label = os.getenv("LANGFUSE_PROMPT_LABEL", "production")
    local_variants = {
        "candidate-v2": (DEFAULT_PROMPT_V2_TEMPLATE, "local-v2"),
        "v2": (DEFAULT_PROMPT_V2_TEMPLATE, "local-v2"),
        "candidate-v3": (DEFAULT_PROMPT_V3_TEMPLATE, "local-v3"),
        "v3": (DEFAULT_PROMPT_V3_TEMPLATE, "local-v3"),
        "candidate": (DEFAULT_PROMPT_V4_TEMPLATE, "local-v4"),
        "candidate-v4": (DEFAULT_PROMPT_V4_TEMPLATE, "local-v4"),
        "v4": (DEFAULT_PROMPT_V4_TEMPLATE, "local-v4"),
        "staging": (DEFAULT_PROMPT_V4_TEMPLATE, "local-v4"),
    }
    template, version_name = local_variants.get(
        label, (DEFAULT_PROMPT_TEMPLATE, "local-v1")
    )
    text = _compile_local_prompt(feature=feature, docs=docs, message=message, template=template)
    if enabled:
        try:
            managed_prompt = client.get_prompt(
                name,
                label=label,
                type="text",
                fallback=DEFAULT_PROMPT_TEMPLATE,
                cache_ttl_seconds=60,
                fetch_timeout_seconds=2,
                max_retries=0,
            )
            if getattr(managed_prompt, "is_fallback", False):
                return ResolvedPrompt(
                    text=text,
                    name=name,
                    label=label,
                    version=version_name,
                    source="local-fallback",
                    fetch_error="LangfuseFallback",
                )
            return ResolvedPrompt(
                text=managed_prompt.compile(
                    feature=feature,
                    docs="\n".join(docs),
                    message=message,
                ),
                name=name,
                label=label,
                version=str(managed_prompt.version),
                source="langfuse",
                managed_prompt=managed_prompt,
            )
        except Exception as exc:  # Langfuse là dependency ngoài; app phải có fallback local
            return ResolvedPrompt(
                text=text,
                name=name,
                label=label,
                version=version_name,
                source="local-fallback",
                fetch_error=type(exc).__name__,
            )

    return ResolvedPrompt(
        text=text,
        name=name,
        label=label,
        version=version_name,
        source="local",
    )


