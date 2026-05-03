import asyncio
import logging
import os
from collections import Counter
from threading import Thread
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from services.sentiment_analyzer import SentimentAnalyzer
from services.aspect_sentiment_analyzer import AspectSentimentAnalyzer
from services.comparison_engine import ComparisonEngine
from services.imdb_scraper import IMDbScraper
from services.verdict_generator import VerdictGenerator
from services.youtube_analyzer import YouTubeAnalyzer
from services.product_analyzer import ProductAnalyzer

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Movie Sentiment Analyzer API",
    description="Analyze sentiment for movies and YouTube videos",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
# Global placeholders
sentiment_analyzer = None
aspect_sentiment_analyzer = None
imdb_scraper = None
verdict_generator = None
youtube_analyzer = None
product_analyzer = None
comparison_engine = None


@app.on_event("startup")
async def load_services():
    global sentiment_analyzer, aspect_sentiment_analyzer
    global imdb_scraper, verdict_generator
    global youtube_analyzer, product_analyzer, comparison_engine

    print("🚀 Loading services...")

    sentiment_analyzer = SentimentAnalyzer()
    aspect_sentiment_analyzer = AspectSentimentAnalyzer()
    imdb_scraper = IMDbScraper()
    verdict_generator = VerdictGenerator()
    youtube_analyzer = YouTubeAnalyzer(api_key=os.getenv("YOUTUBE_API_KEY", ""))
    product_analyzer = ProductAnalyzer(api_key=os.getenv("SERPAPI_KEY", ""))
    comparison_engine = ComparisonEngine()

    def warm_up_models():
        try:
            logger.info("Starting background model warm-up")
            sentiment_analyzer._load_models()
            logger.info("Background model warm-up complete")
        except Exception as exc:
            logger.warning("Background model warm-up failed: %s", exc)

    Thread(target=warm_up_models, daemon=True).start()
    print("✅ Services loaded")

# Request/Response Models
class MovieAnalysisRequest(BaseModel):
    movie_name: Optional[str] = None
    imdb_link: Optional[str] = None
    include_aspects: Optional[bool] = True
    max_aspects: Optional[int] = 12
    min_aspect_mentions: Optional[int] = 2


class MovieAspectMention(BaseModel):
    aspect: str
    sentiment: str
    sentiment_score: float
    confidence: float
    snippet: str

class ReviewData(BaseModel):
    text: str
    sentiment: str
    sentiment_score: float
    emotions: Dict[str, float]
    important_words: List[str]
    aspect_mentions: List[MovieAspectMention] = Field(default_factory=list)


class AspectSentimentData(BaseModel):
    aspect: str
    mentions: int
    sentiment: str
    sentiment_score: float
    confidence: float
    sentiment_distribution: Dict[str, float]
    representative_keywords: List[str]
    example_snippets: List[str]


class AspectSentimentSummary(BaseModel):
    aspects: List[AspectSentimentData]
    aspects_detected: int
    coverage_percentage: float
    average_confidence: float
    positive_aspects: List[str]
    negative_aspects: List[str]
    neutral_aspects: List[str]
    extraction_method: str

class AnalysisResponse(BaseModel):
    movie_title: str
    movie_poster: str
    imdb_rating: float
    review_count: int
    overall_sentiment: str
    sentiment_percentages: Dict[str, float]
    emotion_scores: Dict[str, float]
    top_keywords: List[str]
    aspect_sentiment: AspectSentimentSummary
    reviews: List[ReviewData]
    verdict: str
    verdict_explanation: str


class MovieAspectAnalysisRequest(BaseModel):
    movie_name: Optional[str] = None
    imdb_link: Optional[str] = None
    max_aspects: Optional[int] = 12
    min_aspect_mentions: Optional[int] = 2
    include_review_mentions: Optional[bool] = False


class ReviewAspectResult(BaseModel):
    text: str
    aspect_mentions: List[MovieAspectMention]


class MovieAspectAnalysisResponse(BaseModel):
    movie_title: str
    movie_poster: str
    imdb_rating: float
    review_count: int
    aspect_sentiment: AspectSentimentSummary
    review_aspects: List[ReviewAspectResult] = Field(default_factory=list)


