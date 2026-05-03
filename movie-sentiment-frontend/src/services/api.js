import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

export const movieAPI = {
  analyzeMovie: async (movieName, imdbLink, aspectOptions = {}) => {
    try {
      const response = await apiClient.post('/analyze', {
        movie_name: movieName,
        imdb_link: imdbLink,
        ...aspectOptions,
      });
      return response.data;
    } catch (error) {
      console.error('Error analyzing movie:', error);
      throw error;
    }
  },

  analyzeMovieAspects: async (movieName, imdbLink, options = {}) => {
    try {
      const response = await apiClient.post('/analyze/aspects', {
        movie_name: movieName,
        imdb_link: imdbLink,
        ...options,
      });
      return response.data;
    } catch (error) {
      console.error('Error analyzing movie aspects:', error);
      throw error;
    }
  },

  compareMovies: async (leftMovie, rightMovie, options = {}) => {
    try {
      const response = await apiClient.post('/compare/movie', {
        left: {
          movie_name: leftMovie,
          imdb_link: null,
        },
        right: {
          movie_name: rightMovie,
          imdb_link: null,
        },
        ...options,
      });
      return response.data;
    } catch (error) {
      console.error('Error comparing movies:', error);
      throw error;
    }
  },

  compareProducts: async (leftQuery, rightQuery, options = {}) => {
    try {
      const response = await apiClient.post('/compare/product', {
        left: {
          product_query: leftQuery,
          marketplace: options.leftMarketplace || options.marketplace || 'any',
        },
        right: {
          product_query: rightQuery,
          marketplace: options.rightMarketplace || options.marketplace || 'any',
        },
        max_comments: options.maxComments ?? 60,
        max_aspects: options.maxAspects ?? 12,
        min_aspect_mentions: options.minAspectMentions ?? 2,
      });
      return response.data;
    } catch (error) {
      console.error('Error comparing products:', error);
      throw error;
    }
  },

  compareYouTubeTargets: async (leftTarget, rightTarget, options = {}) => {
    try {
      const response = await apiClient.post('/compare/youtube', {
        left: {
          target_input: leftTarget,
        },
        right: {
          target_input: rightTarget,
        },
        max_comments: options.maxComments ?? 80,
        max_videos: options.maxVideos ?? 6,
        max_aspects: options.maxAspects ?? 12,
        min_aspect_mentions: options.minAspectMentions ?? 2,
      });
      return response.data;
    } catch (error) {
      console.error('Error comparing YouTube targets:', error);
      throw error;
    }
  },

  analyzeYouTube: async (youtubeUrl, maxComments = 100) => {
    try {
      const response = await apiClient.post('/analyze-youtube', {
        youtube_url: youtubeUrl,
        max_comments: maxComments,
      });
      return response.data;
    } catch (error) {
      console.error('Error analyzing YouTube video:', error);
      throw error;
    }
  },

  analyzeProduct: async (productQuery, marketplace = 'any', maxComments = 60) => {
    try {
      const response = await apiClient.post('/analyze-product', {
        product_query: productQuery,
        marketplace,
        max_comments: maxComments,
      });
      return response.data;
    } catch (error) {
      console.error('Error analyzing product:', error);
      throw error;
    }
  },

  getRecentSearches: async () => {
    try {
      const response = await apiClient.get('/recent-searches');
      return response.data.recent_searches;
    } catch (error) {
      console.error('Error fetching recent searches:', error);
      return [];
    }
  },

  healthCheck: async () => {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      return null;
    }
  },
};

export default apiClient;
