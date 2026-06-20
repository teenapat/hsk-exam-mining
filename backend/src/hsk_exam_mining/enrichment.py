from __future__ import annotations

import json
from pathlib import Path

from pypinyin import Style, pinyin

from .models import VocabularyCard, VocabularyStats

try:
    from cedict.cedict import DictionaryData, search as cedict_search
except Exception:  # pragma: no cover - optional runtime dependency fallback.
    DictionaryData = None
    cedict_search = None

try:
    from deep_translator import GoogleTranslator
except Exception:  # pragma: no cover - optional runtime dependency fallback.
    GoogleTranslator = None

DEFAULT_MEANINGS = {
    "工作": "to work; job",
    "学习": "to study; learning",
    "时间": "time",
    "朋友": "friend",
    "公司": "company",
    "问题": "question; problem",
    "觉得": "to feel; to think",
    "知道": "to know",
    "准备": "to prepare",
    "应该": "should; ought to",
}

_DICT_DATA = None
_TH_TRANSLATOR = None
_TH_CACHE: dict[str, str] = {}
_TH_CACHE_LOADED = False
TH_CACHE_PATH = Path(__file__).resolve().parents[3] / "output" / "json" / "meaning_th_cache.json"

DEFAULT_THAI_MEANINGS = {
    "工作": "ทำงาน; งาน",
    "学习": "เรียน; การเรียนรู้",
    "时间": "เวลา",
    "朋友": "เพื่อน",
    "公司": "บริษัท",
    "问题": "คำถาม; ปัญหา",
    "觉得": "รู้สึก; คิดว่า",
    "知道": "รู้",
    "准备": "เตรียม",
    "应该": "ควร",
}


def build_vocabulary_cards(stats: list[VocabularyStats], question_texts: dict[str, list[str]]) -> list[VocabularyCard]:
    cards: list[VocabularyCard] = []
    for item in stats:
        examples = _example_sentences(item.word, question_texts)
        meaning_en = _get_meaning_en(item.word)
        meaning_th = _get_meaning_th(item.word)
        cards.append(
            VocabularyCard(
                word=item.word,
                pinyin=_build_tone_pinyin(item.word),
                meaning=_compose_meaning(meaning_th, meaning_en),
                frequency=item.totalOccurrences,
                exampleSentences=examples,
            )
        )
    _save_thai_cache()
    return cards


def _example_sentences(word: str, question_texts: dict[str, list[str]]) -> list[str]:
    examples: list[str] = []
    for docs in question_texts.values():
        for sentence in docs:
            if word in sentence:
                examples.append(sentence[:140])
                if len(examples) == 3:
                    return examples
    return examples


def _build_tone_pinyin(word: str) -> str:
    tokenized = pinyin(word, style=Style.TONE, neutral_tone_with_five=False, heteronym=False)
    return " ".join(chunk[0] for chunk in tokenized if chunk and chunk[0]).strip()


def _get_meaning_en(word: str) -> str:
    if word in DEFAULT_MEANINGS:
        return DEFAULT_MEANINGS[word]

    dictionary_data = _get_dictionary_data()
    if dictionary_data and cedict_search:
        try:
            row = cedict_search(word, dictionary_data)
            if row:
                meaning = str(row[0]).strip()
                if meaning:
                    return _clean_meaning(meaning)
        except Exception:
            pass
    return "no dictionary entry"


def _get_meaning_th(word: str) -> str:
    _load_thai_cache()
    if word in _TH_CACHE:
        return _TH_CACHE[word]
    if word in DEFAULT_THAI_MEANINGS:
        _TH_CACHE[word] = DEFAULT_THAI_MEANINGS[word]
        return _TH_CACHE[word]

    translator = _get_th_translator()
    if translator:
        try:
            translated = translator.translate(word)
            translated = translated.strip()
            if translated:
                _TH_CACHE[word] = translated
                return translated
        except Exception:
            pass
    return "ไม่มีคำแปล"


def _clean_meaning(meaning: str) -> str:
    normalized = meaning.replace("  ", " ").strip()
    if ";" in normalized:
        normalized = normalized.split(";", maxsplit=1)[0].strip()
    return normalized


def _get_dictionary_data():
    global _DICT_DATA
    if _DICT_DATA is not None:
        return _DICT_DATA
    if DictionaryData is None:
        return None
    try:
        _DICT_DATA = DictionaryData()
        return _DICT_DATA
    except Exception:
        return None


def _get_th_translator():
    global _TH_TRANSLATOR
    if _TH_TRANSLATOR is not None:
        return _TH_TRANSLATOR
    if GoogleTranslator is None:
        return None
    try:
        _TH_TRANSLATOR = GoogleTranslator(source="zh-CN", target="th")
        return _TH_TRANSLATOR
    except Exception:
        return None


def _load_thai_cache() -> None:
    global _TH_CACHE_LOADED, _TH_CACHE
    if _TH_CACHE_LOADED:
        return
    _TH_CACHE_LOADED = True
    if not TH_CACHE_PATH.exists():
        return
    try:
        payload = json.loads(TH_CACHE_PATH.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            _TH_CACHE = {str(k): str(v) for k, v in payload.items()}
    except Exception:
        pass


def _save_thai_cache() -> None:
    TH_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TH_CACHE_PATH.write_text(json.dumps(_TH_CACHE, ensure_ascii=False, indent=2), encoding="utf-8")


def _compose_meaning(meaning_th: str, meaning_en: str) -> str:
    if meaning_th and meaning_en:
        return f"{meaning_th} ({meaning_en})"
    if meaning_th:
        return meaning_th
    return meaning_en


def dump_cards(cards: list[VocabularyCard], output_json_dir: Path) -> None:
    output_json_dir.mkdir(parents=True, exist_ok=True)
    (output_json_dir / "vocabulary_cards.json").write_text(
        json.dumps([c.to_dict() for c in cards], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

