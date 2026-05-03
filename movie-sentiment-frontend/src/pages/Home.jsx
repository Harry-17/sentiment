import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, Film, Sparkles } from 'lucide-react';
import { movieAPI } from '../services/api';
import { addSearchHistoryItem, clearSearchHistory, getSearchHistory } from '../utils/searchHistory';

const MOVIE_HISTORY_KEY = 'movie-search-history';

export default function Home() {
  const navigate = useNavigate();
  const [movieInput, setMovieInput] = useState('');
  const [searchHistory, setSearchHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [compareLeft, setCompareLeft] = useState('');
  const [compareRight, setCompareRight] = useState('');
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareError, setCompareError] = useState('');

  useEffect(() => {
    setSearchHistory(getSearchHistory(MOVIE_HISTORY_KEY));
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    
    const trimmedInput = movieInput.trim();

    if (!trimmedInput) {
      setError('Please enter a movie name or IMDb link');
      return;
    }

    const updatedHistory = addSearchHistoryItem(MOVIE_HISTORY_KEY, trimmedInput);
    setSearchHistory(updatedHistory);
    setLoading(true);
    setError('');

    try {
      const result = await movieAPI.analyzeMovie(trimmedInput, null);
      
      // Store result and navigate to results page
      sessionStorage.setItem('analysisResult', JSON.stringify(result));
      navigate('/results', { state: { data: result } });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze movie. Please try again.');
      console.error('Analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = () => {
    clearSearchHistory(MOVIE_HISTORY_KEY);
    setSearchHistory([]);
  };

  const handleCompare = async (e) => {
    e.preventDefault();

    const leftValue = compareLeft.trim() || movieInput.trim();
    const rightValue = compareRight.trim();

    if (!leftValue || !rightValue) {
      setCompareError('Please enter both movies to compare.');
      return;
    }

    setCompareLoading(true);
    setCompareError('');

    try {
      const result = await movieAPI.compareMovies(leftValue, rightValue, {
        max_aspects: 12,
        min_aspect_mentions: 2,
      });
      sessionStorage.setItem('movieComparisonResult', JSON.stringify(result));
      navigate('/movie/compare', { state: { data: result } });
    } catch (err) {
      setCompareError(err.response?.data?.detail || 'Failed to compare movies. Please try again.');
      console.error('Comparison error:', err);
    } finally {
      setCompareLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-black">
      {/* Navigation */}
      <nav className="bg-black bg-opacity-40 backdrop-blur-md border-b border-purple-500 border-opacity-20">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Film className="w-8 h-8 text-purple-400" />
            <h1 className="text-2xl font-bold text-white">Movie Sentiment Analyzer</h1>
          </div>
          <div className="flex gap-4">
            <Link to="/" className="text-purple-300 hover:text-purple-100 transition">Hub</Link>
            <Link to="/youtube" className="text-purple-300 hover:text-purple-100 transition">YouTube</Link>
            <Link to="/product" className="text-purple-300 hover:text-purple-100 transition">Product</Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 py-12 sm:py-16">
        <div className="grid grid-cols-1 lg:grid-cols-[280px_minmax(0,1fr)_320px] gap-8 items-start">
          <aside className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border border-purple-400 border-opacity-20 lg:sticky lg:top-8">
            <div className="flex items-center justify-between mb-4 gap-4">
              <h3 className="text-white font-semibold text-lg">Analysis History</h3>
              {searchHistory.length > 0 && (
                <button
                  type="button"
                  onClick={handleClearHistory}
                  className="text-sm text-purple-200 hover:text-white transition"
                >
                  Clear
                </button>
              )}
            </div>

            {searchHistory.length === 0 ? (
              <p className="text-purple-200 text-sm">
                No previous analyses yet. Your recent movie searches will appear here.
              </p>
            ) : (
              <div className="space-y-3">
                {searchHistory.map((item, index) => (
                  <button
                    key={`${item}-${index}`}
                    type="button"
                    onClick={() => setMovieInput(item)}
                    className="w-full text-left rounded-xl p-3 bg-black bg-opacity-20 border border-purple-300 border-opacity-20 hover:bg-opacity-30 transition"
                  >
                    <p className="text-white font-medium line-clamp-2">{item}</p>
                  </button>
                ))}
              </div>
            )}
          </aside>

          <section className="min-w-0">
            <div className="text-center mb-10">
              <div className="flex justify-center mb-6">
                <Sparkles className="w-16 h-16 text-purple-400 animate-pulse" />
              </div>
              <h2 className="text-5xl font-bold text-white mb-4">
                Movie Sentiment Analyzer
              </h2>
              <p className="text-xl text-purple-200">
                Analyze movie sentiments with AI-powered insights.
              </p>
            </div>

            {/* Search Form */}
            <form onSubmit={handleSearch} className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-8 border border-purple-400 border-opacity-20 shadow-2xl mb-12">
              <div className="flex gap-3">
                <input
                  type="text"
                  value={movieInput}
                  onChange={(e) => setMovieInput(e.target.value)}
                  placeholder="Enter movie name or IMDb link..."
                  className="flex-1 bg-white bg-opacity-10 border border-purple-400 border-opacity-30 rounded-lg px-4 py-3 text-white placeholder-purple-300 focus:outline-none focus:border-purple-400 focus:bg-opacity-20 transition"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 text-white px-8 py-3 rounded-lg font-semibold flex items-center gap-2 transition transform hover:scale-105"
                >
                  <Search className="w-5 h-5" />
                  {loading ? 'Analyzing...' : 'Analyze'}
                </button>
              </div>

              {error && (
                <div className="mt-4 p-4 bg-red-500 bg-opacity-20 border border-red-500 rounded-lg text-red-200">
                  {error}
                </div>
              )}
            </form>

            {/* Features Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white bg-opacity-5 backdrop-blur-lg rounded-xl p-6 border border-purple-400 border-opacity-20 hover:border-opacity-40 transition">
                <div className="w-12 h-12 bg-purple-500 bg-opacity-30 rounded-lg flex items-center justify-center mb-4">
                  <Sparkles className="w-6 h-6 text-purple-300" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">AI Analysis</h3>
                <p className="text-purple-200">Advanced sentiment & emotion detection powered by DistilBERT</p>
              </div>

              <div className="bg-white bg-opacity-5 backdrop-blur-lg rounded-xl p-6 border border-purple-400 border-opacity-20 hover:border-opacity-40 transition">
                <div className="w-12 h-12 bg-pink-500 bg-opacity-30 rounded-lg flex items-center justify-center mb-4">
                  <Film className="w-6 h-6 text-pink-300" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Real Reviews</h3>
                <p className="text-purple-200">Analysis of genuine IMDb reviews from actual movie watchers</p>
              </div>

              <div className="bg-white bg-opacity-5 backdrop-blur-lg rounded-xl p-6 border border-purple-400 border-opacity-20 hover:border-opacity-40 transition">
                <div className="w-12 h-12 bg-blue-500 bg-opacity-30 rounded-lg flex items-center justify-center mb-4">
                  <Sparkles className="w-6 h-6 text-blue-300" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Explainable AI</h3>
                <p className="text-purple-200">LIME-powered insights on which words influence sentiment</p>
              </div>
            </div>
          </section>

          <aside className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border border-purple-400 border-opacity-20 lg:sticky lg:top-8">
            <div className="mb-4">
              <h3 className="text-white font-semibold text-lg">Comparative Analysis</h3>
              <p className="text-purple-200 text-sm mt-1">
                Compare two movies side by side with sentiment, emotion, and aspect-level insights.
              </p>
            </div>

            <form onSubmit={handleCompare} className="space-y-4">
              <div>
                <label className="block text-purple-100 text-sm font-semibold mb-2" htmlFor="compare-movie-left">
                  Movie A
                </label>
                <input
                  id="compare-movie-left"
                  type="text"
                  value={compareLeft}
                  onChange={(e) => setCompareLeft(e.target.value)}
                  placeholder="e.g. Interstellar"
                  className="w-full bg-white bg-opacity-10 border border-purple-400 border-opacity-30 rounded-lg px-3 py-2.5 text-white placeholder-purple-300 focus:outline-none focus:border-purple-300"
                  disabled={compareLoading}
                />
              </div>

              <div>
                <label className="block text-purple-100 text-sm font-semibold mb-2" htmlFor="compare-movie-right">
                  Movie B
                </label>
                <input
                  id="compare-movie-right"
                  type="text"
                  value={compareRight}
                  onChange={(e) => setCompareRight(e.target.value)}
                  placeholder="e.g. Oppenheimer"
                  className="w-full bg-white bg-opacity-10 border border-purple-400 border-opacity-30 rounded-lg px-3 py-2.5 text-white placeholder-purple-300 focus:outline-none focus:border-purple-300"
                  disabled={compareLoading}
                />
              </div>

              <button
                type="submit"
                disabled={compareLoading}
                className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 text-white py-2.5 rounded-lg font-semibold transition transform hover:scale-[1.02]"
              >
                {compareLoading ? 'Comparing...' : 'Compare Movies'}
              </button>

              {compareError && (
                <div className="p-3 bg-red-500 bg-opacity-20 border border-red-500 rounded-lg text-red-100 text-sm">
                  {compareError}
                </div>
              )}
            </form>

            <div className="mt-5 pt-4 border-t border-purple-400 border-opacity-20">
              <button
                type="button"
                onClick={() => setCompareLeft(movieInput)}
                className="text-sm text-purple-200 hover:text-white transition"
                disabled={!movieInput.trim()}
              >
                Use current search as Movie A
              </button>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
