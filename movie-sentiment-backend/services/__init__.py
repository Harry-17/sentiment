# Services Package
from services.sentiment_analyzer import SentimentAnalyzer
from services.aspect_sentiment_analyzer import AspectSentimentAnalyzer
from services.comparison_engine import ComparisonEngine
from services.imdb_scraper import IMDbScraper
from services.verdict_generator import VerdictGenerator

__all__ = [
    'SentimentAnalyzer',
    'AspectSentimentAnalyzer',
    'ComparisonEngine',
    'IMDbScraper',
    'VerdictGenerator',
]