class YouTubeAnalysisRequest(BaseModel):
    youtube_url: str
    max_comments: Optional[int] = 100


class YouTubeCommentData(BaseModel):
    text: str
    author: Optional[str] = None
    like_count: int
    published_at: Optional[str] = None
    sentiment: str
    sentiment_score: float
    emotions: Dict[str, float]
    important_words: List[str]


class ToxicCommentExample(BaseModel):
    text: str
    author: Optional[str] = None
    reason: str


class RepeatedCommentExample(BaseModel):
    text: str
    count: int


class SpamPatternExample(BaseModel):
    pattern: str
    count: int


class SafetyReport(BaseModel):
    toxicity_level: str
    spam_level: str
    warnings: List[str]
    summary: str
    clean_comments: bool


class ContentSafetyAnalysis(BaseModel):
    toxicity_percentage: float
    toxicity_comment_count: int
    toxic_comment_examples: List[ToxicCommentExample]
    spam_percentage: float
    spam_comment_count: int
    repeated_comments: List[RepeatedCommentExample]
    spam_patterns: List[SpamPatternExample]
    safety_report: SafetyReport


class YouTubeAnalysisResponse(BaseModel):
    source_type: str
    video_id: str
    video_url: str
    video_title: str
    channel_title: str
    thumbnail_url: str
    published_at: Optional[str] = None
    view_count: int
    like_count: int
    comment_count: int
    engagement_rate: float
    like_ratio: float
    rating: float
    overall_sentiment: str
    sentiment_percentages: Dict[str, float]
    emotion_scores: Dict[str, float]
    top_keywords: List[str]
    verdict: str
    verdict_explanation: str
    content_safety: ContentSafetyAnalysis
    comments_analyzed: int
    comments: List[YouTubeCommentData]


class ProductAnalysisRequest(BaseModel):
    product_query: str
    marketplace: Optional[str] = "any"
    max_comments: Optional[int] = 60


class ProductReviewData(BaseModel):
    text: str
    source: Optional[str] = None
    sentiment: str
    sentiment_score: float
    rating: float
    emotions: Dict[str, float]
    important_words: List[str]


class ProductAnalysisResponse(BaseModel):
    source_type: str
    product_title: str
    product_url: str
    thumbnail_url: str
    marketplace: str
    primary_store: str
    price: str
    rating: float
    review_count: int
    offers_count: int
    buy_signal_score: float
    real_verdict_score: float
    overall_sentiment: str
    sentiment_percentages: Dict[str, float]
    emotion_scores: Dict[str, float]
    top_keywords: List[str]
    verdict: str
    verdict_explanation: str
    comments_analyzed: int
    trusted_sources: List[str]
    reviews: List[ProductReviewData]


class MovieComparisonTarget(BaseModel):
    movie_name: Optional[str] = None
    imdb_link: Optional[str] = None


class MovieComparisonRequest(BaseModel):
    left: MovieComparisonTarget
    right: MovieComparisonTarget
    max_aspects: Optional[int] = 12
    min_aspect_mentions: Optional[int] = 2


class ProductComparisonTarget(BaseModel):
    product_query: str
    marketplace: Optional[str] = "any"


class ProductComparisonRequest(BaseModel):
    left: ProductComparisonTarget
    right: ProductComparisonTarget
    max_comments: Optional[int] = 60
    max_aspects: Optional[int] = 12
    min_aspect_mentions: Optional[int] = 2


class YouTubeComparisonTarget(BaseModel):
    target_input: str


class YouTubeComparisonRequest(BaseModel):
    left: YouTubeComparisonTarget
    right: YouTubeComparisonTarget
    max_comments: Optional[int] = 80
    max_videos: Optional[int] = 6
    max_aspects: Optional[int] = 12
    min_aspect_mentions: Optional[int] = 2


class ComparisonResponse(BaseModel):
    domain: str
    left_entity: Dict[str, Any]
    right_entity: Dict[str, Any]
    comparison: Dict[str, Any]


