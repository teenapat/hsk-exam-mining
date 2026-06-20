# HSK4 Project Task Breakdown

## Foundation
- [x] Set up backend and frontend project structures.
- [x] Prepare `data/raw`, `output/json`, `output/csv`, and `output/reports`.
- [x] Add run entrypoint for full pipeline.

## Backend Pipeline
- [x] Phase 1: Parse exam files (HTML/PDF/TXT), answers, and audio scripts.
- [x] Phase 2: Normalize Chinese text.
- [x] Phase 3: Tokenize with jieba and store word occurrences.
- [x] Phase 4: Build vocabulary frequency statistics + CSV exports.
- [x] Phase 5: Build high-value ranking score.
- [x] Phase 6: Mine recurring grammar patterns.
- [x] Phase 7: Listening vocabulary analysis.
- [x] Phase 8: Reading vocabulary analysis.
- [x] Phase 9: Topic detection with TF-IDF + KMeans.
- [x] Phase 10: Vocabulary co-occurrence graph data with networkx.
- [x] Phase 11: Pinyin and vocabulary cards.
- [x] Phase 12: Study recommendation tiers (S/A/B).
- [x] Bonus: Word cloud, exam similarity, predictive relevance.

## Reports and Study Pack
- [x] Generate summary markdown report.
- [x] Generate Top 100 / 300 / 500 PDF study packs.

## Frontend Dashboard
- [x] Build React + Vite + TypeScript dashboard.
- [x] Implement pages: Overview, Vocabulary, Grammar, Listening, Reading, Search.
- [x] Add charts with Recharts and table views.
- [x] Load generated JSON from `frontend/public/data`.

## Operations
- [x] Sync backend JSON output to frontend data folder.
- [x] Add setup and run guide.

