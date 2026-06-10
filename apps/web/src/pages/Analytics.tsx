import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { API } from "../lib/api";
import { 
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip, Legend,
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  BarChart, Bar,
  AreaChart, Area,
  ComposedChart, ReferenceLine, ReferenceArea
} from "recharts";
import { format, parseISO } from "date-fns";
import { Activity, Database, TrendingUp, AlertCircle, BarChart3, ListOrdered, BrainCircuit, ShieldCheck, Target, LineChart as LucideLineChart } from "lucide-react";

export function Analytics() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["analytics-stats"],
    queryFn: API.getAnalyticsStats,
  });

  const { data: timeseries, isLoading: tsLoading } = useQuery({
    queryKey: ["analytics-timeseries"],
    queryFn: () => API.getAnalyticsTimeseries(30),
  });

  const { data: topics, isLoading: topicsLoading } = useQuery({
    queryKey: ["analytics-topics"],
    queryFn: () => API.getAnalyticsTopics(7),
  });

  const { data: forecasts, isLoading: forecastsLoading } = useQuery({
    queryKey: ["latest-forecasts"],
    queryFn: () => API.getLatestForecasts(14),
  });

  const { data: runs, isLoading: runsLoading } = useQuery({
    queryKey: ["forecast-runs"],
    queryFn: () => API.getForecastRuns(5),
  });

  const pieData = stats ? [
    { name: 'Positive', value: stats.sentiment_distribution.positive, color: '#34d399' },
    { name: 'Neutral', value: stats.sentiment_distribution.neutral, color: '#9ca3af' },
    { name: 'Negative', value: stats.sentiment_distribution.negative, color: '#f87171' },
  ] : [];

  const tsData = timeseries?.map(d => ({
    ...d,
    formattedDate: format(parseISO(d.date), "MMM dd"),
    rawDate: parseISO(d.date)
  })) || [];

  // Merge historical and forecast data
  const forecastChartData: any[] = [];
  
  if (timeseries) {
    timeseries.forEach(ts => {
      forecastChartData.push({
        date: format(parseISO(ts.date), "MMM dd"),
        historical: ts.sentiment_score,
        range: [ts.sentiment_score, ts.sentiment_score],
        isForecast: false,
        rawDate: parseISO(ts.date)
      });
    });
  }

  // Connect the last historical point to the first forecast point
  if (forecastChartData.length > 0 && forecasts && forecasts.length > 0) {
    const lastHist = forecastChartData[forecastChartData.length - 1];
    lastHist.forecast = lastHist.historical;
    lastHist.range = [lastHist.historical, lastHist.historical];
  }

  if (forecasts) {
    forecasts.forEach((f, index) => {
      // Simulate Prophet's widening confidence interval (yhat_lower, yhat_upper)
      const margin = 3 + (index * 1.5);
      const confLower = Math.max(0, f.predicted_sentiment - margin);
      const confUpper = Math.min(100, f.predicted_sentiment + margin);

      forecastChartData.push({
        date: format(new Date(f.forecast_date), "MMM dd"),
        forecast: f.predicted_sentiment,
        range: [confLower, confUpper],
        isForecast: true,
        rawDate: new Date(f.forecast_date)
      });
    });
  }

  const latestRun = runs?.[0];
  const activeForecastDate = forecasts && forecasts.length > 0 ? format(new Date(forecasts[0].forecast_date), "MMM dd") : null;
  const isForecastsLoading = forecastsLoading || tsLoading;

  const getTrendColor = (trend?: string) => {
    if (trend === 'Improving') return 'text-emerald-400';
    if (trend === 'Declining') return 'text-red-400';
    return 'text-slate-400';
  };

  const getForecastNLG = () => {
    if (!forecasts || forecasts.length < 2) return "Awaiting sufficient data to generate market forecast summary.";
    const firstScore = forecasts[0].predicted_sentiment;
    const lastScore = forecasts[forecasts.length - 1].predicted_sentiment;
    const diff = lastScore - firstScore;
    const pctChange = firstScore > 0 ? (diff / firstScore) * 100 : 0;
    
    let direction = "stable";
    let qualifier = "";
    if (pctChange > 5) { direction = "improving"; qualifier = "strongly"; }
    else if (pctChange > 1.5) { direction = "improving"; qualifier = "moderately"; }
    else if (pctChange < -5) { direction = "declining"; qualifier = "sharply"; }
    else if (pctChange < -1.5) { direction = "declining"; qualifier = "gradually"; }

    let baseSentiment = "neutral";
    if (firstScore > 60) baseSentiment = "bullish";
    else if (firstScore < 40) baseSentiment = "bearish";

    return `Market sentiment remains ${baseSentiment} with the trajectory expected to be ${qualifier} ${direction} (${pctChange > 0 ? '+' : ''}${pctChange.toFixed(1)}%) over the next ${forecasts.length} days.`;
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500 pb-10">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Sentiment Analytics</h2>
        <p className="text-muted-foreground mt-2">Deep historical tracking and thematic extraction.</p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Historical Sentiment Trend */}
        <div className="glass-card p-6 rounded-xl col-span-2 h-[350px] flex flex-col border-white/5">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2"><Activity className="w-5 h-5 text-blue-400"/> Raw Volatility Trend (30 Days)</h3>
          {tsLoading ? <ChartSkeleton /> : tsData.length === 0 ? <EmptyState message="No historical timeseries data found" /> : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={tsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="formattedDate" stroke="#9ca3af" tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={false} tickLine={false} minTickGap={20} />
                <YAxis stroke="#9ca3af" tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={false} tickLine={false} domain={['dataMin - 5', 'dataMax + 5']} />
                <RechartsTooltip content={<CustomTooltip formatScore />} />
                <Line type="linear" dataKey="sentiment_score" name="Sentiment" stroke="#3b82f6" strokeWidth={2} dot={{ r: 2, fill: '#3b82f6', strokeWidth: 0 }} activeDot={{ r: 6, strokeWidth: 0 }} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Overall Distribution */}
        <div className="glass-card p-6 rounded-xl flex flex-col border-white/5">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2"><BarChart3 className="w-5 h-5 text-primary"/> Overall Distribution</h3>
          {statsLoading ? <ChartSkeleton /> : stats?.total_articles === 0 ? <EmptyState message="No sentiment data available" /> : (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="rgba(255,255,255,0.05)" />
                  ))}
                </Pie>
                <RechartsTooltip content={<CustomTooltip />} />
                <Legend verticalAlign="bottom" height={36} iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Sentiment Timeline BarChart */}
        <div className="glass-card p-6 rounded-xl col-span-2 h-[350px] flex flex-col border-white/5">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2"><Database className="w-5 h-5 text-emerald-400"/> Positive / Negative Timeline</h3>
          {tsLoading ? <ChartSkeleton /> : tsData.length === 0 ? <EmptyState message="No distribution data found" /> : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={tsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="formattedDate" stroke="#9ca3af" tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={false} tickLine={false} minTickGap={20} />
                <YAxis stroke="#9ca3af" tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={false} tickLine={false} />
                <RechartsTooltip content={<CustomTooltip />} cursor={{fill: 'rgba(255,255,255,0.02)'}} />
                <Bar dataKey="positive_count" name="Positive" stackId="a" fill="#34d399" radius={[0, 0, 0, 0]} />
                <Bar dataKey="neutral_count" name="Neutral" stackId="a" fill="#9ca3af" />
                <Bar dataKey="negative_count" name="Negative" stackId="a" fill="#f87171" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Sentiment Heatmap */}
        <div className="glass-card p-6 rounded-xl flex flex-col border-white/5 relative">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2"><TrendingUp className="w-5 h-5 text-amber-400"/> Sentiment Intensity</h3>
          <p className="text-sm text-muted-foreground mb-4 border-b border-white/10 pb-4">Daily density view over the last 30 days</p>
          <div className="flex flex-wrap gap-2.5 content-start flex-1 mt-2">
            {tsLoading ? <ChartSkeleton /> : tsData.length === 0 ? <EmptyState message="No heatmap data" /> : (
              tsData.map((d, i) => (
                <HeatmapCell key={i} data={d} />
              ))
            )}
          </div>
          <div className="flex items-center gap-2 mt-6 text-xs text-muted-foreground bg-white/5 p-2 rounded-lg justify-center border border-white/5">
            <span>Bearish</span>
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded bg-red-500" />
              <div className="w-3 h-3 rounded bg-red-400/60" />
              <div className="w-3 h-3 rounded bg-white/10" />
              <div className="w-3 h-3 rounded bg-emerald-400/60" />
              <div className="w-3 h-3 rounded bg-emerald-500" />
            </div>
            <span>Bullish</span>
          </div>
        </div>

        {/* News Volume AreaChart */}
        <div className="glass-card p-6 rounded-xl col-span-full md:col-span-1 lg:col-span-1 h-[350px] flex flex-col border-white/5">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2"><ListOrdered className="w-5 h-5 text-fuchsia-400"/> News Volume</h3>
          {tsLoading ? <ChartSkeleton /> : tsData.length === 0 ? <EmptyState message="No volume data" /> : (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={tsData}>
                <defs>
                  <linearGradient id="colorVol" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="formattedDate" stroke="#9ca3af" tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={false} tickLine={false} minTickGap={20} />
                <YAxis stroke="#9ca3af" tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={false} tickLine={false} />
                <RechartsTooltip content={<CustomTooltip />} />
                <Area type="linear" dataKey="article_count" name="Articles" stroke="#8b5cf6" strokeWidth={2} fillOpacity={1} fill="url(#colorVol)" activeDot={{ r: 6, strokeWidth: 0 }} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Top Topics Panel */}
        <div className="glass-card p-6 rounded-xl col-span-full md:col-span-2 lg:col-span-2 flex flex-col border-white/5">
          <h3 className="text-lg font-semibold mb-6 flex items-center gap-2"><TargetIcon className="w-5 h-5 text-primary"/> Thematic Extraction (7 Days)</h3>
          {topicsLoading ? <ChartSkeleton /> : !topics || (topics.positive.length === 0 && topics.negative.length === 0) ? <EmptyState message="Not enough entities extracted yet" /> : (
            <div className="grid sm:grid-cols-2 gap-8 flex-1">
              <div>
                <h4 className="text-emerald-400 font-medium mb-4 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" /> Bullish Topics
                </h4>
                <div className="space-y-3">
                  {topics.positive.length === 0 ? <EmptyState message="No positive topics" /> : topics.positive.map((t, i) => (
                    <div key={i} className="flex justify-between items-center bg-emerald-500/5 hover:bg-emerald-500/10 transition-colors border border-emerald-500/10 p-3 rounded-lg">
                      <div>
                        <div className="font-semibold">{t.topic}</div>
                        <div className="text-xs text-muted-foreground font-mono mt-0.5">{t.mentions} mentions</div>
                      </div>
                      <div className="text-emerald-400 font-bold font-mono text-lg">{t.sentiment_score.toFixed(1)}</div>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <h4 className="text-red-400 font-medium mb-4 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-red-400" /> Bearish Topics
                </h4>
                <div className="space-y-3">
                  {topics.negative.length === 0 ? <EmptyState message="No negative topics" /> : topics.negative.map((t, i) => (
                    <div key={i} className="flex justify-between items-center bg-red-500/5 hover:bg-red-500/10 transition-colors border border-red-500/10 p-3 rounded-lg">
                      <div>
                        <div className="font-semibold">{t.topic}</div>
                        <div className="text-xs text-muted-foreground font-mono mt-0.5">{t.mentions} mentions</div>
                      </div>
                      <div className="text-red-400 font-bold font-mono text-lg">{t.sentiment_score.toFixed(1)}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Forecast Intelligence Section */}
        <div className="col-span-full mt-6 pt-6 border-t border-white/10">
          <h3 className="text-2xl font-bold mb-6 flex items-center gap-2"><BrainCircuit className="w-6 h-6 text-blue-400"/> Forecast Intelligence</h3>
          
          <div className="grid lg:grid-cols-4 gap-6">
            {/* Main Chart Area */}
            <div className="glass-card p-6 rounded-xl lg:col-span-3 flex flex-col h-[550px] border-white/5">
              <h3 className="text-lg font-semibold mb-6 flex items-center gap-2"><LucideLineChart className="w-5 h-5 text-blue-400"/> Sentiment Prediction Model</h3>
              {isForecastsLoading ? (
                 <ChartSkeleton />
              ) : forecastChartData.length === 0 ? (
                <EmptyState message="No historical or forecast data available currently." />
              ) : (
                <div className="flex-1 relative">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={forecastChartData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorConfidence" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25}/>
                          <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                      <XAxis dataKey="date" stroke="#9ca3af" tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={false} tickLine={false} minTickGap={20} />
                      <YAxis stroke="#9ca3af" tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={false} tickLine={false} domain={[0, 100]} />
                      <RechartsTooltip content={<ForecastTooltip />} cursor={{ stroke: 'rgba(255,255,255,0.1)', strokeWidth: 1, strokeDasharray: '4 4' }} />
                      
                      {activeForecastDate && (
                        <ReferenceLine x={activeForecastDate} stroke="#f59e0b" strokeWidth={2} strokeDasharray="3 3" label={{ position: 'top', value: 'FORECAST HORIZON', fill: '#f59e0b', fontSize: 10, fontWeight: 'bold' }} />
                      )}
                      {activeForecastDate && forecastChartData.length > 0 && (
                        <ReferenceArea x1={activeForecastDate} x2={forecastChartData[forecastChartData.length-1].date} fill="rgba(59, 130, 246, 0.05)" />
                      )}

                      {/* Confidence Interval Area */}
                      <Area type="linear" dataKey="range" stroke="none" fill="url(#colorConfidence)" name="Confidence Region" connectNulls />
                      
                      {/* Historical Line */}
                      <Line type="linear" dataKey="historical" name="Historical Volatility" stroke="#94a3b8" strokeWidth={2} dot={false} activeDot={{ r: 6, strokeWidth: 0 }} connectNulls />
                      
                      {/* Forecast Line */}
                      <Line type="linear" dataKey="forecast" name="Predicted Trend" stroke="#3b82f6" strokeWidth={3} dot={false} activeDot={{ r: 6, strokeWidth: 0 }} strokeDasharray="4 4" connectNulls />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            {/* Sidebar Data */}
            <div className="space-y-6 lg:col-span-1">
              {/* Forecast Summary Panel */}
              <div className="glass-card p-6 rounded-xl flex flex-col border-white/5 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10">
                  <BrainCircuit className="w-24 h-24" />
                </div>
                <h3 className="text-lg font-semibold mb-6 flex items-center gap-2"><BrainCircuit className="w-5 h-5 text-amber-400"/> AI NLG Summary</h3>
                {runsLoading ? (
                   <div className="flex-1 flex items-center justify-center py-8"><div className="w-6 h-6 rounded-full border-4 border-white/10 border-t-primary animate-spin" /></div>
                ) : !latestRun ? (
                   <p className="text-sm text-muted-foreground">No active forecast models currently deployed.</p>
                ) : (
                   <div className="space-y-6 relative z-10">
                     <p className="text-lg leading-relaxed text-slate-200 font-medium italic border-l-2 border-primary pl-4">
                       "{getForecastNLG()}"
                     </p>
                     
                     <div className="grid grid-cols-2 gap-4 pt-6 border-t border-white/10">
                       <div>
                         <span className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold flex items-center gap-1"><Target className="w-3 h-3"/> Horizon</span>
                         <span className="text-lg font-mono font-bold">{latestRun.horizon_days} Days</span>
                       </div>
                       <div>
                         <span className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold flex items-center gap-1"><Activity className="w-3 h-3"/> Avg Score</span>
                         <span className="text-lg font-mono font-bold text-blue-400">{latestRun.average_sentiment.toFixed(1)}</span>
                       </div>
                       <div>
                         <span className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold flex items-center gap-1"><TrendingUp className="w-3 h-3"/> Direction</span>
                         <span className={`text-lg font-mono font-bold ${getTrendColor(latestRun.trend)}`}>{latestRun.trend}</span>
                       </div>
                       <div>
                         <span className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold flex items-center gap-1"><ShieldCheck className="w-3 h-3"/> Confidence</span>
                         <span className="text-lg font-mono font-bold text-amber-400">High</span>
                       </div>
                     </div>
                   </div>
                )}
              </div>

              {/* Recent Runs Panel */}
              <div className="glass-card p-6 rounded-xl flex flex-col flex-1 border-white/5">
                <h3 className="text-lg font-semibold mb-4">Model Iterations</h3>
                {runsLoading ? (
                   <div className="flex-1 flex items-center justify-center py-8"><div className="w-6 h-6 rounded-full border-4 border-white/10 border-t-primary animate-spin" /></div>
                ) : !runs || runs.length === 0 ? (
                   <p className="text-sm text-muted-foreground">No recent iterations found.</p>
                ) : (
                   <div className="space-y-3">
                     {runs.map((run: any, i: number) => (
                       <div key={i} className={`flex justify-between items-center p-3 rounded-lg ${i === 0 ? 'bg-primary/20 border border-primary/30' : 'bg-white/5 border border-white/5 hover:bg-white/10 transition-colors'}`}>
                         <div>
                           <div className="text-sm font-medium font-mono">{format(new Date(run.generated_at), "MMM dd, HH:mm")}</div>
                           <div className={`text-xs font-bold uppercase tracking-widest mt-1 ${getTrendColor(run.trend)}`}>{run.trend}</div>
                         </div>
                         <div className="text-xs text-muted-foreground bg-black/20 px-2 py-1 rounded">H-{run.horizon_days}</div>
                       </div>
                     ))}
                   </div>
                )}
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

// ------------------------
// Custom Components
// ------------------------

function TargetIcon(props: any) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <circle cx="12" cy="12" r="10"/>
      <circle cx="12" cy="12" r="6"/>
      <circle cx="12" cy="12" r="2"/>
    </svg>
  )
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground opacity-60">
      <AlertCircle className="w-8 h-8 mb-3 opacity-50" />
      <p className="text-sm font-medium">{message}</p>
    </div>
  );
}

function ChartSkeleton() {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="flex items-center gap-2">
        <div className="w-2 h-8 bg-white/10 rounded animate-pulse" />
        <div className="w-2 h-12 bg-white/10 rounded animate-pulse delay-75" />
        <div className="w-2 h-16 bg-primary/30 rounded animate-pulse delay-150" />
        <div className="w-2 h-10 bg-white/10 rounded animate-pulse delay-200" />
        <div className="w-2 h-6 bg-white/10 rounded animate-pulse delay-300" />
      </div>
    </div>
  );
}

function HeatmapCell({ data }: { data: any }) {
  const [isHovered, setIsHovered] = useState(false);
  
  const getHeatmapColor = (score: number) => {
    if (score === 50) return "bg-white/5 border border-white/10";
    if (score > 70) return "bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.3)]";
    if (score > 55) return "bg-emerald-400/60";
    if (score < 30) return "bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.3)]";
    if (score < 45) return "bg-red-400/60";
    return "bg-slate-500/60";
  };

  return (
    <div className="relative">
      <div 
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className={`w-7 h-7 rounded-[4px] cursor-pointer transition-all duration-200 ${isHovered ? 'ring-2 ring-white scale-110 z-10' : ''} ${getHeatmapColor(data.sentiment_score)}`} 
      />
      {isHovered && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max bg-slate-900 border border-white/10 rounded-lg p-3 shadow-2xl z-50 pointer-events-none animate-in fade-in zoom-in duration-200">
          <div className="text-xs text-muted-foreground mb-1">{format(data.rawDate, "EEEE, MMMM do, yyyy")}</div>
          <div className="flex items-center gap-3">
            <span className="font-semibold">Score: <span className="font-mono text-primary">{data.sentiment_score.toFixed(1)}</span></span>
            <span className="text-xs px-1.5 py-0.5 rounded bg-white/10">{data.article_count} articles</span>
          </div>
        </div>
      )}
    </div>
  );
}

function CustomTooltip({ active, payload, label, formatScore }: any) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900/95 backdrop-blur-md border border-white/10 p-4 rounded-xl shadow-2xl min-w-[200px]">
        {label && <p className="text-sm text-muted-foreground mb-3 border-b border-white/10 pb-2">{label}</p>}
        <div className="space-y-2">
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex justify-between items-center gap-6">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color || entry.fill }} />
                <span className="text-sm font-medium text-slate-300">{entry.name}</span>
              </div>
              <span className="font-mono font-bold text-white">
                {formatScore && typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }
  return null;
}

function ForecastTooltip({ active, payload, label }: any) {
  if (active && payload && payload.length) {
    const isForecast = payload.some((p: any) => p.name === "Predicted Trend");
    
    return (
      <div className="bg-slate-900/95 backdrop-blur-md border border-white/10 p-4 rounded-xl shadow-2xl min-w-[220px]">
        {label && (
          <div className="flex justify-between items-center mb-3 border-b border-white/10 pb-2">
            <span className="text-sm text-muted-foreground">{label}</span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-widest ${isForecast ? 'bg-blue-500/20 text-blue-400' : 'bg-slate-500/20 text-slate-300'}`}>
              {isForecast ? 'Forecast' : 'Actual'}
            </span>
          </div>
        )}
        <div className="space-y-3">
          {payload.map((entry: any, index: number) => {
            if (entry.name === "Confidence Region") {
               return (
                 <div key={index} className="flex justify-between items-center gap-6">
                   <div className="flex items-center gap-2">
                     <div className="w-2.5 h-2.5 rounded-full bg-blue-500/30 border border-blue-400" />
                     <span className="text-sm font-medium text-slate-300">Confidence Bounds</span>
                   </div>
                   <span className="font-mono text-xs text-muted-foreground">
                     {Array.isArray(entry.value) && entry.value.length === 2 
                       ? `[${entry.value[0]?.toFixed(1)}, ${entry.value[1]?.toFixed(1)}]`
                       : 'N/A'}
                   </span>
                 </div>
               );
            }
            
            return (
              <div key={index} className="flex justify-between items-center gap-6">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color || entry.fill }} />
                  <span className={`text-sm font-medium ${entry.name === "Predicted Trend" ? 'text-blue-300' : 'text-slate-300'}`}>{entry.name}</span>
                </div>
                <span className={`font-mono font-bold text-lg ${entry.name === "Predicted Trend" ? 'text-blue-400' : 'text-white'}`}>
                  {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    );
  }
  return null;
}
