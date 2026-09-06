"""Small helpers: language detection, code extraction, formatting."""

from __future__ import annotations

import re

DETECTORS = [
    ("python", [r"\bdef\s+\w+\s*\(", r"^\s*import\s+\w+", r"\bprint\s*\(", r"\belif\b", r"__init__"]),
    ("javascript", [r"\b(?:const|let|var)\s+\w+\s*=", r"=>", r"console\.log", r"\bfunction\s*\("]),
    ("typescript", [r":\s*(?:string|number|boolean)\b", r"\binterface\s+\w+", r"\btype\s+\w+\s*="]),
    ("java", [r"\bpublic\s+class\b", r"System\.out\.println", r"\bvoid\s+main\b"]),
    ("cpp", [r"#include\s*<", r"std::", r"\bcout\b"]),
    ("csharp", [r"\busing\s+System\b", r"Console\.WriteLine"]),
    ("go", [r"\bfunc\s+\w+\s*\(", r"\bpackage\s+main\b", r"fmt\."]),
    ("rust", [r"\bfn\s+\w+\s*\(", r"\blet\s+mut\b", r"println!"]),
    ("php", [r"<\?php", r"\$\w+\s*="]),
    ("ruby", [r"\bdef\s+\w+\s*$", r"\bend\b", r"puts\s"]),
    ("sql", [r"\bSELECT\b.+\bFROM\b", r"\bINSERT\s+INTO\b", r"\bCREATE\s+TABLE\b"]),
    ("bash", [r"^#!/bin/(?:ba)?sh", r"\becho\s+", r"\bsudo\b"]),
    ("html", [r"<!DOCTYPE html>", r"</\w+>"]),
]


def detect_language(code: str) -> str | None:
    """Best-effort language guess for syntax highlighting."""
    if not code or not code.strip():
        return None
    scores: dict[str, int] = {}
    for lang, patterns in DETECTORS:
        hits = sum(
            1
            for p in patterns
            if re.search(p, code, flags=re.IGNORECASE | re.MULTILINE)
        )
        if hits:
            scores[lang] = hits
    if not scores:
        return None
    return max(scores, key=scores.get)


def count_lines(code: str) -> int:
    if not code or not code.strip():
        return 0
    return len(code.strip().splitlines())


def looks_like_code(text: str) -> bool:
    """Rough check used to decide whether a chat message contains code."""
    if not text:
        return False
    if "```" in text:
        return True
    return detect_language(text) is not None and count_lines(text) >= 2


def encode_image(file_bytes: bytes, mime_type: str = "image/png") -> str:
    """Turn uploaded image bytes into the data URI the chat API expects."""
    import base64

    encoded = base64.b64encode(file_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def image_blocks(images: list[dict]) -> list[dict]:
    """Build the image content blocks for a multimodal message.

    `images` is a list of {"bytes": ..., "mime": ...} dicts.
    """
    blocks = []
    for image in images:
        blocks.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": encode_image(image["bytes"], image.get("mime", "image/png")),
                    "detail": "high",  # code screenshots need the fine detail
                },
            }
        )
    return blocks


def truncate(text: str, limit: int = 60) -> str:
    text = (text or "").strip().replace("\n", " ")
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def find_repetition(text: str, window: int = 500) -> str | None:
    """Detect a degenerate repetition loop at the END of the text.

    Language models occasionally get stuck emitting the same token forever
    ("six six six six…"). It happens most with near-greedy decoding, and the
    stream will happily run until the token limit, producing a wall of garbage.

    Returns the repeating unit when the tail is one short string repeated over
    and over, otherwise None.

    Deliberately conservative — code and prose legitimately repeat lines and
    words, and truncating a good answer is worse than the bug being guarded
    against. Short units must repeat many more times than long ones.
    """
    tail = text[-window:]
    if len(tail) < 40:
        return None

    for unit_len in range(1, 41):
        unit = tail[-unit_len:]
        if not unit.strip():
            continue
        repeats, pos = 0, len(tail)
        while pos - unit_len >= 0 and tail[pos - unit_len:pos] == unit:
            repeats += 1
            pos -= unit_len
        span = repeats * unit_len
        need = 12 if unit_len <= 3 else (8 if unit_len <= 10 else 5)
        if repeats >= need and span >= 40:
            return unit
    return None
