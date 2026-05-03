import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft, Sparkles } from 'lucide-react';
import ComparisonDashboard from '../components/ComparisonDashboard';

export default function MovieComparisonResults() {
  const location = useLocation();
  const navigate = useNavigate();
  const [data, setData] = useState(null);

  useEffect(() => {
    const comparisonData =
      location.state?.data || JSON.parse(sessionStorage.getItem('movieComparisonResult'));
    if (!comparisonData) {
      navigate('/movie');
      return;
    }
    setData(comparisonData);
  }, [location, navigate]);

  if (!data) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-black flex items-center justify-center">
        <p className="text-white">Loading comparison...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-black">
      <nav className="bg-black bg-opacity-40 backdrop-blur-md border-b border-purple-500 border-opacity-20">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <button
            onClick={() => navigate('/movie')}
            className="flex items-center gap-2 text-purple-300 hover:text-purple-100 transition"
          >
            <ArrowLeft className="w-5 h-5" />
            Back to Movie Search
          </button>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-300" />
            <h1 className="text-white font-semibold">Movie Comparative Analysis</h1>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-10">
        <ComparisonDashboard
          data={data}
          accentClass="text-purple-200"
          borderClass="border-purple-400 border-opacity-20"
          leftColor="#a855f7"
          rightColor="#38bdf8"
        />
      </div>
    </div>
  );
}
