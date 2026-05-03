# Movie Sentiment Analyzer - Full Stack Application

A comprehensive full-stack web application for analyzing movie sentiments using AI. The system fetches reviews from IMDb, performs sentiment and emotion analysis, and generates intelligent verdicts about movies.

## 🎯 Features

### Core Functionality
- 🔍 **Movie Search**: Find movies by name or IMDb link
- 📊 **Sentiment Analysis**: AI-powered sentiment classification (positive/negative/neutral)
- 😊 **Emotion Detection**: Identify 6 emotions (joy, sadness, anger, fear, surprise, neutral)
- 🎯 **LIME Explainability**: Understand which words influence sentiment
- 🏆 **AI Verdict**: Generate intelligent recommendations based on analysis
- 📈 **Rich Visualizations**: Pie charts, bar charts, and keyword highlighting

### Pages
1. **Home Page**: Search interface with feature highlights
2. **Results Dashboard**: Comprehensive analytics with charts and verdict
3. **Review Analysis**: Detailed review breakdown with sentiment and emotion tags
4. **Responsive Design**: Works on desktop, tablet, and mobile

## 🧱 Tech Stack

### Backend
- **FastAPI**: Modern async Python web framework
- **Transformers (Hugging Face)**: DistilBERT for sentiment & emotion analysis
- **LIME**: Local Interpretable Model-Agnostic Explanations
- **BeautifulSoup**: Web scraping for IMDb data
- **Pandas**: Data processing and aggregation

### Frontend
- **React 18**: Modern UI library with hooks
- **React Router**: Multi-page navigation
- **Recharts**: Interactive data visualization
- **Tailwind CSS**: Utility-first styling
- **Vite**: Lightning-fast build tool
- **Lucide Icons**: Beautiful SVG icons

## 📁 Project Structure

```
movie-sentiment-analyzer/
├── movie-sentiment-backend/
│   ├── main.py                    # FastAPI app
│   ├── requirements.txt           # Python dependencies
│   ├── services/
│   │   ├── sentiment_analyzer.py  # DistilBERT + emotions + LIME
│   │   ├── imdb_scraper.py        # IMDb data fetching
│   │   └── verdict_generator.py   # AI verdict logic
│   └── README.md
│
└── movie-sentiment-frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── Home.jsx           # Search & landing page
    │   │   ├── Results.jsx        # Analytics dashboard
    │   │   └── Reviews.jsx        # Detailed review analysis
    │   ├── services/
    │   │   └── api.js             # API communication
    │   ├── App.jsx                # Main app component
    │   ├── main.jsx               # React entry point
    │   └── index.css              # Tailwind styles
    ├── index.html                 # HTML template
    ├── vite.config.js             # Vite configuration
    ├── tailwind.config.js         # Tailwind configuration
    ├── package.json               # Node dependencies
    └── README.md
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+ and npm
- 8GB RAM (for ML models)

### Backend Setup

```bash
cd movie-sentiment-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
python main.py
```

Backend runs on `http://localhost:8000`

### Frontend Setup

```bash
cd movie-sentiment-frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs on `http://localhost:3000`

## 📚 API Documentation

### POST /analyze
Analyzes a movie and returns comprehensive sentiment data.

**Request:**
```json
{
  "movie_name": "The Shawshank Redemption",
  "imdb_link": null
}
```

**Response:**
```json
{
  "movie_title": "The Shawshank Redemption",
  "movie_poster": "https://...",
  "imdb_rating": 9.3,
  "review_count": 100,
  "overall_sentiment": "positive",
  "sentiment_percentages": {
    "positive": 78.0,
    "negative": 12.0,
    "neutral": 10.0
  },
  "emotion_scores": {
    "joy": 0.45,
    "sadness": 0.25,
    "anger": 0.08,
    "fear": 0.05,
    "surprise": 0.12,
    "neutral": 0.05
  },
  "top_keywords": ["inspiring", "excellent", "masterpiece", "powerful", "moving"],
  "reviews": [...],
  "verdict": "🎬 Highly Recommended",
  "verdict_explanation": "78% of users loved this movie..."
}
```

## 🤖 AI Models

### Sentiment Analysis
- **Model**: `distilbert-base-uncased-finetuned-sst-2-english`
- **Task**: Binary classification (positive/negative)
- **Size**: 268MB, optimized DistilBERT

### Emotion Detection
- **Model**: `j-hartmann/emotion-english-distilroberta-base`
- **Task**: Multi-label emotion classification
- **Emotions**: Joy, Sadness, Anger, Fear, Surprise, Neutral

### Explainability
- **Method**: LIME (Local Interpretable Model-Agnostic Explanations)
- **Purpose**: Highlight key words influencing sentiment

## 🎨 UI Features

- **Glassmorphism Design**: Modern frosted glass effect
- **Gradient Backgrounds**: Purple, blue, and dark color scheme
- **Responsive Charts**: Interactive Recharts visualizations
- **Dark Mode**: Eye-friendly dark interface
- **Smooth Animations**: Transitions and hover effects
- **Loading States**: Skeleton screens and spinners

## 📊 Data Processing Pipeline

1. **Input**: Movie name or IMDb link
2. **Scraping**: Fetch movie data and reviews from IMDb
3. **Preprocessing**: Clean and tokenize text
4. **Sentiment**: Classify each review (positive/negative/neutral)
5. **Emotions**: Detect 6 emotion categories
6. **Explainability**: Extract important words using LIME
7. **Aggregation**: Calculate percentages and scores
8. **Verdict**: Generate AI recommendation based on analysis
9. **Output**: Rich dashboard with visualizations

## 🔧 Customization

### Add New Emotions
Edit `services/sentiment_analyzer.py`:
```python
self.emotion_pipe = pipeline(
    "text-classification",
    model="your-custom-emotion-model",  # Change model
)
```

### Modify Verdict Logic
Edit `services/verdict_generator.py`:
```python
if positive_pct >= 70:
    verdict = "Your custom verdict"  # Customize
```

### Update UI Colors
Edit `movie-sentiment-frontend/tailwind.config.js`:
```javascript
colors: {
  purple: {...},  // Customize color palette
}
```

## ⚙️ Performance Optimizations

- **Model Caching**: Models are cached after first download
- **Async Operations**: FastAPI uses async/await for concurrency
- **Batch Processing**: Process multiple reviews efficiently
- **Frontend Optimization**: Lazy loading, code splitting with Vite
- **GPU Support**: Automatic CUDA detection for faster inference

## 🐛 Troubleshooting

### Backend Issues
```bash
# Check if models download correctly
python -c "from transformers import pipeline; pipeline('sentiment-analysis')"

# Use CPU if GPU not available
# Models auto-detect, but can force with: device=-1
```

### Frontend Issues
```bash
# Clear node_modules and reinstall
rm -rf node_modules
npm install

# Check if backend is running
curl http://localhost:8000/health
```

## 📦 Deployment

### Backend (Docker)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

### Frontend (Vercel/Netlify)
```bash
npm run build
# Deploy 'dist' folder to your hosting provider
```

## 📄 License

MIT License - Feel free to use for personal and commercial projects

## 🤝 Contributing

Contributions welcome! Please submit pull requests or open issues for bugs/features.

## 📞 Support

For issues or questions:
1. Check existing GitHub issues
2. Review the README and code comments
3. Test with mock data first

## 🎓 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Hugging Face Transformers](https://huggingface.co/transformers/)
- [LIME Documentation](https://lime-ml.readthedocs.io/)
- [React Documentation](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)

---

**Built with ❤️ using React, FastAPI, and AI**
