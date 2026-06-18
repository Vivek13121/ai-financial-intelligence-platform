import axios from "axios";

// Vite proxy redirects /api to the backend
const apiClient = axios.create({
  baseURL: "/api/v1",
  headers: {
    "Content-type": "application/json",
  },
});

export interface Article {
  id: string;
  title: string;
  content: string;
  source?: string;
  company?: string;
  published_at?: string;
  article_url?: string;
  created_at: string;
}

export interface SentimentResult {
  id: string;
  article_id: string;
  sentiment_label: string;
  score: number;
  model_name: string;
  processed_at: string;
}

export interface QueueStatus {
  name: string;
  size: number;
}

export interface SystemStatus {
  status: string;
  redis: string;
  db: string;
  worker: string;
  active_workers: number;
  queue_sizes: QueueStatus[];
  last_activity: string | null;
  last_sentiment_time: string | null;
  scheduler_heartbeat: string | null;
  articles_per_hour: number;
}

export interface SentimentDistribution {
  positive: number;
  negative: number;
  neutral: number;
}

export interface TrendingCompany {
  company: string;
  mentions: number;
  sentiment: string;
  direction: "up" | "down" | "flat";
}

export interface AnalyticsStats {
  total_articles: number;
  total_forecasts: number;
  market_sentiment_score: number;
  sentiment_distribution: SentimentDistribution;
  market_mood: string;
  mood_change: number;
  articles_today: number;
  sentiment_change: number;
  trending_companies: TrendingCompany[];
  window_used?: string;
}

export interface ActivityEvent {
  id: string;
  timestamp: string;
  type: string;
  message: string;
}

export interface ForecastResult {
  id: string;
  forecast_date: string;
  predicted_sentiment: number;
  confidence_lower: number;
  confidence_upper: number;
  generated_at: string;
}

export const API = {
  getArticles: async (skip = 0, limit = 10, search = ""): Promise<Article[]> => {
    const res = await apiClient.get(`/articles/?skip=${skip}&limit=${limit}&search=${encodeURIComponent(search)}`);
    return res.data;
  },
  
  getArticleSentiment: async (articleId: string): Promise<SentimentResult[]> => {
    const res = await apiClient.get(`/articles/${articleId}/sentiment`);
    return res.data;
  },

  getLatestForecasts: async (limit = 14): Promise<ForecastResult[]> => {
    const res = await apiClient.get(`/forecast/latest?limit=${limit}`);
    return res.data;
  },

  getAnalyticsStats: async (): Promise<AnalyticsStats> => {
    const res = await apiClient.get("/analytics/stats");
    return res.data;
  },

  getSystemStatus: async (): Promise<SystemStatus> => {
    const res = await apiClient.get("/system/status");
    return res.data;
  },

  getActivityFeed: async (limit = 10): Promise<ActivityEvent[]> => {
    const res = await apiClient.get(`/analytics/activity-feed?limit=${limit}`);
    return res.data;
  },

  getAnalyticsTimeseries: async (days = 30): Promise<TimeSeriesDataPoint[]> => {
    const res = await apiClient.get(`/analytics/timeseries?days=${days}`);
    return res.data;
  },

  getAnalyticsTopics: async (days = 7): Promise<{ positive: TopicStats[]; negative: TopicStats[] }> => {
    const res = await apiClient.get(`/analytics/topics?days=${days}`);
    return res.data;
  },

  getForecastRuns: async (limit = 5): Promise<ForecastRunStats[]> => {
    const res = await apiClient.get(`/forecasts/runs?limit=${limit}`);
    return res.data;
  },

  getCompanyIntelligence: async (companyName: string): Promise<CompanyIntelligence> => {
    const res = await apiClient.get(`/intelligence/${encodeURIComponent(companyName)}`);
    return res.data;
  },
  getSearchSuggestions: async (query: string): Promise<string[]> => {
    const res = await apiClient.get(`/intelligence/suggestions?q=${encodeURIComponent(query)}`);
    return res.data;
  },

  getAISummaryStatus: async (companyName: string): Promise<AISummaryStatusResponse> => {
    const res = await apiClient.get(`/intelligence/${encodeURIComponent(companyName)}/summary/status`);
    return res.data;
  },

  getAISummary: async (companyName: string): Promise<AISummaryResponse> => {
    const res = await apiClient.get(`/intelligence/${encodeURIComponent(companyName)}/summary`);
    return res.data;
  }
};

export interface AISummaryStatusResponse {
  is_cached: boolean;
  generated_at: string | null;
}

export interface AISummaryResponse {
  executive_summary: string;
  risks: string[];
  opportunities: string[];
  forecast_outlook: string;
  generated_at: string;
}

export interface ForecastDataPoint {
  date: string;
  predicted_sentiment: number;
}

export interface IntelligenceOverview {
  total_articles: number;
  current_sentiment: number;
  forecast_direction: string;
}

export interface CompanyIntelligence {
  company_name: string;
  overview: IntelligenceOverview;
  news_feed: Article[];
  sentiment_trend: TimeSeriesDataPoint[];
  forecast: ForecastDataPoint[];
  insights: string;
  sentiment_distribution: SentimentDistribution;
  related_topics: string[];
}

export interface TimeSeriesDataPoint {
  date: string;
  sentiment_score: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  article_count: number;
}

export interface TopicStats {
  topic: string;
  mentions: number;
  sentiment_score: number;
}

export interface ForecastRunStats {
  generated_at: string;
  horizon_days: number;
  average_sentiment: number;
  trend: string;
}
