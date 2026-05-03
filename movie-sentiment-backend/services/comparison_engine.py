import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


class ComparisonEngine:
    """Reusable comparison engine across movie, product, and YouTube analyzers."""

    METRIC_CONFIGS: Dict[str, List[Dict[str, Any]]] = {
        "movie": [
            {
                "key": "imdb_rating",
                "label": "IMDb Rating",
                "unit": "/10",
                "higher_is_better": True,
                "normalize_min": 0.0,
                "normalize_max": 10.0,
                "weight": 0.35,
                "description": "Higher external rating indicates stronger broad audience approval.",
            },
            {
                "key": "positive_sentiment",
                "label": "Positive Sentiment",
                "unit": "%",
                "higher_is_better": True,
                "normalize_min": 0.0,
                "normalize_max": 100.0,
                "weight": 0.25,
                "description": "Share of reviews classified as positive.",
            },
            {
                "key": "emotional_resonance",
                "label": "Emotional Resonance",
                "unit": "/100",
                "higher_is_better": True,
                "normalize_min": 0.0,
                "normalize_max": 100.0,
                "weight": 0.20,
                "description": "Net emotional signal from positive vs negative emotions.",
            },
            {
                "key": "aspect_confidence",
                "label": "Aspect Confidence",
                "unit": "%",
                "higher_is_better": True,
                "normalize_min": 0.0,
                "normalize_max": 100.0,
                "weight": 0.20,
                "description": "Confidence of extracted aspect-level sentiment patterns.",
            },
        ],
        "product": [
            {
                "key": "rating",
                "label": "Store Rating",
                "unit": "/5",
                "higher_is_better": True,
                "normalize_min": 0.0,
                "normalize_max": 5.0,
                "weight": 0.25,
                "description": "Marketplace product rating from listing/store data.",
            },
            {
                "key": "buy_signal_score",
                "label": "Buy Signal",
                "unit": "/100",
                "higher_is_better": True,
                "normalize_min": 0.0,
                "normalize_max": 100.0,
                "weight": 0.25,
                "description": "Composite buying momentum score from rating, review depth, and sentiment.",
            },
            {
                "key": "real_verdict_score",
                "label": "Real Verdict",
                "unit": "/10",
                "higher_is_better": True,
                "normalize_min": 1.0,
                "normalize_max": 10.0,
                "weight": 0.20,
                "description": "Final quality score combining sentiment, social proof, and market depth.",
            },
            {
                "key": "positive_sentiment",
                "label": "Positive Sentiment",
                "unit": "%",
                "higher_is_better": True,
                "normalize_min": 0.0,
                "normalize_max": 100.0,
                "weight": 0.15,
                "description": "Share of positive review snippets.",
            },
            {
                "key": "negative_sentiment",
                "label": "Negative Sentiment",
                "unit": "%",
                "higher_is_better": False,
                "normalize_min": 0.0,
                "normalize_max": 100.0,
                "weight": 0.15,
                "description": "Lower negative sentiment indicates fewer critical comments.",
            },
        ],
        "youtube": [
            {
                "key": "rating",
                "label": "Audience Rating",
                "unit": "/10",
                "higher_is_better": True,
                "normalize_min": 1.0,
                "normalize_max": 10.0,
                "weight": 0.25,
                "description": "Composite rating from sentiment + engagement signals.",
            },
            {
                "key": "positive_sentiment",
                "label": "Positive Sentiment",
                "unit": "%",
                "higher_is_better": True,
                "normalize_min": 0.0,
                "normalize_max": 100.0,
                "weight": 0.20,
                "description": "Share of positive audience comments.",
            },
            {
                "key": "engagement_rate",
                "label": "Engagement",
                "unit": "%",
                "higher_is_better": True,
                "normalize_min": 0.0,
                "normalize_max": 20.0,
                "weight": 0.20,
                "description": "Higher engagement suggests stronger audience interaction.",
            },
            {
                "key": "toxicity_percentage",
                "label": "Toxicity",
                "unit": "%",
                "higher_is_better": False,
                "normalize_min": 0.0,
                "normalize_max": 100.0,
                "weight": 0.15,
                "description": "Lower toxicity indicates healthier audience discussion.",
            },
            {
                "key": "spam_percentage",
                "label": "Spam",
                "unit": "%",
                "higher_is_better": False,
                "normalize_min": 0.0,
                "normalize_max": 100.0,
                "weight": 0.10,
                "description": "Lower spam indicates cleaner, more authentic conversation.",
            },
            {
                "key": "like_ratio",
                "label": "Like Ratio",
                "unit": "%",
                "higher_is_better": True,
                "normalize_min": 0.0,
                "normalize_max": 10.0,
                "weight": 0.10,
                "description": "Likes as a fraction of views.",
            },
        ],
    }

    SENTIMENT_KEYS = ("positive", "negative", "neutral")

    def compare(self, domain: str, left_entity: Dict[str, Any], right_entity: Dict[str, Any]) -> Dict[str, Any]:
        metric_cards = self._build_metric_cards(domain, left_entity, right_entity)
        left_metric_scores = {card["key"]: card["left_score"] for card in metric_cards}
        right_metric_scores = {card["key"]: card["right_score"] for card in metric_cards}

        left_overall, right_overall = self._weighted_overall_score(domain, metric_cards)
        overall_winner = self._pick_winner(left_overall, right_overall)
        score_delta = round(abs(left_overall - right_overall), 2)

        sentiment_chart = self._build_sentiment_chart(left_entity, right_entity)
        emotion_radar = self._build_emotion_radar(left_entity, right_entity)

        aspect_comparison = self._compare_aspects(
            left_entity.get("aspect_sentiment") or {},
            right_entity.get("aspect_sentiment") or {},
        )

        insights = self._generate_insights(
            domain=domain,
            left=left_entity,
            right=right_entity,
            metric_cards=metric_cards,
            overall_winner=overall_winner,
            score_delta=score_delta,
            aspect_comparison=aspect_comparison,
        )

        summary_cards = self._build_summary_cards(
            domain=domain,
            left=left_entity,
            right=right_entity,
            left_overall=left_overall,
            right_overall=right_overall,
            overall_winner=overall_winner,
            score_delta=score_delta,
            aspect_comparison=aspect_comparison,
        )

        winner_label = (
            left_entity.get("label")
            if overall_winner == "left"
            else right_entity.get("label")
            if overall_winner == "right"
            else "Tie"
        )

        return {
            "overall_scores": {
                "left": left_overall,
                "right": right_overall,
            },
            "overall_winner": overall_winner,
            "winner_label": winner_label,
            "score_delta": score_delta,
            "metric_cards": metric_cards,
            "sentiment_chart": sentiment_chart,
            "emotion_radar": emotion_radar,
            "aspect_table": aspect_comparison["aspect_table"],
            "shared_complaints": aspect_comparison["shared_complaints"],
            "shared_strengths": aspect_comparison["shared_strengths"],
            "unique_advantages": aspect_comparison["unique_advantages"],
            "ai_insights": insights,
            "summary_cards": summary_cards,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "explainability": {
                "normalization": "All metrics are normalized to 0-100 before weighted scoring.",
                "weights": {
                    config["key"]: config["weight"]
                    for config in self.METRIC_CONFIGS.get(domain, [])
                },
                "winner_rule": (
                    "Overall winner is selected by weighted normalized score. "
                    "Per-metric winners are determined by direction-aware comparison."
                ),
            },
            "left_metric_scores": left_metric_scores,
            "right_metric_scores": right_metric_scores,
        }

    def _build_metric_cards(
        self,
        domain: str,
        left_entity: Dict[str, Any],
        right_entity: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        cards: List[Dict[str, Any]] = []
        for config in self.METRIC_CONFIGS.get(domain, []):
            key = config["key"]
            left_value = self._to_float((left_entity.get("metrics") or {}).get(key))
            right_value = self._to_float((right_entity.get("metrics") or {}).get(key))

            left_score = self._normalize_score(
                left_value,
                min_value=config["normalize_min"],
                max_value=config["normalize_max"],
                higher_is_better=config["higher_is_better"],
            )
            right_score = self._normalize_score(
                right_value,
                min_value=config["normalize_min"],
                max_value=config["normalize_max"],
                higher_is_better=config["higher_is_better"],
            )

            winner = self._pick_winner(left_score, right_score)

            cards.append(
                {
                    "key": key,
                    "label": config["label"],
                    "unit": config["unit"],
                    "higher_is_better": config["higher_is_better"],
                    "left_value": round(left_value, 3),
                    "right_value": round(right_value, 3),
                    "left_score": round(left_score, 2),
                    "right_score": round(right_score, 2),
                    "winner": winner,
                    "delta": round(abs(left_value - right_value), 3),
                    "description": config["description"],
                }
            )

        return cards

    def _weighted_overall_score(
        self,
        domain: str,
        metric_cards: List[Dict[str, Any]],
    ) -> Tuple[float, float]:
        weight_map = {
            entry["key"]: float(entry.get("weight", 0.0))
            for entry in self.METRIC_CONFIGS.get(domain, [])
        }
        left_weighted_sum = 0.0
        right_weighted_sum = 0.0
        weight_total = 0.0

        for card in metric_cards:
            weight = weight_map.get(card["key"], 0.0)
            left_weighted_sum += card["left_score"] * weight
            right_weighted_sum += card["right_score"] * weight
            weight_total += weight

        if weight_total <= 0:
            return 0.0, 0.0

        return (
            round(left_weighted_sum / weight_total, 2),
            round(right_weighted_sum / weight_total, 2),
        )

    def _build_sentiment_chart(
        self,
        left_entity: Dict[str, Any],
        right_entity: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        left_sent = left_entity.get("sentiment_percentages") or {}
        right_sent = right_entity.get("sentiment_percentages") or {}

        return [
            {
                "label": key.capitalize(),
                "left": round(self._to_float(left_sent.get(key)), 2),
                "right": round(self._to_float(right_sent.get(key)), 2),
            }
            for key in self.SENTIMENT_KEYS
        ]

    def _build_emotion_radar(
        self,
        left_entity: Dict[str, Any],
        right_entity: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        left_emo = left_entity.get("emotion_scores") or {}
        right_emo = right_entity.get("emotion_scores") or {}
        all_keys = sorted(set(left_emo.keys()).union(right_emo.keys()))
        radar = []
        for key in all_keys:
            radar.append(
                {
                    "emotion": key.capitalize(),
                    "left": round(self._to_float(left_emo.get(key)) * 100, 2),
                    "right": round(self._to_float(right_emo.get(key)) * 100, 2),
                }
            )
        return radar

    def _compare_aspects(
        self,
        left_aspect_summary: Dict[str, Any],
        right_aspect_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        left_rows = left_aspect_summary.get("aspects") or []
        right_rows = right_aspect_summary.get("aspects") or []

        left_map = {str(row.get("aspect", "")).lower(): row for row in left_rows}
        right_map = {str(row.get("aspect", "")).lower(): row for row in right_rows}

        all_aspects = sorted(
            set(left_map.keys()).union(right_map.keys()),
            key=lambda key: (
                self._to_float((left_map.get(key) or {}).get("mentions"))
                + self._to_float((right_map.get(key) or {}).get("mentions"))
            ),
            reverse=True,
        )

        aspect_table = []
        shared_complaints = []
        shared_strengths = []
        left_unique_advantages = []
        right_unique_advantages = []

        for aspect_key in all_aspects[:18]:
            left_row = left_map.get(aspect_key) or {}
            right_row = right_map.get(aspect_key) or {}
            left_sent = str(left_row.get("sentiment") or "neutral").lower()
            right_sent = str(right_row.get("sentiment") or "neutral").lower()

            row_winner = self._pick_aspect_winner(left_sent, right_sent, left_row, right_row)
            aspect_label = (
                left_row.get("aspect")
                or right_row.get("aspect")
                or aspect_key.title()
            )

            aspect_table.append(
                {
                    "aspect": aspect_label,
                    "left_sentiment": left_sent,
                    "right_sentiment": right_sent,
                    "left_mentions": int(self._to_float(left_row.get("mentions"))),
                    "right_mentions": int(self._to_float(right_row.get("mentions"))),
                    "left_confidence": round(self._to_float(left_row.get("confidence")), 3),
                    "right_confidence": round(self._to_float(right_row.get("confidence")), 3),
                    "winner": row_winner,
                }
            )

            if left_sent == "negative" and right_sent == "negative":
                shared_complaints.append(aspect_label)
            if left_sent == "positive" and right_sent == "positive":
                shared_strengths.append(aspect_label)

            if left_sent == "positive" and right_sent != "positive":
                left_unique_advantages.append(aspect_label)
            if right_sent == "positive" and left_sent != "positive":
                right_unique_advantages.append(aspect_label)

        return {
            "aspect_table": aspect_table,
            "shared_complaints": shared_complaints[:8],
            "shared_strengths": shared_strengths[:8],
            "unique_advantages": {
                "left": left_unique_advantages[:8],
                "right": right_unique_advantages[:8],
            },
        }

    def _pick_aspect_winner(
        self,
        left_sentiment: str,
        right_sentiment: str,
        left_row: Dict[str, Any],
        right_row: Dict[str, Any],
    ) -> str:
        rank = {"positive": 2, "neutral": 1, "negative": 0}
        left_rank = rank.get(left_sentiment, 1)
        right_rank = rank.get(right_sentiment, 1)

        if left_rank > right_rank:
            return "left"
        if right_rank > left_rank:
            return "right"

        left_strength = self._to_float(left_row.get("confidence")) * max(1.0, self._to_float(left_row.get("mentions")))
        right_strength = self._to_float(right_row.get("confidence")) * max(1.0, self._to_float(right_row.get("mentions")))
        return self._pick_winner(left_strength, right_strength)

    def _generate_insights(
        self,
        domain: str,
        left: Dict[str, Any],
        right: Dict[str, Any],
        metric_cards: List[Dict[str, Any]],
        overall_winner: str,
        score_delta: float,
        aspect_comparison: Dict[str, Any],
    ) -> List[str]:
        insights: List[str] = []
        left_label = left.get("label", "Left option")
        right_label = right.get("label", "Right option")

        if overall_winner == "left":
            insights.append(
                f"{left_label} leads overall by {score_delta:.1f} normalized points across weighted metrics."
            )
        elif overall_winner == "right":
            insights.append(
                f"{right_label} leads overall by {score_delta:.1f} normalized points across weighted metrics."
            )
        else:
            insights.append(
                "Both options are nearly tied overall, with trade-offs across different metrics."
            )

        win_counts = {"left": 0, "right": 0, "tie": 0}
        for card in metric_cards:
            winner = card.get("winner", "tie")
            win_counts[winner] = win_counts.get(winner, 0) + 1

        insights.append(
            f"Metric wins -> {left_label}: {win_counts.get('left', 0)}, "
            f"{right_label}: {win_counts.get('right', 0)}, ties: {win_counts.get('tie', 0)}."
        )

        shared_complaints = aspect_comparison.get("shared_complaints") or []
        if shared_complaints:
            insights.append(
                "Shared complaints suggest both options may need improvement in: "
                + ", ".join(shared_complaints[:3])
                + "."
            )

        unique_advantages = aspect_comparison.get("unique_advantages") or {}
        left_unique = unique_advantages.get("left") or []
        right_unique = unique_advantages.get("right") or []
        if left_unique:
            insights.append(
                f"Unique strengths for {left_label}: " + ", ".join(left_unique[:3]) + "."
            )
        if right_unique:
            insights.append(
                f"Unique strengths for {right_label}: " + ", ".join(right_unique[:3]) + "."
            )

        if domain == "youtube":
            left_toxic = self._to_float((left.get("metrics") or {}).get("toxicity_percentage"))
            right_toxic = self._to_float((right.get("metrics") or {}).get("toxicity_percentage"))
            better_clean = left_label if left_toxic < right_toxic else right_label
            if abs(left_toxic - right_toxic) > 2:
                insights.append(
                    f"{better_clean} has cleaner audience conversations based on lower toxicity."
                )

        return insights[:6]

    def _build_summary_cards(
        self,
        domain: str,
        left: Dict[str, Any],
        right: Dict[str, Any],
        left_overall: float,
        right_overall: float,
        overall_winner: str,
        score_delta: float,
        aspect_comparison: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        left_label = left.get("label", "Left option")
        right_label = right.get("label", "Right option")
        winner_label = (
            left_label if overall_winner == "left"
            else right_label if overall_winner == "right"
            else "Tie"
        )

        shared_complaints = aspect_comparison.get("shared_complaints") or []
        shared_strengths = aspect_comparison.get("shared_strengths") or []

        return [
            {
                "title": "Overall Winner",
                "value": winner_label,
                "description": (
                    f"Score delta: {score_delta:.1f} points."
                    if overall_winner != "tie"
                    else "Both options are close on weighted scoring."
                ),
            },
            {
                "title": f"{left_label} Score",
                "value": f"{left_overall:.1f}/100",
                "description": "Weighted normalized score.",
            },
            {
                "title": f"{right_label} Score",
                "value": f"{right_overall:.1f}/100",
                "description": "Weighted normalized score.",
            },
            {
                "title": "Shared Strengths",
                "value": str(len(shared_strengths)),
                "description": ", ".join(shared_strengths[:3]) if shared_strengths else "No strong overlap detected.",
            },
            {
                "title": "Shared Complaints",
                "value": str(len(shared_complaints)),
                "description": ", ".join(shared_complaints[:3]) if shared_complaints else "No major shared complaints detected.",
            },
        ]

    def build_entity_payload(
        self,
        label: str,
        source_type: str,
        sentiment_percentages: Dict[str, Any],
        emotion_scores: Dict[str, Any],
        aspect_sentiment: Dict[str, Any],
        metrics: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "label": label,
            "source_type": source_type,
            "sentiment_percentages": {
                key: round(self._to_float((sentiment_percentages or {}).get(key)), 2)
                for key in self.SENTIMENT_KEYS
            },
            "emotion_scores": {
                key: round(self._to_float(value), 3)
                for key, value in (emotion_scores or {}).items()
            },
            "aspect_sentiment": aspect_sentiment or {},
            "metrics": {
                key: round(self._to_float(value), 4)
                for key, value in (metrics or {}).items()
            },
            "metadata": metadata or {},
        }

    def _normalize_score(
        self,
        value: float,
        min_value: float,
        max_value: float,
        higher_is_better: bool = True,
    ) -> float:
        if max_value <= min_value:
            return 0.0
        normalized = ((value - min_value) / (max_value - min_value)) * 100.0
        normalized = max(0.0, min(100.0, normalized))
        if not higher_is_better:
            normalized = 100.0 - normalized
        return normalized

    def _pick_winner(self, left_value: float, right_value: float, tolerance: float = 1e-6) -> str:
        if abs(left_value - right_value) <= tolerance:
            return "tie"
        return "left" if left_value > right_value else "right"

    def _to_float(self, value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if value is None:
            return 0.0
        text = str(value).strip()
        if not text:
            return 0.0
        try:
            return float(text)
        except (TypeError, ValueError):
            return 0.0

    def derive_emotional_resonance(self, emotion_scores: Dict[str, Any]) -> float:
        joy = self._to_float((emotion_scores or {}).get("joy"))
        surprise = self._to_float((emotion_scores or {}).get("surprise"))
        sadness = self._to_float((emotion_scores or {}).get("sadness"))
        anger = self._to_float((emotion_scores or {}).get("anger"))
        fear = self._to_float((emotion_scores or {}).get("fear"))

        positive_signal = joy + (0.75 * surprise)
        negative_signal = anger + (0.8 * sadness) + (0.9 * fear)
        raw = positive_signal - negative_signal

        # Map approximately from [-1, 1] to [0, 100].
        scaled = (max(-1.0, min(1.0, raw)) + 1.0) * 50.0
        return round(max(0.0, min(100.0, scaled)), 2)

    def aspect_confidence_percent(self, aspect_summary: Dict[str, Any]) -> float:
        return round(self._to_float((aspect_summary or {}).get("average_confidence")) * 100.0, 2)

    def log_volume_score(self, value: float, max_anchor: float = 1_000_000.0) -> float:
        safe = max(0.0, self._to_float(value))
        if safe == 0.0:
            return 0.0
        score = (math.log10(safe + 1) / math.log10(max_anchor + 1)) * 100.0
        return round(max(0.0, min(100.0, score)), 2)
