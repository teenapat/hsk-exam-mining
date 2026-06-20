from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont


def write_summary_report(
    output_reports_dir: Path,
    total_exams: int,
    total_questions: int,
    total_vocabulary: int,
    total_scripts: int,
    top_words: list[dict],
    grammar_patterns: list[dict],
) -> None:
    output_reports_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_reports_dir / "analysis_summary.md"
    lines = [
        "# HSK4 Historical Exam Intelligence Report",
        "",
        "## Overview",
        f"- Total exams analyzed: {total_exams}",
        f"- Total questions: {total_questions}",
        f"- Total vocabulary: {total_vocabulary}",
        f"- Total listening scripts: {total_scripts}",
        "",
        "## Top 20 High Value Words",
        "",
    ]
    for item in top_words[:20]:
        lines.append(f"- {item['word']} (score={item['score']}, freq={item['frequency']}, coverage={item['examCoverage']})")
    lines.extend(["", "## Top Grammar Patterns", ""])
    for item in grammar_patterns[:10]:
        lines.append(f"- {item['pattern']} (count={item['occurrenceCount']}, exams={item['examCount']})")
    md_path.write_text("\n".join(lines), encoding="utf-8")


def write_study_pack_pdfs(output_reports_dir: Path, cards: list[dict], high_value_words: list[dict]) -> None:
    output_reports_dir.mkdir(parents=True, exist_ok=True)
    top_cards_by_word = {c["word"]: c for c in cards}
    for size in (100, 300, 500):
        selected = high_value_words[:size]
        pdf_path = output_reports_dir / f"study_pack_top_{size}.pdf"
        _render_study_pack(pdf_path, selected, top_cards_by_word, title=f"HSK4 Study Pack - Top {size} Words")


def _render_study_pack(pdf_path: Path, ranking_rows: list[dict], card_map: dict[str, dict], title: str) -> None:
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4
    font_name = _register_cjk_font()
    y = height - 20 * mm
    c.setFont(font_name, 14)
    c.drawString(15 * mm, y, title)
    y -= 10 * mm
    c.setFont(font_name, 10)

    for idx, row in enumerate(ranking_rows, start=1):
        card = card_map.get(row["word"], {})
        example = (card.get("exampleSentences") or [""])[0]
        text = (
            f"{idx}. {row['word']} | score {row['score']} | pinyin: {card.get('pinyin', '')} | "
            f"meaning: {card.get('meaning', '')} | freq: {row['frequency']} | coverage: {row['examCoverage']} | ex: {example}"
        )
        wrapped = _wrap_text(text, max_chars=95)
        for line in wrapped:
            c.drawString(12 * mm, y, line)
            y -= 5 * mm
            if y <= 15 * mm:
                c.showPage()
                c.setFont(font_name, 10)
                y = height - 20 * mm
    c.save()


def _register_cjk_font() -> str:
    # Primary: built-in CJK CID font from ReportLab (good compatibility for Chinese text).
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        return "STSong-Light"
    except Exception:
        pass

    # Fallback: common Windows Chinese fonts.
    candidates = [
        ("MicrosoftYaHei", Path("C:/Windows/Fonts/msyh.ttc")),
        ("SimSun", Path("C:/Windows/Fonts/simsun.ttc")),
        ("SimHei", Path("C:/Windows/Fonts/simhei.ttf")),
    ]
    for font_alias, font_path in candidates:
        if not font_path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont(font_alias, str(font_path)))
            return font_alias
        except Exception:
            continue

    return "Helvetica"


def _wrap_text(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    lines = []
    start = 0
    while start < len(text):
        lines.append(text[start : start + max_chars])
        start += max_chars
    return lines


def write_overview_json(
    output_json_dir: Path,
    total_exams: int,
    total_questions: int,
    total_vocabulary: int,
    total_scripts: int,
) -> None:
    payload = {
        "totalExams": total_exams,
        "totalQuestions": total_questions,
        "totalVocabulary": total_vocabulary,
        "totalListeningScripts": total_scripts,
    }
    (output_json_dir / "overview.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

