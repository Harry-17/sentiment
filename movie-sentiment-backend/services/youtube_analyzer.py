import logging
import re
from collections import Counter
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

import requests

logger = logging.getLogger(__name__)


class YouTubeAnalyzer:
    """Fetch and analyze public YouTube video metadata + comments."""

    API_BASE_URL = "https://www.googleapis.com/youtube/v3"
    REQUEST_TIMEOUT_SECONDS = 20
    MAX_COMMENTS = 100
    TOXICITY_MODERATE_THRESHOLD = 10.0
    TOXICITY_HIGH_THRESHOLD = 25.0
    SPAM_MODERATE_THRESHOLD = 12.0
    SPAM_HIGH_THRESHOLD = 30.0
    MAX_TOXIC_EXAMPLES = 3
    MAX_REPEATED_EXAMPLES = 5
    MAX_SPAM_PATTERNS = 5
    SIMILARITY_THRESHOLD = 0.9
    MIN_SIMILAR_LENGTH = 18

    TOXICITY_RULES: List[Tuple[str, re.Pattern[str]]] = [
        (
            "Abusive language",
            re.compile(
                r"\b(?:idiot|moron|stupid|dumb|trash|garbage|loser|pathetic|clown|shut up)\b",
                re.IGNORECASE,
            ),
        ),
        (
            "Harmful phrasing",
            re.compile(
                r"\b(?:kill yourself|go die|die\b|kys\b|worthless)\b",
                re.IGNORECASE,
            ),
        ),
        (
            "Direct attack",
            re.compile(
                r"\b(?:you|u|you're|youre)\b.{0,25}\b(?:idiot|stupid|trash|worst)\b",
                re.IGNORECASE,
            ),
        ),
    ]

    SPAM_RULES: List[Tuple[str, re.Pattern[str]]] = [
        (
            "Promotional links or self-promo",
            re.compile(
                r"(?:https?://|www\.|subscribe|check out my channel|promo code|discount|offer)",
                re.IGNORECASE,
            ),
        ),
        (
            "Engagement bait",
            re.compile(
                r"(?:sub\s*for\s*sub|like\s*for\s*like|follow\s*me|support\s*my\s*channel)",
                re.IGNORECASE,
            ),
        ),
        (
            "Scam-like money pitch",
            re.compile(
                r"(?:earn money|double your money|investment plan|crypto signal|guaranteed return)",
                re.IGNORECASE,
            ),
        ),
        (
            "Contact solicitation",
            re.compile(
                r"(?:whatsapp|telegram|dm me|inbox me|contact me)",
                re.IGNORECASE,
            ),
        ),
    ]

    def __init__(self, api_key: str):
        self.api_key = (api_key or "").strip()

    def analyze_video(
        self,
        video_input: str,
        sentiment_analyzer: Any,
        max_comments: int = 100,
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError(
                "YouTube API key is not configured on the backend. Set YOUTUBE_API_KEY in environment."
            )

        video_id = self.extract_video_id(video_input)
        if not video_id:
            raise ValueError(
                "Invalid YouTube URL or ID. Please provide a full YouTube video/shorts link."
            )

        video_data = self._fetch_video_details(video_id)
        comments = self._fetch_comments(video_id, max_comments=min(max_comments, self.MAX_COMMENTS))

        if not comments:
            raise ValueError(
                "No public comments available for this video. Comments may be disabled."
            )

        analyzed_comments = []
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        emotion_totals: Dict[str, float] = {}
        all_keywords: List[str] = []

        for comment in comments:
            text = (comment.get("text") or "").strip()
            if not text:
                continue

            sentiment_result = sentiment_analyzer.predict_sentiment(text)
            emotions = sentiment_analyzer.predict_emotions(text)
            important_words = sentiment_analyzer.get_important_words(text)

            sentiment_key = (sentiment_result.get("label") or "Neutral").lower()
            if sentiment_key not in sentiment_counts:
                sentiment_key = "neutral"
            sentiment_counts[sentiment_key] += 1

            for emotion, score in emotions.items():
                emotion_totals[emotion] = emotion_totals.get(emotion, 0.0) + float(score)

            all_keywords.extend(important_words)

            analyzed_comments.append(
                {
                    "text": text,
                    "author": comment.get("author"),
                    "like_count": comment.get("like_count", 0),
                    "published_at": comment.get("published_at"),
                    "sentiment": sentiment_result.get("label", "Neutral"),
                    "sentiment_score": float(sentiment_result.get("score", 0.5)),
                    "emotions": emotions,
                    "important_words": important_words,
                }
            )

        total_comments = len(analyzed_comments)
        if total_comments == 0:
            raise ValueError("No valid comments were available for analysis.")

        sentiment_percentages = {
            key: round((count / total_comments) * 100, 2)
            for key, count in sentiment_counts.items()
        }
        emotion_scores = {
            emotion: round(score / total_comments, 3)
            for emotion, score in emotion_totals.items()
        }
        top_keywords = [word for word, _ in Counter(all_keywords).most_common(12)]

        overall_sentiment = max(
            sentiment_percentages.items(),
            key=lambda item: item[1],
        )[0]

        rating = self._calculate_rating(
            positive_pct=sentiment_percentages.get("positive", 0.0),
            negative_pct=sentiment_percentages.get("negative", 0.0),
            engagement_rate=video_data.get("engagement_rate", 0.0),
            like_ratio=video_data.get("like_ratio", 0.0),
        )

        verdict, verdict_explanation = self._generate_verdict(
            rating=rating,
            overall_sentiment=overall_sentiment,
            sentiment_percentages=sentiment_percentages,
            engagement_rate=video_data.get("engagement_rate", 0.0),
        )
        content_safety = self._analyze_content_safety(analyzed_comments)

        return {
            "source_type": "youtube",
            "video_id": video_id,
            "video_url": f"https://www.youtube.com/watch?v={video_id}",
            "video_title": video_data["video_title"],
            "channel_title": video_data["channel_title"],
            "thumbnail_url": video_data["thumbnail_url"],
            "published_at": video_data["published_at"],
            "view_count": video_data["view_count"],
            "like_count": video_data["like_count"],
            "comment_count": video_data["comment_count"],
            "engagement_rate": video_data["engagement_rate"],
            "like_ratio": video_data["like_ratio"],
            "rating": rating,
            "overall_sentiment": overall_sentiment,
            "sentiment_percentages": sentiment_percentages,
            "emotion_scores": emotion_scores,
            "top_keywords": top_keywords,
            "verdict": verdict,
            "verdict_explanation": verdict_explanation,
            "content_safety": content_safety,
            "comments_analyzed": total_comments,
            "comments": analyzed_comments[:50],
        }

    def analyze_target(
        self,
        target_input: str,
        sentiment_analyzer: Any,
        max_comments: int = 100,
        max_videos: int = 6,
    ) -> Dict[str, Any]:
        """Analyze either a single YouTube video or a channel aggregate."""
        video_id = self.extract_video_id(target_input)
        if video_id:
            return self.analyze_video(target_input, sentiment_analyzer, max_comments=max_comments)

        channel_id = self._resolve_channel_id(target_input)
        if not channel_id:
            raise ValueError(
                "Invalid YouTube input. Please provide a valid video URL/ID or channel URL/handle."
            )

        return self._analyze_channel(
            channel_id=channel_id,
            target_input=target_input,
            sentiment_analyzer=sentiment_analyzer,
            max_comments=max_comments,
            max_videos=max_videos,
        )

    def extract_video_id(self, raw_value: str) -> Optional[str]:
        value = (raw_value or "").strip()
        if not value:
            return None

        raw_id_match = re.fullmatch(r"[A-Za-z0-9_-]{11}", value)
        if raw_id_match:
            return value

        parsed = urlparse(value)
        host = (parsed.netloc or "").lower()
        path = (parsed.path or "").strip("/")

        if "youtu.be" in host:
            candidate = path.split("/")[0]
            return candidate if re.fullmatch(r"[A-Za-z0-9_-]{11}", candidate) else None

        if "youtube.com" in host or "youtube-nocookie.com" in host:
            query = parse_qs(parsed.query or "")

            if path == "watch":
                candidate = (query.get("v") or [None])[0]
                if candidate and re.fullmatch(r"[A-Za-z0-9_-]{11}", candidate):
                    return candidate

            if path.startswith("shorts/") or path.startswith("embed/") or path.startswith("live/"):
                candidate = path.split("/")[1] if "/" in path else None
                if candidate and re.fullmatch(r"[A-Za-z0-9_-]{11}", candidate):
                    return candidate

        generic_match = re.search(r"(?:v=|/)([A-Za-z0-9_-]{11})(?:[?&/]|$)", value)
        if generic_match:
            return generic_match.group(1)

        return None

    def _resolve_channel_id(self, raw_input: str) -> Optional[str]:
        value = (raw_input or "").strip()
        if not value:
            return None

        # Raw channel ID support.
        if re.fullmatch(r"UC[a-zA-Z0-9_-]{22}", value):
            return value

        parsed = urlparse(value)
        host = (parsed.netloc or "").lower()
        path = (parsed.path or "").strip("/")

        handle_hint = ""
        channel_hint = ""

        if "youtube.com" in host or "youtube-nocookie.com" in host:
            if path.startswith("channel/"):
                maybe_id = path.split("/")[1] if "/" in path else ""
                if re.fullmatch(r"UC[a-zA-Z0-9_-]{22}", maybe_id):
                    return maybe_id
                channel_hint = maybe_id
            elif path.startswith("@"):
                handle_hint = path
            elif path.startswith("c/") or path.startswith("user/"):
                channel_hint = path.split("/")[1] if "/" in path else ""

        if value.startswith("@"):
            handle_hint = value

        query = handle_hint or channel_hint or value
        if not query:
            return None

        if query.startswith("@"):
            query = query[1:]

        # Try exact username resolution for legacy URLs.
        if channel_hint and not channel_hint.startswith("@"):
            try:
                legacy_payload = self._request_json(
                    f"{self.API_BASE_URL}/channels",
                    params={
                        "part": "id",
                        "forUsername": channel_hint,
                        "maxResults": 1,
                        "key": self.api_key,
                    },
                )
                legacy_items = legacy_payload.get("items") or []
                if legacy_items:
                    legacy_id = str(legacy_items[0].get("id") or "").strip()
                    if legacy_id:
                        return legacy_id
            except Exception:
                pass

        # Fallback to channel search.
        try:
            payload = self._request_json(
                f"{self.API_BASE_URL}/search",
                params={
                    "part": "snippet",
                    "type": "channel",
                    "q": query,
                    "maxResults": 1,
                    "key": self.api_key,
                },
            )
        except Exception:
            return None
        items = payload.get("items") or []
        if not items:
            return None

        channel_id = str(((items[0].get("snippet") or {}).get("channelId")) or "").strip()
        return channel_id or None

    def _fetch_channel_details(self, channel_id: str) -> Dict[str, Any]:
        payload = self._request_json(
            f"{self.API_BASE_URL}/channels",
            params={
                "part": "snippet,statistics",
                "id": channel_id,
                "key": self.api_key,
            },
        )
        items = payload.get("items") or []
        if not items:
            raise ValueError("YouTube channel not found.")

        item = items[0]
        snippet = item.get("snippet") or {}
        stats = item.get("statistics") or {}

        thumbnails = snippet.get("thumbnails") or {}
        thumbnail_url = (
            (thumbnails.get("high") or {}).get("url")
            or (thumbnails.get("medium") or {}).get("url")
            or (thumbnails.get("default") or {}).get("url")
            or ""
        )

        return {
            "channel_id": channel_id,
            "channel_title": (snippet.get("title") or "").strip() or "Unknown Channel",
            "thumbnail_url": thumbnail_url,
            "published_at": snippet.get("publishedAt"),
            "subscriber_count": self._to_int(stats.get("subscriberCount")),
            "channel_view_count": self._to_int(stats.get("viewCount")),
            "video_count": self._to_int(stats.get("videoCount")),
        }

    def _fetch_recent_channel_video_ids(self, channel_id: str, max_videos: int = 6) -> List[str]:
        payload = self._request_json(
            f"{self.API_BASE_URL}/search",
            params={
                "part": "id",
                "channelId": channel_id,
                "type": "video",
                "order": "date",
                "maxResults": max(2, min(10, max_videos)),
                "key": self.api_key,
            },
        )
        items = payload.get("items") or []
        video_ids: List[str] = []
        for item in items:
            video_id = str(((item.get("id") or {}).get("videoId")) or "").strip()
            if video_id and video_id not in video_ids:
                video_ids.append(video_id)
        return video_ids

    def _analyze_channel(
        self,
        channel_id: str,
        target_input: str,
        sentiment_analyzer: Any,
        max_comments: int = 100,
        max_videos: int = 6,
    ) -> Dict[str, Any]:
        channel = self._fetch_channel_details(channel_id)
        video_ids = self._fetch_recent_channel_video_ids(channel_id, max_videos=max_videos)
        if not video_ids:
            raise ValueError("No recent channel videos found for comparison.")

        comments_budget = max(20, min(self.MAX_COMMENTS, int(max_comments or 100)))
        per_video_comments = max(5, comments_budget // max(1, len(video_ids)))

        aggregated_comments: List[Dict[str, Any]] = []
        view_count_total = 0
        like_count_total = 0
        comment_count_total = 0

        for video_id in video_ids:
            try:
                video_details = self._fetch_video_details(video_id)
            except Exception:
                continue

            view_count_total += self._to_int(video_details.get("view_count"))
            like_count_total += self._to_int(video_details.get("like_count"))
            comment_count_total += self._to_int(video_details.get("comment_count"))

            try:
                comments = self._fetch_comments(video_id, max_comments=per_video_comments)
            except Exception:
                comments = []

            for comment in comments:
                comment["video_id"] = video_id
                aggregated_comments.append(comment)
                if len(aggregated_comments) >= comments_budget:
                    break

            if len(aggregated_comments) >= comments_budget:
                break

        if not aggregated_comments:
            raise ValueError("No public comments available across recent channel videos.")

        analyzed_comments = []
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        emotion_totals: Dict[str, float] = {}
        all_keywords: List[str] = []

        for comment in aggregated_comments:
            text = (comment.get("text") or "").strip()
            if not text:
                continue

            sentiment_result = sentiment_analyzer.predict_sentiment(text)
            emotions = sentiment_analyzer.predict_emotions(text)
            important_words = sentiment_analyzer.get_important_words(text)

            sentiment_key = (sentiment_result.get("label") or "Neutral").lower()
            if sentiment_key not in sentiment_counts:
                sentiment_key = "neutral"
            sentiment_counts[sentiment_key] += 1

            for emotion, score in emotions.items():
                emotion_totals[emotion] = emotion_totals.get(emotion, 0.0) + float(score)

            all_keywords.extend(important_words)

            analyzed_comments.append(
                {
                    "text": text,
                    "author": comment.get("author"),
                    "like_count": comment.get("like_count", 0),
                    "published_at": comment.get("published_at"),
                    "video_id": comment.get("video_id"),
                    "sentiment": sentiment_result.get("label", "Neutral"),
                    "sentiment_score": float(sentiment_result.get("score", 0.5)),
                    "emotions": emotions,
                    "important_words": important_words,
                }
            )

        total_comments = len(analyzed_comments)
        if total_comments == 0:
            raise ValueError("No valid comments were available for channel-level analysis.")

        sentiment_percentages = {
            key: round((count / total_comments) * 100, 2)
            for key, count in sentiment_counts.items()
        }
        emotion_scores = {
            emotion: round(score / total_comments, 3)
            for emotion, score in emotion_totals.items()
        }
        top_keywords = [word for word, _ in Counter(all_keywords).most_common(12)]
        overall_sentiment = max(sentiment_percentages.items(), key=lambda item: item[1])[0]

        engagement_base = like_count_total + comment_count_total
        engagement_rate = round((engagement_base / view_count_total) * 100, 2) if view_count_total > 0 else 0.0
        like_ratio = round((like_count_total / view_count_total) * 100, 2) if view_count_total > 0 else 0.0

        rating = self._calculate_rating(
            positive_pct=sentiment_percentages.get("positive", 0.0),
            negative_pct=sentiment_percentages.get("negative", 0.0),
            engagement_rate=engagement_rate,
            like_ratio=like_ratio,
        )

        verdict, verdict_explanation = self._generate_verdict(
            rating=rating,
            overall_sentiment=overall_sentiment,
            sentiment_percentages=sentiment_percentages,
            engagement_rate=engagement_rate,
        )
        content_safety = self._analyze_content_safety(analyzed_comments)

        canonical_url = (
            f"https://www.youtube.com/channel/{channel_id}"
            if not str(target_input or "").strip().startswith("http")
            else target_input
        )

        return {
            "source_type": "youtube_channel",
            "video_id": channel_id,
            "video_url": canonical_url,
            "video_title": f"{channel['channel_title']} (recent videos)",
            "channel_title": channel["channel_title"],
            "thumbnail_url": channel["thumbnail_url"],
            "published_at": channel["published_at"],
            "view_count": view_count_total,
            "like_count": like_count_total,
            "comment_count": comment_count_total,
            "engagement_rate": engagement_rate,
            "like_ratio": like_ratio,
            "rating": rating,
            "overall_sentiment": overall_sentiment,
            "sentiment_percentages": sentiment_percentages,
            "emotion_scores": emotion_scores,
            "top_keywords": top_keywords,
            "verdict": verdict,
            "verdict_explanation": (
                f"{verdict_explanation} Channel aggregate from {len(video_ids)} recent videos."
            ),
            "content_safety": content_safety,
            "comments_analyzed": total_comments,
            "comments": analyzed_comments[:50],
            "channel_id": channel_id,
            "videos_analyzed": len(video_ids),
            "subscriber_count": channel["subscriber_count"],
            "channel_view_count": channel["channel_view_count"],
            "channel_video_count": channel["video_count"],
        }

    def _fetch_video_details(self, video_id: str) -> Dict[str, Any]:
        payload = self._request_json(
            f"{self.API_BASE_URL}/videos",
            params={
                "part": "snippet,statistics",
                "id": video_id,
                "key": self.api_key,
            },
        )

        items = payload.get("items") or []
        if not items:
            raise ValueError("YouTube video not found. Please check the URL and try again.")

        item = items[0]
        snippet = item.get("snippet") or {}
        stats = item.get("statistics") or {}

        thumbnails = snippet.get("thumbnails") or {}
        thumbnail_url = (
            (thumbnails.get("maxres") or {}).get("url")
            or (thumbnails.get("high") or {}).get("url")
            or (thumbnails.get("medium") or {}).get("url")
            or (thumbnails.get("default") or {}).get("url")
            or ""
        )

        view_count = self._to_int(stats.get("viewCount"))
        like_count = self._to_int(stats.get("likeCount"))
        comment_count = self._to_int(stats.get("commentCount"))

        engagement_base = like_count + comment_count
        engagement_rate = round((engagement_base / view_count) * 100, 2) if view_count > 0 else 0.0
        like_ratio = round((like_count / view_count) * 100, 2) if view_count > 0 else 0.0

        return {
            "video_title": (snippet.get("title") or "").strip() or "Untitled Video",
            "channel_title": (snippet.get("channelTitle") or "").strip() or "Unknown Channel",
            "thumbnail_url": thumbnail_url,
            "published_at": snippet.get("publishedAt"),
            "view_count": view_count,
            "like_count": like_count,
            "comment_count": comment_count,
            "engagement_rate": engagement_rate,
            "like_ratio": like_ratio,
        }

    def _fetch_comments(self, video_id: str, max_comments: int) -> List[Dict[str, Any]]:
        comments: List[Dict[str, Any]] = []
        page_token: Optional[str] = None

        while len(comments) < max_comments:
            page_size = min(100, max_comments - len(comments))
            params = {
                "part": "snippet",
                "videoId": video_id,
                "maxResults": page_size,
                "order": "relevance",
                "textFormat": "plainText",
                "key": self.api_key,
            }
            if page_token:
                params["pageToken"] = page_token

            try:
                payload = self._request_json(f"{self.API_BASE_URL}/commentThreads", params=params)
            except requests.HTTPError as exc:
                if exc.response is not None and exc.response.status_code == 403:
                    error_reason = self._extract_error_reason(exc.response)
                    if error_reason == "commentsDisabled":
                        logger.info("Comments are disabled for video %s", video_id)
                        return []
                raise

            items = payload.get("items") or []
            if not items:
                break

            for item in items:
                thread_snippet = item.get("snippet") or {}
                top_level = (thread_snippet.get("topLevelComment") or {}).get("snippet") or {}

                text = (top_level.get("textDisplay") or top_level.get("textOriginal") or "").strip()
                text = self._clean_text(text)
                if len(text) < 5:
                    continue

                comments.append(
                    {
                        "text": text,
                        "author": top_level.get("authorDisplayName"),
                        "like_count": self._to_int(top_level.get("likeCount")),
                        "published_at": top_level.get("publishedAt"),
                    }
                )

                if len(comments) >= max_comments:
                    break

            page_token = payload.get("nextPageToken")
            if not page_token:
                break

        return comments

    def _calculate_rating(
        self,
        positive_pct: float,
        negative_pct: float,
        engagement_rate: float,
        like_ratio: float,
    ) -> float:
        sentiment_component = max(0.0, min(10.0, 5.0 + ((positive_pct - negative_pct) / 20.0)))
        engagement_component = max(0.0, min(10.0, engagement_rate * 1.2))
        like_component = max(0.0, min(10.0, like_ratio * 2.0))

        weighted_score = (
            (sentiment_component * 0.6)
            + (engagement_component * 0.25)
            + (like_component * 0.15)
        )

        return round(max(1.0, min(10.0, weighted_score)), 1)

    def _generate_verdict(
        self,
        rating: float,
        overall_sentiment: str,
        sentiment_percentages: Dict[str, float],
        engagement_rate: float,
    ) -> Tuple[str, str]:
        positive_pct = sentiment_percentages.get("positive", 0.0)
        negative_pct = sentiment_percentages.get("negative", 0.0)

        if rating >= 8.5:
            verdict = "Excellent Audience Response"
        elif rating >= 7.0:
            verdict = "Strong Positive Reception"
        elif rating >= 5.5:
            verdict = "Mixed Reception"
        else:
            verdict = "Weak Audience Reception"

        explanation = (
            f"Rating {rating}/10 based on comment sentiment and engagement. "
            f"Positive: {positive_pct:.1f}%, Negative: {negative_pct:.1f}%, "
            f"Overall sentiment: {overall_sentiment.capitalize()}, "
            f"Engagement rate: {engagement_rate:.2f}%."
        )
        return verdict, explanation

    def _request_json(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.get(
            url,
            params=params,
            timeout=self.REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code >= 400:
            message = self._extract_error_message(response)
            raise requests.HTTPError(message, response=response)
        return response.json()

    def _extract_error_message(self, response: requests.Response) -> str:
        try:
            payload = response.json()
            error = payload.get("error") or {}
            message = error.get("message")
            if message:
                return message
        except Exception:
            pass
        return f"YouTube API request failed with status {response.status_code}."

    def _extract_error_reason(self, response: requests.Response) -> str:
        try:
            payload = response.json()
            errors = ((payload.get("error") or {}).get("errors")) or []
            if errors:
                return errors[0].get("reason", "")
        except Exception:
            return ""
        return ""

    def _to_int(self, value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _clean_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", (text or "").strip())

    def _analyze_content_safety(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_comments = len(comments)
        if total_comments == 0:
            return {
                "toxicity_percentage": 0.0,
                "toxicity_comment_count": 0,
                "toxic_comment_examples": [],
                "spam_percentage": 0.0,
                "spam_comment_count": 0,
                "repeated_comments": [],
                "spam_patterns": [],
                "safety_report": {
                    "toxicity_level": "Low",
                    "spam_level": "Low",
                    "warnings": [],
                    "summary": "No comments were available for content safety analysis.",
                    "clean_comments": True,
                },
            }

        toxic_indices = set()
        toxic_examples = []

        for index, comment in enumerate(comments):
            text = comment.get("text", "")
            reasons = self._detect_toxicity_reasons(text)
            if not reasons:
                continue

            toxic_indices.add(index)
            if len(toxic_examples) < self.MAX_TOXIC_EXAMPLES:
                toxic_examples.append(
                    {
                        "text": text,
                        "author": comment.get("author"),
                        "reason": ", ".join(reasons),
                    }
                )

        toxic_count = len(toxic_indices)
        toxicity_percentage = round((toxic_count / total_comments) * 100, 2)

        duplicate_indices, repeated_comments = self._detect_repeated_comments(comments)
        spam_pattern_counts, spam_pattern_indices = self._detect_spam_patterns(comments)

        spam_indices = duplicate_indices.union(spam_pattern_indices)
        spam_count = len(spam_indices)
        spam_percentage = round((spam_count / total_comments) * 100, 2)

        spam_patterns = [
            {"pattern": pattern, "count": count}
            for pattern, count in spam_pattern_counts.most_common(self.MAX_SPAM_PATTERNS)
        ]

        toxicity_level = self._to_safety_level(
            toxicity_percentage,
            moderate_threshold=self.TOXICITY_MODERATE_THRESHOLD,
            high_threshold=self.TOXICITY_HIGH_THRESHOLD,
        )
        spam_level = self._to_safety_level(
            spam_percentage,
            moderate_threshold=self.SPAM_MODERATE_THRESHOLD,
            high_threshold=self.SPAM_HIGH_THRESHOLD,
        )

        warnings = []
        if toxicity_level == "High":
            warnings.append(
                f"High toxicity detected ({toxicity_percentage:.1f}% of comments show abusive or harmful language)."
            )
        if spam_level == "High":
            warnings.append(
                f"High spam activity detected ({spam_percentage:.1f}% of comments look repetitive or promotional)."
            )

        clean_comments = len(warnings) == 0
        if warnings:
            summary = " ".join(warnings)
        else:
            summary = "No high-risk toxicity or spam signals detected. Comments appear mostly clean."

        return {
            "toxicity_percentage": toxicity_percentage,
            "toxicity_comment_count": toxic_count,
            "toxic_comment_examples": toxic_examples,
            "spam_percentage": spam_percentage,
            "spam_comment_count": spam_count,
            "repeated_comments": repeated_comments,
            "spam_patterns": spam_patterns,
            "safety_report": {
                "toxicity_level": toxicity_level,
                "spam_level": spam_level,
                "warnings": warnings,
                "summary": summary,
                "clean_comments": clean_comments,
            },
        }

    def _detect_toxicity_reasons(self, text: str) -> List[str]:
        value = text or ""
        reasons: List[str] = []

        for reason, pattern in self.TOXICITY_RULES:
            if pattern.search(value):
                reasons.append(reason)

        upper_chars = sum(1 for char in value if char.isupper())
        alpha_chars = sum(1 for char in value if char.isalpha())
        if alpha_chars >= 12 and upper_chars / alpha_chars > 0.6 and value.count("!") >= 3:
            reasons.append("Aggressive shouting tone")

        return reasons

    def _detect_repeated_comments(
        self,
        comments: List[Dict[str, Any]],
    ) -> Tuple[set[int], List[Dict[str, Any]]]:
        normalized_map: Dict[str, List[int]] = {}
        for index, comment in enumerate(comments):
            normalized = self._normalize_for_comparison(comment.get("text", ""))
            if not normalized:
                continue
            normalized_map.setdefault(normalized, []).append(index)

        repeated_indices: set[int] = set()
        repeated_examples: List[Dict[str, Any]] = []

        for normalized_text, indices in normalized_map.items():
            if len(indices) < 2:
                continue
            repeated_indices.update(indices)
            representative = comments[indices[0]].get("text", "")
            repeated_examples.append(
                {
                    "text": representative,
                    "count": len(indices),
                }
            )

        non_duplicate_indices = [
            index
            for index in range(len(comments))
            if index not in repeated_indices
        ]

        visited = set()
        for i, left_index in enumerate(non_duplicate_indices):
            if left_index in visited:
                continue

            left_text = self._normalize_for_comparison(comments[left_index].get("text", ""))
            if len(left_text) < self.MIN_SIMILAR_LENGTH:
                continue

            cluster = [left_index]

            for right_index in non_duplicate_indices[i + 1 :]:
                if right_index in visited:
                    continue

                right_text = self._normalize_for_comparison(comments[right_index].get("text", ""))
                if len(right_text) < self.MIN_SIMILAR_LENGTH:
                    continue

                if SequenceMatcher(None, left_text, right_text).ratio() >= self.SIMILARITY_THRESHOLD:
                    cluster.append(right_index)

            if len(cluster) >= 3:
                repeated_indices.update(cluster)
                visited.update(cluster)
                repeated_examples.append(
                    {
                        "text": comments[cluster[0]].get("text", ""),
                        "count": len(cluster),
                    }
                )

        repeated_examples.sort(key=lambda item: item["count"], reverse=True)
        return repeated_indices, repeated_examples[: self.MAX_REPEATED_EXAMPLES]

    def _detect_spam_patterns(
        self,
        comments: List[Dict[str, Any]],
    ) -> Tuple[Counter[str], set[int]]:
        pattern_counts: Counter[str] = Counter()
        spam_indices: set[int] = set()

        for index, comment in enumerate(comments):
            text = comment.get("text", "")
            lowered = text.lower()

            for pattern_name, regex in self.SPAM_RULES:
                if regex.search(lowered):
                    pattern_counts[pattern_name] += 1
                    spam_indices.add(index)

            if re.search(r"(.)\1{6,}", lowered):
                pattern_counts["Repeated characters"] += 1
                spam_indices.add(index)

        return pattern_counts, spam_indices

    def _to_safety_level(
        self,
        percentage: float,
        moderate_threshold: float,
        high_threshold: float,
    ) -> str:
        if percentage >= high_threshold:
            return "High"
        if percentage >= moderate_threshold:
            return "Moderate"
        return "Low"

    def _normalize_for_comparison(self, text: str) -> str:
        without_links = re.sub(r"https?://\S+|www\.\S+", " ", text or "", flags=re.IGNORECASE)
        alphanumeric = re.sub(r"[^a-z0-9\s]", " ", without_links.lower())
        return re.sub(r"\s+", " ", alphanumeric).strip()
