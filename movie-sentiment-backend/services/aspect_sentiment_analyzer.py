import logging
import re
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Set, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


class AspectSentimentAnalyzer:
    """
    Extracts review aspects/topics and computes sentiment for each aspect.

    Pipeline:
    1) Candidate phrase mining (TF-IDF n-grams, KeyBERT-like approach)
    2) Aspect normalization (map aliases -> canonical aspects)
    3) Sentence-level sentiment per matched aspect
    4) Aggregate polarity, confidence, and coverage metrics
    """

    MOVIE_ASPECT_SYNONYMS: Dict[str, Set[str]] = {
        "acting": {
            "acting",
            "actor",
            "actors",
            "performance",
            "performances",
            "cast",
            "lead actor",
            "supporting actor",
        },
        "direction": {
            "direction",
            "director",
            "directing",
            "filmmaking",
            "vision",
        },
        "story": {
            "story",
            "plot",
            "narrative",
            "screenplay",
            "script",
            "writing",
            "storyline",
        },
        "pacing": {
            "pacing",
            "pace",
            "slow",
            "slow paced",
            "rushed",
            "drag",
            "dragging",
            "runtime",
        },
        "cinematography": {
            "cinematography",
            "visuals",
            "camera work",
            "camera",
            "shots",
            "framing",
            "photography",
            "production design",
        },
        "music": {
            "music",
            "songs",
            "soundtrack",
            "score",
            "background score",
            "bgm",
        },
        "editing": {
            "editing",
            "edit",
            "cuts",
            "cutting",
            "transition",
            "transitions",
        },
        "characters": {
            "character",
            "characters",
            "characterization",
            "character arc",
            "protagonist",
            "antagonist",
        },
        "dialogue": {
            "dialogue",
            "dialogues",
            "lines",
            "writing",
            "punchline",
        },
        "visual_effects": {
            "visual effects",
            "effects",
            "vfx",
            "cgi",
            "animation",
            "graphics",
        },
        "ending": {
            "ending",
            "climax",
            "finale",
            "last act",
            "twist ending",
        },
        # Product-centric aspects
        "battery": {
            "battery",
            "battery life",
            "backup",
            "charging",
            "fast charging",
            "drain",
        },
        "camera": {
            "camera",
            "front camera",
            "rear camera",
            "selfie",
            "photo quality",
            "video quality",
            "lens",
        },
        "display": {
            "display",
            "screen",
            "brightness",
            "resolution",
            "refresh rate",
            "panel",
        },
        "performance": {
            "performance",
            "speed",
            "processor",
            "lag",
            "smoothness",
            "gaming",
            "multitasking",
        },
        "build_quality": {
            "build quality",
            "build",
            "design",
            "durability",
            "material",
            "finish",
        },
        "price": {
            "price",
            "cost",
            "expensive",
            "cheap",
            "value",
            "value for money",
            "pricing",
        },
        "software": {
            "software",
            "ui",
            "interface",
            "update",
            "bugs",
            "os",
        },
        "audio": {
            "audio",
            "sound",
            "speaker",
            "bass",
            "volume",
            "microphone",
        },
        "delivery": {
            "delivery",
            "shipping",
            "packaging",
            "installation",
            "courier",
        },
        "customer_service": {
            "customer service",
            "support",
            "service center",
            "replacement",
            "refund",
            "warranty",
        },
        # YouTube/content-centric aspects
        "content_quality": {
            "content",
            "quality",
            "informative",
            "useful",
            "value",
            "topic",
        },
        "presenter": {
            "presenter",
            "host",
            "creator",
            "speaker",
            "narration",
            "explanation",
        },
        "thumbnail_title": {
            "thumbnail",
            "title",
            "clickbait",
        },
    }

    STOPWORDS = {
        "a",
        "about",
        "after",
        "again",
        "all",
        "also",
        "am",
        "an",
        "and",
        "any",
        "are",
        "as",
        "at",
        "be",
        "because",
        "been",
        "before",
        "being",
        "between",
        "both",
        "but",
        "by",
        "can",
        "could",
        "did",
        "do",
        "does",
        "doing",
        "down",
        "during",
        "each",
        "few",
        "for",
        "from",
        "further",
        "had",
        "has",
        "have",
        "having",
        "he",
        "her",
        "here",
        "hers",
        "herself",
        "him",
        "himself",
        "his",
        "how",
        "i",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "itself",
        "just",
        "me",
        "more",
        "most",
        "my",
        "myself",
        "no",
        "nor",
        "not",
        "of",
        "off",
        "on",
        "once",
        "only",
        "or",
        "other",
        "our",
        "ours",
        "ourselves",
        "out",
        "over",
        "own",
        "same",
        "she",
        "should",
        "so",
        "some",
        "such",
        "than",
        "that",
        "the",
        "their",
        "theirs",
        "them",
        "themselves",
        "then",
        "there",
        "these",
        "they",
        "this",
        "those",
        "through",
        "to",
        "too",
        "under",
        "until",
        "up",
        "very",
        "was",
        "we",
        "were",
        "what",
        "when",
        "where",
        "which",
        "while",
        "who",
        "whom",
        "why",
        "will",
        "with",
        "you",
        "your",
        "yours",
        "yourself",
        "yourselves",
        "movie",
        "film",
        "watch",
        "watched",
        "review",
        "reviews",
    }

    GENERIC_CANDIDATE_FILTER = {
        "good",
        "bad",
        "great",
        "amazing",
        "terrible",
        "nice",
        "awesome",
    }

    def __init__(self):
        self._canonical_aliases = {
            aspect: {aspect, *aliases} for aspect, aliases in self.MOVIE_ASPECT_SYNONYMS.items()
        }

    def empty_summary(self) -> Dict[str, Any]:
        return {
            "aspects": [],
            "aspects_detected": 0,
            "coverage_percentage": 0.0,
            "average_confidence": 0.0,
            "positive_aspects": [],
            "negative_aspects": [],
            "neutral_aspects": [],
            "extraction_method": (
                "tfidf_phrase_mining + canonical_aspect_mapping + "
                "sentence_level_transformer_sentiment"
            ),
        }

    def analyze_reviews(
        self,
        reviews: List[Dict[str, Any]],
        sentiment_analyzer: Any,
        max_aspects: int = 12,
        min_aspect_mentions: int = 2,
    ) -> Tuple[Dict[str, Any], Dict[str, List[Dict[str, Any]]]]:
        if not reviews:
            return self.empty_summary(), {}

        texts = [str((item or {}).get("text", "")).strip() for item in reviews]
        texts = [text for text in texts if text]
        if not texts:
            return self.empty_summary(), {}

        max_aspects = max(3, min(30, int(max_aspects or 12)))
        min_aspect_mentions = max(1, min(10, int(min_aspect_mentions or 2)))

        aspect_aliases = self._build_aspect_aliases(texts)
        aspect_patterns = self._compile_aspect_patterns(aspect_aliases)

        if not aspect_patterns:
            return self.empty_summary(), {}

        aspect_stats = {
            aspect: {
                "mentions": 0,
                "sentiment_counts": {"positive": 0, "negative": 0, "neutral": 0},
                "signed_score_sum": 0.0,
                "confidence_sum": 0.0,
                "snippets": [],
                "token_counter": Counter(),
            }
            for aspect in aspect_patterns
        }

        sentence_sentiment_cache: Dict[str, Dict[str, Any]] = {}
        review_aspect_mentions: Dict[str, List[Dict[str, Any]]] = {}
        reviews_with_any_aspect = 0

        for review in reviews:
            text = str((review or {}).get("text", "")).strip()
            if not text:
                continue

            sentences = self._split_sentences(text)
            if not sentences:
                sentences = [text]

            per_review_mentions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

            for sentence in sentences:
                matched_aspects = self._match_aspects(sentence, aspect_patterns)
                if not matched_aspects:
                    continue

                for aspect in matched_aspects:
                    aspect_context = self._extract_aspect_context(sentence, aspect_patterns[aspect])
                    cache_key = aspect_context
                    if cache_key in sentence_sentiment_cache:
                        sentiment_result = sentence_sentiment_cache[cache_key]
                    else:
                        sentiment_result = sentiment_analyzer.predict_sentiment(
                            aspect_context,
                            author_rating=None,
                        )
                        sentence_sentiment_cache[cache_key] = sentiment_result

                    label = self._normalize_sentiment_label(sentiment_result.get("label"))
                    score = self._bounded_float(sentiment_result.get("score"), default=0.5)
                    signed_score = self._signed_sentiment_score(label, score)

                    aspect_stat = aspect_stats[aspect]
                    aspect_stat["mentions"] += 1
                    aspect_stat["sentiment_counts"][label] += 1
                    aspect_stat["signed_score_sum"] += signed_score
                    aspect_stat["confidence_sum"] += score
                    aspect_stat["snippets"].append(aspect_context)

                    tokens = self._extract_keywords_from_text(aspect_context, limit=8)
                    aspect_stat["token_counter"].update(tokens)

                    per_review_mentions[aspect].append(
                        {
                            "sentiment": label,
                            "sentiment_score": round(score, 3),
                            "snippet": aspect_context,
                        }
                    )

            if per_review_mentions:
                reviews_with_any_aspect += 1
                review_aspect_mentions[text] = self._aggregate_review_mentions(per_review_mentions)

        finalized = self._finalize_aspects(
            aspect_stats=aspect_stats,
            max_aspects=max_aspects,
            min_aspect_mentions=min_aspect_mentions,
            total_reviews=max(1, len(texts)),
            reviews_with_any_aspect=reviews_with_any_aspect,
        )

        return finalized, review_aspect_mentions

    def _build_aspect_aliases(self, texts: List[str]) -> Dict[str, Set[str]]:
        aliases = {aspect: set(values) for aspect, values in self._canonical_aliases.items()}
        candidates = self._extract_candidate_phrases(texts, top_k=60)

        for phrase, _score in candidates:
            mapped_aspect = self._map_phrase_to_aspect(phrase)
            if mapped_aspect:
                aliases[mapped_aspect].add(phrase)

        return aliases

    def _extract_candidate_phrases(self, texts: List[str], top_k: int = 60) -> List[Tuple[str, float]]:
        cleaned_texts = [self._normalize_whitespace(text) for text in texts if text and text.strip()]
        if not cleaned_texts:
            return []

        min_df = 2 if len(cleaned_texts) >= 8 else 1
        max_df = 0.95 if len(cleaned_texts) >= 10 else 1.0

        try:
            vectorizer = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 3),
                min_df=min_df,
                max_df=max_df,
                lowercase=True,
                token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z']+\b",
            )
            matrix = vectorizer.fit_transform(cleaned_texts)
        except Exception as exc:
            logger.warning("TF-IDF candidate extraction failed: %s", exc)
            return []

        feature_names = vectorizer.get_feature_names_out()
        scores = matrix.mean(axis=0).A1
        ranked = sorted(zip(feature_names, scores), key=lambda item: item[1], reverse=True)

        candidates: List[Tuple[str, float]] = []
        for term, score in ranked:
            term = term.strip().lower()
            if not self._is_valid_candidate(term):
                continue
            candidates.append((term, float(score)))
            if len(candidates) >= top_k:
                break
        return candidates

    def _map_phrase_to_aspect(self, phrase: str) -> str:
        phrase_tokens = set(phrase.split())
        best_aspect = ""
        best_score = 0.0

        for aspect, synonyms in self._canonical_aliases.items():
            for synonym in synonyms:
                syn = synonym.lower()
                if phrase == syn:
                    return aspect

                syn_tokens = set(syn.split())
                overlap = len(phrase_tokens.intersection(syn_tokens))
                if overlap == 0:
                    continue

                precision = overlap / max(1, len(phrase_tokens))
                recall = overlap / max(1, len(syn_tokens))
                f1 = (2 * precision * recall) / max(0.0001, precision + recall)
                if f1 > best_score:
                    best_score = f1
                    best_aspect = aspect

        if best_score >= 0.67:
            return best_aspect
        return ""

    def _compile_aspect_patterns(self, aspect_aliases: Dict[str, Set[str]]) -> Dict[str, re.Pattern]:
        patterns: Dict[str, re.Pattern] = {}
        for aspect, aliases in aspect_aliases.items():
            cleaned_aliases = sorted(
                {alias.strip().lower() for alias in aliases if alias and alias.strip()},
                key=len,
                reverse=True,
            )
            if not cleaned_aliases:
                continue

            escaped = [re.escape(alias) for alias in cleaned_aliases]
            regex = r"\b(?:%s)\b" % "|".join(escaped)
            patterns[aspect] = re.compile(regex, flags=re.IGNORECASE)

        return patterns

    def _match_aspects(self, sentence: str, patterns: Dict[str, re.Pattern]) -> List[str]:
        sentence = sentence.strip()
        if not sentence:
            return []
        return [aspect for aspect, pattern in patterns.items() if pattern.search(sentence)]

    def _extract_aspect_context(self, sentence: str, aspect_pattern: re.Pattern) -> str:
        sentence = self._normalize_whitespace(sentence)
        if not sentence:
            return ""

        match = aspect_pattern.search(sentence)
        if not match:
            return sentence[:220]

        context_start = max(0, match.start() - 55)
        context_end = min(len(sentence), match.end() + 75)

        left_pivot = max(
            sentence.rfind(".", 0, context_start),
            sentence.rfind(",", 0, context_start),
            sentence.rfind(";", 0, context_start),
            sentence.rfind(":", 0, context_start),
        )
        if left_pivot != -1:
            context_start = left_pivot + 1

        right_candidates = [
            idx for idx in [
                sentence.find(".", context_end),
                sentence.find(",", context_end),
                sentence.find(";", context_end),
                sentence.find(":", context_end),
            ] if idx != -1
        ]
        if right_candidates:
            context_end = min(right_candidates)

        context = sentence[context_start:context_end].strip()
        if not context:
            context = sentence

        # Favor the clause around the aspect when conjunctions split mixed sentiment.
        clause_parts = re.split(r"\b(?:but|however|although|though|yet)\b", context, flags=re.IGNORECASE)
        if len(clause_parts) > 1:
            for clause in clause_parts:
                if aspect_pattern.search(clause):
                    context = clause.strip()
                    break

        return context[:220]

    def _aggregate_review_mentions(
        self,
        review_mentions: Dict[str, List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        aggregated = []
        for aspect, mentions in review_mentions.items():
            if not mentions:
                continue

            counts = {"positive": 0, "negative": 0, "neutral": 0}
            score_sum = 0.0
            for item in mentions:
                label = item["sentiment"]
                if label not in counts:
                    label = "neutral"
                counts[label] += 1
                score_sum += float(item["sentiment_score"])

            total = max(1, len(mentions))
            dominant = max(counts.items(), key=lambda pair: pair[1])[0]
            confidence = max(counts.values()) / total
            aggregated.append(
                {
                    "aspect": self._humanize_aspect(aspect),
                    "sentiment": dominant,
                    "sentiment_score": round(score_sum / total, 3),
                    "confidence": round(confidence, 3),
                    "snippet": mentions[0]["snippet"][:220],
                }
            )

        return sorted(aggregated, key=lambda row: row["confidence"], reverse=True)

    def _finalize_aspects(
        self,
        aspect_stats: Dict[str, Dict[str, Any]],
        max_aspects: int,
        min_aspect_mentions: int,
        total_reviews: int,
        reviews_with_any_aspect: int,
    ) -> Dict[str, Any]:
        finalized_aspects = []

        for aspect, stats in aspect_stats.items():
            mentions = int(stats["mentions"])
            if mentions < min_aspect_mentions:
                continue

            distribution = {
                key: round((value / mentions) * 100, 2)
                for key, value in stats["sentiment_counts"].items()
            }

            avg_signed = stats["signed_score_sum"] / mentions
            sentiment = self._label_from_signed_score(avg_signed, distribution)

            confidence = self._compute_aspect_confidence(
                mentions=mentions,
                total_reviews=total_reviews,
                avg_signed=avg_signed,
                distribution=distribution,
                avg_model_confidence=(stats["confidence_sum"] / mentions),
            )

            representative_keywords = [word for word, _ in stats["token_counter"].most_common(5)]
            if not representative_keywords:
                representative_keywords = [self._humanize_aspect(aspect).lower()]

            snippets = []
            seen_snippets = set()
            for snippet in stats["snippets"]:
                cleaned = self._normalize_whitespace(snippet)
                if not cleaned or cleaned in seen_snippets:
                    continue
                seen_snippets.add(cleaned)
                snippets.append(cleaned[:220])
                if len(snippets) >= 3:
                    break

            sentiment_score = self._compute_aspect_sentiment_score(sentiment, distribution, avg_signed)

            finalized_aspects.append(
                {
                    "aspect": self._humanize_aspect(aspect),
                    "mentions": mentions,
                    "sentiment": sentiment,
                    "sentiment_score": round(sentiment_score, 3),
                    "confidence": round(confidence, 3),
                    "sentiment_distribution": distribution,
                    "representative_keywords": representative_keywords,
                    "example_snippets": snippets,
                }
            )

        if not finalized_aspects:
            return self.empty_summary()

        finalized_aspects.sort(
            key=lambda item: (item["mentions"], item["confidence"], item["sentiment_score"]),
            reverse=True,
        )
        finalized_aspects = finalized_aspects[:max_aspects]

        positive_aspects = [row["aspect"] for row in finalized_aspects if row["sentiment"] == "positive"]
        negative_aspects = [row["aspect"] for row in finalized_aspects if row["sentiment"] == "negative"]
        neutral_aspects = [row["aspect"] for row in finalized_aspects if row["sentiment"] == "neutral"]

        avg_confidence = sum(row["confidence"] for row in finalized_aspects) / max(1, len(finalized_aspects))
        coverage_percentage = round((reviews_with_any_aspect / max(1, total_reviews)) * 100, 2)

        return {
            "aspects": finalized_aspects,
            "aspects_detected": len(finalized_aspects),
            "coverage_percentage": coverage_percentage,
            "average_confidence": round(avg_confidence, 3),
            "positive_aspects": positive_aspects,
            "negative_aspects": negative_aspects,
            "neutral_aspects": neutral_aspects,
            "extraction_method": (
                "tfidf_phrase_mining + canonical_aspect_mapping + "
                "sentence_level_transformer_sentiment"
            ),
        }

    def _compute_aspect_confidence(
        self,
        mentions: int,
        total_reviews: int,
        avg_signed: float,
        distribution: Dict[str, float],
        avg_model_confidence: float,
    ) -> float:
        dominant_distribution = max(distribution.values()) / 100.0
        polarity_strength = min(1.0, abs(avg_signed))
        coverage = mentions / max(1, total_reviews)
        coverage_strength = min(1.0, coverage * 2.5)
        model_conf = min(1.0, max(0.0, avg_model_confidence))

        confidence = (
            (0.25 * dominant_distribution)
            + (0.25 * polarity_strength)
            + (0.25 * coverage_strength)
            + (0.25 * model_conf)
        )
        return min(0.99, max(0.05, confidence))

    def _compute_aspect_sentiment_score(
        self,
        sentiment: str,
        distribution: Dict[str, float],
        avg_signed: float,
    ) -> float:
        pos = distribution.get("positive", 0.0) / 100.0
        neg = distribution.get("negative", 0.0) / 100.0
        neu = distribution.get("neutral", 0.0) / 100.0

        if sentiment == "positive":
            return max(0.0, min(1.0, (0.65 * pos) + (0.35 * max(0.0, avg_signed))))
        if sentiment == "negative":
            return max(0.0, min(1.0, (0.65 * neg) + (0.35 * max(0.0, -avg_signed))))

        neutral_balance = 1.0 - min(1.0, abs(avg_signed))
        return max(0.0, min(1.0, (0.6 * neu) + (0.4 * neutral_balance)))

    def _label_from_signed_score(self, avg_signed: float, distribution: Dict[str, float]) -> str:
        if avg_signed >= 0.12 and distribution.get("positive", 0.0) >= distribution.get("negative", 0.0):
            return "positive"
        if avg_signed <= -0.12 and distribution.get("negative", 0.0) >= distribution.get("positive", 0.0):
            return "negative"
        return "neutral"

    def _signed_sentiment_score(self, label: str, score: float) -> float:
        if label == "positive":
            return score
        if label == "negative":
            return -score
        return 0.0

    def _normalize_sentiment_label(self, label: Any) -> str:
        raw = str(label or "").strip().lower()
        if raw in {"positive", "pos"}:
            return "positive"
        if raw in {"negative", "neg"}:
            return "negative"
        return "neutral"

    def _is_valid_candidate(self, phrase: str) -> bool:
        if not phrase:
            return False

        tokens = phrase.split()
        if len(tokens) > 3:
            return False
        if any(token in self.GENERIC_CANDIDATE_FILTER for token in tokens):
            return False
        if all(token in self.STOPWORDS for token in tokens):
            return False
        if any(len(token) <= 2 for token in tokens if token not in {"vfx", "fx"}):
            return False
        if any(any(ch.isdigit() for ch in token) for token in tokens):
            return False
        if len(tokens) == 1 and tokens[0] in self.STOPWORDS:
            return False
        return True

    def _extract_keywords_from_text(self, text: str, limit: int = 8) -> List[str]:
        words = [word for word in self._tokenize(text) if word not in self.STOPWORDS and len(word) > 3]
        if not words:
            return []
        return [word for word, _ in Counter(words).most_common(limit)]

    def _split_sentences(self, text: str) -> List[str]:
        text = self._normalize_whitespace(text)
        if not text:
            return []
        chunks = re.split(r"(?<=[.!?])\s+", text)
        return [chunk.strip() for chunk in chunks if chunk and chunk.strip()]

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[a-zA-Z']+", (text or "").lower())

    def _normalize_whitespace(self, text: str) -> str:
        return re.sub(r"\s+", " ", text or "").strip()

    def _humanize_aspect(self, aspect_key: str) -> str:
        return " ".join(part.capitalize() for part in aspect_key.split("_"))

    def _bounded_float(self, value: Any, default: float = 0.5) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return default
        return max(0.0, min(1.0, numeric))
