import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, Sparkles, Youtube } from 'lucide-react';
import { movieAPI } from '../services/api';

const YOUTUBE_HISTORY_KEY = 'youtube-search-history';
const YOUTUBE_HISTORY_LIMIT = 8;

function toNullableNumber(value) {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }
  return null;
}

function normalizeHistoryEntry(entry) {
  if (typeof entry === 'string') {
    const normalizedUrl = entry.trim();
    if (!normalizedUrl) {
      return null;
    }
    return {
      url: normalizedUrl,
      video_title: '',
      rating: null,
      comments_analyzed: null,
      toxicity_percentage: null,
      spam_percentage: null,
      toxicity_level: null,
      spam_level: null,
      created_at: null,
    };
  }

  if (!entry || typeof entry !== 'object') {
    return null;
  }

  const normalizedUrl =
    (typeof entry.url === 'string' && entry.url.trim()) ||
    (typeof entry.query === 'string' && entry.query.trim()) ||
    '';

  if (!normalizedUrl) {
    return null;
  }

  return {
    url: normalizedUrl,
    video_title: typeof entry.video_title === 'string' ? entry.video_title : '',
    rating: toNullableNumber(entry.rating),
    comments_analyzed: toNullableNumber(entry.comments_analyzed),
    toxicity_percentage: toNullableNumber(entry.toxicity_percentage),
    spam_percentage: toNullableNumber(entry.spam_percentage),
    toxicity_level: typeof entry.toxicity_level === 'string' ? entry.toxicity_level : null,
    spam_level: typeof entry.spam_level === 'string' ? entry.spam_level : null,
    created_at: typeof entry.created_at === 'string' ? entry.created_at : null,
  };
}

function getYouTubeHistory() {
  if (typeof window === 'undefined' || typeof window.localStorage === 'undefined') {
    return [];
  }

  try {
    const rawValue = window.localStorage.getItem(YOUTUBE_HISTORY_KEY);
    if (!rawValue) {
      return [];
    }

    const parsed = JSON.parse(rawValue);
    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed.map(normalizeHistoryEntry).filter(Boolean);
  } catch (error) {
    return [];
  }
}

function saveYouTubeHistory(entries) {
  if (typeof window === 'undefined' || typeof window.localStorage === 'undefined') {
    return;
  }
  window.localStorage.setItem(YOUTUBE_HISTORY_KEY, JSON.stringify(entries));
}

function addYouTubeHistoryEntry(entry, limit = YOUTUBE_HISTORY_LIMIT) {
  const normalizedEntry = normalizeHistoryEntry(entry);
  if (!normalizedEntry) {
    return getYouTubeHistory();
  }

  const existingEntries = getYouTubeHistory();
  const deduped = existingEntries.filter(
    (item) => item.url.toLowerCase() !== normalizedEntry.url.toLowerCase()
  );
  const nextEntries = [normalizedEntry, ...deduped].slice(0, limit);

  saveYouTubeHistory(nextEntries);
  return nextEntries;
}

function clearYouTubeHistory() {
  if (typeof window === 'undefined' || typeof window.localStorage === 'undefined') {
    return;
  }
  window.localStorage.removeItem(YOUTUBE_HISTORY_KEY);
}