def _resolve_movie_identifier(movie_name: Optional[str], imdb_link: Optional[str]) -> str:
    movie_identifier = (imdb_link or movie_name or "").strip()
    if not movie_identifier:
        raise HTTPException(status_code=400, detail="Please provide either movie_name or imdb_link")
    return movie_identifier


def _prepare_review_inputs(reviews: List[Any]) -> List[Dict[str, Any]]:
    prepared_reviews: List[Dict[str, Any]] = []
    for review_entry in reviews:
        if isinstance(review_entry, dict):
            review_text = str(review_entry.get("text", "")).strip()
            author_rating = review_entry.get("author_rating")
        else:
            review_text = str(review_entry).strip()
            author_rating = None

        if not review_text:
            continue

        prepared_reviews.append(
            {
                "text": review_text,
                "author_rating": author_rating,
            }
        )
    return prepared_reviews


def _model_to_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, dict):
        return value
    return {}


def _build_aspect_summary_from_rows(
    rows: List[Dict[str, Any]],
    text_key: str = "text",
    rating_key: Optional[str] = None,
    max_aspects: int = 12,
    min_aspect_mentions: int = 2,
) -> Dict[str, Any]:
    prepared: List[Dict[str, Any]] = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        text = str(row.get(text_key, "")).strip()
        if not text:
            continue

        rating_value = row.get(rating_key) if rating_key else None
        prepared.append(
            {
                "text": text,
                "author_rating": rating_value,
            }
        )

    if not prepared:
        return aspect_sentiment_analyzer.empty_summary()

    summary, _review_mentions = aspect_sentiment_analyzer.analyze_reviews(
        prepared,
        sentiment_analyzer=sentiment_analyzer,
        max_aspects=max_aspects,
        min_aspect_mentions=min_aspect_mentions,
    )
    return summary


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "Movie Sentiment Analyzer API is running",
        "version": "1.0.0"
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_movie(request: MovieAnalysisRequest):
    """
    Analyze sentiment of a movie based on IMDb reviews
    
    Parameters:
    - movie_name: Name of the movie (alternative to IMDb link)
    - imdb_link: Direct link to IMDb movie page
    
    Returns: Comprehensive analysis with sentiments, emotions, and verdict
    """
    try:
        movie_identifier = _resolve_movie_identifier(request.movie_name, request.imdb_link)
        
        logger.info(f"Analyzing movie: {movie_identifier}")
        
        # Scrape IMDb data
        movie_data, reviews = await imdb_scraper.fetch_movie_data(movie_identifier)
        
        if not reviews or len(reviews) == 0:
            raise HTTPException(status_code=404, detail="No reviews found for this movie")
        
        logger.info(f"Fetched {len(reviews)} reviews for {movie_data['title']}")

        prepared_reviews = _prepare_review_inputs(reviews)
        if not prepared_reviews:
            raise HTTPException(status_code=404, detail="No usable review text was found for this movie")

        max_aspects = max(3, min(30, request.max_aspects or 12))
        min_aspect_mentions = max(1, min(10, request.min_aspect_mentions or 2))

        aspect_summary = aspect_sentiment_analyzer.empty_summary()
        review_aspect_map: Dict[str, List[Dict[str, Any]]] = {}
        if request.include_aspects is not False:
            aspect_summary, review_aspect_map = aspect_sentiment_analyzer.analyze_reviews(
                prepared_reviews,
                sentiment_analyzer=sentiment_analyzer,
                max_aspects=max_aspects,
                min_aspect_mentions=min_aspect_mentions,
            )
        
        # Analyze sentiments and emotions
        analyzed_reviews = []
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        emotion_aggregates = {}
        all_keywords = []
        
        for review_entry in prepared_reviews:
            review_text = review_entry["text"]
            author_rating = review_entry["author_rating"]

            sentiment_result = sentiment_analyzer.predict_sentiment(
                review_text,
                author_rating=author_rating,
            )
            emotions = sentiment_analyzer.predict_emotions(review_text)
            important_words = sentiment_analyzer.get_important_words(review_text)
            
            # Update aggregates
            sentiment_key = sentiment_result["label"].lower()
            if sentiment_key not in sentiment_counts:
                sentiment_key = "neutral"
            sentiment_counts[sentiment_key] += 1
            for emotion, score in emotions.items():
                emotion_aggregates[emotion] = emotion_aggregates.get(emotion, 0) + score
            all_keywords.extend(important_words)
            
            # Store review data
            aspect_mentions = [
                MovieAspectMention(**mention)
                for mention in review_aspect_map.get(review_text, [])
            ]
            analyzed_reviews.append(ReviewData(
                text=review_text,
                sentiment=sentiment_result["label"],
                sentiment_score=sentiment_result["score"],
                emotions=emotions,
                important_words=important_words,
                aspect_mentions=aspect_mentions,
            ))
        
        # Calculate percentages
        total_reviews = len(analyzed_reviews)
        if total_reviews == 0:
            raise HTTPException(status_code=404, detail="No usable review text was found for this movie")

        sentiment_percentages = {
            k: round((v / total_reviews) * 100, 2) for k, v in sentiment_counts.items()
        }
        
        # Normalize emotion scores
        emotion_scores = {
            emotion: round(score / total_reviews, 3) 
            for emotion, score in emotion_aggregates.items()
        }
        
        # Get top keywords
        top_keywords = [word for word, _ in Counter(all_keywords).most_common(10)]
        
        # Generate verdict
        overall_sentiment = max(sentiment_percentages.items(), key=lambda x: x[1])[0]
        verdict, explanation = verdict_generator.generate_verdict(
            overall_sentiment=overall_sentiment,
            sentiment_percentages=sentiment_percentages,
            emotion_scores=emotion_scores,
            keywords=top_keywords
        )
        
        return AnalysisResponse(
            movie_title=movie_data["title"],
            movie_poster=movie_data["poster"],
            imdb_rating=movie_data["rating"],
            review_count=total_reviews,
            overall_sentiment=overall_sentiment,
            sentiment_percentages=sentiment_percentages,
            emotion_scores=emotion_scores,
            top_keywords=top_keywords,
            aspect_sentiment=AspectSentimentSummary(**aspect_summary),
            reviews=analyzed_reviews[:50],  # Return top 50 reviews
            verdict=verdict,
            verdict_explanation=explanation
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error analyzing movie: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing movie: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="Unable to fetch reliable IMDb data right now. Please try again in a moment.",
        )


