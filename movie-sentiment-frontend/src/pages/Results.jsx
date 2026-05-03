import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  PieChart,
  Pie,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { ThumbsUp, ThumbsDown, Sparkles, ArrowLeft, Share2 } from 'lucide-react';

export default function Results() {
  const location = useLocation();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get data from location state or sessionStorage
    const analysisData = location.state?.data || JSON.parse(sessionStorage.getItem('analysisResult'));
    
    if (analysisData) {
      setData(analysisData);
      setLoading(false);
    } else {
      navigate('/movie');
    }
  }, [location, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-black flex items-center justify-center">
        <div className="text-center">
          <Sparkles className="w-12 h-12 text-purple-400 animate-spin mx-auto mb-4" />
          <p className="text-white text-lg">Loading analysis...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-black flex items-center justify-center">
        <p className="text-white">No data available. Please search for a movie.</p>
      </div>
    );
  }

  const sentimentData = [
    { name: 'Positive', value: data.sentiment_percentages.positive, fill: '#10b981' },
    { name: 'Negative', value: data.sentiment_percentages.negative, fill: '#ef4444' },
    { name: 'Neutral', value: data.sentiment_percentages.neutral || 0, fill: '#6b7280' },
  ];

  const emotionData = Object.entries(data.emotion_scores).map(([emotion, score]) => ({
    emotion: emotion.charAt(0).toUpperCase() + emotion.slice(1),
    score: Math.round(score * 100),
  }));

  const aspectRows = data.aspect_sentiment?.aspects || [];

  const getAspectSentimentBadge = (sentiment) => {
    if (sentiment === 'positive') {
      return 'bg-green-500 bg-opacity-20 text-green-200 border-green-400 border-opacity-40';
    }
    if (sentiment === 'negative') {
      return 'bg-red-500 bg-opacity-20 text-red-200 border-red-400 border-opacity-40';
    }
    return 'bg-gray-500 bg-opacity-20 text-gray-200 border-gray-400 border-opacity-40';
  };

  const getVerdictColor = (verdict) => {
    if (verdict.includes('Highly Recommended')) return 'from-green-500 to-emerald-500';
    if (verdict.includes('Recommended')) return 'from-blue-500 to-cyan-500';
    if (verdict.includes('Mixed')) return 'from-yellow-500 to-orange-500';
    if (verdict.includes('Not Recommended')) return 'from-red-500 to-pink-500';
    return 'from-purple-500 to-pink-500';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-black">
      {/* Navigation */}
      <nav className="bg-black bg-opacity-40 backdrop-blur-md border-b border-purple-500 border-opacity-20">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <button
            onClick={() => navigate('/movie')}
            className="flex items-center gap-2 text-purple-300 hover:text-purple-100 transition"
          >
            <ArrowLeft className="w-5 h-5" />
            Back to Home
          </button>
          <div className="flex items-center gap-3">
            <Sparkles className="w-6 h-6 text-purple-400" />
            <h1 className="text-xl font-bold text-white">Results</h1>
          </div>
          <button className="text-purple-300 hover:text-purple-100 transition flex items-center gap-2">
            <Share2 className="w-5 h-5" />
            Share
          </button>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-4 py-12">
        {/* Movie Header */}
        <div className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-8 border border-purple-400 border-opacity-20 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-start">
            {/* Movie Poster */}
            <div className="md:col-span-1">
              {data.movie_poster && (
                <img
                  src={data.movie_poster}
                  alt={data.movie_title}
                  className="w-full rounded-lg shadow-lg"
                  onError={(e) => {
                    e.target.src = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22300%22%3E%3Crect fill=%22%236b7280%22 width=%22200%22 height=%22300%22/%3E%3C/svg%3E';
                  }}
                />
              )}
            </div>

            {/* Movie Info */}
            <div className="md:col-span-3">
              <h2 className="text-4xl font-bold text-white mb-4">{data.movie_title}</h2>
              
              <div className="flex items-center gap-8 mb-6">
                <div>
                  <p className="text-purple-300 text-sm">IMDb Rating</p>
                  <p className="text-3xl font-bold text-yellow-400">{data.imdb_rating}</p>
                </div>
                <div>
                  <p className="text-purple-300 text-sm">Reviews Analyzed</p>
                  <p className="text-3xl font-bold text-purple-300">{data.review_count}</p>
                </div>
              </div>

              {/* Verdict Card */}
              <div className={`bg-gradient-to-r ${getVerdictColor(data.verdict)} rounded-xl p-6 text-white`}>
                <p className="text-sm opacity-90 mb-2">AI VERDICT</p>
                <h3 className="text-3xl font-bold mb-3">{data.verdict}</h3>
                <p className="text-lg opacity-95">{data.verdict_explanation}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Analytics Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Sentiment Distribution */}
          <div className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border border-purple-400 border-opacity-20">
            <h3 className="text-xl font-semibold text-white mb-6">Sentiment Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={sentimentData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {sentimentData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => `${value}%`} />
              </PieChart>
            </ResponsiveContainer>
            
            <div className="grid grid-cols-3 gap-4 mt-6">
              <div className="text-center">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <ThumbsUp className="w-5 h-5 text-green-400" />
                  <span className="text-green-400 font-bold">
                    {data.sentiment_percentages.positive}%
                  </span>
                </div>
                <p className="text-purple-300 text-sm">Positive</p>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <ThumbsDown className="w-5 h-5 text-red-400" />
                  <span className="text-red-400 font-bold">
                    {data.sentiment_percentages.negative}%
                  </span>
                </div>
                <p className="text-purple-300 text-sm">Negative</p>
              </div>
              <div className="text-center">
                <span className="text-gray-400 font-bold text-lg">
                  {data.sentiment_percentages.neutral || 0}%
                </span>
                <p className="text-purple-300 text-sm">Neutral</p>
              </div>
            </div>
          </div>

          {/* Emotion Breakdown */}
          <div className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border border-purple-400 border-opacity-20">
            <h3 className="text-xl font-semibold text-white mb-6">Emotion Breakdown</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={emotionData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(168,85,247,0.2)" />
                <XAxis dataKey="emotion" stroke="rgba(168,85,247,0.5)" />
                <YAxis stroke="rgba(168,85,247,0.5)" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    border: '1px solid rgba(168,85,247,0.5)',
                    borderRadius: '8px',
                  }}
                  formatter={(value) => `${value}%`}
                />
                <Bar dataKey="score" fill="#a855f7" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Key Keywords */}
        <div className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border border-purple-400 border-opacity-20 mb-8">
          <h3 className="text-xl font-semibold text-white mb-6">Key Words Influencing Sentiment</h3>
          <div className="flex flex-wrap gap-3">
            {data.top_keywords.map((keyword, index) => (
              <span
                key={index}
                className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full text-white font-medium hover:shadow-lg transition"
              >
                {keyword}
              </span>
            ))}
          </div>
        </div>

        {aspectRows.length > 0 && (
          <div className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border border-purple-400 border-opacity-20 mb-8">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-6">
              <h3 className="text-xl font-semibold text-white">Aspect-Based Sentiment</h3>
              <p className="text-purple-200 text-sm">
                Coverage: {data.aspect_sentiment?.coverage_percentage || 0}% | Aspects: {data.aspect_sentiment?.aspects_detected || 0}
              </p>
            </div>

            <div className="space-y-4">
              {aspectRows.slice(0, 8).map((aspect) => (
                <div
                  key={aspect.aspect}
                  className="rounded-xl border border-purple-300 border-opacity-20 bg-black bg-opacity-20 p-4"
                >
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-3">
                    <div>
                      <h4 className="text-white font-semibold text-lg">{aspect.aspect}</h4>
                      <p className="text-purple-200 text-sm">Mentions: {aspect.mentions}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`px-3 py-1 rounded-full border text-xs font-semibold uppercase tracking-wide ${getAspectSentimentBadge(aspect.sentiment)}`}>
                        {aspect.sentiment}
                      </span>
                      <span className="text-purple-100 text-sm">
                        Confidence: {Math.round((aspect.confidence || 0) * 100)}%
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2 mb-3">
                    {(aspect.representative_keywords || []).map((keyword) => (
                      <span
                        key={`${aspect.aspect}-${keyword}`}
                        className="px-2 py-1 rounded-full bg-purple-500 bg-opacity-20 border border-purple-300 border-opacity-30 text-purple-100 text-xs"
                      >
                        {keyword}
                      </span>
                    ))}
                  </div>

                  {aspect.example_snippets?.[0] && (
                    <p className="text-purple-100 text-sm italic">"{aspect.example_snippets[0]}"</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-4">
          <button
            onClick={() => navigate('/reviews')}
            className="flex-1 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white py-3 rounded-lg font-semibold transition transform hover:scale-105"
          >
            View Detailed Reviews
          </button>
          <button
            onClick={() => navigate('/movie')}
            className="flex-1 bg-white bg-opacity-10 hover:bg-opacity-20 border border-purple-400 border-opacity-50 text-purple-200 py-3 rounded-lg font-semibold transition"
          >
            Analyze Another Movie
          </button>
        </div>
      </div>
    </div>
  );
}
