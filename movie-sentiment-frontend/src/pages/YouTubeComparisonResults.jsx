import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft, Sparkles } from 'lucide-react';
import ComparisonDashboard from '../components/ComparisonDashboard';

export default function YouTubeComparisonResults() {
  const location = useLocation();
  const navigate = useNavigate();
  const [data, setData] = useState(null);

  useEffect(() => {
    const comparisonData =
      location.state?.data || JSON.parse(sessionStorage.getItem('youtubeComparisonResult'));
    if (!comparisonData) {
      navigate('/youtube');
      return;
    }
    setData(comparisonData);
  }, [location, navigate]);

  if (!data) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-rose-950 via-fuchsia-950 to-slate-950 flex items-center justify-center">
        <p className="text-white">Loading comparison...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-rose-950 via-fuchsia-950 to-slate-950">
      <nav className="bg-black bg-opacity-40 backdrop-blur-md border-b border-fuchsia-400 border-opacity-20">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <button
            onClick={() => navigate('/youtube')}
            className="flex items-center gap-2 text-fuchsia-200 hover:text-fuchsia-100 transition"
          >
            <ArrowLeft className="w-5 h-5" />
            Back to YouTube Search
          </button>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-fuchsia-300" />
            <h1 className="text-white font-semibold">YouTube Comparative Analysis</h1>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-10">
        <ComparisonDashboard
          data={data}
          accentClass="text-fuchsia-100"
          borderClass="border-fuchsia-400 border-opacity-20"
          leftColor="#d946ef"
          rightColor="#fb7185"
        />
      </div>
    </div>
  );
}
