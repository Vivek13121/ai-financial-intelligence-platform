import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { API } from "../lib/api";
import { 
  ArrowLeft, BrainCircuit, Activity, Newspaper, Target,
  TrendingUp, TrendingDown, Minus, Clock, ExternalLink 
} from "lucide-react";
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  AreaChart, Area, PieChart, Pie, Cell, Legend
} from "recharts";
import { format, parseISO } from "date-fns";

export function Company() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();

  const { data: intel, isLoading, isError } = useQuery({
    queryKey: ["company-intel", name],
    queryFn: () => API.getCompanyIntelligence(name!),
    enabled: !!name,
  });

  if (isLoading) {
    return (
      <div className="space-y-6 animate-in fade-in duration-500 pb-10">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-white/10 animate-pulse" />
          <div className="space-y-2">
            <div className="h-8 w-48 bg-white/10 rounded animate-pulse" />
            <div className="h-4 w-64 bg-white/5 rounded animate-pulse" />
          </div>
        </div>
        
        <div className="grid md:grid-cols-3 gap-6">
          {[1, 2, 3].map(i => (
            <div key={i} className="glass-card p-6 rounded-xl flex items-center gap-4 animate-pulse">
              <div className="w-14 h-14 rounded-full bg-white/10" />
              <div className="space-y-2 flex-1">
                <div className="h-4 w-24 bg-white/10 rounded" />
                <div className="h-8 w-16 bg-white/10 rounded" />
              </div>
            </div>
          ))}
        </div>

        <div className="glass-card p-8 rounded-2xl h-32 animate-pulse bg-white/5" />

        <div className="grid lg:grid-cols-3 gap-6">
          <div className="glass-card p-6 rounded-xl lg:col-span-2 h-[350px] animate-pulse bg-white/5" />
          <div className="glass-card p-6 rounded-xl h-[350px] animate-pulse bg-white/5" />
        </div>
      </div>
    );
  }

  if (isError || !intel) {
    return (
      <div className="h-full flex flex-col items-center justify-center space-y-4">
        <p className="text-red-400">Failed to load intelligence data.</p>
        <button onClick={() => navigate("/search")} className="text-primary hover:underline flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" /> Back to Search
        </button>
      </div>
    );
  }

  const getScoreColor = (score: number) => {
    if (score > 60) return "text-emerald-400";
    if (score < 40) return "text-red-400";
    return "text-slate-400";
  };

  const getTrendIcon = (direction: string) => {
    if (direction === "Bullish") return <TrendingUp className="w-6 h-6 text-emerald-400" />;
    if (direction === "Bearish") return <TrendingDown className="w-6 h-6 text-red-400" />;
    return <Minus className="w-6 h-6 text-slate-400" />;
  };

  const tsData = intel.sentiment_trend.map(d => ({
    ...d,
    formattedDate: format(parseISO(d.date), "MMM dd")
  }));

  const forecastData = intel.forecast.map(d => ({
    ...d,
    formattedDate: format(parseISO(d.date), "MMM dd")
  }));

  // Connect forecast to historical
  if (tsData.length > 0 && forecastData.length > 0) {
      forecastData.unshift({
          ...tsData[tsData.length - 1],
          predicted_sentiment: tsData[tsData.length - 1].sentiment_score
      } as any);
  }

  const pieData = [
    { name: 'Positive', value: intel.sentiment_distribution.positive, color: '#34d399' },
    { name: 'Neutral', value: intel.sentiment_distribution.neutral, color: '#9ca3af' },
    { name: 'Negative', value: intel.sentiment_distribution.negative, color: '#f87171' },
  ];

  const CustomTooltip = ({ active, payload, label, isForecast = false }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="glass-card p-4 rounded-xl border border-white/10 shadow-2xl backdrop-blur-xl bg-slate-900/90">
          <p className="text-muted-foreground mb-2 font-medium">{label}</p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.color }} />
              <span className="font-semibold text-lg" style={{ color: entry.color }}>
                {isForecast && entry.name === 'Predicted' ? entry.value.toFixed(1) : (entry.name === 'Sentiment' ? entry.value.toFixed(1) : entry.value)}
              </span>
              <span className="text-muted-foreground text-sm uppercase tracking-wide">{entry.name}</span>
            </div>
          ))}
          {isForecast && (
            <div className="mt-3 pt-3 border-t border-white/10 flex justify-between items-center text-xs">
              <span className="text-muted-foreground">Confidence</span>
              <span className="text-amber-400 font-medium">Moderate</span>
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500 pb-10">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate("/search")} className="p-2 hover:bg-white/10 rounded-full transition-colors text-muted-foreground hover:text-foreground">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h2 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            {intel.company_name} <span className="px-3 py-1 bg-primary/20 text-primary text-sm rounded-full border border-primary/30">Intelligence</span>
          </h2>
          <p className="text-muted-foreground mt-1">Real-time sentiment and forecasting analysis.</p>
        </div>
      </div>

      {/* KPI Overview */}
      <div className="grid md:grid-cols-3 gap-6">
        <div className="glass-card p-6 rounded-xl flex items-center gap-4">
          <div className="p-4 bg-blue-500/20 rounded-full">
            <Newspaper className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground font-medium">Analyzed Articles</p>
            <p className="text-3xl font-bold">{intel.overview.total_articles}</p>
          </div>
        </div>
        
        <div className="glass-card p-6 rounded-xl flex items-center gap-4">
          <div className="p-4 bg-purple-500/20 rounded-full">
            <Activity className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground font-medium">Current Sentiment</p>
            <p className={`text-3xl font-bold ${getScoreColor(intel.overview.current_sentiment)}`}>
              {intel.overview.current_sentiment.toFixed(1)}
            </p>
          </div>
        </div>

        <div className="glass-card p-6 rounded-xl flex items-center gap-4">
          <div className="p-4 bg-white/5 rounded-full">
            {getTrendIcon(intel.overview.forecast_direction)}
          </div>
          <div>
            <p className="text-sm text-muted-foreground font-medium">Forecast Direction</p>
            <p className="text-3xl font-bold">{intel.overview.forecast_direction}</p>
          </div>
        </div>
      </div>

      {/* AI Insight Panel */}
      <div className="relative glass-card p-8 rounded-2xl overflow-hidden border-primary/30">
        <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-blue-400 to-emerald-400" />
        <div className="flex gap-4 items-start">
          <div className="p-3 bg-primary/20 rounded-xl">
            <BrainCircuit className="w-8 h-8 text-primary" />
          </div>
          <div>
            <h3 className="text-lg font-bold mb-2">AI Summary Insight</h3>
            <p className="text-xl leading-relaxed font-medium text-slate-200">
              "{intel.insights}"
            </p>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Sentiment Trend */}
        <div className="glass-card p-6 rounded-xl lg:col-span-2 h-[350px] flex flex-col relative">
          <h3 className="text-lg font-semibold mb-4">Historical Trend (30 Days)</h3>
          {tsData.length === 0 ? (
            <div className="absolute inset-0 flex items-center justify-center bg-background/50 rounded-xl backdrop-blur-sm z-10">
              <p className="text-muted-foreground font-mono">Insufficient historical data</p>
            </div>
          ) : null}
          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={tsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                <XAxis dataKey="formattedDate" stroke="#9ca3af" tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis stroke="#9ca3af" tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={false} tickLine={false} domain={[0, 100]} />
                <RechartsTooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(255,255,255,0.1)', strokeWidth: 2 }} />
                <Line type="monotone" dataKey="sentiment_score" name="Sentiment" stroke="#8b5cf6" strokeWidth={3} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Forecast Graph */}
        <div className="glass-card p-6 rounded-xl h-[350px] flex flex-col relative">
          <h3 className="text-lg font-semibold mb-4">7-Day Forecast</h3>
          {forecastData.length <= 1 ? (
            <div className="absolute inset-0 flex items-center justify-center bg-background/50 rounded-xl backdrop-blur-sm z-10">
              <p className="text-muted-foreground font-mono">Insufficient forecast data</p>
            </div>
          ) : null}
          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={forecastData}>
                <defs>
                  <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="formattedDate" stroke="#9ca3af" tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis stroke="#9ca3af" tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={false} tickLine={false} domain={[0, 100]} hide />
                <RechartsTooltip content={<CustomTooltip isForecast={true} />} cursor={{ stroke: 'rgba(255,255,255,0.1)', strokeWidth: 2 }} />
                <Area type="monotone" dataKey="predicted_sentiment" name="Predicted" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorForecast)" strokeDasharray="5 5" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sentiment Distribution */}
        <div className="glass-card p-6 rounded-xl flex flex-col relative">
          <h3 className="text-lg font-semibold mb-4">Sentiment Distribution</h3>
          {pieData.every(d => d.value === 0) ? (
            <div className="absolute inset-0 flex items-center justify-center bg-background/50 rounded-xl backdrop-blur-sm z-10">
              <p className="text-muted-foreground font-mono">No distribution data</p>
            </div>
          ) : null}
          <div className="flex-1 h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="rgba(255,255,255,0.1)" />
                  ))}
                </Pie>
                <RechartsTooltip content={<CustomTooltip />} />
                <Legend verticalAlign="bottom" height={36} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          
          {/* Related Keywords */}
          <div className="mt-6 pt-6 border-t border-white/10">
            <h4 className="text-sm font-medium text-muted-foreground mb-3 flex items-center gap-2">
              <Target className="w-4 h-4" /> Related Topics
            </h4>
            <div className="flex flex-wrap gap-2">
              {intel.related_topics.map((topic, i) => (
                <span key={i} className="px-2.5 py-1 rounded-md bg-white/5 border border-white/10 text-xs font-medium">
                  {topic}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Related News Feed */}
        <div className="glass-card p-6 rounded-xl lg:col-span-2 flex flex-col">
          <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
            <Newspaper className="w-5 h-5" /> Recent {intel.company_name} News
          </h3>
          <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
            {intel.news_feed.length === 0 ? (
              <p className="text-muted-foreground text-sm">No recent news found for this company.</p>
            ) : intel.news_feed.map(article => (
              <div key={article.id} className="p-4 rounded-lg bg-white/5 hover:bg-white/10 transition-colors">
                <h4 className="font-medium mb-2 leading-tight">{article.title}</h4>
                <p className="text-sm text-muted-foreground line-clamp-2 mb-3">{article.content}</p>
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" />
                    {article.published_at ? format(new Date(article.published_at), "MMM d, h:mm a") : 'Unknown date'}
                  </div>
                  {article.article_url && (
                    <a href={article.article_url} target="_blank" rel="noreferrer" className="flex items-center gap-1 hover:text-primary transition-colors">
                      <ExternalLink className="w-3.5 h-3.5" /> Read Original
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
