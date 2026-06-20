from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path

from pypdf import PdfReader


FUNCTION_WORD_SEED = {
    "我",
    "你",
    "他",
    "她",
    "它",
    "我们",
    "你们",
    "他们",
    "她们",
    "什么",
    "怎么",
    "为什么",
    "哪",
    "哪里",
    "谁",
    "几",
    "吗",
    "呢",
    "吧",
    "的",
    "了",
    "着",
    "过",
    "是",
    "有",
    "在",
    "和",
    "跟",
    "对",
    "把",
    "被",
    "给",
    "从",
    "到",
    "就",
    "才",
    "还",
    "也",
    "都",
    "又",
    "很",
    "太",
    "更",
    "最",
    "不",
    "没",
}


def _normalized_entropy(counts: list[int]) -> float:
    total = sum(counts)
    if total <= 0:
        return 0.0
    probs = [c / total for c in counts if c > 0]
    if len(probs) <= 1:
        return 0.0
    entropy = -sum(p * math.log(p) for p in probs)
    return entropy / math.log(len(counts))


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _read_text(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(file_path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    return file_path.read_text(encoding="utf-8", errors="ignore")


def _load_basic_seed_from_raw_vocab(root: Path) -> set[str]:
    raw_dir = root / "data" / "raw"
    if not raw_dir.exists():
        return set()

    seed: set[str] = set()
    for file_path in raw_dir.iterdir():
        if not file_path.is_file():
            continue
        name = file_path.name.lower()
        if "vocabulary level" not in name and "hsk" not in name:
            continue
        if file_path.suffix.lower() not in {".pdf", ".txt", ".csv", ".json"}:
            continue
        try:
            text = _read_text(file_path)
        except Exception:
            continue

        for token in re.findall(r"[\u4e00-\u9fff]{1,6}", text):
            word = token.strip()
            if not word:
                continue
            # Keep mostly single-word vocabulary entries.
            if len(word) > 4:
                continue
            seed.add(word)
    return seed


def build_basic_candidates(root: Path) -> tuple[list[dict], Path, Path]:
    overview_path = root / "output" / "json" / "overview.json"
    stats_path = root / "output" / "json" / "vocabulary_stats.json"
    if not overview_path.exists() or not stats_path.exists():
        raise FileNotFoundError("Missing overview.json or vocabulary_stats.json. Run pipeline first.")

    overview = json.loads(overview_path.read_text(encoding="utf-8"))
    stats = json.loads(stats_path.read_text(encoding="utf-8"))
    total_exams = max(1, int(overview.get("totalExams", 1)))
    raw_seed_words = _load_basic_seed_from_raw_vocab(root)
    basic_seed = set(FUNCTION_WORD_SEED) | raw_seed_words

    rows: list[dict] = []
    for item in stats:
        word = str(item.get("word", "")).strip()
        if not word:
            continue
        freq = int(item.get("totalOccurrences", 0))
        exams = int(item.get("examsAppeared", 0))
        listening = int(item.get("listeningCount", 0))
        reading = int(item.get("readingCount", 0))
        grammar = int(item.get("grammarCount", 0))
        vocab = int(item.get("vocabularyCount", 0))
        total_sections = max(1, listening + reading + grammar + vocab)

        coverage_ratio = exams / total_exams
        listening_ratio = listening / total_sections
        section_entropy = _normalized_entropy([listening, reading, grammar, vocab])
        is_short = 1 if len(word) <= 2 else 0
        is_seed = 1 if word in basic_seed else 0
        is_raw_seed = 1 if word in raw_seed_words else 0

        # High score = likely "basic" word rather than exam-discriminative word.
        score = (
            coverage_ratio * 0.50
            + section_entropy * 0.20
            + listening_ratio * 0.15
            + is_short * 0.05
            + is_seed * 0.35
        )
        score = _clamp01(score)

        reasons: list[str] = []
        if coverage_ratio >= 0.75:
            reasons.append("high_coverage")
        if section_entropy >= 0.80:
            reasons.append("multi_section_common")
        if listening_ratio >= 0.55:
            reasons.append("listening_heavy")
        if is_short:
            reasons.append("short_word")
        if is_seed:
            reasons.append("seed_function_word")
        if is_raw_seed:
            reasons.append("raw_hsk_basic_seed")

        is_candidate = coverage_ratio >= 0.45 and (score >= 0.58 or is_seed == 1)
        if not is_candidate:
            continue

        rows.append(
            {
                "word": word,
                "totalOccurrences": freq,
                "examsAppeared": exams,
                "coverageRatio": round(coverage_ratio, 4),
                "listeningRatio": round(listening_ratio, 4),
                "sectionEntropy": round(section_entropy, 4),
                "isShort": bool(is_short),
                "isSeedWord": bool(is_seed),
                "isRawHskSeedWord": bool(is_raw_seed),
                "basicCandidateScore": round(score, 4),
                "reasons": "|".join(reasons) if reasons else "",
            }
        )

    rows.sort(key=lambda x: (x["basicCandidateScore"], x["coverageRatio"], x["totalOccurrences"]), reverse=True)

    output_csv = root / "output" / "csv" / "basic_words_candidates.csv"
    output_json = root / "output" / "json" / "basic_words_candidates.json"
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)

    if rows:
        with output_csv.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    else:
        output_csv.write_text("", encoding="utf-8")

    output_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return rows, output_csv, output_json


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    raw_seed_words = _load_basic_seed_from_raw_vocab(root)
    rows, csv_path, json_path = build_basic_candidates(root)
    print(
        json.dumps(
            {
                "candidateCount": len(rows),
                "rawSeedWordCount": len(raw_seed_words),
                "csv": str(csv_path),
                "json": str(json_path),
                "top10": rows[:10],
            },
            ensure_ascii=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

