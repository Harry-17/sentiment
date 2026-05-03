# Movie Sentiment Backend

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the FastAPI server:
```bash
python main.py
```

API base URL: `http://localhost:8000`

## API Endpoints

- `GET /`: Health check
- `POST /analyze`: Full movie analysis
  - Input: `movie_name` or `imdb_link`
  - Output: review sentiment, emotion scores, aspect-based sentiment, keywords, verdict
- `POST /analyze/aspects`: Aspect-only movie analysis
  - Input: `movie_name` or `imdb_link`
  - Output: extracted aspects/topics, per-aspect sentiment, confidence, coverage
- `POST /analyze-youtube`: YouTube audience sentiment analysis
- `POST /analyze-product`: Product sentiment and verdict analysis
- `POST /compare/movie`: Movie vs movie comparative analysis
- `POST /compare/product`: Product vs product comparative analysis
- `POST /compare/youtube`: YouTube video/channel vs video/channel comparison
- `GET /recent-searches`: Placeholder endpoint
- `GET /health`: Health check

## Features

- Transformer-based sentiment classification (with graceful fallback heuristics)
- Emotion classification
- Aspect-based sentiment analysis (acting, story, pacing, cinematography, etc.)
- Cross-entity comparative analysis with normalized metric scoring and winner indicators
- TF-IDF phrase mining + canonical aspect mapping
- Sentence-level aspect sentiment scoring
- Confidence scoring and coverage aggregation
- IMDb metadata and review ingestion
- Verdict generation from aggregate sentiment/emotions

## Architecture

```text
services/
├── sentiment_analyzer.py          # DistilBERT sentiment + emotion + keyword explanations
├── aspect_sentiment_analyzer.py   # Aspect extraction + aspect-level sentiment/confidence
├── imdb_scraper.py                # IMDb metadata/review fetching
├── verdict_generator.py           # Verdict and explanation generation
├── youtube_analyzer.py            # YouTube analysis pipeline
└── product_analyzer.py            # Product analysis pipeline
main.py                            # FastAPI routes and response models
```

## Notes

- Models may download on first run (internet required for first-time model fetch).
- The system automatically falls back to lightweight heuristics if model loading fails.
- Aspect analysis can be tuned per request with:
  - `max_aspects`
  - `min_aspect_mentions`
  - `include_aspects`
