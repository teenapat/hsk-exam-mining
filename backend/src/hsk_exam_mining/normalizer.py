from __future__ import annotations

import re

_FULLWIDTH_MAP = str.maketrans(
    {
        "，": ",",
        "。": ".",
        "；": ";",
        "：": ":",
        "！": "!",
        "？": "?",
        "（": "(",
        "）": ")",
        "【": "[",
        "】": "]",
        "「": '"',
        "」": '"',
        "『": '"',
        "』": '"',
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "　": " ",
    }
)

_PUNCT_RE = re.compile(r"[^\w\s\u4e00-\u9fff\.,;:!\?'\"-]")
_SPACE_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    normalized = text.translate(_FULLWIDTH_MAP)
    normalized = _PUNCT_RE.sub(" ", normalized)
    normalized = _SPACE_RE.sub(" ", normalized)
    return normalized.strip()

