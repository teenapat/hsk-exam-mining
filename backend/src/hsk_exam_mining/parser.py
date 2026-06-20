from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from bs4 import BeautifulSoup
from pypdf import PdfReader

from .models import ExamQuestion, ListeningScript
from .normalizer import normalize_text

EXAM_ID_RE = re.compile(r"(H\d{5})", re.IGNORECASE)
QUESTION_RE = re.compile(r"(?m)(\d{1,3})[\.、]\s*(.+?)(?=(?:\n\d{1,3}[\.、])|\Z)", re.S)
OPTION_RE = re.compile(r"[A-D][\.．、:：]\s*([^\n]+)")
ANSWER_RE = re.compile(r"(?m)(\d{1,3})\s*[\.\-、:：]?\s*([A-D])")
HSK_51_55_RE = re.compile(
    r"(?ms)\b(5[1-5])\s*[\.、:：]?\s*(.+?)(?=(?:\n\s*5[1-5]\s*[\.、:：])|(?:\n\s*5[6-9]\s*[\.、:：])|(?:\n\s*第\s*96)|\Z)"
)
HSK_96_100_WORD_RE = re.compile(r"(?m)\b(9[6-9]|100)\s*[\.．、:：]?\s*([\u4e00-\u9fff]{1,8})\b")
HSK_96_100_ANSWER_LINE_RE = re.compile(r"(?m)^\s*(9[6-9]|100)\s*[\.．、:：]?\s*(.{4,80})$")
EXAM_MARKER_RE = re.compile(r"H\d{5}\s*-\s*\d+")
_RAPID_OCR_ENGINE = None


@dataclass(slots=True)
class ParsedData:
    questions: list[ExamQuestion]
    scripts: list[ListeningScript]
    corpus_by_exam_section: dict[str, dict[str, list[str]]]
    raw_exam_texts: dict[str, str]
    exam_file_map: dict[str, str]

    def to_dict(self) -> dict:
        return asdict(self)


