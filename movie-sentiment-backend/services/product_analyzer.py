import logging
import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)


class ProductAnalyzer:
    """Fetch and analyze real marketplace product signals using SerpAPI."""

    API_BASE_URL = "https://serpapi.com/search.json"
    REQUEST_TIMEOUT_SECONDS = 25
    MAX_COMMENTS = 120
    SUPPORTED_MARKETPLACES = {"any", "amazon", "flipkart"}

    def __init__(self, api_key: str):
        self.api_key = (api_key or "").strip()

    def analyze_product(
        self,
        product_query: str,
        sentiment_analyzer: Any,
        marketplace: str = "any",
        max_comments: int = 60,
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError(
                "Product data API key is not configured. Set SERPAPI_KEY in backend environment."
            )

        query = (product_query or "").strip()
        if not query:
            raise ValueError("Please provide a product name or model.")

        marketplace_filter = self._normalize_marketplace(marketplace)
        comment_limit = max(15, min(self.MAX_COMMENTS, int(max_comments or 60)))

        search_payload = self._request_json(
            params={
                "engine": "google_shopping",
                "q": query,
                "gl": "in",
                "hl": "en",
                "num": 20,
                "api_key": self.api_key,
            }
        )
        shopping_results = search_payload.get("shopping_results") or []
        if not shopping_results:
            raise ValueError("No product listings found. Try a more specific product query.")

        selected_listing = self._select_best_listing(shopping_results, marketplace_filter)
        immersive_payload = self._fetch_immersive_product(selected_listing)
        product_results = immersive_payload.get("product_results") or {}

        title = (
            str(product_results.get("title") or selected_listing.get("title") or query).strip()
            or query
        )
        thumbnail = self._resolve_thumbnail(product_results, selected_listing)

        stores = product_results.get("stores") or []
        chosen_store = self._pick_store(stores, marketplace_filter, selected_listing)

        rating = self._resolve_rating(product_results, selected_listing, chosen_store)
        review_count = self._resolve_review_count(product_results, selected_listing, chosen_store)
        offers_count = len(stores) if stores else (1 if chosen_store.get("name") else 0)

        review_snippets = self._extract_review_snippets(
            product_results=product_results,
            selected_listing=selected_listing,
            max_comments=comment_limit,
        )
        if not review_snippets:
            raise ValueError(
                "No review comments were returned for this product. Try another product or marketplace."
            )

        analyzed_reviews, sentiment_percentages, emotion_scores, top_keywords = self._analyze_reviews(
            review_snippets,
            sentiment_analyzer,
        )
        if not analyzed_reviews:
            raise ValueError("Comments were fetched, but none were valid for analysis.")

        overall_sentiment = max(
            sentiment_percentages.items(),
            key=lambda item: item[1],
        )[0]

        buy_signal_score = self._calculate_buy_signal_score(
            rating=rating,
            review_count=review_count,
            positive_pct=sentiment_percentages.get("positive", 0.0),
        )
        real_verdict_score = self._calculate_real_verdict_score(
            rating=rating,
            positive_pct=sentiment_percentages.get("positive", 0.0),
            negative_pct=sentiment_percentages.get("negative", 0.0),
            review_count=review_count,
            offers_count=offers_count,
        )
        verdict, verdict_explanation = self._generate_verdict(
            real_verdict_score=real_verdict_score,
            rating=rating,
            review_count=review_count,
            overall_sentiment=overall_sentiment,
            positive_pct=sentiment_percentages.get("positive", 0.0),
            negative_pct=sentiment_percentages.get("negative", 0.0),
            buy_signal_score=buy_signal_score,
            marketplace_name=chosen_store.get("name") or selected_listing.get("source") or "Marketplace",
        )

        price = (
            chosen_store.get("price")
            or selected_listing.get("price")
            or product_results.get("price_range")
            or "Not available"
        )
        product_url = chosen_store.get("link") or selected_listing.get("product_link") or ""
        trusted_sources = self._collect_sources(stores, selected_listing)

        return {
            "source_type": "product",
            "product_title": title,
            "product_url": product_url,
            "thumbnail_url": thumbnail,
            "marketplace": marketplace_filter,
            "primary_store": chosen_store.get("name") or selected_listing.get("source") or "Unknown",
            "price": price,
            "rating": rating,
            "review_count": review_count,
            "offers_count": offers_count,
            "buy_signal_score": buy_signal_score,
            "real_verdict_score": real_verdict_score,
            "overall_sentiment": overall_sentiment,
            "sentiment_percentages": sentiment_percentages,
            "emotion_scores": emotion_scores,
            "top_keywords": top_keywords,
            "verdict": verdict,
            "verdict_explanation": verdict_explanation,
            "comments_analyzed": len(analyzed_reviews),
            "trusted_sources": trusted_sources,
            "reviews": analyzed_reviews[:50],
        }

    def _normalize_marketplace(self, marketplace: str) -> str:
        value = (marketplace or "any").strip().lower()
        return value if value in self.SUPPORTED_MARKETPLACES else "any"

    def _select_best_listing(self, listings: List[Dict[str, Any]], marketplace: str) -> Dict[str, Any]:
        def score(index: int, item: Dict[str, Any]) -> Tuple[int, float, int, int]:
            source = str(item.get("source") or "").lower()
            preferred_penalty = 0
            if marketplace != "any":
                preferred_penalty = 0 if marketplace in source else 1

            rating = self._to_float(item.get("rating"))
            reviews = self._to_int(item.get("reviews"))
            return (
                preferred_penalty,
                -rating,
                -reviews,
                index,
            )

        ranked = sorted(enumerate(listings), key=lambda pair: score(pair[0], pair[1]))
        return ranked[0][1] if ranked else listings[0]

    def _fetch_immersive_product(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        page_token = listing.get("immersive_product_page_token")
        if not page_token:
            return {}

        try:
            return self._request_json(
                params={
                    "engine": "google_immersive_product",
                    "page_token": page_token,
                    "more_stores": "true",
                    "gl": "in",
                    "hl": "en",
                    "api_key": self.api_key,
                }
            )
        except Exception as exc:
            logger.warning("Unable to fetch immersive product details: %s", exc)
            return {}

    def _resolve_thumbnail(self, product_results: Dict[str, Any], listing: Dict[str, Any]) -> str:
        thumbs = product_results.get("thumbnails")
        if isinstance(thumbs, list) and thumbs:
            return str(thumbs[0])
        if isinstance(thumbs, str):
            return thumbs
        return str(listing.get("thumbnail") or "")

    def _pick_store(
        self,
        stores: List[Dict[str, Any]],
        marketplace: str,
        listing: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not stores:
            return {
                "name": listing.get("source"),
                "price": listing.get("price"),
                "link": listing.get("product_link"),
                "rating": listing.get("rating"),
                "reviews": listing.get("reviews"),
            }

        def rank(store: Dict[str, Any]) -> Tuple[int, float, int]:
            name = str(store.get("name") or "").lower()
            preferred_penalty = 0
            if marketplace != "any":
                preferred_penalty = 0 if marketplace in name else 1

            rating = self._to_float(store.get("rating"))
            reviews = self._to_int(store.get("reviews"))
            return preferred_penalty, -rating, -reviews

        return sorted(stores, key=rank)[0]

    def _resolve_rating(
        self,
        product_results: Dict[str, Any],
        listing: Dict[str, Any],
        store: Dict[str, Any],
    ) -> float:
        for candidate in [
            product_results.get("rating"),
            store.get("rating"),
            listing.get("rating"),
        ]:
            rating = self._to_float(candidate)
            if rating > 0:
                return round(min(5.0, rating), 2)

        derived_rating = self._derive_rating_from_review_text(product_results)
        return round(derived_rating, 2)

    def _resolve_review_count(
        self,
        product_results: Dict[str, Any],
        listing: Dict[str, Any],
        store: Dict[str, Any],
    ) -> int:
        for candidate in [
            product_results.get("reviews"),
            store.get("reviews"),
            listing.get("reviews"),
        ]:
            count = self._to_int(candidate)
            if count > 0:
                return count

        user_reviews = product_results.get("user_reviews") or []
        if isinstance(user_reviews, list):
            return len(user_reviews)
        return 0

    def _derive_rating_from_review_text(self, product_results: Dict[str, Any]) -> float:
        ratings = []
        for entry in (product_results.get("user_reviews") or []):
            if not isinstance(entry, dict):
                continue
            value = self._to_float(entry.get("rating"))
            if value > 0:
                ratings.append(value)

        if ratings:
            return max(1.0, min(5.0, sum(ratings) / len(ratings)))

        return 0.0

    def _extract_review_snippets(
        self,
        product_results: Dict[str, Any],
        selected_listing: Dict[str, Any],
        max_comments: int,
    ) -> List[Dict[str, Any]]:
        snippets: List[Dict[str, Any]] = []
        seen = set()

        def push(text: str, source: str, rating: Optional[float] = None) -> None:
            cleaned = self._clean_text(text)
            if len(cleaned) < 15:
                return
            key = cleaned.lower()
            if key in seen:
                return
            seen.add(key)
            snippets.append({"text": cleaned, "source": source, "rating": rating})

        user_reviews = product_results.get("user_reviews") or []
        if isinstance(user_reviews, list):
            for review in user_reviews:
                if not isinstance(review, dict):
                    continue
                text = review.get("text") or review.get("snippet") or review.get("title") or ""
                push(
                    text=str(text),
                    source=str(review.get("source") or "User Review"),
                    rating=self._to_float(review.get("rating")),
                )

        top_insights = (product_results.get("top_insights") or {}).get("items") or []
        if isinstance(top_insights, list):
            for insight in top_insights:
                if not isinstance(insight, dict):
                    continue
                push(
                    text=str(insight.get("snippet") or insight.get("key_point") or ""),
                    source=str(insight.get("source") or "Insight"),
                )
                for pro in insight.get("pros") or []:
                    push(text=str(pro), source=str(insight.get("source") or "Insight"))
                for con in insight.get("cons") or []:
                    push(text=str(con), source=str(insight.get("source") or "Insight"))

        listing_snippet = selected_listing.get("snippet")
        if listing_snippet:
            push(text=str(listing_snippet), source=str(selected_listing.get("source") or "Listing"))

        for extension in selected_listing.get("extensions") or []:
            push(text=str(extension), source=str(selected_listing.get("source") or "Listing"))

        return snippets[:max_comments]

    def _analyze_reviews(
        self,
        review_snippets: List[Dict[str, Any]],
        sentiment_analyzer: Any,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, float], Dict[str, float], List[str]]:
        analyzed_reviews: List[Dict[str, Any]] = []
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        emotion_totals: Dict[str, float] = {}
        all_keywords: List[str] = []

        for entry in review_snippets:
            text = str(entry.get("text") or "").strip()
            if not text:
                continue

            sentiment_result = sentiment_analyzer.predict_sentiment(
                text,
                author_rating=entry.get("rating"),
            )
            emotions = sentiment_analyzer.predict_emotions(text)
            important_words = sentiment_analyzer.get_important_words(text)

            sentiment_key = (sentiment_result.get("label") or "Neutral").lower()
            if sentiment_key not in sentiment_counts:
                sentiment_key = "neutral"
            sentiment_counts[sentiment_key] += 1

            for emotion, score in emotions.items():
                emotion_totals[emotion] = emotion_totals.get(emotion, 0.0) + float(score)
            all_keywords.extend(important_words)

            analyzed_reviews.append(
                {
                    "text": text,
                    "source": entry.get("source"),
                    "sentiment": sentiment_result.get("label", "Neutral"),
                    "sentiment_score": round(float(sentiment_result.get("score", 0.5)), 3),
                    "rating": float(entry.get("rating") or 0),
                    "emotions": emotions,
                    "important_words": important_words,
                }
            )

        total_reviews = len(analyzed_reviews)
        if total_reviews == 0:
            return [], {"positive": 0.0, "negative": 0.0, "neutral": 0.0}, {}, []

        sentiment_percentages = {
            key: round((count / total_reviews) * 100, 2)
            for key, count in sentiment_counts.items()
        }
        emotion_scores = {
            emotion: round(score / total_reviews, 3)
            for emotion, score in emotion_totals.items()
        }
        top_keywords = [word for word, _ in Counter(all_keywords).most_common(12)]

        return analyzed_reviews, sentiment_percentages, emotion_scores, top_keywords

    def _calculate_buy_signal_score(
        self,
        rating: float,
        review_count: int,
        positive_pct: float,
    ) -> float:
        rating_component = (max(0.0, min(5.0, rating)) / 5.0) * 45.0
        volume_component = min(1.0, math.log10(review_count + 1) / 4.5) * 30.0
        sentiment_component = (max(0.0, min(100.0, positive_pct)) / 100.0) * 25.0
        return round(min(100.0, rating_component + volume_component + sentiment_component), 2)

    def _calculate_real_verdict_score(
        self,
        rating: float,
        positive_pct: float,
        negative_pct: float,
        review_count: int,
        offers_count: int,
    ) -> float:
        rating_component = max(0.0, min(5.0, rating)) * 1.2  # max 6.0
        sentiment_balance = (positive_pct - negative_pct + 100.0) / 200.0
        sentiment_component = max(0.0, min(1.0, sentiment_balance)) * 2.5
        social_proof_component = min(1.0, math.log10(review_count + 1) / 4.0) * 1.0
        market_depth_component = min(0.5, offers_count / 20.0)

        score = rating_component + sentiment_component + social_proof_component + market_depth_component
        return round(max(1.0, min(10.0, score)), 1)

    def _generate_verdict(
        self,
        real_verdict_score: float,
        rating: float,
        review_count: int,
        overall_sentiment: str,
        positive_pct: float,
        negative_pct: float,
        buy_signal_score: float,
        marketplace_name: str,
    ) -> Tuple[str, str]:
        if real_verdict_score >= 8.5:
            verdict = "Strong Buy"
        elif real_verdict_score >= 7.0:
            verdict = "Good Option"
        elif real_verdict_score >= 5.5:
            verdict = "Consider Carefully"
        else:
            verdict = "High Risk Purchase"

        explanation = (
            f"RealVerdict {real_verdict_score}/10 from live {marketplace_name} signals: "
            f"rating {rating:.1f}/5, ~{review_count} reviews, "
            f"{positive_pct:.1f}% positive vs {negative_pct:.1f}% negative comments, "
            f"overall sentiment {overall_sentiment.capitalize()}, "
            f"buy signal {buy_signal_score:.1f}/100."
        )
        return verdict, explanation

    def _collect_sources(
        self,
        stores: List[Dict[str, Any]],
        listing: Dict[str, Any],
    ) -> List[str]:
        sources: List[str] = []
        for store in stores:
            name = str(store.get("name") or "").strip()
            if name and name not in sources:
                sources.append(name)

        listing_source = str(listing.get("source") or "").strip()
        if listing_source and listing_source not in sources:
            sources.append(listing_source)

        return sources[:8]

    def _request_json(self, params: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.get(
            self.API_BASE_URL,
            params=params,
            timeout=self.REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code >= 400:
            message = self._extract_error_message(response)
            raise requests.HTTPError(message, response=response)

        payload = response.json()
        if payload.get("error"):
            raise RuntimeError(str(payload.get("error")))

        return payload

    def _extract_error_message(self, response: requests.Response) -> str:
        try:
            payload = response.json()
            if payload.get("error"):
                return str(payload["error"])
            error = payload.get("search_metadata", {}).get("status")
            if error:
                return f"SerpAPI request failed: {error}"
        except Exception:
            pass
        return f"SerpAPI request failed with status {response.status_code}."

    def _to_int(self, value: Any) -> int:
        if value is None:
            return 0
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        text = str(value).strip().lower()
        if not text:
            return 0

        multiplier = 1
        if text.endswith("k"):
            multiplier = 1000
            text = text[:-1]
        elif text.endswith("m"):
            multiplier = 1_000_000
            text = text[:-1]

        text = text.replace(",", "").replace("reviews", "").strip()
        try:
            return int(float(text) * multiplier)
        except (TypeError, ValueError):
            return 0

    def _to_float(self, value: Any) -> float:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip().replace(",", "")
        if not text:
            return 0.0

        match = re.search(r"-?\d+(?:\.\d+)?", text)
        if not match:
            return 0.0

        try:
            return float(match.group(0))
        except (TypeError, ValueError):
            return 0.0

    def _clean_text(self, text: str) -> str:
        return " ".join((text or "").split())
