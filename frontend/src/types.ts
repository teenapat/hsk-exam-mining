export interface Overview {
  totalExams: number;
  totalQuestions: number;
  totalVocabulary: number;
  totalListeningScripts: number;
}

export interface VocabStat {
  word: string;
  totalOccurrences: number;
  examsAppeared: number;
  listeningCount: number;
  readingCount: number;
  grammarCount: number;
  vocabularyCount: number;
}

export interface GrammarPattern {
  pattern: string;
  occurrenceCount: number;
  examCount: number;
  sectionDistribution?: Record<string, number>;
}
    
export interface TierRecommendation {
  tier: "S" | "A" | "B";
  word: string;
  frequency: number;
  examCoverage: number;
}

export interface VocabularyCard {
  word: string;
  pinyin: string;
  meaning: string;
  frequency: number;
  exampleSentences: string[];
}

export interface WordOccurrence {
  word: string;
  examId: string;
  section: string;
}

export interface TopicItem {
  topicId: number;
  topicLabel: string;
  examIds: string[];
  topWords: string[];
  frequency: number;
}

export interface HighValueWord {
  rank: number;
  word: string;
  score: number;
  frequency: number;
  examCoverage: number;
  coverageRatio?: number;
  isBasicWord?: boolean;
  rankingReasons?: string[];
  pinyin: string;
  meaning: string;
}

export interface SimilarityRow {
  examA: string;
  examB: string;
  jaccardSimilarity: number;
  sharedWords: number;
}

export interface PredictiveRow {
  word: string;
  frequency: number;
  coverage: number;
  predictedRelevanceScore: number;
}

export interface VocabGraph {
  nodes: Array<{ id: string; degree: number }>;
  edges: Array<{ source: string; target: string; weight: number }>;
}

export interface SentenceBuilderItem {
  id: string;
  examId: string;
  questionNo: number;
  section: string;
  prompt: string;
  keywords: string[];
  options: string[];
  answer?: string;
  hasImageHint: boolean;
  confidence: number;
  parseMethod: string;
  isTrusted: boolean;
  imagePath?: string | null;
}