@app.post("/analyze/aspects", response_model=MovieAspectAnalysisResponse)
async def analyze_movie_aspects(request: MovieAspectAnalysisRequest):
    """
    Analyze movie reviews at aspect/topic level.

    Returns aspect extraction + sentiment per aspect with confidence and coverage.
    """
    try:
        movie_identifier = _resolve_movie_identifier(request.movie_name, request.imdb_link)
        logger.info("Analyzing movie aspects for: %s", movie_identifier)

        movie_data, reviews = await imdb_scraper.fetch_movie_data(movie_identifier)
        if not reviews:
            raise HTTPException(status_code=404, detail="No reviews found for this movie")

        prepared_reviews = _prepare_review_inputs(reviews)
        if not prepared_reviews:
            raise HTTPException(status_code=404, detail="No usable review text was found for this movie")

        max_aspects = max(3, min(30, request.max_aspects or 12))
        min_aspect_mentions = max(1, min(10, request.min_aspect_mentions or 2))

        aspect_summary, review_aspect_map = aspect_sentiment_analyzer.analyze_reviews(
            prepared_reviews,
            sentiment_analyzer=sentiment_analyzer,
            max_aspects=max_aspects,
            min_aspect_mentions=min_aspect_mentions,
        )

        review_aspects: List[ReviewAspectResult] = []
        if request.include_review_mentions:
            for review in prepared_reviews[:30]:
                text = review["text"]
                mentions = [
                    MovieAspectMention(**mention)
                    for mention in review_aspect_map.get(text, [])
                ]
                if mentions:
                    review_aspects.append(
                        ReviewAspectResult(
                            text=text,
                            aspect_mentions=mentions,
                        )
                    )

        return MovieAspectAnalysisResponse(
            movie_title=movie_data["title"],
            movie_poster=movie_data["poster"],
            imdb_rating=movie_data["rating"],
            review_count=len(prepared_reviews),
            aspect_sentiment=AspectSentimentSummary(**aspect_summary),
            review_aspects=review_aspects,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Validation error analyzing movie aspects: %s", str(e))
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Error analyzing movie aspects: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="Unable to run aspect analysis right now. Please try again in a moment.",
        )


