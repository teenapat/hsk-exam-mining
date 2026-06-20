import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis
} from "recharts";
import type { TooltipProps } from "recharts";
import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { Search, Sparkles, Target, TrendingUp } from "lucide-react";

import type {
  HighValueWord,
  GrammarPattern,
  Overview,
  PredictiveRow,
  SentenceBuilderItem,
  SimilarityRow,
  TierRecommendation,
  TopicItem,
  VocabGraph,
  VocabularyCard,
  VocabStat,
  WordOccurrence
} from "./types";
import { Button } from "./components/ui/button";
import { Card, CardTitle, CardValue } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Input } from "./components/ui/input";
import { ForceGraph } from "./components/ForceGraph";

type Page =
  | "home"
  | "vocab"
  | "grammar"
  | "listening"
  | "reading"
  | "similarity"
  | "word"
  | "strategy"
  | "highValue"
  | "csvAll"
  | "sentenceBuilder";

const PAGE_LABELS: Record<Page, string> = {
  home: "หน้าหลัก",
  vocab: "วิเคราะห์คำศัพท์",
  grammar: "วิเคราะห์ไวยากรณ์",
  listening: "วิเคราะห์พาร์ตฟัง",
  reading: "วิเคราะห์พาร์ตอ่าน",
  similarity: "ความคล้ายข้อสอบ",
  word: "รายละเอียดคำศัพท์",
  strategy: "กลยุทธ์การอ่าน",
  highValue: "ไฟล์คำมูลค่าสูง (CSV)",
  csvAll: "ตาราง CSV ทั้งหมด",
  sentenceBuilder: "หมวดแต่งประโยค"
};

type ScatterPoint = {
  word: string;
  coveragePct: number;
  frequency: number;
  difficulty: number;
  sectionFrequency: number;
  tier: "S" | "A" | "B";
  color: string;
};

type ExamQuestion = { examId: string; question: string };
const TOPIC_LABEL_TH: Record<string, string> = {
  Work: "งานและอาชีพ",
  Travel: "การท่องเที่ยว",
  Shopping: "การซื้อของ",
  Health: "สุขภาพ",
  Education: "การศึกษา",
  Technology: "เทคโนโลยี",
  Food: "อาหาร",
  Transportation: "การเดินทาง",
  Family: "ครอบครัว"
};
const SENTENCE_STORAGE_KEY = "hsk4_sentence_builder_saved_v1";

async function fetchJson<T>(name: string): Promise<T> {
  const res = await fetch(`/data/${name}.json`);
  if (!res.ok) {
    throw new Error(`failed to load ${name}.json`);
  }
  return (await res.json()) as T;
}

