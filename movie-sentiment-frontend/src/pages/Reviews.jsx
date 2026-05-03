import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { MessageSquare, ThumbsUp, ThumbsDown, ArrowLeft, Sparkles } from 'lucide-react';

export default function Reviews() {
  const location = useLocation();
  const navigate = useNavigate();
  const [reviews, setReviews] = useState([]);
  const [movieTitle, setMovieTitle] = useState('');
  const [filterSentiment, setFilterSentiment] = useState('all');

  useEffect(() => {
    const analysisData = location.state?.data || JSON.parse(sessionStorage.getItem('analysisResult'));
    
    if (analysisData) {
      setReviews(analysisData.reviews || []);
      setMovieTitle(analysisData.movie_title);
    } else {
      navigate('/movie');
    }
  }, [location, navigate]);

  const filteredReviews = reviews.filter((review) => {
    if (filterSentiment === 'all') return true;
    return review.sentiment.toLowerCase() === filterSentiment.toLowerCase();
  });

  const getSentimentColor = (sentiment) => {
    switch (sentiment.toLowerCase()) {
      case 'positive':
        return 'from-green-500 to-emerald-500';
      case 'negative':
        return 'from-red-500 to-pink-500';
      default:
        return 'from-gray-500 to-slate-500';
    }
  };

  const getEmotionEmoji = (emotion) => {
    const emojiMap = {
      joy: '😊',
      sadness: '😢',
      anger: '😠',
      fear: '😨',
      surprise: '😲',
      neutral: '😐',
    };
    return emojiMap[emotion.toLowerCase()] || '🎬';
  };

  const escapeHtml = (value) =>
    value
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');

  const escapeRegex = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

  const highlightKeywords = (text, keywords) => {
    let highlightedText = escapeHtml(text);
    (keywords || []).forEach((keyword) => {
      const safeKeyword = escapeHtml(keyword);
      const regex = new RegExp(`\\b${escapeRegex(safeKeyword)}\\b`, 'gi');
      highlightedText = highlightedText.replace(
        regex,
        '<mark style="background-color: rgba(168,85,247,0.5); padding: 2px 4px; border-radius: 3px;">$&</mark>'
      );
    });
    return highlightedText;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-black">
      {/* Navigation */}
      <nav className="bg-black bg-opacity-40 backdrop-blur-md border-b border-purple-500 border-opacity-20 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <button
            onClick={() => navigate('/results')}
            className="flex items-center gap-2 text-purple-300 hover:text-purple-100 transition"
          >
            <ArrowLeft className="w-5 h-5" />
            Back to Results
          </button>
          <div className="flex items-center gap-3">
            <MessageSquare className="w-6 h-6 text-purple-400" />
            <h1 className="text-xl font-bold text-white">Reviews</h1>
          </div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h2 className="text-4xl font-bold text-white mb-4">{movieTitle}</h2>
          <p className="text-purple-200 mb-6">
            Analyzing {reviews.length} reviews with AI-powered sentiment and emotion detection
          </p>

          {/* Filter Buttons */}
          <div className="flex gap-3 flex-wrap">
            {['all', 'positive', 'negative', 'neutral'].map((sentiment) => (
              <button
                key={sentiment}
                onClick={() => setFilterSentiment(sentiment)}
                className={`px-6 py-2 rounded-lg font-semibold transition ${
                  filterSentiment === sentiment
                    ? 'bg-purple-500 text-white'
                    : 'bg-white bg-opacity-10 text-purple-200 hover:bg-opacity-20'
                }`}
              >
                {sentiment === 'all'
                  ? `All Reviews (${reviews.length})`
                  : `${sentiment.charAt(0).toUpperCase() + sentiment.slice(1)} (${
                      reviews.filter((r) => r.sentiment.toLowerCase() === sentiment).length
                    })`}
              </button>
            ))}
          </div>
        </div>

        {/* Reviews List */}
        <div className="space-y-4">
          {filteredReviews.length > 0 ? (
            filteredReviews.map((review, index) => (
              <div
                key={index}
                className="bg-white bg-opacity-5 backdrop-blur-lg rounded-xl p-6 border border-purple-400 border-opacity-20 hover:border-opacity-40 transition"
              >
                {/* Review Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div
                      className={`px-4 py-2 bg-gradient-to-r ${getSentimentColor(
                        review.sentiment
                      )} rounded-lg text-white font-semibold text-sm flex items-center gap-2`}
                    >
                      {review.sentiment.toLowerCase() === 'positive' ? (
                        <ThumbsUp className="w-4 h-4" />
                      ) : (
                        <ThumbsDown className="w-4 h-4" />
                      )}
                      {review.sentiment}
                    </div>
                    <span className="text-purple-300 text-sm">
                      Confidence: {(review.sentiment_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                {/* Review Text */}
                <p
                  className="text-purple-100 mb-4 leading-relaxed"
                  dangerouslySetInnerHTML={{
                    __html: highlightKeywords(review.text, review.important_words),
                  }}
                />

                {/* Emotions and Keywords */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Emotions */}
                  <div>
                    <p className="text-sm text-purple-300 font-semibold mb-2">Emotions Detected:</p>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(review.emotions || {})
                        .sort((a, b) => b[1] - a[1])
                        .slice(0, 3)
                        .map(([emotion, score]) => (
                          <span
                            key={emotion}
                            className="px-3 py-1 bg-white bg-opacity-10 rounded-full text-purple-200 text-sm flex items-center gap-1"
                          >
                            {getEmotionEmoji(emotion)} {emotion} ({(score * 100).toFixed(0)}%)
                          </span>
                        ))}
                    </div>
                  </div>

                  {/* Important Words */}
                  <div>
                    <p className="text-sm text-purple-300 font-semibold mb-2">Key Words:</p>
                    <div className="flex flex-wrap gap-2">
                      {(review.important_words || []).map((word, idx) => (
                        <span
                          key={idx}
                          className="px-3 py-1 bg-purple-500 bg-opacity-30 rounded-full text-purple-200 text-sm"
                        >
                          {word}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-12">
              <Sparkles className="w-12 h-12 text-purple-400 mx-auto mb-4 opacity-50" />
              <p className="text-purple-200">No reviews found with the selected filter</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