def _read_file_text(file_path: Path) -> str:
    if file_path.suffix.lower() in {".html", ".htm"}:
        soup = BeautifulSoup(file_path.read_text(encoding="utf-8", errors="ignore"), "lxml")
        return soup.get_text(separator="\n")
    if file_path.suffix.lower() == ".pdf":
        reader = PdfReader(str(file_path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    return file_path.read_text(encoding="utf-8", errors="ignore")


def _classify_file_type(name: str) -> str:
    lowered = name.lower()
    if "audio" in lowered or "script" in lowered:
        return "audio_script"
    if "answer" in lowered and "exam" not in lowered:
        return "answer"
    if "answer-sheet" in lowered:
        return "answer"
    return "exam"


def _infer_section(question_no: int) -> str:
    if question_no <= 45:
        return "Listening"
    if question_no <= 65:
        return "Vocabulary"
    if question_no <= 85:
        return "Grammar"
    return "Reading"


def _discover_files(raw_dirs: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for directory in raw_dirs:
        if not directory.exists():
            continue
        files.extend(
            path
            for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() in {".html", ".htm", ".pdf", ".txt"}
        )
    return sorted(files)


def parse_raw_exams(raw_dirs: Iterable[Path]) -> ParsedData:
    file_groups: dict[str, dict[str, Path]] = {}
    for file_path in _discover_files(raw_dirs):
        match = EXAM_ID_RE.search(file_path.name)
        if not match:
            continue
        exam_id = match.group(1).upper()
        file_type = _classify_file_type(file_path.name)
        file_groups.setdefault(exam_id, {})[file_type] = file_path

    questions: list[ExamQuestion] = []
    scripts: list[ListeningScript] = []
    corpus_by_exam_section: dict[str, dict[str, list[str]]] = {}
    raw_exam_texts: dict[str, str] = {}

    for exam_id, files in file_groups.items():
        exam_raw_text = _read_file_text(files["exam"]) if "exam" in files else ""
        answer_raw_text = _read_file_text(files["answer"]) if "answer" in files else ""
        exam_text = _normalize_keep_lines(exam_raw_text) if exam_raw_text else ""
        answer_text = _normalize_keep_lines(answer_raw_text) if answer_raw_text else ""
        is_exam_answer_pdf = bool(
            "exam" in files
            and files["exam"].suffix.lower() == ".pdf"
            and "answer" in files["exam"].name.lower()
            and "exam" in files["exam"].name.lower()
        )
        audio_text = normalize_text(_read_file_text(files["audio_script"])) if "audio_script" in files else ""

        if is_exam_answer_pdf and not answer_text:
            # Combined exam-answer PDFs usually embed both content + answer keys.
            answer_text = exam_text

        writing_answers_override: dict[int, str] = {}
        candidate_text = answer_text if answer_text else exam_text
        target_pdf: Path | None = None
        if is_exam_answer_pdf and "exam" in files and files["exam"].suffix.lower() == ".pdf":
            target_pdf = files["exam"]
        if target_pdf is not None and not _extract_hsk4_96_100_reference_answers(candidate_text):
            writing_answers_override = _extract_hsk4_96_100_answers_from_pdf_ocr(target_pdf)

        if audio_text:
            scripts.append(ListeningScript(examId=exam_id, content=audio_text))

        answers = {int(m.group(1)): m.group(2) for m in ANSWER_RE.finditer(answer_text)}
        exam_questions = _extract_questions(
            exam_id,
            exam_text,
            answers,
            answer_text=answer_text,
            writing_answers_override=writing_answers_override,
            is_exam_answer_pdf=is_exam_answer_pdf,
        )
        questions.extend(exam_questions)
        raw_exam_texts[exam_id] = exam_text
        corpus_by_exam_section[exam_id] = _build_exam_corpus(exam_questions, audio_text)

    return ParsedData(
        questions=questions,
        scripts=scripts,
        corpus_by_exam_section=corpus_by_exam_section,
        raw_exam_texts=raw_exam_texts,
        exam_file_map={exam_id: str(files["exam"]) for exam_id, files in file_groups.items() if "exam" in files},
    )


def _extract_questions(
    exam_id: str,
    exam_text: str,
    answers: dict[int, str],
    answer_text: str = "",
    writing_answers_override: dict[int, str] | None = None,
    is_exam_answer_pdf: bool = False,
) -> list[ExamQuestion]:
    results: list[ExamQuestion] = []

    for match in QUESTION_RE.finditer(exam_text):
        question_no = int(match.group(1))
        block = match.group(2).strip()
        if is_exam_answer_pdf and _is_suspicious_block(block):
            continue
        options = [opt.strip() for opt in OPTION_RE.findall(block)]
        question_text = OPTION_RE.sub("", block).strip()
        if not question_text:
            continue
        section = _infer_section(question_no)
        results.append(
            ExamQuestion(
                examId=exam_id,
                section=section,
                questionNo=question_no,
                question=question_text,
                options=options,
                answer=answers.get(question_no),
                confidence=0.92,
                parseMethod="question_regex",
            )
        )

    fixed_rows = _extract_hsk4_fixed_questions(
        exam_id,
        exam_text,
        answers,
        answer_text=answer_text,
        writing_answers_override=writing_answers_override,
    )
    if fixed_rows:
        fixed_map = {q.questionNo: q for q in fixed_rows}
        replaced: list[ExamQuestion] = []
        replaced_nos: set[int] = set()
        for q in results:
            if q.questionNo in fixed_map and fixed_map[q.questionNo].confidence > q.confidence:
                replaced.append(fixed_map[q.questionNo])
                replaced_nos.add(q.questionNo)
            else:
                replaced.append(q)
        for q_no, q in fixed_map.items():
            if q_no not in replaced_nos and all(existing.questionNo != q_no for existing in replaced):
                replaced.append(q)
        results = replaced

    # Fallback when OCR text lacks numeric markers, or parse quality is too low.
    if exam_text and len(results) < 30:
        existing_nos = {q.questionNo for q in results}
        chunks = [chunk.strip() for chunk in re.split(r"(?<=[\.\?!])\s+", exam_text) if len(chunk.strip()) > 10]
        for idx, sentence in enumerate(chunks[:100], start=1):
            if idx in existing_nos:
                continue
            results.append(
                ExamQuestion(
                    examId=exam_id,
                    section=_infer_section(idx),
                    questionNo=idx,
                    question=sentence,
                    options=[],
                    answer=answers.get(idx),
                    confidence=0.22,
                    parseMethod="sentence_fallback_low_conf",
                )
            )
    results.sort(key=lambda x: x.questionNo)

    # Combined exam-answer PDFs are noisier; keep only plausible range.
    if is_exam_answer_pdf:
        results = [q for q in results if 1 <= q.questionNo <= 100]
    return results


def _extract_hsk4_fixed_questions(
    exam_id: str,
    exam_text: str,
    answers: dict[int, str],
    answer_text: str = "",
    writing_answers_override: dict[int, str] | None = None,
) -> list[ExamQuestion]:
    results: list[ExamQuestion] = []
    writing_answers = dict(writing_answers_override or {})
    writing_answers.update(_extract_hsk4_96_100_reference_answers(answer_text))
    if not writing_answers:
        writing_answers = _extract_hsk4_96_100_reference_answers(exam_text)

    for match in HSK_51_55_RE.finditer(exam_text):
        question_no = int(match.group(1))
        block = match.group(2).strip()
        if _is_suspicious_block(block):
            continue
        question_text = OPTION_RE.sub("", block).strip()
        if len(question_text) < 6:
            continue
        results.append(
            ExamQuestion(
                examId=exam_id,
                section=_infer_section(question_no),
                questionNo=question_no,
                question=question_text,
                options=[opt.strip() for opt in OPTION_RE.findall(block)],
                answer=answers.get(question_no),
                confidence=0.86,
                parseMethod="hsk4_51_55_rule",
            )
        )

    for match in HSK_96_100_WORD_RE.finditer(exam_text):
        question_no = int(match.group(1))
        vocab = match.group(2).strip()
        if not vocab:
            continue
        results.append(
            ExamQuestion(
                examId=exam_id,
                section=_infer_section(question_no),
                questionNo=question_no,
                question=f"看图，用词造句：{vocab}",
                options=[],
                answer=writing_answers.get(question_no, answers.get(question_no)),
                confidence=0.95,
                parseMethod="hsk4_96_100_rule",
            )
        )

    # OCR-only scanned papers may have no readable question words in text layer.
    # In that case, still emit 96-100 rows so reference answers are not lost.
    existing_96_100 = {q.questionNo for q in results if 96 <= q.questionNo <= 100}
    for question_no in range(96, 101):
        if question_no in existing_96_100:
            continue
        if question_no not in writing_answers:
            continue
        results.append(
            ExamQuestion(
                examId=exam_id,
                section=_infer_section(question_no),
                questionNo=question_no,
                question="看图，用词造句",
                options=[],
                answer=writing_answers.get(question_no, answers.get(question_no)),
                confidence=0.75,
                parseMethod="hsk4_96_100_ocr_answer_only",
            )
        )
    return results


def _extract_hsk4_96_100_reference_answers(exam_text: str) -> dict[int, str]:
    result: dict[int, str] = {}
    for match in HSK_96_100_ANSWER_LINE_RE.finditer(exam_text):
        question_no = int(match.group(1))
        line = match.group(2).strip()
        if question_no < 96 or question_no > 100:
            continue
        # Keep only sentence-like lines from reference answers.
        if len(line) < 5:
            continue
        if not re.search(r"[。！？!?\.]$", line):
            continue
        if "看图" in line or "用词造句" in line:
            continue
        result[question_no] = line
    return result


def _extract_hsk4_96_100_answers_from_pdf_ocr(pdf_path: Path) -> dict[int, str]:
    try:
        import fitz
        import numpy as np
        from rapidocr_onnxruntime import RapidOCR
    except Exception:
        return {}

    try:
        doc = fitz.open(str(pdf_path))
    except Exception:
        return {}

    global _RAPID_OCR_ENGINE
    if _RAPID_OCR_ENGINE is None:
        _RAPID_OCR_ENGINE = RapidOCR()
    ocr = _RAPID_OCR_ENGINE
    lines: list[str] = []
    found_answers: dict[int, str] = {}
    try:
        start_idx = max(0, doc.page_count - 6)
        for page_idx in range(doc.page_count - 1, start_idx - 1, -1):
            page = doc[page_idx]
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False)
            image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            ocr_result, _ = ocr(image)
            if not ocr_result:
                continue
            page_lines = [str(item[1]).strip() for item in ocr_result if len(item) >= 2 and str(item[1]).strip()]
            lines.extend(page_lines)
            page_answers = _extract_hsk4_96_100_reference_answers("\n".join(page_lines))
            found_answers.update(page_answers)
            if all(no in found_answers for no in range(96, 101)):
                return found_answers
    except Exception:
        return {}
    finally:
        doc.close()

    if not lines:
        return {}
    ocr_text = "\n".join(lines)
    return _extract_hsk4_96_100_reference_answers(ocr_text)


def _is_suspicious_block(text: str) -> bool:
    if EXAM_MARKER_RE.search(text):
        return True
    if len(text) > 260:
        return True
    numeric_hits = len(re.findall(r"\b\d{1,3}\b", text))
    if numeric_hits >= 8:
        return True
    return False


def _normalize_keep_lines(text: str) -> str:
    normalized_lines: list[str] = []
    for line in text.replace("\r", "\n").split("\n"):
        cleaned = normalize_text(line)
        if cleaned:
            normalized_lines.append(cleaned)
    return "\n".join(normalized_lines)


def _build_exam_corpus(questions: list[ExamQuestion], audio_text: str) -> dict[str, list[str]]:
    sections = {"Listening": [], "Reading": [], "Grammar": [], "Vocabulary": []}
    for question in questions:
        sections.setdefault(question.section, []).append(" ".join([question.question, *question.options]))
    if audio_text:
        sections["Listening"].append(audio_text)
    return sections


def dump_phase1(parsed: ParsedData, output_json_dir: Path) -> None:
    output_json_dir.mkdir(parents=True, exist_ok=True)
    (output_json_dir / "phase1_questions.json").write_text(
        json.dumps([q.to_dict() for q in parsed.questions], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_json_dir / "phase1_listening_scripts.json").write_text(
        json.dumps([s.to_dict() for s in parsed.scripts], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

