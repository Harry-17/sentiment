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
import {
  ArrowLeft,
  ExternalLink,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  Youtube,
} from 'lucide-react';

const numberFormatter = new Intl.NumberFormat('en-US');

export default function YouTubeResults() {
  const location = useLocation();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const analysisData =
      location.state?.data || JSON.parse(sessionStorage.getItem('youtubeAnalysisResult'));

    if (analysisData) {
      setData(analysisData);
      setLoading(false);
    } else {
      navigate('/youtube');
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

  const contentSafety = useMemo(() => {
    if (!data) return null;
    return (
      data.content_safety || {
        toxicity_percentage: 0,
        toxicity_comment_count: 0,
        toxic_comment_examples: [],
        spam_percentage: 0,
        spam_comment_count: 0,
        repeated_comments: [],
        spam_patterns: [],
        safety_report: {
          toxicity_level: 'Low',
          spam_level: 'Low',
          warnings: [],
          summary: 'Content safety metrics are unavailable for this analysis.',
          clean_comments: true,
        },
      }
    );
  }, [data]);

  const engagementChartData = useMemo(() => {
    if (!data) return [];
    const views = Math.max(1, data.view_count || 0);
    return [
      { name: 'Likes / 1k views', value: Number((((data.like_count || 0) / views) * 1000).toFixed(2)) },
      {
        name: 'Comments / 1k views',
        value: Number((((data.comment_count || 0) / views) * 1000).toFixed(2)),
      },
      { name: 'Engagement %', value: Number((data.engagement_rate || 0).toFixed(2)) },
    ];
  }, [data]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-rose-950 via-fuchsia-950 to-slate-950 flex items-center justify-center">
        <div className="text-center">
          <Sparkles className="w-12 h-12 text-fuchsia-300 animate-spin mx-auto mb-4" />
          <p className="text-white text-lg">Loading YouTube analysis...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-rose-950 via-fuchsia-950 to-slate-950 flex items-center justify-center">
        <p className="text-white">No YouTube analysis found.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-rose-950 via-fuchsia-950 to-slate-950">
      <nav className="bg-black bg-opacity-40 backdrop-blur-md border-b border-fuchsia-500 border-opacity-20">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <button
            onClick={() => navigate('/youtube')}
            className="flex items-center gap-2 text-fuchsia-200 hover:text-fuchsia-100 transition"
          >
            <ArrowLeft className="w-5 h-5" />
            Back to YouTube Search
          </button>
          <div className="flex items-center gap-3">
            <Youtube className="w-6 h-6 text-fuchsia-300" />
            <h1 className="text-xl font-bold text-white">YouTube Results</h1>
          </div>
          <a
            href={data.video_url}
            target="_blank"
            rel="noreferrer"
            className="text-fuchsia-200 hover:text-fuchsia-100 transition flex items-center gap-2"
          >
            Open Video
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-4 py-10">
        <div className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-7 border border-fuchsia-400 border-opacity-20 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="md:col-span-1">
              {data.thumbnail_url && (
                <img
                  src={data.thumbnail_url}
                  alt={data.video_title}
                  className="w-full rounded-lg shadow-lg"
                />
              )}
            </div>
            <div className="md:col-span-3">
              <h2 className="text-3xl font-bold text-white mb-2">{data.video_title}</h2>
              <p className="text-fuchsia-100 mb-5">Channel: {data.channel_title}</p>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <MetricCard label="Views" value={numberFormatter.format(data.view_count || 0)} />
                <MetricCard label="Likes" value={numberFormatter.format(data.like_count || 0)} />
                <MetricCard label="Comments" value={numberFormatter.format(data.comment_count || 0)} />
                <MetricCard label="Analyzed" value={numberFormatter.format(data.comments_analyzed || 0)} />
              </div>

              <div className="bg-gradient-to-r from-fuchsia-500 to-rose-500 rounded-xl p-6 text-white">
                <p className="text-sm opacity-90 mb-1">AI VIDEO RATING</p>
                <h3 className="text-4xl font-bold mb-2">{data.rating}/10</h3>
                <p className="text-xl font-semibold mb-2">{data.verdict}</p>
                <p className="opacity-95">{data.verdict_explanation}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border border-fuchsia-400 border-opacity-20">
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
                <p className="text-fuchsia-100 text-sm">Positive</p>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center gap-2 mb-1">
                  <ThumbsDown className="w-4 h-4 text-red-400" />
                  <span className="text-red-300 font-semibold">
                    {data.sentiment_percentages.negative || 0}%
                  </span>
                </div>
                <p className="text-fuchsia-100 text-sm">Negative</p>
              </div>
              <div className="text-center">
                <span className="text-slate-300 font-semibold">{data.sentiment_percentages.neutral || 0}%</span>
                <p className="text-fuchsia-100 text-sm">Neutral</p>
              </div>
            </div>
          </div>

          <div className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border border-fuchsia-400 border-opacity-20">
            <h3 className="text-xl font-semibold text-white mb-6">Engagement Signals</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={engagementChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(232,121,249,0.2)" />
                <XAxis dataKey="name" stroke="rgba(244,114,182,0.8)" />
                <YAxis stroke="rgba(244,114,182,0.8)" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    border: '1px solid rgba(232,121,249,0.5)',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="value" fill="#ec4899" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <p className="text-fuchsia-100 mt-4">
              Engagement rate: <span className="font-semibold text-fuchsia-200">{data.engagement_rate}%</span>
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border border-fuchsia-400 border-opacity-20">
            <h3 className="text-xl font-semibold text-white mb-6">Emotion Breakdown</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={emotionData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(232,121,249,0.2)" />
                <XAxis dataKey="emotion" stroke="rgba(244,114,182,0.8)" />
                <YAxis stroke="rgba(244,114,182,0.8)" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    border: '1px solid rgba(232,121,249,0.5)',
                    borderRadius: '8px',
                  }}
                  formatter={(value) => `${value}%`}
                />
                <Bar dataKey="score" fill="#a21caf" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border border-fuchsia-400 border-opacity-20">
            <h3 className="text-xl font-semibold text-white mb-6">Top Keywords</h3>
            <div className="flex flex-wrap gap-3">
              {(data.top_keywords || []).map((keyword, idx) => (
                <span
                  key={`${keyword}-${idx}`}
                  className="px-4 py-2 bg-gradient-to-r from-fuchsia-500 to-rose-500 rounded-full text-white font-medium"
                >
                  {keyword}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border border-fuchsia-400 border-opacity-20 mb-8">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-6">
            <div>
              <h3 className="text-xl font-semibold text-white mb-2">Content Safety Analysis</h3>
              <p className="text-fuchsia-100">
                {contentSafety?.safety_report?.summary || 'No content safety summary available.'}
              </p>
            </div>
            <div
              className={`inline-flex items-center gap-2 px-3 py-2 rounded-full border text-sm font-semibold ${
                contentSafety?.safety_report?.clean_comments
                  ? 'bg-emerald-500 bg-opacity-20 text-emerald-200 border-emerald-400 border-opacity-30'
                  : 'bg-rose-500 bg-opacity-20 text-rose-100 border-rose-300 border-opacity-40'
              }`}
            >
              {contentSafety?.safety_report?.clean_comments ? (
                <ShieldCheck className="w-4 h-4" />
              ) : (
                <ShieldAlert className="w-4 h-4" />
              )}
              {contentSafety?.safety_report?.clean_comments ? 'Mostly Clean' : 'High-Risk Signals'}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="rounded-xl border border-rose-300 border-opacity-25 bg-black bg-opacity-20 p-4">
              <div className="flex items-center justify-between mb-2">
                <p className="text-rose-100 font-semibold">Toxicity Detection</p>
                <span
                  className={`px-2 py-1 rounded-full text-xs font-semibold ${getSafetyLevelBadgeClass(
                    contentSafety?.safety_report?.toxicity_level
                  )}`}
                >
                  {contentSafety?.safety_report?.toxicity_level || 'Low'}
                </span>
              </div>
              <p className="text-white text-2xl font-bold mb-1">{contentSafety?.toxicity_percentage || 0}%</p>
              <p className="text-fuchsia-200 text-sm mb-4">
                Abusive or harmful comments: {contentSafety?.toxicity_comment_count || 0}
              </p>

              <p className="text-rose-100 text-sm font-semibold mb-2">Example Toxic Comments</p>
              {(contentSafety?.toxic_comment_examples || []).length === 0 ? (
                <p className="text-fuchsia-200 text-sm">No toxic examples found in sampled comments.</p>
              ) : (
                <div className="space-y-2">
                  {(contentSafety?.toxic_comment_examples || []).slice(0, 3).map((entry, idx) => (
                    <div key={idx} className="rounded-lg border border-rose-300 border-opacity-20 p-3 bg-rose-500 bg-opacity-10">
                      <p className="text-white text-sm">{entry.text}</p>
                      <p className="text-rose-100 text-xs mt-1">
                        {entry.author || 'YouTube User'} | {entry.reason}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="rounded-xl border border-amber-300 border-opacity-25 bg-black bg-opacity-20 p-4">
              <div className="flex items-center justify-between mb-2">
                <p className="text-amber-100 font-semibold">Spam Detection</p>
                <span
                  className={`px-2 py-1 rounded-full text-xs font-semibold ${getSafetyLevelBadgeClass(
                    contentSafety?.safety_report?.spam_level
                  )}`}
                >
                  {contentSafety?.safety_report?.spam_level || 'Low'}
                </span>
              </div>
              <p className="text-white text-2xl font-bold mb-1">{contentSafety?.spam_percentage || 0}%</p>
              <p className="text-fuchsia-200 text-sm mb-4">
                Repetitive or spam-like comments: {contentSafety?.spam_comment_count || 0}
              </p>

              <p className="text-amber-100 text-sm font-semibold mb-2">Most Repeated Comments</p>
              {(contentSafety?.repeated_comments || []).length === 0 ? (
                <p className="text-fuchsia-200 text-sm">No repeated comment clusters detected.</p>
              ) : (
                <div className="space-y-2 mb-4">
                  {(contentSafety?.repeated_comments || []).slice(0, 3).map((entry, idx) => (
                    <div key={idx} className="rounded-lg border border-amber-300 border-opacity-20 p-3 bg-amber-500 bg-opacity-10">
                      <p className="text-white text-sm">{entry.text}</p>
                      <p className="text-amber-100 text-xs mt-1">Repeated {entry.count} times</p>
                    </div>
                  ))}
                </div>
              )}

              <p className="text-amber-100 text-sm font-semibold mb-2">Common Spam Patterns</p>
              {(contentSafety?.spam_patterns || []).length === 0 ? (
                <p className="text-fuchsia-200 text-sm">No frequent spam patterns found.</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {(contentSafety?.spam_patterns || []).slice(0, 4).map((pattern, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 rounded-full text-xs bg-amber-500 bg-opacity-20 text-amber-100 border border-amber-300 border-opacity-30"
                    >
                      {pattern.pattern} ({pattern.count})
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          {(contentSafety?.safety_report?.warnings || []).length > 0 && (
            <div className="mt-5 rounded-xl border border-rose-300 border-opacity-40 bg-rose-500 bg-opacity-10 p-4">
              <p className="text-rose-100 font-semibold mb-2">Safety Warnings</p>
              <div className="space-y-1">
                {(contentSafety?.safety_report?.warnings || []).map((warning, idx) => (
                  <p key={idx} className="text-rose-100 text-sm">
                    - {warning}
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border border-fuchsia-400 border-opacity-20 mb-8">
          <h3 className="text-xl font-semibold text-white mb-4">Sample Comment Analysis</h3>
          <div className="space-y-4">
            {(data.comments || []).slice(0, 8).map((comment, idx) => (
              <div key={idx} className="bg-black bg-opacity-20 rounded-xl p-4 border border-fuchsia-300 border-opacity-15">
                <div className="flex items-center justify-between mb-2 gap-4">
                  <p className="text-fuchsia-100 text-sm">{comment.author || 'YouTube User'}</p>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-semibold ${getSentimentBadgeClass(
                      comment.sentiment
                    )}`}
                  >
                    {comment.sentiment} ({Math.round((comment.sentiment_score || 0) * 100)}%)
                  </span>
                </div>
                <p className="text-white mb-2">{comment.text}</p>
                <p className="text-fuchsia-200 text-xs">Likes: {numberFormatter.format(comment.like_count || 0)}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="flex flex-col md:flex-row gap-4">
          <button
            onClick={() => navigate('/youtube')}
            className="flex-1 bg-gradient-to-r from-fuchsia-500 to-rose-500 hover:from-fuchsia-600 hover:to-rose-600 text-white py-3 rounded-lg font-semibold transition"
          >
            Analyze Another Video
          </button>
          <button
            onClick={() => navigate('/')}
            className="flex-1 bg-white bg-opacity-10 hover:bg-opacity-20 border border-fuchsia-300 border-opacity-40 text-fuchsia-100 py-3 rounded-lg font-semibold transition"
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
    <div className="bg-black bg-opacity-20 rounded-xl p-4 border border-fuchsia-300 border-opacity-20">
      <p className="text-xs text-fuchsia-200 mb-1 uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  );
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

function getSafetyLevelBadgeClass(level) {
  const normalized = (level || '').toLowerCase();
  if (normalized === 'high') {
    return 'bg-rose-500 bg-opacity-20 text-rose-100 border border-rose-300 border-opacity-30';
  }
  if (normalized === 'moderate') {
    return 'bg-amber-500 bg-opacity-20 text-amber-100 border border-amber-300 border-opacity-30';
  }
  return 'bg-emerald-500 bg-opacity-20 text-emerald-100 border border-emerald-300 border-opacity-30';
}
