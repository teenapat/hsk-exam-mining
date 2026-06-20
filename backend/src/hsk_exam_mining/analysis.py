from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import jieba
import networkx as nx
import numpy as np
import pandas as pd
from pypdf import PdfReader
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from wordcloud import WordCloud

from .models import VocabularyStats, WordOccurrence

GRAMMAR_PATTERNS = [
    "虽然.*但是",
    "不仅.*而且",
    "越来越",
    "一边.*一边",
    "先.*再",
]

TOPIC_LABELS = [
    "Work",
    "Travel",
    "Shopping",
    "Health",
    "Education",
    "Technology",
    "Food",
    "Transportation",
    "Family",
]

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


def compute_vocabulary_stats(occurrences: list[WordOccurrence]) -> list[VocabularyStats]:
    grouped: dict[str, dict] = {}
    for item in occurrences:
        if item.word not in grouped:
            grouped[item.word] = {
                "totalOccurrences": 0,
                "exams": set(),
                "listeningCount": 0,
                "readingCount": 0,
                "grammarCount": 0,
                "vocabularyCount": 0,
            }
        entry = grouped[item.word]
        entry["totalOccurrences"] += 1
        entry["exams"].add(item.examId)
        if item.section == "Listening":
            entry["listeningCount"] += 1
        elif item.section == "Reading":
            entry["readingCount"] += 1
        elif item.section == "Grammar":
            entry["grammarCount"] += 1
        elif item.section == "Vocabulary":
            entry["vocabularyCount"] += 1

    stats = [
        VocabularyStats(
            word=word,
            totalOccurrences=data["totalOccurrences"],
            examsAppeared=len(data["exams"]),
            listeningCount=data["listeningCount"],
            readingCount=data["readingCount"],
            grammarCount=data["grammarCount"],
            vocabularyCount=data["vocabularyCount"],
        )
        for word, data in grouped.items()
    ]
    return sorted(stats, key=lambda x: x.totalOccurrences, reverse=True)


