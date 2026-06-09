import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { API } from "../lib/api";
import { Activity, Server, TrendingUp, Zap, Clock, RefreshCw, BarChart2, Target, Percent } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

export function Dashboard() {
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const { data: stats, isLoading: statsLoading, dataUpdatedAt: statsUpdatedAt } = useQuery({
    queryKey: ["analytics-stats"],
    queryFn: API.getAnalyticsStats,
    refetchInterval: 20000,
  });

  const { data: system, isLoading: systemLoading, dataUpdatedAt: systemUpdatedAt } = useQuery({
    queryKey: ["system-status"],
    queryFn: API.getSystemStatus,
    refetchInterval: 10000,
  });

  const { data: runs, isLoading: runsLoading } = useQuery({
    queryKey: ["forecast-runs"],
    queryFn: () => API.getForecastRuns(1),
    refetchInterval: 10000,
  });

  useEffect(() => {
    setLastUpdated(new Date());
  }, [statsUpdatedAt, systemUpdatedAt]);

  const latestRun = runs?.[0];

  // Helper to calculate percentage
  const dist = stats?.sentiment_distribution;
  const totalSentiments = dist ? (dist.positive + dist.negative + dist.neutral) : 0;
  const posPct = totalSentiments > 0 ? Math.round((dist!.positive / totalSentiments) * 100) : 0;
  const neuPct = totalSentiments > 0 ? Math.round((dist!.neutral / totalSentiments) * 100) : 0;
  const negPct = totalSentiments > 0 ? Math.round((dist!.negative / totalSentiments) * 100) : 0;

  // Sentiment Movement string
  const getMovementText = () => {
    if (!stats) return "Gathering data...";
    if (stats.sentiment_change > 0) {
      return "Bullish Momentum Up";
    } else if (stats.sentiment_change < 0) {
      return "Bearish Momentum Down";
    }
    return "Stable Momentum";
  };
  
  const getMovementSubtext = () => {
    if (!stats) return "";
    if (stats.sentiment_change > 0) {
      return `Market optimism increasing (+${stats.sentiment_change.toFixed(1)} sentiment points)`;
    } else if (stats.sentiment_change < 0) {
      return `Negative sentiment accelerating (${stats.sentiment_change.toFixed(1)} sentiment points)`;
    }
    return "Minor movement detected";
  };

  const getForecastFreshness = () => {
    if (!latestRun) return "Pending";
    return formatDistanceToNow(new Date(latestRun.generated_at), { addSuffix: true });
  };

  const forecastMetricClass = "bg-white/5 rounded-lg p-4 min-h-[112px] flex flex-col justify-center gap-3 border border-white/5";
  const forecastLabelClass = "text-xs text-muted-foreground uppercase leading-tight";

  return (
    <div className="space-y-6 animate-in fade-in duration-500 pb-12 h-full">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            Financial Intelligence Terminal
            <span className="flex h-3 w-3 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
          </h2>
          <p className="text-muted-foreground mt-2 font-mono text-sm">LIVE FEED • CONTINUOUS UPDATE ENABLED</p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-full">
          <RefreshCw className={`w-3.5 h-3.5 ${statsLoading || systemLoading ? 'animate-spin' : ''}`} />
          SYNCED {formatDistanceToNow(lastUpdated, { addSuffix: true }).toUpperCase()}
        </div>
      </div>

      {/* Main Terminal Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        
        {/* A) Market Mood Breakdown */}
        <div className="glass-card rounded-xl p-6 relative overflow-hidden group border-primary/20 hover:border-primary/50 transition-all">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <Percent className="w-24 h-24" />
          </div>
          <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-6 flex items-center gap-2">
            <Target className="w-4 h-4 text-primary" /> Market Mood Breakdown ({stats?.window_used || '7d'})
          </h3>
          
          <div className="space-y-6">
            <div>
              <div className="flex justify-between text-sm mb-1 font-mono">
                <span className="text-emerald-400">Positive</span>
                <span className="text-emerald-400 font-bold">{posPct}%</span>
              </div>
              <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-500 transition-all duration-1000" style={{ width: `${posPct}%` }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-sm mb-1 font-mono">
                <span className="text-slate-400">Neutral</span>
                <span className="text-slate-400 font-bold">{neuPct}%</span>
              </div>
              <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                <div className="h-full bg-slate-500 transition-all duration-1000" style={{ width: `${neuPct}%` }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-sm mb-1 font-mono">
                <span className="text-red-400">Negative</span>
                <span className="text-red-400 font-bold">{negPct}%</span>
              </div>
              <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                <div className="h-full bg-red-500 transition-all duration-1000" style={{ width: `${negPct}%` }} />
              </div>
            </div>
          </div>
        </div>

        {/* B) Trending Companies Panel */}
        <div className="glass-card rounded-xl p-6 flex flex-col border-white/5">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-6 flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-blue-400" /> Top Mentioned Companies ({stats?.window_used || '7d'})
          </h3>
          <div className="flex-1 space-y-4">
            {statsLoading ? (
               <div className="text-center text-muted-foreground animate-pulse mt-10 font-mono text-sm">Scanning feed...</div>
            ) : stats?.trending_companies?.length === 0 ? (
               <div className="text-center text-muted-foreground mt-10 font-mono text-sm">No companies mentioned in the last hour</div>
            ) : (
               stats?.trending_companies.slice(0, 5).map((company, idx) => (
                 <div key={idx} className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/5 hover:bg-white/10 transition-colors">
                   <div className="flex items-center gap-3">
                     <div className="font-mono font-bold text-lg">{company.company}</div>
                   </div>
                   <div className="flex items-center gap-4">
                     <div className="text-xs text-muted-foreground px-2 py-0.5 bg-black/30 rounded">
                       {company.mentions} mentions
                     </div>
                     <div className={`text-sm font-bold w-6 text-center ${company.direction === 'up' ? 'text-emerald-400' : company.direction === 'down' ? 'text-red-400' : 'text-slate-400'}`}>
                       {company.direction === 'up' ? '↑' : company.direction === 'down' ? '↓' : '→'}
                     </div>
                   </div>
                 </div>
               ))
            )}
          </div>
        </div>

        {/* C) Sentiment Movement Widget */}
        <div className="glass-card rounded-xl p-6 flex flex-col border-white/5">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-6 flex items-center gap-2">
            <Activity className="w-4 h-4 text-fuchsia-400" /> Momentum Shift
          </h3>
          <div className="flex-1 flex flex-col justify-center items-center text-center">
            {statsLoading ? (
              <div className="animate-pulse w-10 h-10 bg-white/10 rounded-full mb-4" />
            ) : (
              <div className={`p-4 rounded-full mb-6 ${stats?.sentiment_change && stats.sentiment_change > 0 ? 'bg-emerald-500/20 text-emerald-400' : stats?.sentiment_change && stats.sentiment_change < 0 ? 'bg-red-500/20 text-red-400' : 'bg-slate-500/20 text-slate-400'}`}>
                {stats?.sentiment_change && stats.sentiment_change > 0 ? <TrendingUp className="w-8 h-8" /> : stats?.sentiment_change && stats.sentiment_change < 0 ? <TrendingUp className="w-8 h-8 rotate-180 scale-x-[-1]" /> : <Activity className="w-8 h-8" />}
              </div>
            )}
            <h4 className="text-xl font-bold leading-tight">
              {getMovementText()}
            </h4>
            <p className="text-sm text-muted-foreground mt-4">{getMovementSubtext()}</p>
          </div>
        </div>

        {/* D) Forecast Intelligence Widget */}
        <div className="glass-card rounded-xl p-6 lg:col-span-2 border-white/5 relative overflow-hidden flex flex-col">
          <div className="absolute -bottom-10 -right-10 w-48 h-48 bg-primary/10 blur-3xl rounded-full pointer-events-none" />
          <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-5 flex items-center gap-2 relative z-10">
            <Zap className="w-4 h-4 text-amber-400" /> AI Forecast Intelligence
          </h3>
          
          {runsLoading ? (
             <div className="min-h-[112px] flex items-center justify-center font-mono text-sm text-muted-foreground animate-pulse relative z-10">Running Prophet Models...</div>
          ) : !latestRun ? (
             <div className="min-h-[112px] flex items-center justify-center font-mono text-sm text-muted-foreground relative z-10">No active forecast models running.</div>
          ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 relative z-10">
               <div className={forecastMetricClass}>
                 <span className={forecastLabelClass}>Forecast Direction</span>
                 <span className={`text-xl font-bold leading-none ${latestRun.trend === 'Improving' ? 'text-emerald-400' : latestRun.trend === 'Declining' ? 'text-red-400' : 'text-slate-300'}`}>
                   {latestRun.trend === 'Improving' ? 'Bullish' : latestRun.trend === 'Declining' ? 'Bearish' : 'Neutral'}
                 </span>
               </div>
               <div className={forecastMetricClass}>
                 <span className={forecastLabelClass}>Expected Change</span>
                 <span className={`text-xl font-bold font-mono leading-none ${latestRun.trend === 'Improving' ? 'text-emerald-400' : latestRun.trend === 'Declining' ? 'text-red-400' : 'text-slate-300'}`}>
                   {latestRun.trend === 'Improving' ? '+' : latestRun.trend === 'Declining' ? '-' : ''}{Math.abs(latestRun.average_sentiment - (stats?.market_sentiment_score || 50)).toFixed(1)}%
                 </span>
               </div>
               <div className={forecastMetricClass}>
                 <span className={forecastLabelClass}>Confidence</span>
                 <span className="text-xl font-bold leading-none text-amber-400">Medium</span>
               </div>
               <div className={forecastMetricClass}>
                 <span className={forecastLabelClass}>Forecast Freshness</span>
                 <span className="text-base font-bold leading-tight flex items-center gap-1.5 text-slate-200">
                   <Clock className="w-3.5 h-3.5 shrink-0 text-muted-foreground" /> {getForecastFreshness()}
                 </span>
               </div>
             </div>
          )}
        </div>

        {/* E) Processing Metrics Panel */}
        <div className="glass-card rounded-xl p-6 border-white/5">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-6 flex items-center gap-2">
            <Server className="w-4 h-4 text-slate-400" /> System Processing
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center border-b border-white/5 pb-3">
              <span className="text-sm text-slate-300">Last Ingestion Time</span>
              <span className="font-mono text-xs text-emerald-400">{system?.last_activity ? formatDistanceToNow(new Date(system.last_activity), { addSuffix: true }) : 'N/A'}</span>
            </div>
            <div className="flex justify-between items-center border-b border-white/5 pb-3">
              <span className="text-sm text-slate-300">Last Sentiment Processing Time</span>
              <span className="font-mono text-xs text-blue-400">{system?.last_sentiment_time ? formatDistanceToNow(new Date(system.last_sentiment_time), { addSuffix: true }) : 'N/A'}</span>
            </div>
            <div className="flex justify-between items-center border-b border-white/5 pb-3">
              <span className="text-sm text-slate-300">Scheduler Heartbeat</span>
              <span className="font-mono text-xs">
                {system?.scheduler_heartbeat && (new Date().getTime() - new Date(system.scheduler_heartbeat).getTime()) < 5 * 60 * 1000 ? (
                  <span className="text-emerald-400 flex items-center gap-1">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                    </span>
                    Online
                  </span>
                ) : (
                  <span className="text-red-400">Offline</span>
                )}
              </span>
            </div>
            <div className="flex justify-between items-center border-b border-white/5 pb-3">
              <span className="text-sm text-slate-300">Articles Ingestion (Rolling)</span>
              <span className="font-mono text-sm font-bold text-emerald-400">{system?.articles_per_hour || 0}</span>
            </div>
            <div className="flex justify-between items-center border-b border-white/5 pb-3">
              <span className="text-sm text-slate-300">Sentiment Jobs Completed</span>
              <span className="font-mono text-sm font-bold text-blue-400">{stats?.total_articles || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-slate-300">Forecast Jobs Completed</span>
              <span className="font-mono text-sm font-bold text-purple-400">{stats?.total_forecasts || 0}</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

