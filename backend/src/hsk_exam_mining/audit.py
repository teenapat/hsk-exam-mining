from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

from .config import build_config
from .normalizer import normalize_text
from .parser import ANSWER_RE, EXAM_ID_RE, _classify_file_type, _discover_files, _read_file_text, parse_raw_exams

SUSPECT_EXAM_MARK_RE = re.compile(r"H\d{5}\s*-\s*\d+")
SUSPECT_QUESTION_NO_RE = re.compile(r"\b\d{1,3}\b")


def run_data_audit(root_dir: Path | None = None) -> dict:
    config = build_config(root_dir)
    raw_dirs = [config.raw_dir, config.root_dir / "hsk-exam"]
    parsed = parse_raw_exams(raw_dirs)

    grouped = _group_files(raw_dirs)
    question_by_exam: dict[str, list[dict]] = {}
    for q in parsed.questions:
        question_by_exam.setdefault(q.examId, []).append(q.to_dict())
    scripts_by_exam = {s.examId: s.to_dict() for s in parsed.scripts}

    exam_reports: list[dict] = []
    for exam_id in sorted(grouped.keys()):
        files = grouped[exam_id]
        questions = question_by_exam.get(exam_id, [])
        report = _audit_single_exam(exam_id, files, questions, scripts_by_exam.get(exam_id))
        exam_reports.append(report)

    severity_counter = Counter()
    for row in exam_reports:
        for issue in row["issues"]:
            severity_counter[issue["severity"]] += 1

    summary = {
        "totalExamsDetected": len(grouped),
        "totalExamsParsed": len(question_by_exam),
        "totalQuestionsParsed": len(parsed.questions),
        "totalScriptsParsed": len(parsed.scripts),
        "issueCounts": dict(severity_counter),
    }
    payload = {"summary": summary, "examReports": exam_reports}
    _write_reports(payload, config.output_reports_dir)
    return payload


def _group_files(raw_dirs: Iterable[Path]) -> dict[str, dict[str, Path]]:
    grouped: dict[str, dict[str, Path]] = {}
    for file_path in _discover_files(raw_dirs):
        match = EXAM_ID_RE.search(file_path.name)
        if not match:
            continue
        exam_id = match.group(1).upper()
        grouped.setdefault(exam_id, {})[_classify_file_type(file_path.name)] = file_path
    return grouped


def _audit_single_exam(exam_id: str, files: dict[str, Path], questions: list[dict], script: dict | None) -> dict:
    issues: list[dict] = []
    metrics: dict[str, int | float | str | list[int]] = {}

    has_exam = "exam" in files
    has_answer = "answer" in files
    has_audio = "audio_script" in files
    metrics["hasExamFile"] = int(has_exam)
    metrics["hasAnswerFile"] = int(has_answer)
    metrics["hasAudioFile"] = int(has_audio)

    if not has_exam:
        issues.append(_issue("error", "missing_exam_file", "ไม่พบไฟล์ข้อสอบ (exam file)"))
    if not has_answer:
        issues.append(_issue("warning", "missing_answer_file", "ไม่พบไฟล์เฉลย (answer file)"))
    if not has_audio:
        issues.append(_issue("info", "missing_audio_script", "ไม่พบไฟล์ audio script สำหรับชุดนี้"))

    qnos = [int(q["questionNo"]) for q in questions]
    metrics["parsedQuestionCount"] = len(questions)
    metrics["parsedUniqueQuestionCount"] = len(set(qnos))
    metrics["minQuestionNo"] = min(qnos) if qnos else -1
    metrics["maxQuestionNo"] = max(qnos) if qnos else -1

    if not questions:
        issues.append(_issue("error", "no_questions_parsed", "ไม่สามารถ parse ข้อสอบออกมาได้"))
    elif len(questions) < 60:
        issues.append(_issue("warning", "low_question_count", f"จำนวนข้อที่ parse ได้ค่อนข้างต่ำ ({len(questions)})"))

    duplicates = sorted([no for no, cnt in Counter(qnos).items() if cnt > 1])
    metrics["duplicateQuestionNos"] = duplicates
    if duplicates:
        issues.append(_issue("warning", "duplicate_question_numbers", f"พบเลขข้อซ้ำ: {duplicates[:12]}"))

    if has_answer:
        answer_text = normalize_text(_read_file_text(files["answer"]))
        answer_keys = {int(m.group(1)): m.group(2) for m in ANSWER_RE.finditer(answer_text)}
        metrics["answerKeyCount"] = len(answer_keys)
        covered = sum(1 for q in questions if q.get("answer") in {"A", "B", "C", "D"})
        metrics["mappedAnswerCount"] = covered
        metrics["answerCoverageRatio"] = round((covered / len(questions)), 3) if questions else 0.0

        if answer_keys and questions:
            parsed_nos = {int(q["questionNo"]) for q in questions}
            missing_in_parse = sorted(answer_keys.keys() - parsed_nos)
            missing_in_answer = sorted(parsed_nos - answer_keys.keys())
            metrics["answerButNoQuestion"] = missing_in_parse[:30]
            metrics["questionButNoAnswer"] = missing_in_answer[:30]
            if len(missing_in_parse) > 15:
                issues.append(_issue("warning", "many_answer_keys_without_questions", f"มีเฉลยที่หาเลขข้อใน parsed ไม่เจอ {len(missing_in_parse)} ข้อ"))
            if len(missing_in_answer) > 15:
                issues.append(_issue("warning", "many_questions_without_answer", f"มีข้อที่ parse ได้แต่ไม่มีเฉลยแมพ {len(missing_in_answer)} ข้อ"))

    suspicious = _suspicious_question_rows(questions)
    metrics["suspiciousQuestionRows"] = len(suspicious)
    if suspicious:
        issues.append(_issue("warning", "suspicious_ocr_merge_rows", f"พบบรรทัดน่าสงสัยจาก OCR merge {len(suspicious)} ข้อ"))

    if script:
        script_len = len(script.get("content", ""))
        metrics["audioScriptLength"] = script_len
        if script_len < 120:
            issues.append(_issue("warning", "audio_script_too_short", f"audio script สั้นผิดปกติ ({script_len} chars)"))

    status = _derive_status(issues)
    return {
        "examId": exam_id,
        "status": status,
        "files": {k: str(v) for k, v in files.items()},
        "metrics": metrics,
        "issues": issues,
        "samples": {"suspiciousQuestions": suspicious[:8]},
    }


