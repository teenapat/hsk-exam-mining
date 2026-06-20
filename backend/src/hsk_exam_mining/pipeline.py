from __future__ import annotations

import json
import shutil
from pathlib import Path

from .analysis import (
    build_vocab_graph,
    compute_vocabulary_stats,
    detect_topics,
    dump_phase4_and_advanced,
    exam_similarity,
    generate_wordclouds,
    mine_grammar_patterns,
    predictive_relevance,
    rank_high_value_words,
    top_words_by_section,
)
from .config import build_config
from .enrichment import build_vocabulary_cards, dump_cards
from .parser import dump_phase1, parse_raw_exams
from .recommendations import build_study_recommendations
from .reports import write_overview_json, write_study_pack_pdfs, write_summary_report
from .sentence_builder import build_sentence_builder_items, dump_sentence_builder
from .tokenizer import dump_phase3, tokenize_corpus


def run_pipeline(root_dir: Path | None = None) -> dict:
    config = build_config(root_dir)
    config.raw_dir.mkdir(parents=True, exist_ok=True)
    config.output_json_dir.mkdir(parents=True, exist_ok=True)
    config.output_csv_dir.mkdir(parents=True, exist_ok=True)
    config.output_reports_dir.mkdir(parents=True, exist_ok=True)

    extra_raw = config.root_dir / "hsk-exam"
    parsed = parse_raw_exams([config.raw_dir, extra_raw])
    dump_phase1(parsed, config.output_json_dir)

    occurrences = tokenize_corpus(parsed.corpus_by_exam_section)
    dump_phase3(occurrences, config.output_json_dir)

    stats = compute_vocabulary_stats(occurrences)
    high_value = rank_high_value_words(stats)
    grammar_ranking = mine_grammar_patterns(parsed.raw_exam_texts, parsed.corpus_by_exam_section)
    listening_top = top_words_by_section(stats, "Listening", top_n=150)
    reading_top = top_words_by_section(stats, "Reading", top_n=150)
    topics = detect_topics(occurrences)
    graph = build_vocab_graph(parsed.corpus_by_exam_section)
    recommendations = build_study_recommendations(stats)
    similarity_rows = exam_similarity(occurrences)
    predictive_rows = predictive_relevance(stats, total_exams=len(parsed.corpus_by_exam_section))

    question_texts: dict[str, list[str]] = {}
    for exam_id, section_map in parsed.corpus_by_exam_section.items():
        question_texts[exam_id] = [doc for docs in section_map.values() for doc in docs]
    cards = build_vocabulary_cards(stats[:1000], question_texts=question_texts)
    card_map = {card.word: card for card in cards}
    high_value_enriched = []
    for row in high_value:
        card = card_map.get(row["word"])
        high_value_enriched.append(
            {
                **row,
                "pinyin": card.pinyin if card else "",
                "meaning": card.meaning if card else "Meaning not provided yet",
            }
        )
    dump_phase4_and_advanced(
        stats=stats,
        high_value=high_value_enriched,
        grammar_ranking=grammar_ranking,
        listening_top=listening_top,
        reading_top=reading_top,
        topics=topics,
        vocab_graph=graph,
        recommendations=recommendations,
        similarity_rows=similarity_rows,
        predictive_rows=predictive_rows,
        output_json_dir=config.output_json_dir,
        output_csv_dir=config.output_csv_dir,
    )
    dump_cards(cards, config.output_json_dir)

    write_summary_report(
        output_reports_dir=config.output_reports_dir,
        total_exams=len(parsed.corpus_by_exam_section),
        total_questions=len(parsed.questions),
        total_vocabulary=len(stats),
        total_scripts=len(parsed.scripts),
        top_words=high_value,
        grammar_patterns=grammar_ranking,
    )
    write_study_pack_pdfs(
        output_reports_dir=config.output_reports_dir,
        cards=[c.to_dict() for c in cards],
        high_value_words=high_value_enriched,
    )
    write_overview_json(
        output_json_dir=config.output_json_dir,
        total_exams=len(parsed.corpus_by_exam_section),
        total_questions=len(parsed.questions),
        total_vocabulary=len(stats),
        total_scripts=len(parsed.scripts),
    )
    sentence_items = build_sentence_builder_items(
        parsed.questions,
        exam_file_map=parsed.exam_file_map,
        output_reports_dir=config.output_reports_dir,
    )
    dump_sentence_builder(sentence_items, config.output_json_dir, config.output_csv_dir)
    generate_wordclouds(stats, config.output_reports_dir)
    _sync_frontend_data(config.output_json_dir, config.frontend_public_data_dir, config.output_reports_dir)

    run_result = {
        "totalExams": len(parsed.corpus_by_exam_section),
        "totalQuestions": len(parsed.questions),
        "totalVocabulary": len(stats),
        "totalListeningScripts": len(parsed.scripts),
        "totalSentenceBuilderItems": len(sentence_items),
        "outputJsonDir": str(config.output_json_dir),
        "outputCsvDir": str(config.output_csv_dir),
        "outputReportsDir": str(config.output_reports_dir),
    }
    (config.output_json_dir / "pipeline_run_meta.json").write_text(
        json.dumps(run_result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return run_result


def _sync_frontend_data(output_json_dir: Path, frontend_public_data_dir: Path, output_reports_dir: Path) -> None:
    frontend_public_data_dir.mkdir(parents=True, exist_ok=True)
    for file_path in output_json_dir.glob("*.json"):
        shutil.copy2(file_path, frontend_public_data_dir / file_path.name)
    source_image_dir = output_reports_dir / "sentence_images"
    target_image_dir = frontend_public_data_dir / "sentence_images"
    target_image_dir.mkdir(parents=True, exist_ok=True)
    if source_image_dir.exists():
        for image_path in source_image_dir.glob("*.png"):
            shutil.copy2(image_path, target_image_dir / image_path.name)

