import logging
import re
from collections import Counter
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Handles sentiment and emotion analysis with ML models and safe fallbacks."""

    POSITIVE_WORDS = {
        "amazing", "awesome", "best", "brilliant", "enjoyed", "excellent",
        "fantastic", "fun", "good", "great", "incredible", "love", "loved",
        "masterpiece", "perfect", "powerful", "recommended", "solid", "stunning",
        "superb", "wonderful",
    }
    NEGATIVE_WORDS = {
        "awful", "bad", "boring", "confusing", "disappointed", "disappointing",
        "dull", "forgettable", "hate", "hated", "mess", "poor", "skip", "slow",
        "terrible", "underdeveloped", "unwatchable", "waste", "weak", "worst",
    }
    EMOTION_KEYWORDS = {
        "joy": {"happy", "joy", "fun", "love", "loved", "delight", "amazing", "great"},
        "sadness": {"sad", "heartbreaking", "tragic", "depressing", "tear", "cry"},
        "anger": {"angry", "annoying", "frustrating", "hate", "hated", "terrible"},
        "fear": {"scary", "fear", "tense", "anxious", "horror", "frightening"},
        "surprise": {"surprising", "unexpected", "twist", "shocking", "wow"},
        "neutral": {"okay", "average", "fine", "decent", "normal"},
    }
    STOPWORDS = {
        "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from", "had",
        "has", "have", "he", "her", "his", "i", "in", "is", "it", "its", "me", "my",
        "of", "on", "or", "our", "she", "that", "the", "their", "them", "they", "this",
        "to", "was", "we", "were", "with", "you", "your",
    }

    def __init__(self):
        self.sentiment_pipe = None
        self.emotion_pipe = None
        self.explainer = None
        self.ml_enabled = False

        try:
            import torch
            from lime.lime_text import LimeTextExplainer
            from transformers import pipeline

            self.sentiment_pipe = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=0 if torch.cuda.is_available() else -1,
            )
            self.emotion_pipe = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                device=0 if torch.cuda.is_available() else -1,
                top_k=None,
            )
            self.explainer = LimeTextExplainer(class_names=["Negative", "Positive"])
            self.ml_enabled = True
            logger.info("Sentiment analyzer models loaded successfully")
        except Exception as exc:
            logger.warning(
                "ML models unavailable (%s). Falling back to lightweight heuristics.",
                exc,
            )

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[a-zA-Z']+", text.lower())

    def _predict_sentiment_fallback(self, text: str) -> Dict[str, Any]:
        tokens = self._tokenize(text)
        if not tokens:
            return {"label": "Neutral", "score": 0.5}

        positive_hits = sum(token in self.POSITIVE_WORDS for token in tokens)
        negative_hits = sum(token in self.NEGATIVE_WORDS for token in tokens)

        if positive_hits == negative_hits:
            return {"label": "Neutral", "score": 0.5}

        label = "Positive" if positive_hits > negative_hits else "Negative"
        margin = abs(positive_hits - negative_hits)
        confidence = 0.5 + min(0.49, margin / max(3, len(tokens)))
        return {"label": label, "score": round(confidence, 3)}

    def _predict_sentiment_from_author_rating(self, author_rating: Any) -> Dict[str, Any]:
        """Use explicit IMDb user star rating (1-10) when available."""
        try:
            rating = int(author_rating)
        except (TypeError, ValueError):
            return {}

        if rating < 1 or rating > 10:
            return {}

        if rating >= 7:
            confidence = min(0.99, 0.6 + ((rating - 6) * 0.1))
            return {"label": "Positive", "score": round(confidence, 3)}
        if rating <= 4:
            confidence = min(0.99, 0.6 + ((5 - rating) * 0.1))
            return {"label": "Negative", "score": round(confidence, 3)}

        return {"label": "Neutral", "score": 0.55}

    def predict_sentiment(self, text: str, author_rating: Any = None) -> Dict[str, Any]:
        text = (text or "")[:512]

        rating_based_sentiment = self._predict_sentiment_from_author_rating(author_rating)
        if rating_based_sentiment:
            return rating_based_sentiment

        if self.ml_enabled and self.sentiment_pipe is not None:
            try:
                result = self.sentiment_pipe(text)[0]
                return {
                    "label": "Positive" if result["label"] == "POSITIVE" else "Negative",
                    "score": round(float(result["score"]), 3),
                }
            except Exception as exc:
                logger.error("Error predicting sentiment with model: %s", exc)

        return self._predict_sentiment_fallback(text)

    def _predict_emotions_fallback(self, text: str) -> Dict[str, float]:
        tokens = self._tokenize(text)
        scores = {emotion: 0.0 for emotion in self.EMOTION_KEYWORDS}

        for token in tokens:
            for emotion, keywords in self.EMOTION_KEYWORDS.items():
                if token in keywords:
                    scores[emotion] += 1.0

        total = sum(scores.values())
        if total == 0:
            scores = {emotion: 0.0 for emotion in self.EMOTION_KEYWORDS}
            scores["neutral"] = 1.0
            return scores

        return {emotion: round(value / total, 3) for emotion, value in scores.items()}

    def predict_emotions(self, text: str) -> Dict[str, float]:
        text = (text or "")[:512]

        if self.ml_enabled and self.emotion_pipe is not None:
            try:
                results = self.emotion_pipe(text)[0]
                emotions = {}
                for result in results:
                    emotion = result["label"].lower()
                    emotions[emotion] = round(float(result["score"]), 3)
                return emotions
            except Exception as exc:
                logger.error("Error predicting emotions with model: %s", exc)

        return self._predict_emotions_fallback(text)

    def _get_fallback_keywords(self, text: str) -> List[str]:
        tokens = [
            token for token in self._tokenize(text)
            if len(token) > 3 and token not in self.STOPWORDS
        ]
        if not tokens:
            return ["movie", "review"]
        return [word for word, _ in Counter(tokens).most_common(5)]

    def get_important_words(self, text: str) -> List[str]:
        text = (text or "")[:512]

        if self.ml_enabled and self.explainer is not None and self.sentiment_pipe is not None:
            try:
                import numpy as np

                def predict_fn(texts):
                    results = []
                    for sample in texts:
                        pred = self.sentiment_pipe(sample)[0]
                        pos_score = pred["score"] if pred["label"] == "POSITIVE" else 1 - pred["score"]
                        neg_score = 1 - pos_score
                        results.append([neg_score, pos_score])
                    return np.array(results)

                exp = self.explainer.explain_instance(
                    text_instance=text,
                    classifier_fn=predict_fn,
                    num_features=10,
                )
                important_words = [word for word, weight in exp.as_list() if weight > 0]
                if important_words:
                    return important_words[:5]
            except Exception as exc:
                logger.error("Error extracting important words with LIME: %s", exc)

        return self._get_fallback_keywords(text)

    def batch_analyze(self, texts: List[str]) -> List[Dict[str, Any]]:
        results = []
        for text in texts:
            sentiment = self.predict_sentiment(text)
            emotions = self.predict_emotions(text)
            words = self.get_important_words(text)
            results.append({
                "text": text,
                "sentiment": sentiment,
                "emotions": emotions,
                "important_words": words,
            })
        return results