def _read_text_for_basic_seed(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(file_path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    return file_path.read_text(encoding="utf-8", errors="ignore")


def _load_basic_words_from_raw(root_dir: Path) -> set[str]:
    raw_dir = root_dir / "data" / "raw"
    if not raw_dir.exists():
        return set()

    words: set[str] = set()
    for file_path in raw_dir.iterdir():
        if not file_path.is_file():
            continue
        name = file_path.name.lower()
        if "vocabulary level" not in name and "hsk" not in name:
            continue
        if file_path.suffix.lower() not in {".pdf", ".txt", ".csv", ".json"}:
            continue
        try:
            text = _read_text_for_basic_seed(file_path)
        except Exception:
            continue
        for token in re.findall(r"[\u4e00-\u9fff]{1,4}", text):
            t = token.strip()
            if t:
                words.add(t)
    return words


def _normalized_entropy(values: list[int]) -> float:
    total = sum(values)
    if total <= 0:
        return 0.0
    probs = [v / total for v in values if v > 0]
    if len(probs) <= 1:
        return 0.0
    entropy = -sum(p * math.log(p) for p in probs)
    return entropy / math.log(len(values))


def rank_high_value_words(stats: list[VocabularyStats], total_exams: int, root_dir: Path | None = None) -> list[dict]:
    total_exams = max(1, total_exams)
    basic_seed = set(FUNCTION_WORD_SEED)
    if root_dir is not None:
        basic_seed |= _load_basic_words_from_raw(root_dir)

    ranking: list[dict] = []
    for idx, item in enumerate(stats, start=1):
        coverage_ratio = item.examsAppeared / total_exams
        total_sections = max(1, item.listeningCount + item.readingCount + item.grammarCount + item.vocabularyCount)
        listening_ratio = item.listeningCount / total_sections
        reading_vocab_ratio = (item.readingCount + item.grammarCount + item.vocabularyCount) / total_sections
        section_entropy = _normalized_entropy(
            [item.listeningCount, item.readingCount, item.grammarCount, item.vocabularyCount]
        )

        is_seed_word = item.word in basic_seed
        heuristic_basic = (
            len(item.word) <= 2
            and coverage_ratio >= 0.70
            and listening_ratio >= 0.55
            and section_entropy >= 0.55
        )
        is_basic_word = is_seed_word or heuristic_basic

        base_score = float(item.totalOccurrences * item.examsAppeared)
        coverage_weight = 0.8 + (coverage_ratio * 0.4)
        section_weight = 1.0 + min(0.35, reading_vocab_ratio * 0.35)
        basic_penalty = 0.22 if is_basic_word else 1.12
        final_score = base_score * coverage_weight * section_weight * basic_penalty

        ranking_reasons: list[str] = []
        if coverage_ratio >= 0.75:
            ranking_reasons.append("coverage สูง")
        if reading_vocab_ratio >= 0.55:
            ranking_reasons.append("เด่นในพาร์ตอ่าน/ไวยากรณ์/คำศัพท์")
        elif listening_ratio >= 0.60:
            ranking_reasons.append("เด่นในพาร์ตฟัง")
        if is_basic_word:
            ranking_reasons.append("คำพื้นฐานทั่วไป (ถูกลดคะแนน)")
        else:
            ranking_reasons.append("ไม่ใช่คำพื้นฐาน")

        ranking.append(
            {
                "rank": idx,
                "word": item.word,
                "score": round(final_score, 2),
                "frequency": item.totalOccurrences,
                "examCoverage": item.examsAppeared,
                "coverageRatio": round(coverage_ratio, 4),
                "isBasicWord": is_basic_word,
                "rankingReasons": ranking_reasons,
            }
        )
    ranking.sort(key=lambda x: x["score"], reverse=True)
    for idx, item in enumerate(ranking, start=1):
        item["rank"] = idx
    return ranking


def mine_grammar_patterns(raw_exam_texts: dict[str, str], corpus_by_exam_section: dict[str, dict[str, list[str]]]) -> list[dict]:
    import re

    records: list[dict] = []
    for pattern in GRAMMAR_PATTERNS:
        total_count = 0
        exams = set()
        section_distribution = defaultdict(int)
        compiled = re.compile(pattern)

        for exam_id, text in raw_exam_texts.items():
            count = len(compiled.findall(text))
            if count:
                exams.add(exam_id)
                total_count += count

        for exam_id, sections in corpus_by_exam_section.items():
            for section, docs in sections.items():
                c = sum(len(compiled.findall(doc)) for doc in docs)
                section_distribution[section] += c

        records.append(
            {
                "pattern": pattern,
                "occurrenceCount": total_count,
                "examCount": len(exams),
                "sectionDistribution": dict(section_distribution),
            }
        )
    records.sort(key=lambda x: x["occurrenceCount"], reverse=True)
    return records


def top_words_by_section(stats: list[VocabularyStats], section: str, top_n: int = 100) -> list[dict]:
    key_map = {
        "Listening": "listeningCount",
        "Reading": "readingCount",
        "Grammar": "grammarCount",
        "Vocabulary": "vocabularyCount",
    }
    key = key_map[section]
    ranked = sorted(
        [{"word": s.word, "count": getattr(s, key)} for s in stats if getattr(s, key) > 0],
        key=lambda x: x["count"],
        reverse=True,
    )
    return ranked[:top_n]


def detect_topics(occurrences: list[WordOccurrence], top_k_words: int = 2000) -> list[dict]:
    exam_word_counter: dict[str, Counter] = defaultdict(Counter)
    for item in occurrences:
        exam_word_counter[item.examId][item.word] += 1

    exams = sorted(exam_word_counter.keys())
    if len(exams) < 2:
        return []

    global_counter: Counter = Counter()
    for cnt in exam_word_counter.values():
        global_counter.update(cnt)
    vocab = [w for w, _ in global_counter.most_common(top_k_words)]
    docs = [" ".join(word for word, _ in exam_word_counter[e].most_common()) for e in exams]
    if not docs:
        return []

    vectorizer = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
    matrix = vectorizer.fit_transform(docs)
    n_clusters = min(6, max(2, len(exams) // 2))
    km = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
    labels = km.fit_predict(matrix)

    result: list[dict] = []
    for topic_idx in range(n_clusters):
        exam_ids = [exams[i] for i, label in enumerate(labels) if label == topic_idx]
        combined = Counter()
        for exam_id in exam_ids:
            combined.update(exam_word_counter[exam_id])
        top_words = [w for w, _ in combined.most_common(12)]
        result.append(
            {
                "topicId": topic_idx,
                "topicLabel": TOPIC_LABELS[topic_idx % len(TOPIC_LABELS)],
                "examIds": exam_ids,
                "topWords": top_words,
                "frequency": int(sum(combined.values())),
            }
        )
    return sorted(result, key=lambda x: x["frequency"], reverse=True)


def build_vocab_graph(corpus_by_exam_section: dict[str, dict[str, list[str]]], top_n: int = 500) -> dict:
    token_docs: list[list[str]] = []
    counter = Counter()
    for sections in corpus_by_exam_section.values():
        for docs in sections.values():
            for text in docs:
                tokens = [tok.strip() for tok in jieba.cut(text) if len(tok.strip()) >= 2]
                token_docs.append(tokens)
                counter.update(tokens)

    valid = {word for word, _ in counter.most_common(top_n)}
    graph = nx.Graph()
    for tokens in token_docs:
        filtered = [t for t in tokens if t in valid]
        for i, token in enumerate(filtered):
            for j in range(i + 1, min(i + 6, len(filtered))):
                other = filtered[j]
                if token == other:
                    continue
                if graph.has_edge(token, other):
                    graph[token][other]["weight"] += 1
                else:
                    graph.add_edge(token, other, weight=1)

    edges = sorted(
        [{"source": u, "target": v, "weight": int(d["weight"])} for u, v, d in graph.edges(data=True)],
        key=lambda x: x["weight"],
        reverse=True,
    )[:2000]
    nodes = [{"id": n, "degree": int(graph.degree(n))} for n in graph.nodes()]
    return {"nodes": nodes, "edges": edges}


def generate_wordclouds(stats: list[VocabularyStats], output_reports_dir: Path) -> None:
    output_reports_dir.mkdir(parents=True, exist_ok=True)
    frequencies = {s.word: s.totalOccurrences for s in stats[:800]}
    if not frequencies:
        return
    cloud = WordCloud(
        width=1920,
        height=1080,
        background_color="white",
        font_path=_resolve_cjk_font_path(),
        collocations=False,
        max_words=600,
        prefer_horizontal=0.9,
    )
    image = cloud.generate_from_frequencies(frequencies).to_image()
    image.save(output_reports_dir / "wordcloud_overall.png")


def _resolve_cjk_font_path() -> str | None:
    candidates = [
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simsun.ttc"),
        Path("C:/Windows/Fonts/msyh.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return str(path)
    return None


def exam_similarity(occurrences: list[WordOccurrence]) -> list[dict]:
    exam_vocab: dict[str, set[str]] = defaultdict(set)
    for o in occurrences:
        exam_vocab[o.examId].add(o.word)
    exam_ids = sorted(exam_vocab.keys())
    rows = []
    for i, exam_a in enumerate(exam_ids):
        for exam_b in exam_ids[i + 1 :]:
            inter = len(exam_vocab[exam_a] & exam_vocab[exam_b])
            union = len(exam_vocab[exam_a] | exam_vocab[exam_b]) or 1
            rows.append(
                {
                    "examA": exam_a,
                    "examB": exam_b,
                    "jaccardSimilarity": round(inter / union, 4),
                    "sharedWords": inter,
                }
            )
    rows.sort(key=lambda x: x["jaccardSimilarity"], reverse=True)
    return rows


def predictive_relevance(stats: list[VocabularyStats], total_exams: int) -> list[dict]:
    rows = []
    total_exams = max(total_exams, 1)
    for item in stats:
        coverage_ratio = item.examsAppeared / total_exams
        relevance = (item.totalOccurrences * 0.7) + (coverage_ratio * 100 * 0.3)
        rows.append(
            {
                "word": item.word,
                "frequency": item.totalOccurrences,
                "coverage": item.examsAppeared,
                "predictedRelevanceScore": round(relevance, 2),
            }
        )
    rows.sort(key=lambda x: x["predictedRelevanceScore"], reverse=True)
    return rows


def dump_phase4_and_advanced(
    stats: list[VocabularyStats],
    high_value: list[dict],
    grammar_ranking: list[dict],
    listening_top: list[dict],
    reading_top: list[dict],
    topics: list[dict],
    vocab_graph: dict,
    recommendations: list[dict],
    similarity_rows: list[dict],
    predictive_rows: list[dict],
    output_json_dir: Path,
    output_csv_dir: Path,
) -> None:
    output_json_dir.mkdir(parents=True, exist_ok=True)
    output_csv_dir.mkdir(parents=True, exist_ok=True)

    stats_payload = [s.to_dict() for s in stats]
    (output_json_dir / "vocabulary_stats.json").write_text(
        json.dumps(stats_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_json_dir / "top_100_words.json").write_text(
        json.dumps(stats_payload[:100], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_json_dir / "top_500_words.json").write_text(
        json.dumps(stats_payload[:500], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_json_dir / "high_value_words.json").write_text(
        json.dumps(high_value[:1000], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_json_dir / "grammar_patterns.json").write_text(
        json.dumps(grammar_ranking, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_json_dir / "listening_top_words.json").write_text(
        json.dumps(listening_top, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_json_dir / "reading_top_words.json").write_text(
        json.dumps(reading_top, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_json_dir / "topics.json").write_text(json.dumps(topics, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_json_dir / "vocab_graph.json").write_text(
        json.dumps(vocab_graph, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_json_dir / "study_recommendations.json").write_text(
        json.dumps(recommendations, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_json_dir / "exam_similarity.json").write_text(
        json.dumps(similarity_rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_json_dir / "predictive_analysis.json").write_text(
        json.dumps(predictive_rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    _to_thai_csv(
        pd.DataFrame(stats_payload),
        output_csv_dir / "vocabulary_frequency.csv",
        {
            "word": "คำศัพท์",
            "totalOccurrences": "ความถี่รวม",
            "examsAppeared": "จำนวนข้อสอบที่พบ",
            "listeningCount": "พาร์ตฟัง",
            "readingCount": "พาร์ตอ่าน",
            "grammarCount": "พาร์ตไวยากรณ์",
            "vocabularyCount": "พาร์ตคำศัพท์",
        },
    )
    _to_thai_csv(
        pd.DataFrame(high_value),
        output_csv_dir / "high_value_words.csv",
        {
            "rank": "อันดับ",
            "word": "คำศัพท์",
            "score": "คะแนนความสำคัญ",
            "frequency": "ความถี่",
            "examCoverage": "จำนวนข้อสอบที่ครอบคลุม",
            "pinyin": "พินอิน",
            "meaning": "ความหมาย",
        },
    )
    _to_thai_csv(pd.DataFrame(listening_top), output_csv_dir / "listening_top_words.csv", {"word": "คำศัพท์", "count": "จำนวนครั้ง"})
    _to_thai_csv(pd.DataFrame(reading_top), output_csv_dir / "reading_top_words.csv", {"word": "คำศัพท์", "count": "จำนวนครั้ง"})
    _to_thai_csv(
        pd.DataFrame(grammar_ranking),
        output_csv_dir / "grammar_patterns.csv",
        {"pattern": "แพทเทิร์นไวยากรณ์", "occurrenceCount": "จำนวนครั้ง", "examCount": "จำนวนข้อสอบ", "sectionDistribution": "สัดส่วนตามพาร์ต"},
    )
    _to_thai_csv(
        pd.DataFrame(topics),
        output_csv_dir / "topics.csv",
        {"topicId": "รหัสหัวข้อ", "topicLabel": "หัวข้อ", "examIds": "รหัสข้อสอบ", "topWords": "คำเด่น", "frequency": "ความถี่"},
    )
    _to_thai_csv(
        pd.DataFrame(recommendations),
        output_csv_dir / "study_recommendations.csv",
        {"tier": "ระดับ", "word": "คำศัพท์", "frequency": "ความถี่", "examCoverage": "จำนวนข้อสอบที่ครอบคลุม"},
    )
    _to_thai_csv(
        pd.DataFrame(similarity_rows),
        output_csv_dir / "exam_similarity.csv",
        {"examA": "ข้อสอบ A", "examB": "ข้อสอบ B", "jaccardSimilarity": "คะแนนความคล้าย", "sharedWords": "คำซ้ำร่วม"},
    )
    _to_thai_csv(
        pd.DataFrame(predictive_rows),
        output_csv_dir / "predictive_analysis.csv",
        {"word": "คำศัพท์", "frequency": "ความถี่", "coverage": "จำนวนข้อสอบที่พบ", "predictedRelevanceScore": "คะแนนคาดการณ์"},
    )


def _to_thai_csv(df: pd.DataFrame, output_path: Path, columns_map: dict[str, str]) -> None:
    renamed = df.rename(columns=columns_map)
    renamed.to_csv(output_path, index=False, encoding="utf-8-sig")