@app.post("/analyze-youtube", response_model=YouTubeAnalysisResponse)
async def analyze_youtube_video(request: YouTubeAnalysisRequest):
    """
    Analyze YouTube video audience sentiment from comments + engagement stats.

    Parameters:
    - youtube_url: Any supported YouTube video URL or raw video ID
    - max_comments: Number of comments to analyze (max 100)
    """
    try:
        youtube_url = (request.youtube_url or "").strip()
        if not youtube_url:
            raise HTTPException(status_code=400, detail="Please provide a YouTube video URL.")

        if not youtube_analyzer.api_key:
            raise HTTPException(
                status_code=503,
                detail="YouTube API key is not configured on the backend.",
            )

        requested_comments = request.max_comments or 100
        requested_comments = max(10, min(100, requested_comments))

        logger.info("Analyzing YouTube video input: %s", youtube_url)

        result = await asyncio.to_thread(
            youtube_analyzer.analyze_video,
            youtube_url,
            sentiment_analyzer,
            requested_comments,
        )
        return YouTubeAnalysisResponse(**result)

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Validation error analyzing YouTube video: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error analyzing YouTube video: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="Unable to fetch YouTube analysis right now. Please try again in a moment.",
        )


@app.post("/analyze-product", response_model=ProductAnalysisResponse)
async def analyze_product(request: ProductAnalysisRequest):
    """
    Analyze real marketplace product sentiment using ratings, review comments, and store signals.

    Parameters:
    - product_query: Product name/model (e.g., "iPhone 15 128GB")
    - marketplace: "amazon", "flipkart", or "any"
    - max_comments: Number of review snippets to analyze (15-120)
    """
    try:
        query = (request.product_query or "").strip()
        if not query:
            raise HTTPException(status_code=400, detail="Please provide a product query.")

        if not product_analyzer.api_key:
            raise HTTPException(
                status_code=503,
                detail="SERPAPI_KEY is not configured on the backend.",
            )

        requested_comments = request.max_comments or 60
        requested_comments = max(15, min(120, requested_comments))

        logger.info("Analyzing product query: %s (marketplace=%s)", query, request.marketplace or "any")

        result = await asyncio.to_thread(
            product_analyzer.analyze_product,
            query,
            sentiment_analyzer,
            request.marketplace or "any",
            requested_comments,
        )
        return ProductAnalysisResponse(**result)

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Validation error analyzing product: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error analyzing product: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="Unable to fetch product analysis right now. Please try again in a moment.",
        )


