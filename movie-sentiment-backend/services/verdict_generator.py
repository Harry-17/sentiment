import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class VerdictGenerator:
    """Generates movie verdicts from aggregate sentiment and emotion signals."""

    def generate_verdict(
        self,
        overall_sentiment: str,
        sentiment_percentages: Dict[str, float],
        emotion_scores: Dict[str, float],
        keywords: List[str],
    ) -> Tuple[str, str]:
        """
        Generate a verdict about the movie.

        Returns:
            Tuple of (verdict, explanation).
        """
        try:
            positive_pct = sentiment_percentages.get("positive", 0)
            negative_pct = sentiment_percentages.get("negative", 0)

            if positive_pct >= 70:
                verdict = "Highly Recommended"
                explanation = self._generate_positive_explanation(
                    positive_pct, emotion_scores, keywords
                )
            elif positive_pct >= 55:
                verdict = "Recommended"
                explanation = self._generate_mixed_positive_explanation(
                    positive_pct, negative_pct, emotion_scores, keywords
                )
            elif positive_pct > negative_pct:
                verdict = "Mixed Reviews"
                explanation = self._generate_mixed_explanation(
                    positive_pct, negative_pct, emotion_scores, keywords
                )
            elif negative_pct > positive_pct:
                verdict = "Not Recommended"
                explanation = self._generate_negative_explanation(
                    negative_pct, emotion_scores, keywords
                )
            else:
                verdict = "Neutral Reviews"
                explanation = "Reviews are split between positive and negative opinions."

            return verdict, explanation
        except Exception as exc:
            logger.error("Error generating verdict: %s", exc)
            return "Check Reviews", "Unable to generate verdict. Please check individual reviews."

    def _generate_positive_explanation(
        self,
        positive_pct: float,
        emotion_scores: Dict[str, float],
        keywords: List[str],
    ) -> str:
        joy_score = emotion_scores.get("joy", 0)
        keyword_str = ", ".join(keywords[:3]) if keywords else "its quality"

        base = f"{positive_pct:.0f}% of users loved this movie."
        if joy_score > 0.4:
            base += " Users particularly enjoyed the joy and entertainment value."
        base += f" Common praises include: {keyword_str}. This is a must-watch!"
        return base

    def _generate_mixed_positive_explanation(
        self,
        positive_pct: float,
        negative_pct: float,
        emotion_scores: Dict[str, float],
        keywords: List[str],
    ) -> str:
        keyword_str = ", ".join(keywords[:3]) if keywords else "its quality"
        return (
            f"{positive_pct:.0f}% of viewers enjoyed this movie, while {negative_pct:.0f}% "
            f"had concerns. Most appreciated: {keyword_str}. "
            f"It's a solid choice for most audiences."
        )

    def _generate_mixed_explanation(
        self,
        positive_pct: float,
        negative_pct: float,
        emotion_scores: Dict[str, float],
        keywords: List[str],
    ) -> str:
        keyword_str = ", ".join(keywords[:3]) if keywords else "the film"
        return (
            f"Opinion is divided on this movie. {positive_pct:.0f}% liked it, "
            f"while {negative_pct:.0f}% didn't. Opinions differ on {keyword_str}. "
            f"Your enjoyment may depend on your personal preferences."
        )

    def _generate_negative_explanation(
        self,
        negative_pct: float,
        emotion_scores: Dict[str, float],
        keywords: List[str],
    ) -> str:
        anger_score = emotion_scores.get("anger", 0)
        keyword_str = ", ".join(keywords[:3]) if keywords else "its execution"

        base = f"{negative_pct:.0f}% of viewers were disappointed with this movie."
        if anger_score > 0.3:
            base += f" Common complaints center around frustration with {keyword_str}."
        else:
            base += f" Major criticisms include issues with {keyword_str}."
        base += " This one might be worth skipping."
        return base

    def get_emotion_insight(self, emotion_scores: Dict[str, float]) -> str:
        if not emotion_scores:
            return "Emotions could not be determined."

        sorted_emotions = sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)
        top_emotion = sorted_emotions[0][0].capitalize()
        score = sorted_emotions[0][1]

        if score > 0.4:
            return f"The dominant emotion is {top_emotion}."
        if len(sorted_emotions) > 1:
            second_emotion = sorted_emotions[1][0].capitalize()
            return f"Reviews contain a mix of {top_emotion} and {second_emotion}."
        return f"Viewers experience various emotions, with {top_emotion} being prominent."
