import asyncio
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)


class IMDbScraper:
    """Fetch movie metadata and user reviews from IMDb endpoints."""

    SUGGESTION_URL_TEMPLATE = "https://v2.sg.media-imdb.com/suggestion/{prefix}/{query}.json"
    GRAPHQL_URL = "https://caching.graphql.imdb.com/"
    REQUEST_TIMEOUT_SECONDS = 20
    MAX_PAGE_SIZE = 50

    HTTP_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    GRAPHQL_HEADERS = {
        **HTTP_HEADERS,
        "Content-Type": "application/json",
        "Origin": "https://www.imdb.com",
        "Referer": "https://www.imdb.com/",
        "x-imdb-user-language": "en-US",
        "x-imdb-client-name": "IMDbConsumerSite",
    }

    TYPE_PRIORITY = {
        "movie": 0,
        "tvMovie": 1,
        "tvMiniSeries": 2,
        "tvSeries": 3,
        "video": 4,
        "short": 5,
    }

    async def fetch_movie_data(self, movie_identifier: str, limit: int = 100) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Fetch movie details and reviews.

        Args:
            movie_identifier: IMDb title URL/ID or free-text movie query.
            limit: Maximum number of reviews to fetch.

        Returns:
            Tuple of (movie_data, reviews).
        """
        try:
            movie_id = await self._resolve_movie_id(movie_identifier)
            if not movie_id:
                raise ValueError(
                    "Movie not found on IMDb. Please provide a valid IMDb link or a more specific title."
                )

            logger.info("Resolved movie identifier '%s' -> %s", movie_identifier, movie_id)

            movie_data = await self._get_movie_details(movie_id)
            reviews = await self._get_reviews(movie_id, limit=limit)

            if not reviews:
                raise ValueError("No IMDb user reviews were found for this title.")

            return movie_data, reviews
        except requests.RequestException as exc:
            logger.error("IMDb request failed: %s", exc)
            raise RuntimeError("Unable to reach IMDb right now. Please try again shortly.") from exc

    async def _resolve_movie_id(self, movie_identifier: str) -> Optional[str]:
        """Resolve an IMDb title ID (`tt...`) from URL, ID, or search text."""
        identifier = (movie_identifier or "").strip()
        if not identifier:
            return None

        direct_id = self._extract_imdb_id(identifier)
        if direct_id:
            return direct_id

        return await self._search_movie(identifier)

    def _extract_imdb_id(self, text: str) -> Optional[str]:
        """Extract IMDb title ID from any text (URL, ID, raw input)."""
        match = re.search(r"(tt\d{5,12})", text or "")
        return match.group(1) if match else None

    async def _search_movie(self, movie_name: str) -> Optional[str]:
        """Search IMDb suggestion endpoint and pick the best title match."""
        query = (movie_name or "").strip()
        if not query:
            return None

        prefix = next((char.lower() for char in query if char.isalnum()), "a")
        suggestion_url = self.SUGGESTION_URL_TEMPLATE.format(prefix=prefix, query=quote(query))

        try:
            payload = await asyncio.to_thread(self._request_json, suggestion_url)
        except requests.RequestException as exc:
            logger.error("IMDb suggestion lookup failed for '%s': %s", query, exc)
            return None

        candidates = []
        for item in payload.get("d", []):
            if not isinstance(item, dict):
                continue
            imdb_id = item.get("id", "")
            if isinstance(imdb_id, str) and imdb_id.startswith("tt"):
                candidates.append(item)

        if not candidates:
            return None

        best = self._select_best_candidate(query, candidates)
        return best.get("id") if best else None

    def _select_best_candidate(self, query: str, candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Pick the most relevant title from IMDb suggestion results."""
        query_year = self._extract_year(query)
        query_without_year = re.sub(r"\b(?:19|20)\d{2}\b", " ", query)
        normalized_query = self._normalize_title(query_without_year) or self._normalize_title(query)

        def score(index: int, item: Dict[str, Any]) -> Tuple[int, int, int, int, int, int]:
            title = self._normalize_title(str(item.get("l", "")))
            item_type = str(item.get("qid", ""))
            item_year = item.get("y")

            exact_penalty = 0 if normalized_query and title == normalized_query else 1
            startswith_penalty = 0 if normalized_query and title.startswith(normalized_query) else 1
            contains_penalty = 0 if normalized_query and normalized_query in title else 1
            year_penalty = 0 if query_year is None or item_year == query_year else 1
            type_penalty = self.TYPE_PRIORITY.get(item_type, 99)

            return (
                exact_penalty,
                startswith_penalty,
                contains_penalty,
                year_penalty,
                type_penalty,
                index,
            )

        ranked = sorted(enumerate(candidates), key=lambda pair: score(pair[0], pair[1]))
        return ranked[0][1] if ranked else None

    async def _get_movie_details(self, movie_id: str) -> Dict[str, Any]:
        """Fetch title metadata from IMDb GraphQL."""
        query = """
        query MovieDetails($id: ID!) {
          title(id: $id) {
            titleText { text }
            releaseYear { year }
            primaryImage { url }
            ratingsSummary { aggregateRating voteCount }
          }
        }
        """
        payload = await self._graphql_request(query, {"id": movie_id})
        title_data = ((payload.get("data") or {}).get("title")) or {}

        if not title_data:
            raise ValueError("Movie details were not found on IMDb.")

        title = ((title_data.get("titleText") or {}).get("text") or "").strip() or "Unknown"
        poster = ((title_data.get("primaryImage") or {}).get("url") or "").strip()
        rating_value = ((title_data.get("ratingsSummary") or {}).get("aggregateRating"))

        rating = float(rating_value) if rating_value is not None else 0.0

        return {
            "title": title,
            "rating": rating,
            "poster": poster,
            "imdb_id": movie_id,
        }

    async def _get_reviews(self, movie_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch user reviews from IMDb GraphQL with cursor pagination."""
        query = """
        query TitleReviews(
          $id: ID!
          $first: Int!
          $after: ID
          $sort: ReviewsSort
          $filter: ReviewsFilter
        ) {
          title(id: $id) {
            reviews(first: $first, after: $after, sort: $sort, filter: $filter) {
              pageInfo { hasNextPage endCursor }
              edges {
                node {
                  id
                  authorRating
                  text {
                    originalText {
                      plainText
                    }
                  }
                }
              }
            }
          }
        }
        """

        reviews: List[Dict[str, Any]] = []
        seen_ids = set()
        cursor: Optional[str] = None

        while len(reviews) < limit:
            page_size = min(self.MAX_PAGE_SIZE, limit - len(reviews))
            variables: Dict[str, Any] = {
                "id": movie_id,
                "first": page_size,
                "after": cursor,
                "sort": {"by": "HELPFULNESS_SCORE", "order": "DESC"},
                "filter": {"spoiler": "EXCLUDE"},
            }

            payload = await self._graphql_request(query, variables)
            review_block = (((payload.get("data") or {}).get("title") or {}).get("reviews")) or {}
            edges = review_block.get("edges", [])

            if not edges:
                break

            for edge in edges:
                node = (edge or {}).get("node") or {}
                review_id = node.get("id")
                review_text = (
                    (((node.get("text") or {}).get("originalText") or {}).get("plainText") or "").strip()
                )

                if not review_text or len(review_text) < 20:
                    continue
                if review_id and review_id in seen_ids:
                    continue

                if review_id:
                    seen_ids.add(review_id)
                reviews.append(
                    {
                        "text": review_text,
                        "author_rating": node.get("authorRating"),
                    }
                )

                if len(reviews) >= limit:
                    break

            page_info = review_block.get("pageInfo") or {}
            if not page_info.get("hasNextPage"):
                break

            cursor = page_info.get("endCursor")
            if not cursor:
                break

        return reviews[:limit]

    async def _graphql_request(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Run GraphQL request in a thread to keep the async API non-blocking."""
        return await asyncio.to_thread(self._graphql_request_sync, query, variables)

    def _graphql_request_sync(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.post(
            self.GRAPHQL_URL,
            json={"query": query, "variables": variables},
            headers=self.GRAPHQL_HEADERS,
            timeout=self.REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()

        if payload.get("errors"):
            first_error = payload["errors"][0] if payload["errors"] else {}
            message = first_error.get("message", "IMDb GraphQL returned an error.")
            raise RuntimeError(message)

        return payload

    def _request_json(self, url: str) -> Dict[str, Any]:
        response = requests.get(
            url,
            headers=self.HTTP_HEADERS,
            timeout=self.REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()

    def _normalize_title(self, value: str) -> str:
        cleaned = re.sub(r"[^a-z0-9]+", " ", (value or "").lower())
        return re.sub(r"\s+", " ", cleaned).strip()

    def _extract_year(self, value: str) -> Optional[int]:
        match = re.search(r"\b(19|20)\d{2}\b", value or "")
        return int(match.group(0)) if match else None