@app.post("/compare/movie", response_model=ComparisonResponse)
async def compare_movies(request: MovieComparisonRequest):
    """Compare movie sentiment, emotion, rating, and aspect-level performance."""
    try:
        left_identifier = _resolve_movie_identifier(request.left.movie_name, request.left.imdb_link)
        right_identifier = _resolve_movie_identifier(request.right.movie_name, request.right.imdb_link)

        max_aspects = max(3, min(30, request.max_aspects or 12))
        min_aspect_mentions = max(1, min(10, request.min_aspect_mentions or 2))

        left_task = analyze_movie(
            MovieAnalysisRequest(
                movie_name=request.left.movie_name,
                imdb_link=request.left.imdb_link,
                include_aspects=True,
                max_aspects=max_aspects,
                min_aspect_mentions=min_aspect_mentions,
            )
        )
        right_task = analyze_movie(
            MovieAnalysisRequest(
                movie_name=request.right.movie_name,
                imdb_link=request.right.imdb_link,
                include_aspects=True,
                max_aspects=max_aspects,
                min_aspect_mentions=min_aspect_mentions,
            )
        )
        left_result, right_result = await asyncio.gather(left_task, right_task)

        left_data = _model_to_dict(left_result)
        right_data = _model_to_dict(right_result)

        left_entity = comparison_engine.build_entity_payload(
            label=left_data.get("movie_title") or left_identifier,
            source_type="movie",
            sentiment_percentages=left_data.get("sentiment_percentages") or {},
            emotion_scores=left_data.get("emotion_scores") or {},
            aspect_sentiment=left_data.get("aspect_sentiment") or aspect_sentiment_analyzer.empty_summary(),
            metrics={
                "imdb_rating": left_data.get("imdb_rating", 0.0),
                "positive_sentiment": (left_data.get("sentiment_percentages") or {}).get("positive", 0.0),
                "emotional_resonance": comparison_engine.derive_emotional_resonance(
                    left_data.get("emotion_scores") or {}
                ),
                "aspect_confidence": comparison_engine.aspect_confidence_percent(
                    left_data.get("aspect_sentiment") or {}
                ),
            },
            metadata={
                "review_count": left_data.get("review_count", 0),
                "top_keywords": left_data.get("top_keywords") or [],
                "verdict": left_data.get("verdict", ""),
                "movie_poster": left_data.get("movie_poster", ""),
            },
        )

        right_entity = comparison_engine.build_entity_payload(
            label=right_data.get("movie_title") or right_identifier,
            source_type="movie",
            sentiment_percentages=right_data.get("sentiment_percentages") or {},
            emotion_scores=right_data.get("emotion_scores") or {},
            aspect_sentiment=right_data.get("aspect_sentiment") or aspect_sentiment_analyzer.empty_summary(),
            metrics={
                "imdb_rating": right_data.get("imdb_rating", 0.0),
                "positive_sentiment": (right_data.get("sentiment_percentages") or {}).get("positive", 0.0),
                "emotional_resonance": comparison_engine.derive_emotional_resonance(
                    right_data.get("emotion_scores") or {}
                ),
                "aspect_confidence": comparison_engine.aspect_confidence_percent(
                    right_data.get("aspect_sentiment") or {}
                ),
            },
            metadata={
                "review_count": right_data.get("review_count", 0),
                "top_keywords": right_data.get("top_keywords") or [],
                "verdict": right_data.get("verdict", ""),
                "movie_poster": right_data.get("movie_poster", ""),
            },
        )

        comparison = comparison_engine.compare("movie", left_entity, right_entity)
        return ComparisonResponse(
            domain="movie",
            left_entity=left_entity,
            right_entity=right_entity,
            comparison=comparison,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Validation error comparing movies: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error comparing movies: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="Unable to compare movies right now. Please try again in a moment.",
        )


