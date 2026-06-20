from __future__ import annotations

from .models import VocabularyStats


def build_study_recommendations(stats: list[VocabularyStats]) -> list[dict]:
    if not stats:
        return []
    frequencies = sorted((item.totalOccurrences for item in stats), reverse=True)
    s_threshold = frequencies[max(0, int(len(frequencies) * 0.10) - 1)]
    a_threshold = frequencies[max(0, int(len(frequencies) * 0.35) - 1)]

    recommendations: list[dict] = []
    for item in stats:
        if item.totalOccurrences >= s_threshold:
            tier = "S"
        elif item.totalOccurrences >= a_threshold:
            tier = "A"
        else:
            tier = "B"
        recommendations.append(
            {
                "tier": tier,
                "word": item.word,
                "frequency": item.totalOccurrences,
                "examCoverage": item.examsAppeared,
            }
        )
    order = {"S": 0, "A": 1, "B": 2}
    recommendations.sort(key=lambda x: (order[x["tier"]], -x["frequency"], x["word"]))
    return recommendations

