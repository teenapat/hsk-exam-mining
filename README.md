# HSK4 Historical Exam Intelligence System

End-to-end project for mining historical HSK4 exam data and generating high-priority study insights.

## Project Structure

```text
data/raw/                      # raw html/pdf/txt input files (optional)
hsk-exam/                      # existing source exams
backend/
  requirements.txt
  src/hsk_exam_mining/
frontend/
output/
  json/
  csv/
  reports/
```

## What Is Implemented

- Full pipeline from parsing to dashboard data export.
- Vocabulary frequency, coverage, high-value scoring.
- Grammar pattern mining.
- Listening/reading-specific vocabulary analysis.
- Topic clustering (TF-IDF + KMeans).
- Vocabulary graph (networkx).
- Vocabulary card generation (pinyin + meaning placeholder + examples).
- Study recommendation tiers (S/A/B).
- Bonus outputs: word cloud, exam similarity, predictive relevance.
- PDF study pack generator for Top 100/300/500 words.
- React dashboard to visualize outputs.

## Backend Setup

1) Install dependencies:

```bash
pip install -r backend/requirements.txt
```

2) Put input files in either:
- `data/raw`
- or existing `hsk-exam` folder (already supported)

Supported formats: `.html`, `.htm`, `.pdf`, `.txt`

3) Run full pipeline:

```bash
python backend/run_pipeline.py
```

4) Generate BASIC_WORD candidates (to exclude generic words from high-value ranking):

```bash
python backend/run_basic_words_candidates.py
```

Outputs:
- `output/csv/basic_words_candidates.csv`
- `output/json/basic_words_candidates.json`

Outputs are generated under:
- `output/json`
- `output/csv`
- `output/reports`

JSON files are also copied to:
- `frontend/public/data`

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open: [http://localhost:5173](http://localhost:5173)

## Notes

- The pipeline supports both HTML and PDF sources.
- For scanned PDFs, extraction quality depends on embedded text quality.
- You can improve `DEFAULT_MEANINGS` in `backend/src/hsk_exam_mining/enrichment.py` for richer translations.