@app.post("/compare/product", response_model=ComparisonResponse)
async def compare_products(request: ProductComparisonRequest):
    """Compare product sentiment, ratings, verdict scores, and aspect-level signals."""
    try:
        left_query = (request.left.product_query or "").strip()
        right_query = (request.right.product_query or "").strip()
        if not left_query or not right_query:
            raise HTTPException(status_code=400, detail="Please provide both product queries.")

        if not product_analyzer.api_key:
            raise HTTPException(
                status_code=503,
                detail="SERPAPI_KEY is not configured on the backend.",
            )

        max_comments = max(15, min(120, request.max_comments or 60))
        max_aspects = max(3, min(30, request.max_aspects or 12))
        min_aspect_mentions = max(1, min(10, request.min_aspect_mentions or 2))

        left_task = analyze_product(
            ProductAnalysisRequest(
                product_query=left_query,
                marketplace=request.left.marketplace or "any",
                max_comments=max_comments,
            )
        )
        right_task = analyze_product(
            ProductAnalysisRequest(
                product_query=right_query,
                marketplace=request.right.marketplace or "any",
                max_comments=max_comments,
            )
        )
        left_result, right_result = await asyncio.gather(left_task, right_task)

        left_data = _model_to_dict(left_result)
        right_data = _model_to_dict(right_result)

        left_aspects = _build_aspect_summary_from_rows(
            rows=left_data.get("reviews") or [],
            text_key="text",
            rating_key="rating",
            max_aspects=max_aspects,
            min_aspect_mentions=min_aspect_mentions,
        )
        right_aspects = _build_aspect_summary_from_rows(
            rows=right_data.get("reviews") or [],
            text_key="text",
            rating_key="rating",
            max_aspects=max_aspects,
            min_aspect_mentions=min_aspect_mentions,
        )

        left_entity = comparison_engine.build_entity_payload(
            label=left_data.get("product_title") or left_query,
            source_type="product",
            sentiment_percentages=left_data.get("sentiment_percentages") or {},
            emotion_scores=left_data.get("emotion_scores") or {},
            aspect_sentiment=left_aspects,
            metrics={
                "rating": left_data.get("rating", 0.0),
                "buy_signal_score": left_data.get("buy_signal_score", 0.0),
                "real_verdict_score": left_data.get("real_verdict_score", 0.0),
                "positive_sentiment": (left_data.get("sentiment_percentages") or {}).get("positive", 0.0),
                "negative_sentiment": (left_data.get("sentiment_percentages") or {}).get("negative", 0.0),
            },
            metadata={
                "price": left_data.get("price", ""),
                "primary_store": left_data.get("primary_store", ""),
                "review_count": left_data.get("review_count", 0),
                "offers_count": left_data.get("offers_count", 0),
                "verdict": left_data.get("verdict", ""),
                "thumbnail_url": left_data.get("thumbnail_url", ""),
                "product_url": left_data.get("product_url", ""),
            },
        )

        right_entity = comparison_engine.build_entity_payload(
            label=right_data.get("product_title") or right_query,
            source_type="product",
            sentiment_percentages=right_data.get("sentiment_percentages") or {},
            emotion_scores=right_data.get("emotion_scores") or {},
            aspect_sentiment=right_aspects,
            metrics={
                "rating": right_data.get("rating", 0.0),
                "buy_signal_score": right_data.get("buy_signal_score", 0.0),
                "real_verdict_score": right_data.get("real_verdict_score", 0.0),
                "positive_sentiment": (right_data.get("sentiment_percentages") or {}).get("positive", 0.0),
                "negative_sentiment": (right_data.get("sentiment_percentages") or {}).get("negative", 0.0),
            },
            metadata={
                "price": right_data.get("price", ""),
                "primary_store": right_data.get("primary_store", ""),
                "review_count": right_data.get("review_count", 0),
                "offers_count": right_data.get("offers_count", 0),
                "verdict": right_data.get("verdict", ""),
                "thumbnail_url": right_data.get("thumbnail_url", ""),
                "product_url": right_data.get("product_url", ""),
            },
        )

        comparison = comparison_engine.compare("product", left_entity, right_entity)
        return ComparisonResponse(
            domain="product",
            left_entity=left_entity,
            right_entity=right_entity,
            comparison=comparison,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Validation error comparing products: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error comparing products: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="Unable to compare products right now. Please try again in a moment.",
        )