export default function App() {
  const [page, setPage] = useState<Page>("home");
  const [overview, setOverview] = useState<Overview | null>(null);
  const [stats, setStats] = useState<VocabStat[]>([]);
  const [highValueWords, setHighValueWords] = useState<HighValueWord[]>([]);
  const [grammar, setGrammar] = useState<GrammarPattern[]>([]);
  const [topics, setTopics] = useState<TopicItem[]>([]);
  const [similarityRows, setSimilarityRows] = useState<SimilarityRow[]>([]);
  const [predictiveRows, setPredictiveRows] = useState<PredictiveRow[]>([]);
  const [recommendations, setRecommendations] = useState<TierRecommendation[]>([]);
  const [cards, setCards] = useState<VocabularyCard[]>([]);
  const [occurrences, setOccurrences] = useState<WordOccurrence[]>([]);
  const [vocabGraph, setVocabGraph] = useState<VocabGraph | null>(null);
  const [questions, setQuestions] = useState<ExamQuestion[]>([]);
  const [selectedWord, setSelectedWord] = useState("应该");
  const [searchWord, setSearchWord] = useState("");
  const [highValueSearch, setHighValueSearch] = useState("");
  const [hideBasicWords, setHideBasicWords] = useState(false);
  const [highValueSortBy, setHighValueSortBy] = useState<"rank" | "pinyin">("rank");
  const [highValueSortDirection, setHighValueSortDirection] = useState<"asc" | "desc">("asc");
  const [sentenceItems, setSentenceItems] = useState<SentenceBuilderItem[]>([]);
  const [sentenceSearch, setSentenceSearch] = useState("");
  const [sentenceDraft, setSentenceDraft] = useState("");
  const [sentenceIndex, setSentenceIndex] = useState(0);
  const [showUntrustedSentenceItems, setShowUntrustedSentenceItems] = useState(false);
  const [savedSentenceMap, setSavedSentenceMap] = useState<Record<string, string>>({});
  const [showExampleMode, setShowExampleMode] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");
  const [sectionFilter, setSectionFilter] = useState<"all" | "Listening" | "Reading" | "Grammar" | "Vocabulary">("all");
  const [coverageRange, setCoverageRange] = useState<[number, number]>([0, 100]);
  const [frequencyRange, setFrequencyRange] = useState<[number, number]>([0, 100]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetchJson<Overview>("overview"),
      fetchJson<VocabStat[]>("top_500_words"),
      fetchJson<HighValueWord[]>("high_value_words"),
      fetchJson<GrammarPattern[]>("grammar_patterns"),
      fetchJson<TopicItem[]>("topics"),
      fetchJson<SimilarityRow[]>("exam_similarity"),
      fetchJson<PredictiveRow[]>("predictive_analysis"),
      fetchJson<TierRecommendation[]>("study_recommendations"),
      fetchJson<VocabularyCard[]>("vocabulary_cards"),
      fetchJson<WordOccurrence[]>("phase3_word_occurrences"),
      fetchJson<VocabGraph>("vocab_graph"),
      fetchJson<ExamQuestion[]>("phase1_questions"),
      fetchJson<SentenceBuilderItem[]>("sentence_builder_items")
    ])
      .then(
        ([
          ov,
          statsRows,
          highValueRows,
          grammarRows,
          topicRows,
          similarityData,
          predictiveData,
          tierRows,
          vocabCards,
          occurrenceRows,
          graphRows,
          questionRows,
          sentenceRows
        ]) => {
        setOverview(ov);
        setStats(statsRows);
        setHighValueWords(highValueRows);
        setGrammar(grammarRows);
        setTopics(topicRows);
        setSimilarityRows(similarityData);
        setPredictiveRows(predictiveData);
        setRecommendations(tierRows);
        setCards(vocabCards);
        setOccurrences(occurrenceRows);
        setVocabGraph(graphRows);
        setQuestions(questionRows);
        setSentenceItems(sentenceRows);
        setFrequencyRange([0, Math.max(40, ...statsRows.map((row) => row.totalOccurrences))]);
        }
      )
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const raw = window.localStorage.getItem(SENTENCE_STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw) as Record<string, string>;
      if (parsed && typeof parsed === "object") {
        setSavedSentenceMap(parsed);
      }
    } catch {
      // ignore corrupted local storage payload
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(SENTENCE_STORAGE_KEY, JSON.stringify(savedSentenceMap));
  }, [savedSentenceMap]);

  const tierByWord = useMemo(() => {
    const map = new Map<string, "S" | "A" | "B">();
    recommendations.forEach((row) => map.set(row.word, row.tier));
    return map;
  }, [recommendations]);

  const tierData = useMemo(() => {
    const map = { S: 0, A: 0, B: 0 };
    for (const row of recommendations) {
      map[row.tier] += 1;
    }
    return [
      { tier: "S", value: map.S },
      { tier: "A", value: map.A },
      { tier: "B", value: map.B }
    ];
  }, [recommendations]);

  const scatterData = useMemo<ScatterPoint[]>(() => {
    if (!overview) return [];
    return stats.map((row) => {
      const tier = tierByWord.get(row.word) ?? "B";
      const color = tier === "S" ? "#ef4444" : tier === "A" ? "#f59e0b" : "#38bdf8";
      const sectionFrequency =
        sectionFilter === "Listening"
          ? row.listeningCount
          : sectionFilter === "Reading"
            ? row.readingCount
            : sectionFilter === "Grammar"
              ? row.grammarCount
              : sectionFilter === "Vocabulary"
                ? row.vocabularyCount
                : row.totalOccurrences;
      return {
        word: row.word,
        coveragePct: Number(((row.examsAppeared / overview.totalExams) * 100).toFixed(1)),
        frequency: row.totalOccurrences,
        difficulty: Math.max(1, Math.min(8, row.word.length + (row.totalOccurrences < 8 ? 3 : 0))),
        sectionFrequency,
        tier,
        color,
      };
    });
  }, [overview, sectionFilter, stats, tierByWord]);

  const filteredScatter = useMemo(
    () =>
      scatterData.filter(
        (p) =>
          p.coveragePct >= coverageRange[0] &&
          p.coveragePct <= coverageRange[1] &&
          p.frequency >= frequencyRange[0] &&
          p.frequency <= frequencyRange[1] &&
          (!searchWord || p.word.includes(searchWord.trim()))
      ),
    [coverageRange, frequencyRange, scatterData, searchWord]
  );

  const selectedCard = useMemo(() => cards.find((x) => x.word === selectedWord) ?? null, [cards, selectedWord]);

  const selectedWordTimeline = useMemo(() => {
    const map = new Map<string, number>();
    for (const row of occurrences) {
      if (row.word !== selectedWord) continue;
      map.set(row.examId, (map.get(row.examId) ?? 0) + 1);
    }
    return Array.from(map.entries())
      .map(([examId, count]) => ({ examId, count }))
      .sort((a, b) => a.examId.localeCompare(b.examId));
  }, [occurrences, selectedWord]);

  const relatedWords = useMemo(() => {
    if (!vocabGraph) return [];
    const relations = vocabGraph.edges
      .filter((edge) => edge.source === selectedWord || edge.target === selectedWord)
      .map((edge) => ({
        word: edge.source === selectedWord ? edge.target : edge.source,
        weight: edge.weight
      }))
      .sort((a, b) => b.weight - a.weight)
      .slice(0, 12);
    return relations;
  }, [selectedWord, vocabGraph]);

  const grammarTimeline = useMemo(() => {
    const grouped = new Map<string, string[]>();
    questions.forEach((row) => {
      grouped.set(row.examId, [...(grouped.get(row.examId) ?? []), row.question]);
    });
    const exams = Array.from(grouped.keys()).sort((a, b) => a.localeCompare(b));
    return exams.map((examId) => {
      const corpus = (grouped.get(examId) ?? []).join(" ");
      const row: Record<string, string | number> = { examId };
      grammar.forEach((pattern) => {
        const regex = new RegExp(pattern.pattern);
        row[pattern.pattern] = (corpus.match(regex) || []).length;
      });
      return row;
    });
  }, [grammar, questions]);

  const listeningBubble = useMemo(() => {
    const data = new Map<string, { frequency: number; coverageSet: Set<string> }>();
    for (const item of occurrences) {
      if (item.section !== "Listening") continue;
      if (!data.has(item.word)) data.set(item.word, { frequency: 0, coverageSet: new Set<string>() });
      const row = data.get(item.word)!;
      row.frequency += 1;
      row.coverageSet.add(item.examId);
    }
    return Array.from(data.entries())
      .map(([word, value]) => ({
        word,
        frequency: value.frequency,
        difficulty: Math.max(1, Math.min(9, word.length + (value.frequency < 6 ? 3 : 0))),
        coverage: value.coverageSet.size
      }))
      .sort((a, b) => b.frequency - a.frequency)
      .slice(0, 180);
  }, [occurrences]);

  const listeningReadingQuadrant = useMemo(() => {
    const map = new Map<string, { reading: number; listening: number }>();
    for (const item of occurrences) {
      if (!map.has(item.word)) map.set(item.word, { reading: 0, listening: 0 });
      if (item.section === "Listening") map.get(item.word)!.listening += 1;
      if (item.section === "Reading") map.get(item.word)!.reading += 1;
    }
    return Array.from(map.entries())
      .map(([word, row]) => ({ word, reading: row.reading, listening: row.listening }))
      .filter((row) => row.reading + row.listening >= 4)
      .sort((a, b) => b.reading + b.listening - (a.reading + a.listening))
      .slice(0, 220);
  }, [occurrences]);

  const similarityMatrix = useMemo(() => {
    const exams = Array.from(
      new Set(similarityRows.flatMap((row) => [row.examA, row.examB]))
    ).sort((a, b) => a.localeCompare(b));
    const matrix = new Map<string, number>();
    similarityRows.forEach((row) => {
      matrix.set(`${row.examA}-${row.examB}`, row.jaccardSimilarity);
      matrix.set(`${row.examB}-${row.examA}`, row.jaccardSimilarity);
    });
    return { exams, matrix };
  }, [similarityRows]);

  const coverageCurve = useMemo(() => {
    const total = highValueWords.reduce((sum, row) => sum + row.frequency, 0) || 1;
    let cumulative = 0;
    return highValueWords.slice(0, 500).map((row, index) => {
      cumulative += row.frequency;
      return {
        wordsStudied: index + 1,
        coveragePct: Number(((cumulative / total) * 100).toFixed(2))
      };
    });
  }, [highValueWords]);

  const strategyInsights = useMemo(() => {
    if (!overview || !highValueWords.length || !grammar.length || !topics.length) return [];
    const top20 = highValueWords.slice(0, Math.max(1, Math.floor(highValueWords.length * 0.2)));
    const totalFreq = highValueWords.reduce((sum, row) => sum + row.frequency, 0) || 1;
    const top20Freq = top20.reduce((sum, row) => sum + row.frequency, 0);
    const topPattern = grammar[0];
    const dominantTopic = topics[0];
    const threshold = "H41200";
    const travelWords = ["飞机", "酒店", "旅游", "导游", "机场"];
    let before = 0;
    let after = 0;
    occurrences.forEach((o) => {
      if (!travelWords.includes(o.word)) return;
      if (o.examId >= threshold) after += 1;
      else before += 1;
    });
    return [
      `${top20.length} คำแรกคิดเป็น ${((top20Freq / totalFreq) * 100).toFixed(1)}% ของการปรากฏทั้งหมด — ควรเริ่มจากลิสต์นี้ก่อน`,
      `แพทเทิร์น ${topPattern.pattern} พบใน ${(topPattern.examCount / overview.totalExams * 100).toFixed(0)}% ของข้อสอบ`,
      `หัวข้อเด่นสุดตอนนี้คือ ${TOPIC_LABEL_TH[dominantTopic.topicLabel] ?? dominantTopic.topicLabel} คิดเป็น ${(dominantTopic.frequency / topics.reduce((s, t) => s + t.frequency, 0) * 100).toFixed(1)}% ของคอนเทนต์`,
      `กลุ่มคำ Travel หลัง ${threshold} เพิ่มขึ้น ${before === 0 ? 0 : (((after - before) / before) * 100).toFixed(1)}%`
    ];
  }, [grammar, highValueWords, occurrences, overview, topics]);

  const topVocabularyWord = highValueWords[0];
  const topGrammar = grammar[0];
  const topTopic = topics[0];
  const topPrediction = predictiveRows[0];

  const coverage150 =
    coverageCurve.find((row) => row.wordsStudied === 150)?.coveragePct ??
    coverageCurve[coverageCurve.length - 1]?.coveragePct ??
    0;

  const listeningTopCsv = useMemo(
    () =>
      [...stats]
        .map((row) => ({ word: row.word, count: row.listeningCount }))
        .filter((row) => row.count > 0)
        .sort((a, b) => b.count - a.count),
    [stats]
  );

  const readingTopCsv = useMemo(
    () =>
      [...stats]
        .map((row) => ({ word: row.word, count: row.readingCount }))
        .filter((row) => row.count > 0)
        .sort((a, b) => b.count - a.count),
    [stats]
  );

  const filteredHighValueWords = useMemo(() => {
    const q = highValueSearch.trim();
    const qLower = q.toLowerCase();
    const baseRows = hideBasicWords ? highValueWords.filter((row) => !row.isBasicWord) : highValueWords;
    if (!q) return baseRows;
    return baseRows.filter((row) => {
      const reasonsText = (row.rankingReasons ?? []).join(" ").toLowerCase();
      return (
        row.word.includes(q) ||
        row.pinyin?.toLowerCase().includes(qLower) ||
        row.meaning?.toLowerCase().includes(qLower) ||
        reasonsText.includes(qLower)
      );
    });
  }, [hideBasicWords, highValueSearch, highValueWords]);

  const sortedHighValueWords = useMemo(() => {
    const rows = [...filteredHighValueWords];
    if (highValueSortBy === "pinyin") {
      rows.sort((a, b) => {
        const left = (a.pinyin ?? "").trim().toLowerCase();
        const right = (b.pinyin ?? "").trim().toLowerCase();
        const primary = left.localeCompare(right, "zh-Hans-CN", { sensitivity: "base" });
        if (primary !== 0) return highValueSortDirection === "asc" ? primary : -primary;
        return a.rank - b.rank;
      });
      return rows;
    }
    rows.sort((a, b) => (highValueSortDirection === "asc" ? a.rank - b.rank : b.rank - a.rank));
    return rows;
  }, [filteredHighValueWords, highValueSortBy, highValueSortDirection]);

  const filteredSentenceItems = useMemo(() => {
    const q = sentenceSearch.trim();
    const base = showUntrustedSentenceItems ? sentenceItems : sentenceItems.filter((item) => item.isTrusted);
    if (!q) return base;
    return base.filter(
      (item) =>
        item.prompt.includes(q) ||
        item.keywords.some((k) => k.includes(q)) ||
        item.options.some((opt) => opt.includes(q))
    );
  }, [sentenceItems, sentenceSearch, showUntrustedSentenceItems]);

  useEffect(() => {
    if (!filteredSentenceItems.length) {
      setSentenceIndex(0);
      return;
    }
    if (sentenceIndex > filteredSentenceItems.length - 1) {
      setSentenceIndex(0);
    }
  }, [filteredSentenceItems.length, sentenceIndex]);

  const currentSentenceItem = filteredSentenceItems[sentenceIndex] ?? null;

  const sentenceHintMatched = useMemo(() => {
    if (!currentSentenceItem || !sentenceDraft.trim()) return 0;
    if (!currentSentenceItem.keywords.length) return 0;
    const matched = currentSentenceItem.keywords.filter((k) => sentenceDraft.includes(k)).length;
    return Math.round((matched / currentSentenceItem.keywords.length) * 100);
  }, [currentSentenceItem, sentenceDraft]);

  const sentenceGrammarCheck = useMemo(
    () => evaluateSentenceDraft(sentenceDraft, currentSentenceItem?.keywords ?? []),
    [currentSentenceItem?.keywords, sentenceDraft]
  );

  const exampleModeSentences = useMemo(() => {
    if (!currentSentenceItem) return [];
    const keywords = currentSentenceItem.keywords;
    const pool = cards.flatMap((card) => card.exampleSentences);
    const filtered = pool.filter((sentence) => keywords.some((k) => sentence.includes(k)));
    return Array.from(new Set(filtered)).slice(0, 3);
  }, [cards, currentSentenceItem]);

  useEffect(() => {
    if (!currentSentenceItem) return;
    setSentenceDraft(savedSentenceMap[currentSentenceItem.id] ?? "");
    setSaveMessage("");
    setShowExampleMode(false);
  }, [currentSentenceItem?.id, savedSentenceMap]);

  if (error) {
    return <div className="mx-auto max-w-7xl p-8 text-red-300">โหลดข้อมูลไม่สำเร็จ: {error}</div>;
  }

  if (!overview) {
    return <div className="mx-auto max-w-7xl p-8 text-textMuted">กำลังโหลดแดชบอร์ดวิเคราะห์...</div>;
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 text-text md:px-8">
      <header className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold md:text-3xl">แพลตฟอร์มวิเคราะห์ข้อสอบ HSK4</h1>
          <p className="mt-1 text-sm text-textMuted">แดชบอร์ดสรุปอินไซต์ ช่วยตัดสินใจว่าอ่านอะไรได้ภายใน 10 วินาที</p>
        </div>
        <Badge variant="success">โหมดวิเคราะห์ (Dark)</Badge>
      </header>

      <nav className="mb-6 flex flex-wrap gap-2">
        {(Object.keys(PAGE_LABELS) as Page[]).map((p) => (
          <div key={p} className="relative">
            <Button
              variant={page === p ? "default" : "ghost"}
              aria-current={page === p ? "page" : undefined}
              className={
                page === p
                  ? "border border-primary/50 bg-primary/90 text-white shadow-[0_0_0_1px_rgba(59,130,246,0.45)]"
                  : "border border-transparent text-textMuted hover:border-border hover:text-text"
              }
              onClick={() => setPage(p)}
            >
              {PAGE_LABELS[p]}
            </Button>
            {page === p && <span className="absolute -bottom-1 left-3 right-3 h-0.5 rounded-full bg-cyan-300" />}
          </div>
        ))}
      </nav>

      {page === "home" && (
        <motion.section initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <section className="grid gap-3 md:grid-cols-4">
            <MetricCard title="จำนวนข้อสอบย้อนหลัง" value={`${overview.totalExams}`} />
            <MetricCard title="จำนวนข้อคำถาม" value={`${overview.totalQuestions.toLocaleString()}`} />
            <MetricCard title="คำศัพท์ไม่ซ้ำ" value={`${overview.totalVocabulary.toLocaleString()}`} />
            <MetricCard title="สคริปต์พาร์ตฟัง" value={`${overview.totalListeningScripts}`} />
          </section>
          <section className="grid gap-3 md:grid-cols-3">
            <InsightCard
              icon={<Target size={18} />}
              title="คำศัพท์สำคัญที่สุด"
              value={topVocabularyWord?.word ?? "-"}
              detail={`พบใน ${(100 * ((topVocabularyWord?.examCoverage ?? 0) / overview.totalExams)).toFixed(0)}% ของข้อสอบ`}
            />
            <InsightCard
              icon={<Sparkles size={18} />}
              title="ไวยากรณ์ที่พบบ่อย"
              value={topGrammar?.pattern ?? "-"}
              detail={`ปรากฏ ${topGrammar?.occurrenceCount ?? 0} ครั้ง`}
            />
            <InsightCard
              icon={<TrendingUp size={18} />}
              title="หัวข้อเด่น"
              value={TOPIC_LABEL_TH[topTopic?.topicLabel ?? ""] ?? topTopic?.topicLabel ?? "-"}
              detail={`${(((topTopic?.frequency ?? 0) / Math.max(1, topics.reduce((s, t) => s + t.frequency, 0))) * 100).toFixed(1)}% ของคอนเทนต์ทั้งหมด`}
            />
          </section>
          <Card>
            <CardTitle>คำที่มีแนวโน้มออกซ้ำสูง</CardTitle>
            <CardValue className="text-xl">{topPrediction?.word ?? "-"}</CardValue>
            <p className="mt-2 text-sm text-textMuted">
              ค่าความน่าจะเป็นการปรากฏซ้ำ: {topPrediction?.predictedRelevanceScore ?? 0}
            </p>
          </Card>
        </motion.section>
      )}

      {page === "vocab" && (
        <motion.section initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <Card>
            <CardTitle>อินไซต์ด่วน</CardTitle>
            <p className="mt-2 text-xl font-semibold">
              ถ้าโฟกัส 150 คำแรก จะครอบคลุมประมาณ {coverage150.toFixed(1)}% ของการปรากฏคำทั้งหมด
            </p>
            <p className="mt-1 text-sm text-textMuted">
              ตัดสินใจเร็ว: จุดด้านขวาบน = คำที่ควรอ่านก่อนทันที
            </p>
          </Card>
          <section className="grid gap-3 md:grid-cols-5">
            <div className="md:col-span-2"><Input placeholder="ค้นหาคำ เช่น 应该" value={searchWord} onChange={(e) => setSearchWord(e.target.value)} /></div>
            <div className="md:col-span-1">
              <select
                className="h-10 w-full rounded-xl border border-border bg-panelMuted px-3 text-sm"
                value={sectionFilter}
                onChange={(e) => setSectionFilter(e.target.value as typeof sectionFilter)}
              >
                <option value="all">ทุกพาร์ต</option>
                <option value="Listening">พาร์ตฟัง</option>
                <option value="Reading">พาร์ตอ่าน</option>
                <option value="Grammar">พาร์ตไวยากรณ์</option>
                <option value="Vocabulary">พาร์ตคำศัพท์</option>
              </select>
            </div>
            <div className="md:col-span-1">
              <Input
                type="number"
                value={coverageRange[0]}
                onChange={(e) => setCoverageRange([Number(e.target.value), coverageRange[1]])}
                placeholder="Coverage ขั้นต่ำ"
              />
            </div>
            <div className="md:col-span-1">
              <Input
                type="number"
                value={frequencyRange[0]}
                onChange={(e) => setFrequencyRange([Number(e.target.value), frequencyRange[1]])}
                placeholder="ความถี่ขั้นต่ำ"
              />
            </div>
          </section>
          <section className="grid gap-4 xl:grid-cols-3">
            <Card className="xl:col-span-2">
              <CardTitle>กราฟจุด: การครอบคลุม vs ความถี่</CardTitle>
              <div className="mt-4 h-[430px]">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart>
                    <CartesianGrid stroke="rgba(148,163,184,0.2)" />
                    <XAxis type="number" dataKey="coveragePct" name="Coverage %" />
                    <YAxis type="number" dataKey="frequency" name="Frequency" />
                    <ZAxis type="number" dataKey="difficulty" range={[60, 450]} />
                    <Tooltip content={<ScatterTooltip />} />
                    <Scatter
                      data={filteredScatter}
                      onClick={(payload) => {
                        const point = payload as unknown as ScatterPoint;
                        if (point?.word) {
                          setSelectedWord(point.word);
                          setPage("word");
                        }
                      }}
                    >
                      {filteredScatter.map((point) => (
                        <Cell key={`${point.word}-${point.tier}`} fill={point.color} />
                      ))}
                    </Scatter>
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
              <p className="mt-2 text-sm text-textMuted">
                มุมขวาบน = ควรอ่านทันที, มุมซ้ายล่าง = ความสำคัญต่ำกว่า
              </p>
            </Card>
            <Card>
              <CardTitle>สัดส่วนระดับคำศัพท์</CardTitle>
              <div className="mt-4 h-[260px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={tierData} dataKey="value" nameKey="tier" outerRadius={90} label>
                      {tierData.map((entry) => (
                        <Cell key={entry.tier} fill={entry.tier === "S" ? "#ef4444" : entry.tier === "A" ? "#f59e0b" : "#38bdf8"} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-2 text-sm">
                <p>S-tier: โฟกัสก่อนที่สุด</p>
                <p>A-tier: อ่านต่อเนื่อง</p>
                <p>B-tier: เก็บท้ายรอบ</p>
              </div>
            </Card>
            <Card className="xl:col-span-3">
              <CardTitle>คลัสเตอร์คำศัพท์ (กราฟเครือข่าย)</CardTitle>
              {vocabGraph && (
                <div className="mt-4">
                  <ForceGraph
                    nodes={vocabGraph.nodes}
                    edges={vocabGraph.edges}
                    selectedWord={selectedWord}
                    onWordClick={(word) => {
                      setSelectedWord(word);
                      setPage("word");
                    }}
                  />
                </div>
              )}
            </Card>
          </section>
        </motion.section>
      )}

      {page === "grammar" && (
        <motion.section initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <Card>
            <CardTitle>อินไซต์ด่วน</CardTitle>
            <p className="mt-2 text-xl font-semibold">
              {grammar[0]?.pattern} เป็นแพทเทิร์นที่เจอบ่อยสุด ครอบคลุม {((grammar[0]?.examCount ?? 0) / overview.totalExams * 100).toFixed(0)}% ของข้อสอบ
            </p>
          </Card>
          <section className="grid gap-4 xl:grid-cols-2">
            <Card>
              <CardTitle>อันดับแพทเทิร์นไวยากรณ์</CardTitle>
              <div className="mt-4 h-[340px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={[...grammar].sort((a, b) => b.occurrenceCount - a.occurrenceCount)}>
                    <CartesianGrid stroke="rgba(148,163,184,0.2)" />
                    <XAxis type="number" />
                    <YAxis dataKey="pattern" type="category" width={100} />
                    <Tooltip />
                    <Bar dataKey="occurrenceCount" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
            <Card>
              <CardTitle>ฮีตแมปไวยากรณ์ (แพทเทิร์น x พาร์ต)</CardTitle>
              <div className="mt-4 space-y-2">
                {grammar.map((row) => {
                  const sections = ["Listening", "Reading", "Grammar", "Vocabulary"];
                  return (
                    <div key={row.pattern} className="grid grid-cols-5 gap-1">
                      <div className="truncate text-xs text-textMuted">{row.pattern}</div>
                      {sections.map((section) => {
                        const value = row.sectionDistribution?.[section] ?? 0;
                        const alpha = Math.min(1, value / 12);
                        return (
                          <div key={section} className="rounded p-2 text-center text-xs" style={{ background: `rgba(59,130,246,${0.1 + alpha * 0.7})` }}>
                            {value}
                          </div>
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            </Card>
            <Card className="xl:col-span-2">
              <CardTitle>แนวโน้มแพทเทิร์นตามรหัสข้อสอบ</CardTitle>
              <div className="mt-4 h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={grammarTimeline}>
                    <CartesianGrid stroke="rgba(148,163,184,0.2)" />
                    <XAxis dataKey="examId" />
                    <YAxis />
                    <Tooltip />
                    {grammar.slice(0, 3).map((pattern, idx) => (
                      <Line
                        key={pattern.pattern}
                        type="monotone"
                        dataKey={pattern.pattern}
                        stroke={["#38bdf8", "#f59e0b", "#22c55e"][idx]}
                        strokeWidth={2}
                        dot={false}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </section>
        </motion.section>
      )}

      {page === "listening" && (
        <motion.section initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <Card>
            <CardTitle>อินไซต์ด่วน</CardTitle>
            <p className="mt-2 text-xl font-semibold">
              Listening มักใช้คำงาน/ชีวิตประจำวัน และคำที่ Coverage สูงควรท่องก่อน
            </p>
          </Card>
          <Card>
            <CardTitle>กราฟฟองคำศัพท์พาร์ตฟัง</CardTitle>
            <div className="mt-4 h-[420px]">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart>
                  <CartesianGrid stroke="rgba(148,163,184,0.2)" />
                  <XAxis type="number" dataKey="frequency" name="ความถี่" />
                  <YAxis type="number" dataKey="difficulty" name="ความยาก" />
                  <ZAxis type="number" dataKey="coverage" range={[50, 480]} />
                  <Tooltip content={<ListeningTooltip />} />
                  <Scatter
                    data={listeningBubble}
                    fill="#22c55e"
                    onClick={(payload) => {
                      const point = payload as unknown as { word?: string };
                      if (point?.word) {
                        setSelectedWord(point.word);
                        setPage("word");
                      }
                    }}
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </motion.section>
      )}

      {page === "reading" && (
        <motion.section initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <Card>
            <CardTitle>อินไซต์ด่วน</CardTitle>
            <p className="mt-2 text-xl font-semibold">
              กราฟ 4 ควอดแรนต์ช่วยแยกคำที่เน้นฟัง, เน้นอ่าน และคำแกนกลางที่พบบ่อยทั้งสองพาร์ต
            </p>
          </Card>
          <Card>
            <CardTitle>เทียบพาร์ตฟัง vs พาร์ตอ่าน (Quadrant)</CardTitle>
            <div className="mt-4 h-[420px]">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart>
                  <CartesianGrid stroke="rgba(148,163,184,0.2)" />
                  <XAxis type="number" dataKey="reading" name="ความถี่พาร์ตอ่าน" />
                  <YAxis type="number" dataKey="listening" name="ความถี่พาร์ตฟัง" />
                  <Tooltip content={<CompareTooltip />} />
                  <Scatter
                    data={listeningReadingQuadrant}
                    fill="#f59e0b"
                    onClick={(payload) => {
                      const point = payload as unknown as { word?: string };
                      if (point?.word) {
                        setSelectedWord(point.word);
                        setPage("word");
                      }
                    }}
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </motion.section>
      )}

      {page === "similarity" && (
        <motion.section initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <Card>
            <CardTitle>สำรวจความคล้ายของข้อสอบ</CardTitle>
            <p className="mt-2 text-sm text-textMuted">สีเข้ม = แนวโน้มข้อสอบคล้ายกันสูง (shared vocabulary/pattern)</p>
            <div className="mt-4 overflow-x-auto">
              <div className="grid min-w-[780px] gap-1" style={{ gridTemplateColumns: `140px repeat(${similarityMatrix.exams.length}, minmax(28px, 1fr))` }}>
                <div />
                {similarityMatrix.exams.map((exam) => (
                  <div key={`x-${exam}`} className="truncate text-[10px] text-textMuted">{exam}</div>
                ))}
                {similarityMatrix.exams.map((rowExam) => (
                  <div key={`row-${rowExam}`} className="contents">
                    <div className="text-[10px] text-textMuted">{rowExam}</div>
                    {similarityMatrix.exams.map((colExam) => {
                      const value = rowExam === colExam ? 1 : similarityMatrix.matrix.get(`${rowExam}-${colExam}`) ?? 0;
                      return (
                        <div
                          key={`${rowExam}-${colExam}`}
                          title={`${rowExam} vs ${colExam}: ${(value * 100).toFixed(1)}%`}
                          className="h-7 rounded"
                          style={{ background: `rgba(59,130,246,${0.06 + value * 0.9})` }}
                        />
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </motion.section>
      )}

      {page === "word" && (
        <motion.section initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <Card className="space-y-3">
            <div className="flex items-center gap-2">
              <Search size={16} />
              <Input
                value={selectedWord}
                onChange={(e) => setSelectedWord(e.target.value)}
                placeholder="ค้นหาคำศัพท์"
                className="max-w-sm"
              />
            </div>
            <div className="grid gap-3 md:grid-cols-3">
              <MetricCard title="คำศัพท์" value={selectedCard?.word ?? selectedWord} />
              <MetricCard title="พินอิน" value={selectedCard?.pinyin ?? "-"} />
              <MetricCard title="ความหมาย (ไทย/อังกฤษ)" value={selectedCard?.meaning ?? "-"} />
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge>ระดับ {tierByWord.get(selectedWord) ?? "B"}</Badge>
              <Badge variant="warning">
                Coverage {(selectedWordTimeline.length / Math.max(1, overview.totalExams) * 100).toFixed(1)}%
              </Badge>
              <Badge variant="success">
                Frequency {selectedWordTimeline.reduce((sum, row) => sum + row.count, 0)}
              </Badge>
            </div>
          </Card>
          <section className="grid gap-4 xl:grid-cols-2">
            <Card>
              <CardTitle>ไทม์ไลน์ความถี่</CardTitle>
              <div className="mt-4 h-[260px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={selectedWordTimeline}>
                    <CartesianGrid stroke="rgba(148,163,184,0.2)" />
                    <XAxis dataKey="examId" />
                    <YAxis />
                    <Tooltip />
                    <Line dataKey="count" stroke="#38bdf8" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>
            <Card>
              <CardTitle>คำศัพท์ที่เกี่ยวข้อง</CardTitle>
              <div className="mt-4 flex flex-wrap gap-2">
                {relatedWords.map((item) => (
                  <button
                    key={item.word}
                    className="rounded-full border border-border px-3 py-1 text-sm hover:bg-panelMuted"
                    onClick={() => setSelectedWord(item.word)}
                  >
                    {item.word} ({item.weight})
                  </button>
                ))}
              </div>
            </Card>
            <Card className="xl:col-span-2">
              <CardTitle>ตัวอย่างประโยค</CardTitle>
              <div className="mt-3 space-y-2">
                {(selectedCard?.exampleSentences ?? []).length > 0 ? (
                  selectedCard?.exampleSentences.map((sentence) => (
                    <p key={sentence} className="rounded-xl bg-panelMuted p-3 text-sm">
                      {sentence.split(selectedWord).join(`【${selectedWord}】`)}
                    </p>
                  ))
                ) : (
                  <p className="text-sm text-textMuted">ยังไม่มีตัวอย่างสำหรับคำนี้</p>
                )}
              </div>
            </Card>
          </section>
        </motion.section>
      )}

      {page === "strategy" && (
        <motion.section initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <Card>
            <CardTitle>ระบบแนะนำคำที่ควรอ่าน</CardTitle>
            <p className="mt-2 text-xl font-semibold">
              ถ้าศึกษา 150 คำแรก จะครอบคลุมประมาณ {coverage150.toFixed(1)}% ของความถี่ที่เคยออกทั้งหมด
            </p>
            <div className="mt-4 h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={coverageCurve}>
                  <CartesianGrid stroke="rgba(148,163,184,0.2)" />
                  <XAxis dataKey="wordsStudied" />
                  <YAxis />
                  <Tooltip />
                  <Line dataKey="coveragePct" stroke="#22c55e" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>
          <section className="grid gap-3 md:grid-cols-2">
            {strategyInsights.map((insight) => (
              <Card key={insight}>
                <CardTitle>อินไซต์ที่นำไปใช้ได้ทันที</CardTitle>
                <p className="mt-2 text-lg">{insight}</p>
              </Card>
            ))}
          </section>
          <details className="rounded-2xl border border-border bg-panel p-5">
            <summary className="cursor-pointer text-sm text-textMuted">ระดับ 3: ข้อมูลดิบ (15 คำที่คาดว่าจะออก)</summary>
            <ul className="mt-3 space-y-1 text-sm">
              {predictiveRows.slice(0, 15).map((row) => (
                <li key={row.word}>
                  {row.word} - คะแนน {row.predictedRelevanceScore} (ความถี่ {row.frequency}, coverage {row.coverage})
                </li>
              ))}
            </ul>
          </details>
        </motion.section>
      )}

      {page === "highValue" && (
        <motion.section initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <Card>
            <CardTitle>หน้าเว็บสำหรับข้อมูลจาก high_value_words.csv</CardTitle>
            <p className="mt-2 text-sm text-textMuted">
              แสดงข้อมูลคำศัพท์มูลค่าสูงทั้งหมด พร้อมค้นหาและดูคอลัมน์สำคัญ (อันดับ, คะแนน, ความถี่, การครอบคลุมข้อสอบ)
            </p>
            <div className="mt-3">
              <div className="flex flex-wrap gap-2">
                <Input
                  placeholder="ค้นหาคำศัพท์ / พินอิน / ความหมาย / เหตุผล"
                  value={highValueSearch}
                  onChange={(e) => setHighValueSearch(e.target.value)}
                  className="max-w-md"
                />
                <Button
                  variant={hideBasicWords ? "default" : "outline"}
                  onClick={() => setHideBasicWords((prev) => !prev)}
                >
                  {hideBasicWords ? "กำลังซ่อนคำพื้นฐาน" : "ซ่อนคำพื้นฐาน"}
                </Button>
                <Button
                  variant={highValueSortBy === "pinyin" ? "default" : "outline"}
                  onClick={() =>
                    setHighValueSortBy((prev) => (prev === "pinyin" ? "rank" : "pinyin"))
                  }
                >
                  {highValueSortBy === "pinyin" ? "เรียงตามพินอิน" : "เรียงตามอันดับ"}
                </Button>
                <Button
                  variant="outline"
                  onClick={() =>
                    setHighValueSortDirection((prev) => (prev === "asc" ? "desc" : "asc"))
                  }
                >
                  {highValueSortDirection === "asc" ? "เรียงน้อย→มาก" : "เรียงมาก→น้อย"}
                </Button>
              </div>
            </div>
          </Card>

          <Card>
            <CardTitle>รายการคำศัพท์มูลค่าสูง</CardTitle>
            <div className="mt-3 max-h-[560px] overflow-auto rounded-xl border border-border">
              <table className="min-w-full border-separate border-spacing-0 text-sm">
                <thead>
                  <tr className="text-left text-textMuted">
                    <th className="sticky top-0 z-40 bg-[#0b1220] px-3 py-2 shadow-[0_1px_0_0_rgba(36,50,74,1)]">อันดับ</th>
                    <th className="sticky top-0 z-40 bg-[#0b1220] px-3 py-2 shadow-[0_1px_0_0_rgba(36,50,74,1)]">คำศัพท์</th>
                    <th className="sticky top-0 z-40 bg-[#0b1220] px-3 py-2 shadow-[0_1px_0_0_rgba(36,50,74,1)]">พินอิน</th>
                    <th className="sticky top-0 z-40 bg-[#0b1220] px-3 py-2 shadow-[0_1px_0_0_rgba(36,50,74,1)]">ความหมาย</th>
                    <th className="sticky top-0 z-40 bg-[#0b1220] px-3 py-2 shadow-[0_1px_0_0_rgba(36,50,74,1)]">คะแนน</th>
                    <th className="sticky top-0 z-40 bg-[#0b1220] px-3 py-2 shadow-[0_1px_0_0_rgba(36,50,74,1)]">ความถี่</th>
                    <th className="sticky top-0 z-40 bg-[#0b1220] px-3 py-2 shadow-[0_1px_0_0_rgba(36,50,74,1)]">ครอบคลุมข้อสอบ</th>
                    <th className="sticky top-0 z-40 bg-[#0b1220] px-3 py-2 shadow-[0_1px_0_0_rgba(36,50,74,1)]">สถานะคำ</th>
                    <th className="sticky top-0 z-40 bg-[#0b1220] px-3 py-2 shadow-[0_1px_0_0_rgba(36,50,74,1)]">เหตุผลการจัดอันดับ</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedHighValueWords.slice(0, 1000).map((row) => (
                    <tr
                      key={`${row.rank}-${row.word}`}
                      className="border-t border-white/20 odd:bg-[#0a1424] even:bg-[#0b1728] hover:bg-[#13233a]"
                    >
                      <td className="px-3 py-2">{row.rank}</td>
                      <td className="px-3 py-2 font-medium">
                        <button
                          type="button"
                          className="rounded px-1 text-cyan-300 hover:bg-panelMuted hover:underline"
                          onClick={() => {
                            setSelectedWord(row.word);
                            setPage("word");
                          }}
                        >
                          {row.word}
                        </button>
                      </td>
                      <td className="px-3 py-2">{row.pinyin || "-"}</td>
                      <td className="px-3 py-2">{row.meaning || "-"}</td>
                      <td className="px-3 py-2">{row.score}</td>
                      <td className="px-3 py-2">{row.frequency}</td>
                      <td className="px-3 py-2">{row.examCoverage}</td>
                      <td className="px-3 py-2">
                        {row.isBasicWord ? <Badge variant="warning">คำพื้นฐาน</Badge> : <Badge variant="success">คำเด่นสอบ</Badge>}
                      </td>
                      <td className="px-3 py-2">
                        {(row.rankingReasons ?? []).length > 0 ? (row.rankingReasons ?? []).join(" + ") : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-2 text-xs text-textMuted">
              แสดง {Math.min(sortedHighValueWords.length, 1000)} จาก {sortedHighValueWords.length} รายการ
            </p>
          </Card>
        </motion.section>
      )}

      {page === "csvAll" && (
        <motion.section initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <Card>
            <CardTitle>รวมตารางจากไฟล์ CSV ทั้งหมด</CardTitle>
            <p className="mt-2 text-sm text-textMuted">
              หน้านี้รวมข้อมูลจาก `exam_similarity.csv`, `grammar_patterns.csv`, `listening_top_words.csv`, `predictive_analysis.csv`,
              `reading_top_words.csv`, `study_recommendations.csv`, `topics.csv`, และ `vocabulary_frequency.csv`
            </p>
          </Card>

          <CsvPreviewTable
            title="exam_similarity.csv"
            rows={similarityRows}
            onWordClick={(word) => {
              setSelectedWord(word);
              setPage("word");
            }}
            columns={[
              ["examA", "ข้อสอบ A"],
              ["examB", "ข้อสอบ B"],
              ["jaccardSimilarity", "คะแนนความคล้าย"],
              ["sharedWords", "คำซ้ำร่วม"]
            ]}
          />

          <CsvPreviewTable
            title="grammar_patterns.csv"
            rows={grammar}
            onWordClick={(word) => {
              setSelectedWord(word);
              setPage("word");
            }}
            columns={[
              ["pattern", "แพทเทิร์น"],
              ["occurrenceCount", "จำนวนครั้ง"],
              ["examCount", "จำนวนข้อสอบ"],
              ["sectionDistribution", "สัดส่วนตามพาร์ต"]
            ]}
          />

          <CsvPreviewTable
            title="listening_top_words.csv"
            rows={listeningTopCsv}
            onWordClick={(word) => {
              setSelectedWord(word);
              setPage("word");
            }}
            columns={[
              ["word", "คำศัพท์"],
              ["count", "จำนวนครั้ง"]
            ]}
          />

          <CsvPreviewTable
            title="predictive_analysis.csv"
            rows={predictiveRows}
            onWordClick={(word) => {
              setSelectedWord(word);
              setPage("word");
            }}
            columns={[
              ["word", "คำศัพท์"],
              ["frequency", "ความถี่"],
              ["coverage", "จำนวนข้อสอบที่พบ"],
              ["predictedRelevanceScore", "คะแนนคาดการณ์"]
            ]}
          />

          <CsvPreviewTable
            title="reading_top_words.csv"
            rows={readingTopCsv}
            onWordClick={(word) => {
              setSelectedWord(word);
              setPage("word");
            }}
            columns={[
              ["word", "คำศัพท์"],
              ["count", "จำนวนครั้ง"]
            ]}
          />

          <CsvPreviewTable
            title="study_recommendations.csv"
            rows={recommendations}
            onWordClick={(word) => {
              setSelectedWord(word);
              setPage("word");
            }}
            columns={[
              ["tier", "ระดับ"],
              ["word", "คำศัพท์"],
              ["frequency", "ความถี่"],
              ["examCoverage", "ครอบคลุมข้อสอบ"]
            ]}
          />

          <CsvPreviewTable
            title="topics.csv"
            rows={topics}
            onWordClick={(word) => {
              setSelectedWord(word);
              setPage("word");
            }}
            columns={[
              ["topicId", "รหัสหัวข้อ"],
              ["topicLabel", "หัวข้อ"],
              ["examIds", "ข้อสอบ"],
              ["topWords", "คำเด่น"],
              ["frequency", "ความถี่"]
            ]}
          />

          <CsvPreviewTable
            title="vocabulary_frequency.csv"
            rows={stats}
            onWordClick={(word) => {
              setSelectedWord(word);
              setPage("word");
            }}
            columns={[
              ["word", "คำศัพท์"],
              ["totalOccurrences", "ความถี่รวม"],
              ["examsAppeared", "จำนวนข้อสอบที่พบ"],
              ["listeningCount", "พาร์ตฟัง"],
              ["readingCount", "พาร์ตอ่าน"],
              ["grammarCount", "พาร์ตไวยากรณ์"],
              ["vocabularyCount", "พาร์ตคำศัพท์"]
            ]}
          />
        </motion.section>
      )}

      {page === "sentenceBuilder" && (
        <motion.section initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <Card>
            <CardTitle>หมวดคำศัพท์แต่งประโยค (แนวข้อสอบรูปภาพ/คำศัพท์)</CardTitle>
            <p className="mt-2 text-sm text-textMuted">
              ฝึกจากโจทย์ที่มีลักษณะ "ดูภาพ/เติมประโยค/แต่งประโยค" ซึ่งคัดจากข้อสอบจริงอัตโนมัติ
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Input
                placeholder="ค้นหาโจทย์/คีย์เวิร์ด"
                value={sentenceSearch}
                onChange={(e) => {
                  setSentenceSearch(e.target.value);
                  setSentenceIndex(0);
                }}
                className="max-w-md"
              />
              <Button
                variant="outline"
                onClick={() => {
                  if (!filteredSentenceItems.length) return;
                  setSentenceIndex(Math.floor(Math.random() * filteredSentenceItems.length));
                }}
              >
                สุ่มโจทย์
              </Button>
              <Button
                variant={showUntrustedSentenceItems ? "default" : "outline"}
                onClick={() => {
                  setShowUntrustedSentenceItems((prev) => !prev);
                  setSentenceIndex(0);
                }}
              >
                {showUntrustedSentenceItems ? "กำลังแสดงทุกข้อ" : "แสดงเฉพาะข้อเชื่อถือสูง"}
              </Button>
              <Button
                variant={showExampleMode ? "default" : "outline"}
                onClick={() => setShowExampleMode((prev) => !prev)}
              >
                {showExampleMode ? "ซ่อนเฉลยตัวอย่าง" : "เปิดโหมดเฉลยตัวอย่าง"}
              </Button>
            </div>
          </Card>

          {currentSentenceItem ? (
            <Card className="space-y-3">
              <div className="flex flex-wrap items-center gap-2 text-sm text-textMuted">
                <span>ข้อสอบ: {currentSentenceItem.examId}</span>
                <span>ข้อที่: {currentSentenceItem.questionNo}</span>
                <span>พาร์ต: {currentSentenceItem.section}</span>
                <span>confidence: {(currentSentenceItem.confidence * 100).toFixed(0)}%</span>
                <span>วิธี parse: {currentSentenceItem.parseMethod}</span>
                {currentSentenceItem.hasImageHint && <Badge variant="warning">มีคำใบ้รูปภาพ</Badge>}
                {currentSentenceItem.isTrusted ? <Badge variant="success">เชื่อถือได้สูง</Badge> : <Badge variant="danger">ความเชื่อถือต่ำ</Badge>}
              </div>
              <div className="rounded-xl border border-border bg-panelMuted p-3">
                <p className="text-sm text-textMuted">โจทย์</p>
                <p className="mt-1 text-base">{currentSentenceItem.prompt}</p>
              </div>
              {currentSentenceItem.imagePath && (
                <div className="rounded-xl border border-border bg-panelMuted p-3">
                  <p className="mb-2 text-sm text-textMuted">ภาพจากข้อสอบ</p>
                  <img
                    src={currentSentenceItem.imagePath}
                    alt={`exam-${currentSentenceItem.examId}-q${currentSentenceItem.questionNo}`}
                    className="max-h-[520px] w-full rounded-lg object-contain"
                    loading="lazy"
                  />
                </div>
              )}

              <div>
                <p className="mb-2 text-sm text-textMuted">คีย์เวิร์ดที่ควรพยายามใช้</p>
                <div className="flex flex-wrap gap-2">
                  {currentSentenceItem.keywords.map((k) => (
                    <button
                      type="button"
                      key={k}
                      className="rounded-full border border-border px-2 py-1 text-xs hover:bg-panelMuted"
                      onClick={() => {
                        setSentenceDraft((prev) => `${prev}${prev ? " " : ""}${k}`);
                      }}
                    >
                      {k}
                    </button>
                  ))}
                </div>
              </div>

              {currentSentenceItem.options.length > 0 && (
                <div>
                  <p className="mb-2 text-sm text-textMuted">ตัวเลือกจากข้อสอบ (ใช้เป็นคำใบ้ได้)</p>
                  <div className="flex flex-wrap gap-2">
                    {currentSentenceItem.options.map((opt) => (
                      <button
                        type="button"
                        key={opt}
                        className="rounded border border-border px-2 py-1 text-xs hover:bg-panelMuted"
                        onClick={() => setSentenceDraft((prev) => `${prev}${prev ? " " : ""}${opt}`)}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <p className="mb-2 text-sm text-textMuted">แต่งประโยคของคุณ</p>
                <textarea
                  value={sentenceDraft}
                  onChange={(e) => setSentenceDraft(e.target.value)}
                  className="min-h-[120px] w-full rounded-xl border border-border bg-panelMuted p-3 text-sm text-text"
                  placeholder="พิมพ์ประโยคภาษาจีนที่แต่งเอง..."
                />
                <div className="mt-2 flex flex-wrap gap-2">
                  <Button
                    variant="default"
                    onClick={() => {
                      if (!currentSentenceItem) return;
                      setSavedSentenceMap((prev) => ({ ...prev, [currentSentenceItem.id]: sentenceDraft.trim() }));
                      setSaveMessage("บันทึกประโยคเรียบร้อยแล้ว");
                    }}
                  >
                    บันทึกประโยคที่แต่งไว้
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => {
                      if (!currentSentenceItem) return;
                      setSentenceDraft(savedSentenceMap[currentSentenceItem.id] ?? "");
                      setSaveMessage("โหลดประโยคที่บันทึกไว้แล้ว");
                    }}
                  >
                    โหลดประโยคที่บันทึกไว้
                  </Button>
                </div>
                {saveMessage && <p className="mt-2 text-xs text-cyan-300">{saveMessage}</p>}
              </div>

              <div className="rounded-xl border border-border bg-panelMuted p-3 text-sm">
                <p>การใช้คีย์เวิร์ดตรงโจทย์: {sentenceHintMatched}%</p>
                <p>คะแนน grammar เบื้องต้น: {sentenceGrammarCheck.score}/100</p>
                {sentenceGrammarCheck.issues.length > 0 ? (
                  <ul className="mt-1 list-disc space-y-0.5 pl-5 text-textMuted">
                    {sentenceGrammarCheck.issues.map((issue) => (
                      <li key={issue}>{issue}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-textMuted">โครงสร้างพื้นฐานผ่านเงื่อนไขเบื้องต้น</p>
                )}
                <p className="mt-1 text-textMuted">*เป็นการประเมิน grammar แบบเบื้องต้น ไม่ใช่ตัวตรวจไวยากรณ์ระดับ NLP เต็มรูปแบบ</p>
              </div>

              {showExampleMode && (
                <div className="rounded-xl border border-border bg-panelMuted p-3 text-sm">
                  <p className="font-medium">เฉลยตัวอย่างต่อข้อ</p>
                  {currentSentenceItem.answer &&
                    !["A", "B", "C", "D"].includes(currentSentenceItem.answer) && (
                      <div className="mt-2 rounded-lg border border-green-500/35 bg-green-500/10 p-2">
                        <p className="text-xs text-green-300">เฉลยอ้างอิงจากข้อสอบ</p>
                        <p className="mt-1 text-sm">{currentSentenceItem.answer}</p>
                      </div>
                    )}
                  {exampleModeSentences.length > 0 ? (
                    <ul className="mt-2 list-disc space-y-1 pl-5">
                      {exampleModeSentences.map((sentence) => (
                        <li key={sentence}>{sentence}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="mt-2 text-textMuted">ยังไม่มีตัวอย่างที่จับคู่คีย์เวิร์ดได้ในคลังข้อมูล</p>
                  )}
                </div>
              )}

              <div className="flex gap-2">
                <Button
                  variant="ghost"
                  onClick={() => {
                    setSentenceIndex((prev) => Math.max(0, prev - 1));
                  }}
                >
                  ข้อก่อนหน้า
                </Button>
                <Button
                  variant="default"
                  onClick={() => {
                    setSentenceIndex((prev) => Math.min(filteredSentenceItems.length - 1, prev + 1));
                  }}
                >
                  ข้อถัดไป
                </Button>
              </div>
            </Card>
          ) : (
            <Card>
              <p className="text-sm text-textMuted">ไม่พบโจทย์ที่ตรงเงื่อนไขการค้นหา</p>
            </Card>
          )}
        </motion.section>
      )}
    </div>
  );
}

function MetricCard({ title, value }: { title: string; value: string }) {
  return (
    <Card>
      <CardTitle>{title}</CardTitle>
      <CardValue>{value}</CardValue>
    </Card>
  );
}

function InsightCard({
  title,
  value,
  detail,
  icon
}: {
  title: string;
  value: string;
  detail: string;
  icon: ReactNode;
}) {
  return (
    <Card>
      <div className="flex items-center justify-between">
        <CardTitle>{title}</CardTitle>
        {icon}
      </div>
      <CardValue className="text-2xl">{value}</CardValue>
      <p className="mt-1 text-sm text-textMuted">{detail}</p>
    </Card>
  );
}

function ScatterTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload as ScatterPoint;
  return (
    <div className="rounded-xl border border-border bg-panel p-3 text-sm">
      <p className="font-semibold">{point.word}</p>
      <p>การครอบคลุม: {point.coveragePct}%</p>
      <p>ความถี่: {point.frequency}</p>
      <p>ความยาก: {point.difficulty}</p>
      <p>ระดับ: {point.tier}</p>
    </div>
  );
}

function ListeningTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload as { word: string; frequency: number; difficulty: number; coverage: number };
  return (
    <div className="rounded-xl border border-border bg-panel p-3 text-sm">
      <p className="font-semibold">{point.word}</p>
      <p>ความถี่: {point.frequency}</p>
      <p>ความยาก: {point.difficulty}</p>
      <p>การครอบคลุม: {point.coverage}</p>
    </div>
  );
}

function CompareTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload as { word: string; listening: number; reading: number };
  return (
    <div className="rounded-xl border border-border bg-panel p-3 text-sm">
      <p className="font-semibold">{point.word}</p>
      <p>พาร์ตฟัง: {point.listening}</p>
      <p>พาร์ตอ่าน: {point.reading}</p>
    </div>
  );
}

function CsvPreviewTable({
  title,
  rows,
  columns,
  onWordClick
}: {
  title: string;
  rows: object[];
  columns: Array<[string, string]>;
  onWordClick?: (word: string) => void;
}) {
  return (
    <Card>
      <CardTitle>{title}</CardTitle>
      <div className="mt-3 max-h-[360px] overflow-auto rounded-xl border border-border">
        <table className="min-w-full border-separate border-spacing-0 text-sm">
          <thead>
            <tr className="text-left text-textMuted">
              {columns.map(([, label]) => (
                <th key={label} className="sticky top-0 z-40 bg-[#0b1220] px-3 py-2 shadow-[0_1px_0_0_rgba(36,50,74,1)]">
                  {label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 300).map((row, idx) => (
              <tr
                key={`${title}-${idx}`}
                className="border-t border-white/20 odd:bg-[#0a1424] even:bg-[#0b1728] hover:bg-[#13233a]"
              >
                {columns.map(([key]) => (
                  <td key={`${title}-${idx}-${key}`} className="max-w-[360px] truncate px-3 py-2">
                    {renderCsvCell((row as Record<string, unknown>)[key], key, onWordClick)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-xs text-textMuted">แสดง {Math.min(rows.length, 300)} จาก {rows.length} รายการ</p>
    </Card>
  );
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return "-";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function renderCsvCell(value: unknown, key: string, onWordClick?: (word: string) => void) {
  if (!onWordClick) return formatCell(value);

  if (key === "word" && typeof value === "string" && hasChinese(value)) {
    return (
      <button
        type="button"
        className="rounded px-1 text-cyan-300 hover:bg-panelMuted hover:underline"
        onClick={() => onWordClick(value)}
      >
        {value}
      </button>
    );
  }

  if (key === "topWords" && Array.isArray(value)) {
    return (
      <div className="flex flex-wrap gap-1">
        {value.map((item) => {
          const text = String(item);
          const clickable = hasChinese(text);
          return clickable ? (
            <button
              key={text}
              type="button"
              className="rounded-full border border-border px-2 py-0.5 text-xs text-cyan-300 hover:bg-panelMuted hover:underline"
              onClick={() => onWordClick(text)}
            >
              {text}
            </button>
          ) : (
            <span key={text} className="rounded-full border border-border px-2 py-0.5 text-xs">
              {text}
            </span>
          );
        })}
      </div>
    );
  }

  return formatCell(value);
}

function hasChinese(text: string): boolean {
  return /[\u4e00-\u9fff]/.test(text);
}

function evaluateSentenceDraft(draft: string, keywords: string[]): { score: number; issues: string[] } {
  const text = draft.trim();
  const issues: string[] = [];

  if (!text) {
    return { score: 0, issues: ["ยังไม่ได้พิมพ์ประโยค"] };
  }

  const chineseChars = (text.match(/[\u4e00-\u9fff]/g) || []).length;
  if (chineseChars < 8) {
    issues.push("ประโยคสั้นเกินไป (แนะนำอย่างน้อย 8 ตัวอักษรจีน)");
  }

  const hasEndingPunctuation = /[。！？!?]$/.test(text);
  if (!hasEndingPunctuation) {
    issues.push("ควรลงท้ายด้วยเครื่องหมายวรรคตอน เช่น 。");
  }

  const matchedKeywords = keywords.filter((k) => text.includes(k)).length;
  if (keywords.length > 0 && matchedKeywords === 0) {
    issues.push("ยังไม่มีคีย์เวิร์ดจากโจทย์ในประโยค");
  }

  let score = 100;
  if (chineseChars < 8) score -= 30;
  if (!hasEndingPunctuation) score -= 20;
  if (keywords.length > 0) {
    const ratio = matchedKeywords / keywords.length;
    if (ratio < 0.2) score -= 25;
    else if (ratio < 0.4) score -= 15;
    else if (ratio < 0.6) score -= 8;
  }
  if (/(。。|，，|！！|\?\?)/.test(text)) {
    score -= 10;
    issues.push("พบเครื่องหมายซ้ำหลายตัวติดกัน");
  }

  score = Math.max(0, Math.min(100, Math.round(score)));
  return { score, issues };
}

