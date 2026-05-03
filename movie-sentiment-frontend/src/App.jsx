import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import Home from './pages/Home';
import Results from './pages/Results';
import Reviews from './pages/Reviews';
import YouTubeHome from './pages/YouTubeHome';
import YouTubeResults from './pages/YouTubeResults';
import ProductHome from './pages/ProductHome';
import ProductResults from './pages/ProductResults';
import MovieComparisonResults from './pages/MovieComparisonResults';
import ProductComparisonResults from './pages/ProductComparisonResults';
import YouTubeComparisonResults from './pages/YouTubeComparisonResults';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/movie" element={<Home />} />
        <Route path="/results" element={<Results />} />
        <Route path="/movie/compare" element={<MovieComparisonResults />} />
        <Route path="/reviews" element={<Reviews />} />
        <Route path="/youtube" element={<YouTubeHome />} />
        <Route path="/youtube/results" element={<YouTubeResults />} />
        <Route path="/youtube/compare" element={<YouTubeComparisonResults />} />
        <Route path="/product" element={<ProductHome />} />
        <Route path="/product/results" element={<ProductResults />} />
        <Route path="/product/compare" element={<ProductComparisonResults />} />
      </Routes>
    </Router>
  );
}

export default App;
