# HSK4 Historical Exam Intelligence System

## Project Goal

Build a system that analyzes historical HSK4 exams and generates insights to optimize study efficiency.

Instead of studying all HSK4 vocabulary equally, the system should identify:

* Frequently tested vocabulary
* Frequently tested grammar patterns
* Listening-heavy vocabulary
* Reading-heavy vocabulary
* Recurring sentence structures
* Vocabulary clusters and topics
* High-priority study lists

The final output should help a student answer:

> "If I only have limited study time, which words, grammar patterns, and topics should I focus on to maximize my score?"

---

# Source Data

The system will process historical HSK exam files.

Examples:
 
```text
H41001-exam.html
H41001-answer.html
H41001-audio-script.html

H41002-exam.html
H41002-answer.html
H41002-audio-script.html

H41003-exam-answer.html
```

File types:

### Exam File

Contains:

* Questions
* Options
* Reading passages
* Listening questions

### Answer File

Contains:

* Correct answers

### Audio Script File

Contains:

* Listening transcripts

---

# Technical Requirements

## Preferred Stack

Backend:

* Python 3.12+
* pandas
* beautifulsoup4
* lxml
* jieba
* numpy
* networkx
* scikit-learn
* wordcloud

Frontend:

* React
* Vite
* TypeScript
* Recharts

Storage:

* JSON
* CSV

No database required initially.

---

# Folder Structure

```text
project-root/

data/
    raw/
        *.html

output/
    json/
    csv/
    reports/

frontend/

backend/
```

---

# Phase 1 - HTML Extraction

Create parser pipeline.

For every exam:

Extract:

```typescript
interface ExamQuestion {
  examId: string;
  section: string;
  questionNo: number;

  question: string;

  options: string[];

  answer?: string;
}
```

---

Extract listening scripts:

```typescript
interface ListeningScript {
  examId: string;
  content: string;
}
```

---

Store parsed data as JSON.

---

# Phase 2 - Text Normalization

Normalize Chinese text.

Requirements:

* Remove duplicate spaces
* Remove unnecessary punctuation
* Convert full-width symbols
* Standardize quotes
* Trim whitespace

Output clean text.

---

# Phase 3 - Chinese Tokenization

Use jieba.

Generate:

```typescript
interface WordOccurrence {
  word: string;
  examId: string;
  section: string;
}
```

Sections:

* Listening
* Reading
* Grammar
* Vocabulary

---

# Phase 4 - Vocabulary Frequency Analysis

Calculate:

```typescript
interface VocabularyStats {
  word: string;

  totalOccurrences: number;

  examsAppeared: number;

  listeningCount: number;

  readingCount: number;

  grammarCount: number;
}
```

Generate:

### Top 100 most frequent words

### Top 500 most frequent words

### Vocabulary frequency CSV

---

# Phase 5 - High Value Vocabulary Ranking

Create scoring algorithm.

Example:

score =
frequency × examCoverage

Where:

frequency =
total occurrences

examCoverage =
number of exams containing the word

Output:

```text
Rank
Word
Pinyin
Meaning
Score
```

Generate:

Top 100 High Value Words

---

# Phase 6 - Grammar Pattern Mining

Automatically detect recurring patterns.

Examples:

```text
虽然...但是

不仅...而且

越来越

一边...一边

先...再...
```

For every pattern:

Calculate:

* occurrence count
* exam count
* section distribution

Generate ranking.

---

# Phase 7 - Listening Analysis

Analyze listening transcripts separately.

Output:

Most frequent listening vocabulary.

Example:

```text
Word          Count

经理          42
公司          38
飞机          35
```

Goal:

Identify vocabulary frequently used in listening sections.

---

# Phase 8 - Reading Analysis

Analyze reading passages separately.

Output:

Most frequent reading vocabulary.

Goal:

Identify reading-specific vocabulary.

---

# Phase 9 - Topic Detection

Cluster vocabulary into themes.

Possible categories:

```text
Work
Travel
Shopping
Health
Education
Technology
Food
Transportation
Family
```

Use:

* TF-IDF
* KMeans

Generate:

Topic frequency distribution.

---

# Phase 10 - Vocabulary Network Graph

Create co-occurrence graph.

Example:

```text
工作
 ├─ 公司
 ├─ 同事
 ├─ 老板

旅游
 ├─ 酒店
 ├─ 飞机
 ├─ 导游
```

Use networkx.

Generate graph data.

---

# Phase 11 - Pinyin + Translation

For every detected vocabulary:

Generate:

```typescript
interface VocabularyCard {
  word: string;
  pinyin: string;
  meaning: string;

  frequency: number;

  exampleSentences: string[];
}
```

Store in JSON.

---

# Phase 12 - Study Recommendation Engine

Generate:

## S-Tier Vocabulary

Appears very frequently.

## A-Tier Vocabulary

Appears regularly.

## B-Tier Vocabulary

Appears occasionally.

Output:

```json
{
  "tier": "S",
  "word": "应该",
  "frequency": 48,
  "examCoverage": 16
}
```

---

# Phase 13 - Dashboard

Build React dashboard.

Pages:

## Overview

Display:

* Total exams analyzed
* Total questions
* Total vocabulary
* Total listening scripts

---

## Vocabulary Rankings

Charts:

* Top words
* Frequency distribution
* Tier breakdown

---

## Grammar Rankings

Charts:

* Most common patterns
* Pattern frequency

---

## Listening Insights

Charts:

* Top listening vocabulary
* Topic breakdown

---

## Reading Insights

Charts:

* Top reading vocabulary
* Topic breakdown

---

## Vocabulary Search

Search word.

Display:

* frequency
* pinyin
* meaning
* example sentences
* exam appearances

---

# Phase 14 - Study Pack Generator

Generate PDF study packs.

Each word should contain:

```text
Word
Pinyin
Meaning

Frequency

Exam Appearances

Example Sentences
```

Sort by High Value Score.

Output:

```text
Top 100 Words
Top 300 Words
Top 500 Words
```

PDF format.

---

# Bonus Features

## Word Cloud

Generate:

* Overall
* Listening
* Reading

---

## Exam Similarity Analysis

Compare exams.

Detect:

* repeated vocabulary
* repeated grammar
* repeated themes

---

## Predictive Analysis

Estimate probability that a word appears again.

Output:

```text
Word

Frequency
Coverage

Predicted Relevance Score
```

Use historical frequency only.

No machine learning required initially.

---

# Success Criteria

The system should enable a student to:

1. Identify the highest value vocabulary.
2. Identify the most common grammar patterns.
3. Focus study time on recurring exam content.
4. Generate personalized study materials.
5. Improve exam preparation efficiency using data from real historical HSK4 exams.
