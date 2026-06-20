from __future__ import annotations

import json
import re
from pathlib import Path

import jieba

from .models import ExamQuestion

IMAGE_SENTENCE_HINTS = [
    "看图",
    "根据图",
    "根据图片",
    "用词造句",
    "造句",
]

BLANK_RE = re.compile(r"(_{2,}|（\s*）|\(\s*\)|\[\s*\])")
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]{2,}")
EXAM_PAGE_MARK_RE = re.compile(r"H\d{5}\s*-\s*\d+")


def build_sentence_builder_items(
    questions: list[ExamQuestion],
    exam_file_map: dict[str, str],
    output_reports_dir: Path,
) -> list[dict]:
    items: list[dict] = []
    for question in questions:
        if question.section not in {"Vocabulary", "Grammar", "Reading"}:
            continue
        is_target = _is_sentence_builder_target(question.question)
        if not is_target:
            continue
        if not _is_clean_prompt(question.question):
            continue

        keywords = _extract_keywords(question.question)
        items.append(
            {
                "id": f"{question.examId}-{question.questionNo}",
                "examId": question.examId,
                "questionNo": question.questionNo,
                "section": question.section,
                "prompt": question.question,
                "keywords": keywords,
                "options": question.options,
                "answer": question.answer,
                "hasImageHint": ("看图" in question.question) or ("根据图" in question.question) or question.questionNo >= 96,
                "confidence": round(float(question.confidence), 3),
                "parseMethod": question.parseMethod,
                "isTrusted": bool(question.confidence >= 0.75),
                "imagePath": None,
            }
        )

    # Fallback: if no direct match, include high-signal vocabulary/grammar questions.
    if not items:
        for question in questions:
            if question.section in {"Vocabulary", "Grammar"} and len(question.question) >= 8:
                items.append(
                    {
                        "id": f"{question.examId}-{question.questionNo}",
                        "examId": question.examId,
                        "questionNo": question.questionNo,
                        "section": question.section,
                        "prompt": question.question,
                        "keywords": _extract_keywords(question.question),
                        "options": question.options,
                        "answer": question.answer,
                        "hasImageHint": False,
                        "confidence": round(float(question.confidence), 3),
                        "parseMethod": question.parseMethod,
                        "isTrusted": bool(question.confidence >= 0.75),
                        "imagePath": None,
                    }
                )
                if len(items) >= 120:
                    break

    image_dir = output_reports_dir / "sentence_images"
    image_dir.mkdir(parents=True, exist_ok=True)
    for item in items:
        exam_path = exam_file_map.get(item["examId"])
        if not exam_path:
            continue
        image_path = _render_question_image_snapshot(
            exam_pdf_path=Path(exam_path),
            exam_id=item["examId"],
            question_no=int(item["questionNo"]),
            prompt=item["prompt"],
            output_dir=image_dir,
        )
        if image_path:
            item["imagePath"] = f"/data/sentence_images/{image_path.name}"

    dedup: dict[str, dict] = {}
    for item in items:
        existing = dedup.get(item["id"])
        if not existing or item["confidence"] > existing["confidence"]:
            dedup[item["id"]] = item

    final_items = list(dedup.values())
    final_items.sort(key=lambda x: (not x["isTrusted"], -x["confidence"], x["examId"], x["questionNo"]))
    return final_items


def _render_question_image_snapshot(
    exam_pdf_path: Path,
    exam_id: str,
    question_no: int,
    prompt: str,
    output_dir: Path,
) -> Path | None:
    if exam_pdf_path.suffix.lower() != ".pdf":
        return None
    try:
        import fitz  # PyMuPDF
    except Exception:
        return None

    output_path = output_dir / f"{exam_id}_q{question_no}.png"
    try:
        doc = fitz.open(str(exam_pdf_path))
    except Exception:
        return None

    try:
        target_page = _select_best_page_for_snapshot(
            doc,
            question_no=question_no,
            prompt=prompt,
            is_combined_exam_answer=("exam" in exam_pdf_path.name.lower() and "answer" in exam_pdf_path.name.lower()),
        )
        if target_page is None:
            return None

        # User requested full-page snapshots for all sentence-builder items.
        pix = target_page.get_pixmap(matrix=fitz.Matrix(2.2, 2.2), alpha=False)
        pix.save(str(output_path))
        return output_path
    except Exception:
        return None
    finally:
        doc.close()


