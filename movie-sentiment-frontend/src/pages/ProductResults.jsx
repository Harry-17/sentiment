import React, { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { ArrowLeft, ExternalLink, ShoppingBag, Sparkles, ThumbsDown, ThumbsUp } from 'lucide-react';

const numberFormatter = new Intl.NumberFormat('en-US');

export default function ProductResults() {
  const location = useLocation();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const analysisData =
      location.state?.data || JSON.parse(sessionStorage.getItem('productAnalysisResult'));

    if (analysisData) {
      setData(analysisData);
      setLoading(false);
    } else {
      navigate('/product');
    }
  }, [location, navigate]);

  const sentimentData = useMemo(() => {
    if (!data) return [];
    return [
      { name: 'Positive', value: data.sentiment_percentages.positive || 0, fill: '#22c55e' },
      { name: 'Negative', value: data.sentiment_percentages.negative || 0, fill: '#ef4444' },
      { name: 'Neutral', value: data.sentiment_percentages.neutral || 0, fill: '#94a3b8' },
    ];
  }, [data]);

  const emotionData = useMemo(() => {
    if (!data) return [];
    return Object.entries(data.emotion_scores || {}).map(([emotion, score]) => ({
      emotion: emotion.charAt(0).toUpperCase() + emotion.slice(1),
      score: Math.round(score * 100),
    }));
  }, [data]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-950 via-teal-950 to-slate-950 flex items-center justify-center">
        <div className="text-center">
          <Sparkles className="w-12 h-12 text-emerald-300 animate-spin mx-auto mb-4" />
          <p className="text-white text-lg">Loading product analysis...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-950 via-teal-950 to-slate-950 flex items-center justify-center">
        <p className="text-white">No product analysis found.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-950 via-teal-950 to-slate-950">
      <nav className="bg-black bg-opacity-35 backdrop-blur-md border-b border-emerald-400 border-opacity-20">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <button
            onClick={() => navigate('/product')}
            className="flex items-center gap-2 text-emerald-100 hover:text-white transition"
          >
            <ArrowLeft className="w-5 h-5" />
            Back to Product Search
          </button>
          <div className="flex items-center gap-3">
            <ShoppingBag className="w-6 h-6 text-emerald-300" />
            <h1 className="text-xl font-bold text-white">Product Results</h1>
          </div>
          {data.product_url ? (
            <a
              href={data.product_url}
              target="_blank"
              rel="noreferrer"
              className="text-emerald-100 hover:text-white transition flex items-center gap-2"
            >
              Open Listing
              <ExternalLink className="w-4 h-4" />
            </a>
          ) : (
            <div className="text-emerald-200 text-sm">Listing unavailable</div>
          )}
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-4 py-10">
        <div className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-7 border border-emerald-300 border-opacity-20 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="md:col-span-1">
              {data.thumbnail_url && (
                <img
                  src={data.thumbnail_url}
                  alt={data.product_title}
                  className="w-full rounded-lg shadow-lg"
                />
              )}
            </div>
            <div className="md:col-span-3">
              <h2 className="text-3xl font-bold text-white mb-2">{data.product_title}</h2>
              <p className="text-emerald-100 mb-5">
                Primary store: {data.primary_store} | Marketplace filter: {data.marketplace}
              </p>

              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
                <MetricCard label="Price" value={data.price || 'N/A'} />
                <MetricCard label="Rating" value={`${data.rating || 0}/5`} />
                <MetricCard label="Reviews" value={numberFormatter.format(data.review_count || 0)} />
                <MetricCard label="Offers" value={numberFormatter.format(data.offers_count || 0)} />
                <MetricCard label="Comments" value={numberFormatter.format(data.comments_analyzed || 0)} />
              </div>

              <div className={`rounded-xl p-6 text-white ${getVerdictStyle(data.real_verdict_score)}`}>
                <p className="text-sm opacity-90 mb-1">REAL VERDICT SCORE</p>
                <h3 className="text-4xl font-bold mb-2">{data.real_verdict_score}/10</h3>
                <p className="text-xl font-semibold mb-2">{data.verdict}</p>
                <p className="opacity-95 mb-3">{data.verdict_explanation}</p>
                <p className="text-sm opacity-90">
                  Buy Signal Score: <span className="font-semibold">{data.buy_signal_score}/100</span>
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border border-emerald-300 border-opacity-20">
            <h3 className="text-xl font-semibold text-white mb-6">Comment Sentiment</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={sentimentData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={95}
                  label={({ name, value }) => `${name}: ${value}%`}
                  labelLine={false}
                >
                  {sentimentData.map((entry, index) => (
                    <Cell key={`${entry.name}-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => `${value}%`} />
              </PieChart>
            </ResponsiveContainer>

            <div className="grid grid-cols-3 gap-4 mt-4">
              <div className="text-center">
                <div className="flex items-center justify-center gap-2 mb-1">
                  <ThumbsUp className="w-4 h-4 text-green-400" />
                  <span className="text-green-300 font-semibold">
                    {data.sentiment_percentages.positive || 0}%
                  </span>
                </div>
                <p className="text-emerald-100 text-sm">Positive</p>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center gap-2 mb-1">
                  <ThumbsDown className="w-4 h-4 text-red-400" />
                  <span className="text-red-300 font-semibold">
                    {data.sentiment_percentages.negative || 0}%
                  </span>
                </div>
                <p className="text-emerald-100 text-sm">Negative</p>
              </div>
              <div className="text-center">
                <span className="text-slate-300 font-semibold">{data.sentiment_percentages.neutral || 0}%</span>
                <p className="text-emerald-100 text-sm">Neutral</p>
              </div>
            </div>
          </div>

          <div className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border border-emerald-300 border-opacity-20">
            <h3 className="text-xl font-semibold text-white mb-6">Emotion Breakdown</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={emotionData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(16,185,129,0.2)" />
                <XAxis dataKey="emotion" stroke="rgba(52,211,153,0.8)" />
                <YAxis stroke="rgba(52,211,153,0.8)" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    border: '1px solid rgba(52,211,153,0.5)',
                    borderRadius: '8px',
                  }}
                  formatter={(value) => `${value}%`}
                />
                <Bar dataKey="score" fill="#10b981" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border border-emerald-300 border-opacity-20">
            <h3 className="text-xl font-semibold text-white mb-6">Top Keywords</h3>
            <div className="flex flex-wrap gap-3">
              {(data.top_keywords || []).map((keyword, idx) => (
                <span
                  key={`${keyword}-${idx}`}
                  className="px-4 py-2 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full text-white font-medium"
                >
                  {keyword}
                </span>
              ))}
            </div>
          </div>

          <div className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border border-emerald-300 border-opacity-20">
            <h3 className="text-xl font-semibold text-white mb-6">Sources Detected</h3>
            <div className="flex flex-wrap gap-3">
              {(data.trusted_sources || []).map((source, idx) => (
                <span
                  key={`${source}-${idx}`}
                  className="px-4 py-2 border border-emerald-300 border-opacity-40 rounded-full text-emerald-100"
                >
                  {source}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border border-emerald-300 border-opacity-20 mb-8">
          <h3 className="text-xl font-semibold text-white mb-4">Sample Comment Analysis</h3>
          <div className="space-y-4">
            {(data.reviews || []).slice(0, 10).map((review, idx) => (
              <div key={idx} className="bg-black bg-opacity-20 rounded-xl p-4 border border-emerald-300 border-opacity-15">
                <div className="flex items-center justify-between gap-4 mb-2">
                  <p className="text-emerald-100 text-sm">{review.source || 'Marketplace Review'}</p>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-semibold ${getSentimentBadgeClass(
                      review.sentiment
                    )}`}
                  >
                    {review.sentiment} ({Math.round((review.sentiment_score || 0) * 100)}%)
                  </span>
                </div>
                <p className="text-white mb-2">{review.text}</p>
                {review.rating > 0 && (
                  <p className="text-emerald-200 text-xs">Review rating: {review.rating}/5</p>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="flex flex-col md:flex-row gap-4">
          <button
            onClick={() => navigate('/product')}
            className="flex-1 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white py-3 rounded-lg font-semibold transition"
          >
            Analyze Another Product
          </button>
          <button
            onClick={() => navigate('/')}
            className="flex-1 bg-white bg-opacity-10 hover:bg-opacity-20 border border-emerald-300 border-opacity-40 text-emerald-100 py-3 rounded-lg font-semibold transition"
          >
            Back to Hub
          </button>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value }) {
  return (
    <div className="bg-black bg-opacity-20 rounded-xl p-4 border border-emerald-300 border-opacity-20">
      <p className="text-xs text-emerald-200 mb-1 uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  );
}

function getVerdictStyle(score) {
  if (score >= 8.5) return 'bg-gradient-to-r from-green-500 to-emerald-500';
  if (score >= 7) return 'bg-gradient-to-r from-emerald-500 to-teal-500';
  if (score >= 5.5) return 'bg-gradient-to-r from-amber-500 to-orange-500';
  return 'bg-gradient-to-r from-rose-500 to-red-600';
}

function getSentimentBadgeClass(sentimentLabel) {
  const sentiment = (sentimentLabel || '').toLowerCase();
  if (sentiment === 'positive') {
    return 'bg-green-500 bg-opacity-20 text-green-300';
  }
  if (sentiment === 'negative') {
    return 'bg-red-500 bg-opacity-20 text-red-300';
  }
  return 'bg-slate-500 bg-opacity-20 text-slate-300';
}
