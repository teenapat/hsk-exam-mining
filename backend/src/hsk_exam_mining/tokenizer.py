from __future__ import annotations

import json
import re
from pathlib import Path

import jieba

from .models import WordOccurrence

CHINESE_WORD_RE = re.compile(r"^[\u4e00-\u9fff]{1,}$")

STOP_WORDS = {
    "的",
    "了",
    "是",
    "在",
    "和",
    "也",
    "就",
    "都",
    "很",
    "吗",
    "呢",
    "啊",
    "把",
    "被",
    "与",
    "及",
    "并",
    "或",
}


def tokenize_corpus(corpus_by_exam_section: dict[str, dict[str, list[str]]]) -> list[WordOccurrence]:
    occurrences: list[WordOccurrence] = []
    for exam_id, section_map in corpus_by_exam_section.items():
        for section, texts in section_map.items():
            for text in texts:
                for token in jieba.cut(text):
                    token = token.strip()
                    if len(token) < 2:
                        continue
                    if token in STOP_WORDS:
                        continue
                    if not CHINESE_WORD_RE.match(token):
                        continue
                    occurrences.append(WordOccurrence(word=token, examId=exam_id, section=section))
    return occurrences


def dump_phase3(occurrences: list[WordOccurrence], output_json_dir: Path) -> None:
    output_json_dir.mkdir(parents=True, exist_ok=True)
    (output_json_dir / "phase3_word_occurrences.json").write_text(
        json.dumps([o.to_dict() for o in occurrences], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