def _suspicious_question_rows(questions: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for q in questions:
        text = str(q.get("question", ""))
        hits = 0
        if SUSPECT_EXAM_MARK_RE.search(text):
            hits += 2
        if len(text) > 220:
            hits += 1
        if len(SUSPECT_QUESTION_NO_RE.findall(text)) >= 6:
            hits += 1
        if hits >= 2:
            rows.append(
                {
                    "questionNo": q.get("questionNo"),
                    "section": q.get("section"),
                    "preview": text[:220],
                }
            )
    return rows


def _derive_status(issues: list[dict]) -> str:
    if any(issue["severity"] == "error" for issue in issues):
        return "error"
    if any(issue["severity"] == "warning" for issue in issues):
        return "warning"
    return "ok"


def _issue(severity: str, code: str, message: str) -> dict:
    return {"severity": severity, "code": code, "message": message}


def _write_reports(payload: dict, output_reports_dir: Path) -> None:
    output_reports_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_reports_dir / "data_quality_audit.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md_path = output_reports_dir / "data_quality_audit.md"
    lines = [
        "# Data Quality Audit",
        "",
        "## Summary",
        f"- Exams detected: {payload['summary']['totalExamsDetected']}",
        f"- Exams parsed: {payload['summary']['totalExamsParsed']}",
        f"- Questions parsed: {payload['summary']['totalQuestionsParsed']}",
        f"- Scripts parsed: {payload['summary']['totalScriptsParsed']}",
        f"- Issue counts: {payload['summary']['issueCounts']}",
        "",
        "## Per Exam Status",
        "",
    ]
    for exam in payload["examReports"]:
        lines.append(f"- {exam['examId']}: {exam['status']} (issues={len(exam['issues'])})")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    csv_path = output_reports_dir / "data_quality_audit_exam_summary.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "examId",
                "status",
                "parsedQuestionCount",
                "parsedUniqueQuestionCount",
                "answerKeyCount",
                "mappedAnswerCount",
                "suspiciousQuestionRows",
                "issuesCount",
            ],
        )
        writer.writeheader()
        for exam in payload["examReports"]:
            metrics = exam["metrics"]
            writer.writerow(
                {
                    "examId": exam["examId"],
                    "status": exam["status"],
                    "parsedQuestionCount": metrics.get("parsedQuestionCount", ""),
                    "parsedUniqueQuestionCount": metrics.get("parsedUniqueQuestionCount", ""),
                    "answerKeyCount": metrics.get("answerKeyCount", ""),
                    "mappedAnswerCount": metrics.get("mappedAnswerCount", ""),
                    "suspiciousQuestionRows": metrics.get("suspiciousQuestionRows", ""),
                    "issuesCount": len(exam["issues"]),
                }
            )