def _select_best_page_for_snapshot(doc, question_no: int, prompt: str, is_combined_exam_answer: bool):
    prompt_word = ""
    if "：" in prompt:
        prompt_word = prompt.split("：", maxsplit=1)[1].strip().split()[0]
    elif ":" in prompt:
        prompt_word = prompt.split(":", maxsplit=1)[1].strip().split()[0]

    candidates: list[tuple[float, int]] = []
    for page_idx in range(doc.page_count):
        page = doc[page_idx]
        text = page.get_text("text")
        image_count = len(page.get_images(full=True))
        drawing_count = len(page.get_drawings())
        score = float(image_count) * 1.2 + min(8.0, drawing_count / 30)

        if f"{question_no}." in text or f"{question_no}、" in text:
            score += 2.2
        if f"{question_no} " in text:
            score += 0.8
        if "第96-100题" in text:
            score += 4.5
        if "用词造句" in text:
            score += 3.0
        if prompt_word and prompt_word in text:
            score += 1.8
        if "答案" in text:
            score -= 6.0
        if "参考答案" in text:
            score -= 7.0
        if "听力原文" in text:
            score -= 4.0
        if "答题卡" in text:
            score -= 3.0

        if question_no >= 96 and image_count > 0:
            score += 1.5
        if question_no >= 96 and "第96-100题" not in text:
            score -= 1.0
        if is_combined_exam_answer and "答案" in text:
            score -= 6.0
        candidates.append((score, page_idx))

    if not candidates:
        return None
    candidates.sort(reverse=True)
    best_page_idx = candidates[0][1]
    return doc[best_page_idx]


def _infer_question_clip_rect(page, question_no: int, prompt: str):
    number_rects = page.search_for(f"{question_no}.") + page.search_for(f"{question_no}、")
    if not number_rects:
        number_rects = page.search_for(str(question_no))
    word_hint = ""
    if "：" in prompt:
        word_hint = prompt.split("：", maxsplit=1)[1].strip()
    elif ":" in prompt:
        word_hint = prompt.split(":", maxsplit=1)[1].strip()
    word_rects = page.search_for(word_hint[:8]) if word_hint else []

    if number_rects:
        anchor = number_rects[0]
        x0 = max(page.rect.x0, anchor.x0 - 80)
        y0 = max(page.rect.y0, anchor.y0 - 90)
        x1 = min(page.rect.x1, page.rect.x1 - 30)
        y1 = min(page.rect.y1, anchor.y0 + 210)
        if question_no >= 96:
            y1 = min(page.rect.y1, anchor.y0 + 280)
        if word_rects:
            w = word_rects[0]
            x0 = min(x0, max(page.rect.x0, w.x0 - 140))
            y0 = min(y0, max(page.rect.y0, w.y0 - 110))
            y1 = max(y1, min(page.rect.y1, w.y1 + 180))
        if y1 - y0 > 80:
            return page.rect.__class__(x0, y0, x1, y1)

    try:
        blocks = page.get_text("dict").get("blocks", [])
    except Exception:
        return None

    image_boxes = []
    for block in blocks:
        if block.get("type") != 1:
            continue
        bbox = block.get("bbox")
        if not bbox:
            continue
        x0, y0, x1, y1 = bbox
        width = max(0, x1 - x0)
        height = max(0, y1 - y0)
        if width < 30 or height < 30:
            continue
        image_boxes.append((x0, y0, x1, y1))

    if not image_boxes:
        return None

    x0 = min(b[0] for b in image_boxes)
    y0 = min(b[1] for b in image_boxes)
    x1 = max(b[2] for b in image_boxes)
    y1 = max(b[3] for b in image_boxes)

    margin = 28
    page_rect = page.rect
    x0 = max(page_rect.x0, x0 - margin)
    y0 = max(page_rect.y0, y0 - margin)
    x1 = min(page_rect.x1, x1 + margin)
    y1 = min(page_rect.y1, y1 + margin)
    return page_rect.__class__(x0, y0, x1, y1)


def _is_sentence_builder_target(text: str) -> bool:
    if any(hint in text for hint in IMAGE_SENTENCE_HINTS):
        return True
    if BLANK_RE.search(text):
        return True
    if "第96-100题" in text:
        return True
    return False


def _is_clean_prompt(text: str) -> bool:
    # OCR noise guard: prompts with embedded exam-page markers are often merged blocks.
    if EXAM_PAGE_MARK_RE.search(text):
        return False
    if len(text) > 220:
        return False
    return True


def _extract_keywords(text: str) -> list[str]:
    keywords: list[str] = []
    for token in jieba.cut(text):
        token = token.strip()
        if len(token) < 2:
            continue
        if not CHINESE_RE.search(token):
            continue
        if token in {"下面", "根据", "选择", "正确", "句子", "图片"}:
            continue
        keywords.append(token)
    # Keep order and deduplicate.
    deduped = list(dict.fromkeys(keywords))
    return deduped[:8]


def dump_sentence_builder(items: list[dict], output_json_dir: Path, output_csv_dir: Path) -> None:
    output_json_dir.mkdir(parents=True, exist_ok=True)
    output_csv_dir.mkdir(parents=True, exist_ok=True)
    (output_json_dir / "sentence_builder_items.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    import pandas as pd

    pd.DataFrame(items).to_csv(output_csv_dir / "sentence_builder_items.csv", index=False, encoding="utf-8-sig")

