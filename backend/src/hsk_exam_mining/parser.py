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


@dataclass(slots=True)
class ParsedData:
    questions: list[ExamQuestion]
    scripts: list[ListeningScript]
    corpus_by_exam_section: dict[str, dict[str, list[str]]]
    raw_exam_texts: dict[str, str]

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
        exam_text = normalize_text(_read_file_text(files["exam"])) if "exam" in files else ""
        answer_text = normalize_text(_read_file_text(files["answer"])) if "answer" in files else ""
        audio_text = normalize_text(_read_file_text(files["audio_script"])) if "audio_script" in files else ""

        if audio_text:
            scripts.append(ListeningScript(examId=exam_id, content=audio_text))

        answers = {int(m.group(1)): m.group(2) for m in ANSWER_RE.finditer(answer_text)}
        exam_questions = _extract_questions(exam_id, exam_text, answers)
        questions.extend(exam_questions)
        raw_exam_texts[exam_id] = exam_text
        corpus_by_exam_section[exam_id] = _build_exam_corpus(exam_questions, audio_text)

    return ParsedData(
        questions=questions,
        scripts=scripts,
        corpus_by_exam_section=corpus_by_exam_section,
        raw_exam_texts=raw_exam_texts,
    )


def _extract_questions(exam_id: str, exam_text: str, answers: dict[int, str]) -> list[ExamQuestion]:
    results: list[ExamQuestion] = []
    for match in QUESTION_RE.finditer(exam_text):
        question_no = int(match.group(1))
        block = match.group(2).strip()
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
            )
        )

    # Fallback when OCR text lacks numeric markers.
    if not results and exam_text:
        chunks = [chunk.strip() for chunk in re.split(r"(?<=[\.\?!])\s+", exam_text) if len(chunk.strip()) > 10]
        for idx, sentence in enumerate(chunks[:100], start=1):
            results.append(
                ExamQuestion(
                    examId=exam_id,
                    section=_infer_section(idx),
                    questionNo=idx,
                    question=sentence,
                    options=[],
                    answer=answers.get(idx),
                )
            )
    return results


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

