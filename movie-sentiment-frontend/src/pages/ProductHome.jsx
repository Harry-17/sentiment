import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, ShoppingBag, Sparkles } from 'lucide-react';
import { movieAPI } from '../services/api';
import { addSearchHistoryItem, clearSearchHistory, getSearchHistory } from '../utils/searchHistory';

const PRODUCT_HISTORY_KEY = 'product-search-history';

export default function ProductHome() {
  const navigate = useNavigate();
  const [productQuery, setProductQuery] = useState('');
  const [searchHistory, setSearchHistory] = useState([]);
  const [marketplace, setMarketplace] = useState('any');
  const [maxComments, setMaxComments] = useState(60);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [compareLeft, setCompareLeft] = useState('');
  const [compareRight, setCompareRight] = useState('');
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareError, setCompareError] = useState('');

  useEffect(() => {
    setSearchHistory(getSearchHistory(PRODUCT_HISTORY_KEY));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const trimmedQuery = productQuery.trim();

    if (!trimmedQuery) {
      setError('Please enter a product name or model.');
      return;
    }

    const updatedHistory = addSearchHistoryItem(PRODUCT_HISTORY_KEY, trimmedQuery);
    setSearchHistory(updatedHistory);
    setLoading(true);
    setError('');

    try {
      const result = await movieAPI.analyzeProduct(trimmedQuery, marketplace, maxComments);
      sessionStorage.setItem('productAnalysisResult', JSON.stringify(result));
      navigate('/product/results', { state: { data: result } });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze product. Please try again.');
      console.error('Product analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = () => {
    clearSearchHistory(PRODUCT_HISTORY_KEY);
    setSearchHistory([]);
  };

  const handleCompare = async (e) => {
    e.preventDefault();
    const leftValue = compareLeft.trim() || productQuery.trim();
    const rightValue = compareRight.trim();

    if (!leftValue || !rightValue) {
      setCompareError('Please enter both products to compare.');
      return;
    }

    setCompareLoading(true);
    setCompareError('');

    try {
      const result = await movieAPI.compareProducts(leftValue, rightValue, {
        marketplace,
        maxComments,
        maxAspects: 12,
        minAspectMentions: 2,
      });
      sessionStorage.setItem('productComparisonResult', JSON.stringify(result));
      navigate('/product/compare', { state: { data: result } });
    } catch (err) {
      setCompareError(err.response?.data?.detail || 'Failed to compare products. Please try again.');
      console.error('Product comparison error:', err);
    } finally {
      setCompareLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-950 via-teal-950 to-slate-950">
      <nav className="bg-black bg-opacity-35 backdrop-blur-md border-b border-emerald-400 border-opacity-20">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <ShoppingBag className="w-8 h-8 text-emerald-300" />
            <h1 className="text-2xl font-bold text-white">Product Review Analyzer</h1>
          </div>
          <div className="flex gap-4">
            <Link to="/" className="text-emerald-100 hover:text-white transition">Hub</Link>
            <Link to="/movie" className="text-emerald-100 hover:text-white transition">Movie</Link>
            <Link to="/youtube" className="text-emerald-100 hover:text-white transition">YouTube</Link>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-12 sm:py-16">
        <div className="grid grid-cols-1 lg:grid-cols-[280px_minmax(0,1fr)_320px] gap-8 items-start">
          <aside className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border border-emerald-300 border-opacity-20 lg:sticky lg:top-8">
            <div className="flex items-center justify-between mb-4 gap-4">
              <h3 className="text-white font-semibold text-lg">Analysis History</h3>
              {searchHistory.length > 0 && (
                <button
                  type="button"
                  onClick={handleClearHistory}
                  className="text-sm text-emerald-100 hover:text-white transition"
                >
                  Clear
                </button>
              )}
            </div>

            {searchHistory.length === 0 ? (
              <p className="text-emerald-100 text-sm">
                No previous analyses yet. Your recent product searches will appear here.
              </p>
            ) : (
              <div className="space-y-3">
                {searchHistory.map((item, index) => (
                  <button
                    key={`${item}-${index}`}
                    type="button"
                    onClick={() => setProductQuery(item)}
                    className="w-full text-left rounded-xl p-3 bg-black bg-opacity-20 border border-emerald-300 border-opacity-20 hover:bg-opacity-30 transition"
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
                <Sparkles className="w-16 h-16 text-emerald-300 animate-pulse" />
              </div>
              <h2 className="text-5xl font-bold text-white mb-4">Real Product Verdict</h2>
              <p className="text-xl text-emerald-100">
                Analyze live marketplace data
              </p>
            </div>

            <form
              onSubmit={handleSubmit}
              className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-8 border border-emerald-300 border-opacity-20 shadow-2xl"
            >
              <label className="block text-emerald-100 font-semibold mb-2" htmlFor="product-query">
                Product Name or Model
              </label>
              <div className="flex flex-col md:flex-row gap-3 mb-5">
                <input
                  id="product-query"
                  type="text"
                  value={productQuery}
                  onChange={(e) => setProductQuery(e.target.value)}
                  placeholder="e.g. iPhone 15 128GB, Samsung 55 inch TV, Noise smartwatch"
                  className="flex-1 bg-white bg-opacity-10 border border-emerald-300 border-opacity-30 rounded-lg px-4 py-3 text-white placeholder-emerald-100 focus:outline-none focus:border-emerald-300"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 disabled:opacity-50 text-white px-8 py-3 rounded-lg font-semibold flex items-center justify-center gap-2 transition transform hover:scale-105"
                >
                  <Search className="w-5 h-5" />
                  {loading ? 'Analyzing...' : 'Analyze'}
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-emerald-100 font-semibold mb-2" htmlFor="marketplace">
                    Marketplace
                  </label>
                  <select
                    id="marketplace"
                    value={marketplace}
                    onChange={(e) => setMarketplace(e.target.value)}
                    className="w-full bg-white bg-opacity-10 border border-emerald-300 border-opacity-30 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-emerald-300"
                    disabled={loading}
                  >
                    <option value="any" className="text-black">Any marketplace</option>
                    <option value="amazon" className="text-black">Amazon</option>
                    <option value="flipkart" className="text-black">Flipkart</option>
                  </select>
                </div>

                <div>
                  <label className="block text-emerald-100 font-semibold mb-2" htmlFor="max-comments">
                    Comments To Analyze
                  </label>
                  <select
                    id="max-comments"
                    value={maxComments}
                    onChange={(e) => setMaxComments(Number(e.target.value))}
                    className="w-full bg-white bg-opacity-10 border border-emerald-300 border-opacity-30 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-emerald-300"
                    disabled={loading}
                  >
                    <option value={30} className="text-black">30 comments</option>
                    <option value={60} className="text-black">60 comments</option>
                    <option value={100} className="text-black">100 comments</option>
                  </select>
                </div>
              </div>

              {error && (
                <div className="mt-4 p-4 bg-red-500 bg-opacity-20 border border-red-500 rounded-lg text-red-100">
                  {error}
                </div>
              )}
            </form>
          </section>

          <aside className="bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border border-emerald-300 border-opacity-20 lg:sticky lg:top-8">
            <div className="mb-4">
              <h3 className="text-white font-semibold text-lg">Comparative Analysis</h3>
              <p className="text-emerald-100 text-sm mt-1">
                Compare two products by sentiment, ratings, buying signal, and aspect-level strengths.
              </p>
            </div>

            <form onSubmit={handleCompare} className="space-y-4">
              <div>
                <label className="block text-emerald-100 text-sm font-semibold mb-2" htmlFor="compare-product-left">
                  Product A
                </label>
                <input
                  id="compare-product-left"
                  type="text"
                  value={compareLeft}
                  onChange={(e) => setCompareLeft(e.target.value)}
                  placeholder="e.g. iPhone 15 128GB"
                  className="w-full bg-white bg-opacity-10 border border-emerald-300 border-opacity-30 rounded-lg px-3 py-2.5 text-white placeholder-emerald-100 focus:outline-none focus:border-emerald-300"
                  disabled={compareLoading}
                />
              </div>

              <div>
                <label className="block text-emerald-100 text-sm font-semibold mb-2" htmlFor="compare-product-right">
                  Product B
                </label>
                <input
                  id="compare-product-right"
                  type="text"
                  value={compareRight}
                  onChange={(e) => setCompareRight(e.target.value)}
                  placeholder="e.g. Samsung S24"
                  className="w-full bg-white bg-opacity-10 border border-emerald-300 border-opacity-30 rounded-lg px-3 py-2.5 text-white placeholder-emerald-100 focus:outline-none focus:border-emerald-300"
                  disabled={compareLoading}
                />
              </div>

              <button
                type="submit"
                disabled={compareLoading}
                className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 disabled:opacity-50 text-white py-2.5 rounded-lg font-semibold transition transform hover:scale-[1.02]"
              >
                {compareLoading ? 'Comparing...' : 'Compare Products'}
              </button>

              {compareError && (
                <div className="p-3 bg-red-500 bg-opacity-20 border border-red-500 rounded-lg text-red-100 text-sm">
                  {compareError}
                </div>
              )}
            </form>

            <div className="mt-5 pt-4 border-t border-emerald-300 border-opacity-20">
              <button
                type="button"
                onClick={() => setCompareLeft(productQuery)}
                className="text-sm text-emerald-100 hover:text-white transition"
                disabled={!productQuery.trim()}
              >
                Use current search as Product A
              </button>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