@app.post("/compare/youtube", response_model=ComparisonResponse)
async def compare_youtube_targets(request: YouTubeComparisonRequest):
    """Compare YouTube video/channel targets on sentiment, safety, and engagement."""
    try:
        left_input = (request.left.target_input or "").strip()
        right_input = (request.right.target_input or "").strip()
        if not left_input or not right_input:
            raise HTTPException(status_code=400, detail="Please provide both YouTube targets.")

        if not youtube_analyzer.api_key:
            raise HTTPException(
                status_code=503,
                detail="YouTube API key is not configured on the backend.",
            )

        max_comments = max(20, min(100, request.max_comments or 80))
        max_videos = max(2, min(10, request.max_videos or 6))
        max_aspects = max(3, min(30, request.max_aspects or 12))
        min_aspect_mentions = max(1, min(10, request.min_aspect_mentions or 2))

        left_task = asyncio.to_thread(
            youtube_analyzer.analyze_target,
            left_input,
            sentiment_analyzer,
            max_comments,
            max_videos,
        )
        right_task = asyncio.to_thread(
            youtube_analyzer.analyze_target,
            right_input,
            sentiment_analyzer,
            max_comments,
            max_videos,
        )
        left_data, right_data = await asyncio.gather(left_task, right_task)

        left_aspects = _build_aspect_summary_from_rows(
            rows=left_data.get("comments") or [],
            text_key="text",
            max_aspects=max_aspects,
            min_aspect_mentions=min_aspect_mentions,
        )
        right_aspects = _build_aspect_summary_from_rows(
            rows=right_data.get("comments") or [],
            text_key="text",
            max_aspects=max_aspects,
            min_aspect_mentions=min_aspect_mentions,
        )

        left_safety = left_data.get("content_safety") or {}
        right_safety = right_data.get("content_safety") or {}

        left_label = left_data.get("video_title") or left_data.get("channel_title") or left_input
        right_label = right_data.get("video_title") or right_data.get("channel_title") or right_input

        left_entity = comparison_engine.build_entity_payload(
            label=left_label,
            source_type=left_data.get("source_type") or "youtube",
            sentiment_percentages=left_data.get("sentiment_percentages") or {},
            emotion_scores=left_data.get("emotion_scores") or {},
            aspect_sentiment=left_aspects,
            metrics={
                "rating": left_data.get("rating", 0.0),
                "positive_sentiment": (left_data.get("sentiment_percentages") or {}).get("positive", 0.0),
                "engagement_rate": left_data.get("engagement_rate", 0.0),
                "toxicity_percentage": left_safety.get("toxicity_percentage", 0.0),
                "spam_percentage": left_safety.get("spam_percentage", 0.0),
                "like_ratio": left_data.get("like_ratio", 0.0),
            },
            metadata={
                "channel_title": left_data.get("channel_title", ""),
                "video_url": left_data.get("video_url", ""),
                "comments_analyzed": left_data.get("comments_analyzed", 0),
                "view_count": left_data.get("view_count", 0),
                "like_count": left_data.get("like_count", 0),
                "comment_count": left_data.get("comment_count", 0),
                "toxicity_level": ((left_safety.get("safety_report") or {}).get("toxicity_level")),
                "spam_level": ((left_safety.get("safety_report") or {}).get("spam_level")),
                "verdict": left_data.get("verdict", ""),
                "thumbnail_url": left_data.get("thumbnail_url", ""),
            },
        )

        right_entity = comparison_engine.build_entity_payload(
            label=right_label,
            source_type=right_data.get("source_type") or "youtube",
            sentiment_percentages=right_data.get("sentiment_percentages") or {},
            emotion_scores=right_data.get("emotion_scores") or {},
            aspect_sentiment=right_aspects,
            metrics={
                "rating": right_data.get("rating", 0.0),
                "positive_sentiment": (right_data.get("sentiment_percentages") or {}).get("positive", 0.0),
                "engagement_rate": right_data.get("engagement_rate", 0.0),
                "toxicity_percentage": right_safety.get("toxicity_percentage", 0.0),
                "spam_percentage": right_safety.get("spam_percentage", 0.0),
                "like_ratio": right_data.get("like_ratio", 0.0),
            },
            metadata={
                "channel_title": right_data.get("channel_title", ""),
                "video_url": right_data.get("video_url", ""),
                "comments_analyzed": right_data.get("comments_analyzed", 0),
                "view_count": right_data.get("view_count", 0),
                "like_count": right_data.get("like_count", 0),
                "comment_count": right_data.get("comment_count", 0),
                "toxicity_level": ((right_safety.get("safety_report") or {}).get("toxicity_level")),
                "spam_level": ((right_safety.get("safety_report") or {}).get("spam_level")),
                "verdict": right_data.get("verdict", ""),
                "thumbnail_url": right_data.get("thumbnail_url", ""),
            },
        )

        comparison = comparison_engine.compare("youtube", left_entity, right_entity)
        return ComparisonResponse(
            domain="youtube",
            left_entity=left_entity,
            right_entity=right_entity,
            comparison=comparison,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Validation error comparing YouTube targets: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error comparing YouTube targets: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="Unable to compare YouTube targets right now. Please try again in a moment.",
        )

@app.get("/recent-searches")
async def get_recent_searches():
    """Get recently analyzed movies"""
    # This would typically fetch from a database
    # For now, returning empty list
    return {"recent_searches": []}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

import uvicorn
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
