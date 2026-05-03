import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft, Sparkles } from 'lucide-react';
import ComparisonDashboard from '../components/ComparisonDashboard';

export default function ProductComparisonResults() {
  const location = useLocation();
  const navigate = useNavigate();
  const [data, setData] = useState(null);

  useEffect(() => {
    const comparisonData =
      location.state?.data || JSON.parse(sessionStorage.getItem('productComparisonResult'));
    if (!comparisonData) {
      navigate('/product');
      return;
    }
    setData(comparisonData);
  }, [location, navigate]);

  if (!data) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-950 via-teal-950 to-slate-950 flex items-center justify-center">
        <p className="text-white">Loading comparison...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-950 via-teal-950 to-slate-950">
      <nav className="bg-black bg-opacity-35 backdrop-blur-md border-b border-emerald-400 border-opacity-20">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <button
            onClick={() => navigate('/product')}
            className="flex items-center gap-2 text-emerald-100 hover:text-white transition"
          >
            <ArrowLeft className="w-5 h-5" />
            Back to Product Search
          </button>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-emerald-300" />
            <h1 className="text-white font-semibold">Product Comparative Analysis</h1>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-10">
        <ComparisonDashboard
          data={data}
          accentClass="text-emerald-100"
          borderClass="border-emerald-300 border-opacity-20"
          leftColor="#10b981"
          rightColor="#2dd4bf"
        />
      </div>
    </div>
  );
}
