import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Film, ShoppingBag, Sparkles, Youtube } from 'lucide-react';

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-900">
      <div className="max-w-6xl mx-auto px-4 py-16 sm:py-24">
        <div className="text-center mb-14">
          <div className="flex justify-center mb-6">
            <Sparkles className="w-16 h-16 text-cyan-300 animate-pulse" />
          </div>
          <h1 className="text-5xl sm:text-6xl font-bold text-white mb-5">
            Sentiment Sphere
          </h1>
          <p className="text-xl text-cyan-100 max-w-3xl mx-auto">
            
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <Link
            to="/movie"
            className="group bg-white bg-opacity-5 border border-cyan-300 border-opacity-20 rounded-2xl p-8 backdrop-blur-lg transition hover:border-opacity-60 hover:-translate-y-1"
          >
            <div className="w-14 h-14 rounded-xl bg-cyan-400 bg-opacity-20 flex items-center justify-center mb-5">
              <Film className="w-7 h-7 text-cyan-200" />
            </div>
            <h2 className="text-3xl font-bold text-white mb-3">Movie Sentiment</h2>
            <p className="text-cyan-100 mb-8">
              Analyze IMDb reviews, emotion trends, and keyword signals to understand how people feel
              about a movie.
            </p>
            <div className="flex items-center gap-2 text-cyan-200 font-semibold">
              Open Movie Analyzer
              <ArrowRight className="w-5 h-5 transition group-hover:translate-x-1" />
            </div>
          </Link>

          <Link
            to="/youtube"
            className="group bg-white bg-opacity-5 border border-fuchsia-300 border-opacity-20 rounded-2xl p-8 backdrop-blur-lg transition hover:border-opacity-60 hover:-translate-y-1"
          >
            <div className="w-14 h-14 rounded-xl bg-fuchsia-400 bg-opacity-20 flex items-center justify-center mb-5">
              <Youtube className="w-7 h-7 text-fuchsia-200" />
            </div>
            <h2 className="text-3xl font-bold text-white mb-3">YouTube Sentiment</h2>
            <p className="text-fuchsia-100 mb-8">
              Paste a YouTube video or Shorts link to analyze comments, views, likes, and generate a
              rating with chart-based insights.
            </p>
            <div className="flex items-center gap-2 text-fuchsia-200 font-semibold">
              Open YouTube Analyzer
              <ArrowRight className="w-5 h-5 transition group-hover:translate-x-1" />
            </div>
          </Link>

          <Link
            to="/product"
            className="group bg-white bg-opacity-5 border border-emerald-300 border-opacity-20 rounded-2xl p-8 backdrop-blur-lg transition hover:border-opacity-60 hover:-translate-y-1"
          >
            <div className="w-14 h-14 rounded-xl bg-emerald-400 bg-opacity-20 flex items-center justify-center mb-5">
              <ShoppingBag className="w-7 h-7 text-emerald-200" />
            </div>
            <h2 className="text-3xl font-bold text-white mb-3">Product Review</h2>
            <p className="text-emerald-100 mb-8">
              Check real marketplace product signals from stores like Amazon and Flipkart with
              sentiment analysis on review snippets and buying confidence scores.
            </p>
            <div className="flex items-center gap-2 text-emerald-200 font-semibold">
              Open Product Analyzer
              <ArrowRight className="w-5 h-5 transition group-hover:translate-x-1" />
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
}
