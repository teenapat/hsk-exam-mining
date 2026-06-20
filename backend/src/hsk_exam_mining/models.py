from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ExamQuestion:
    examId: str
    section: str
    questionNo: int
    question: str
    options: list[str] = field(default_factory=list)
    answer: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ListeningScript:
    examId: str
    content: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class WordOccurrence:
    word: str
    examId: str
    section: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class VocabularyStats:
    word: str
    totalOccurrences: int
    examsAppeared: int
    listeningCount: int
    readingCount: int
    grammarCount: int
    vocabularyCount: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class VocabularyCard:
    word: str
    pinyin: str
    meaning: str
    frequency: int
    exampleSentences: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