function formatHistoryTimestamp(value) {
  if (!value) {
    return '';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '';
  }

  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function YouTubeHome() {
  const navigate = useNavigate();
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [searchHistory, setSearchHistory] = useState([]);
  const [maxComments, setMaxComments] = useState(100);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [compareLeft, setCompareLeft] = useState('');
  const [compareRight, setCompareRight] = useState('');
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareError, setCompareError] = useState('');

  useEffect(() => {
    setSearchHistory(getYouTubeHistory());
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const trimmedUrl = youtubeUrl.trim();

    if (!trimmedUrl) {
      setError('Please paste a YouTube video or Shorts link.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const result = await movieAPI.analyzeYouTube(trimmedUrl, maxComments);
      const safetyReport = result.content_safety?.safety_report || {};
      const updatedHistory = addYouTubeHistoryEntry({
        url: trimmedUrl,
        video_title: result.video_title || '',
        rating: result.rating,
        comments_analyzed: result.comments_analyzed,
        toxicity_percentage: result.content_safety?.toxicity_percentage,
        spam_percentage: result.content_safety?.spam_percentage,
        toxicity_level: safetyReport.toxicity_level || null,
        spam_level: safetyReport.spam_level || null,
        created_at: new Date().toISOString(),
      });
      setSearchHistory(updatedHistory);
      sessionStorage.setItem('youtubeAnalysisResult', JSON.stringify(result));
      navigate('/youtube/results', { state: { data: result } });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze YouTube video. Please try again.');
      console.error('YouTube analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = () => {
    clearYouTubeHistory();
    setSearchHistory([]);
  };

  const handleCompare = async (e) => {
    e.preventDefault();
    const leftValue = compareLeft.trim() || youtubeUrl.trim();
    const rightValue = compareRight.trim();

    if (!leftValue || !rightValue) {
      setCompareError('Please enter both YouTube targets to compare.');
      return;
    }

    setCompareLoading(true);
    setCompareError('');

    try {
      const result = await movieAPI.compareYouTubeTargets(leftValue, rightValue, {
        maxComments,
        maxVideos: 6,
        maxAspects: 12,
        minAspectMentions: 2,
      });
      sessionStorage.setItem('youtubeComparisonResult', JSON.stringify(result));
      navigate('/youtube/compare', { state: { data: result } });
    } catch (err) {
      setCompareError(err.response?.data?.detail || 'Failed to compare YouTube targets. Please try again.');
      console.error('YouTube comparison error:', err);
    } finally {
      setCompareLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-rose-950 via-fuchsia-950 to-slate-950">
      <nav className="bg-black bg-opacity-40 backdrop-blur-md border-b border-fuchsia-400 border-opacity-20">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Youtube className="w-8 h-8 text-fuchsia-300" />
            <h1 className="text-2xl font-bold text-white">YouTube Sentiment Analyzer</h1>
          </div>
          <div className="flex gap-4">
            <Link to="/" className="text-fuchsia-200 hover:text-fuchsia-100 transition">Hub</Link>
            <Link to="/movie" className="text-fuchsia-200 hover:text-fuchsia-100 transition">Movie</Link>
            <Link to="/product" className="text-fuchsia-200 hover:text-fuchsia-100 transition">Product</Link>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-12 sm:py-16">
        <div className="grid grid-cols-1 lg:grid-cols-[280px_minmax(0,1fr)_320px] gap-8 items-start">
          <aside className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border border-fuchsia-400 border-opacity-20 lg:sticky lg:top-8">
            <div className="flex items-center justify-between mb-4 gap-4">
              <h3 className="text-white font-semibold text-lg">Analysis History</h3>
              {searchHistory.length > 0 && (
                <button
                  type="button"
                  onClick={handleClearHistory}
                  className="text-sm text-fuchsia-100 hover:text-white transition"
                >
                  Clear
                </button>
              )}
            </div>

            {searchHistory.length === 0 ? (
              <p className="text-fuchsia-100 text-sm">
                No previous analyses yet. Your recent videos and safety metrics will appear here.
              </p>
            ) : (
              <div className="space-y-3">
                {searchHistory.map((item, index) => (
                  <button
                    key={`${item.url}-${index}`}
                    type="button"
                    onClick={() => setYoutubeUrl(item.url)}
                    className="w-full text-left rounded-xl p-3 bg-black bg-opacity-20 border border-fuchsia-300 border-opacity-20 hover:bg-opacity-30 transition"
                  >
                    <p className="text-white font-medium line-clamp-2">
                      {item.video_title || item.url}
                    </p>
                    {item.video_title && (
                      <p className="text-fuchsia-200 text-xs truncate mt-1">{item.url}</p>
                    )}
                    <div className="flex flex-wrap gap-2 mt-2">
                      {typeof item.rating === 'number' && (
                        <span className="text-xs px-2 py-1 rounded-full bg-fuchsia-500 bg-opacity-20 text-fuchsia-100">
                          {item.rating}/10
                        </span>
                      )}
                      {typeof item.toxicity_percentage === 'number' && (
                        <span className="text-xs px-2 py-1 rounded-full bg-rose-500 bg-opacity-20 text-rose-100">
                          Toxic {item.toxicity_percentage}%
                        </span>
                      )}
                      {typeof item.spam_percentage === 'number' && (
                        <span className="text-xs px-2 py-1 rounded-full bg-amber-500 bg-opacity-20 text-amber-100">
                          Spam {item.spam_percentage}%
                        </span>
                      )}
                    </div>
                    {item.created_at && (
                      <p className="text-fuchsia-300 text-xs mt-2 opacity-80">
                        {formatHistoryTimestamp(item.created_at)}
                      </p>
                    )}
                  </button>
                ))}
              </div>
            )}
          </aside>

          <section className="min-w-0">
            <div className="text-center mb-10">
              <div className="flex justify-center mb-6">
                <Sparkles className="w-16 h-16 text-fuchsia-300 animate-pulse" />
              </div>
              <h2 className="text-5xl font-bold text-white mb-4">YouTube Audience Reaction</h2>
              <p className="text-xl text-fuchsia-100">
                Paste any YouTube video or Shorts URL to analyze
              </p>
            </div>

            <form
              onSubmit={handleSubmit}
              className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-8 border border-fuchsia-400 border-opacity-20 shadow-2xl"
            >
              <label className="block text-fuchsia-100 font-semibold mb-2" htmlFor="youtube-url">
                YouTube Video URL
              </label>
              <div className="flex flex-col md:flex-row gap-3 mb-5">
                <input
                  id="youtube-url"
                  type="text"
                  value={youtubeUrl}
                  onChange={(e) => setYoutubeUrl(e.target.value)}
                  placeholder="https://www.youtube.com/watch?v=... or https://youtube.com/shorts/..."
                  className="flex-1 bg-white bg-opacity-10 border border-fuchsia-400 border-opacity-30 rounded-lg px-4 py-3 text-white placeholder-fuchsia-200 focus:outline-none focus:border-fuchsia-300"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-gradient-to-r from-fuchsia-500 to-rose-500 hover:from-fuchsia-600 hover:to-rose-600 disabled:opacity-50 text-white px-8 py-3 rounded-lg font-semibold flex items-center justify-center gap-2 transition transform hover:scale-105"
                >
                  <Search className="w-5 h-5" />
                  {loading ? 'Analyzing...' : 'Analyze'}
                </button>
              </div>

              <div className="mb-3">
                <label className="block text-fuchsia-100 font-semibold mb-2" htmlFor="max-comments">
                  Comments To Analyze
                </label>
                <select
                  id="max-comments"
                  value={maxComments}
                  onChange={(e) => setMaxComments(Number(e.target.value))}
                  className="bg-white bg-opacity-10 border border-fuchsia-400 border-opacity-30 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-fuchsia-300"
                  disabled={loading}
                >
                  <option value={25} className="text-black">25 comments</option>
                  <option value={50} className="text-black">50 comments</option>
                  <option value={100} className="text-black">100 comments</option>
                </select>
              </div>

              {error && (
                <div className="mt-4 p-4 bg-red-500 bg-opacity-20 border border-red-500 rounded-lg text-red-100">
                  {error}
                </div>
              )}

              <p className="text-fuchsia-200 text-sm mt-5">
                Content Safety Analysis includes toxicity and spam detection for stronger sentiment reliability.
              </p>
            </form>
          </section>

          <aside className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border border-fuchsia-400 border-opacity-20 lg:sticky lg:top-8">
            <div className="mb-4">
              <h3 className="text-white font-semibold text-lg">Comparative Analysis</h3>
              <p className="text-fuchsia-100 text-sm mt-1">
                Compare two videos or channels across sentiment, toxicity, spam, engagement, and aspect signals.
              </p>
            </div>

            <form onSubmit={handleCompare} className="space-y-4">
              <div>
                <label className="block text-fuchsia-100 text-sm font-semibold mb-2" htmlFor="compare-youtube-left">
                  Target A
                </label>
                <input
                  id="compare-youtube-left"
                  type="text"
                  value={compareLeft}
                  onChange={(e) => setCompareLeft(e.target.value)}
                  placeholder="Video or channel URL/handle"
                  className="w-full bg-white bg-opacity-10 border border-fuchsia-400 border-opacity-30 rounded-lg px-3 py-2.5 text-white placeholder-fuchsia-200 focus:outline-none focus:border-fuchsia-300"
                  disabled={compareLoading}
                />
              </div>

              <div>
                <label className="block text-fuchsia-100 text-sm font-semibold mb-2" htmlFor="compare-youtube-right">
                  Target B
                </label>
                <input
                  id="compare-youtube-right"
                  type="text"
                  value={compareRight}
                  onChange={(e) => setCompareRight(e.target.value)}
                  placeholder="Video or channel URL/handle"
                  className="w-full bg-white bg-opacity-10 border border-fuchsia-400 border-opacity-30 rounded-lg px-3 py-2.5 text-white placeholder-fuchsia-200 focus:outline-none focus:border-fuchsia-300"
                  disabled={compareLoading}
                />
              </div>

              <button
                type="submit"
                disabled={compareLoading}
                className="w-full bg-gradient-to-r from-fuchsia-500 to-rose-500 hover:from-fuchsia-600 hover:to-rose-600 disabled:opacity-50 text-white py-2.5 rounded-lg font-semibold transition transform hover:scale-[1.02]"
              >
                {compareLoading ? 'Comparing...' : 'Compare Targets'}
              </button>

              {compareError && (
                <div className="p-3 bg-red-500 bg-opacity-20 border border-red-500 rounded-lg text-red-100 text-sm">
                  {compareError}
                </div>
              )}
            </form>

            <div className="mt-5 pt-4 border-t border-fuchsia-400 border-opacity-20">
              <button
                type="button"
                onClick={() => setCompareLeft(youtubeUrl)}
                className="text-sm text-fuchsia-100 hover:text-white transition"
                disabled={!youtubeUrl.trim()}
              >
                Use current search as Target A
              </button>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
