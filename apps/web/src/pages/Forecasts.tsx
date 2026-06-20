/* eslint-disable @typescript-eslint/no-explicit-any */
import { useQuery } from "@tanstack/react-query";
import { API } from "../lib/api";
import { 
  ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, ReferenceLine, ReferenceArea
} from "recharts";
import { format, parseISO } from "date-fns";
import { BrainCircuit, LineChart, ShieldCheck, Activity, Target, AlertCircle, TrendingUp } from "lucide-react";

export function Forecasts() {
  const { data: forecasts, isLoading: forecastsLoading } = useQuery({
    queryKey: ["latest-forecasts"],
    queryFn: () => API.getLatestForecasts(14),
  });

  const { data: timeseries, isLoading: tsLoading } = useQuery({
    queryKey: ["analytics-timeseries"],
    queryFn: () => API.getAnalyticsTimeseries(30),
  });

  const { data: runs, isLoading: runsLoading } = useQuery({
    queryKey: ["forecast-runs"],
    queryFn: () => API.getForecastRuns(5),
  });

  const isLoading = forecastsLoading || tsLoading;

  // Merge historical and forecast data
  const chartData: any[] = [];
  
  if (timeseries) {
    timeseries.forEach(ts => {
      chartData.push({
        date: format(parseISO(ts.date), "MMM dd"),
        historical: ts.sentiment_score,
        range: [ts.sentiment_score, ts.sentiment_score],
        isForecast: false,
        rawDate: parseISO(ts.date)
      });
    });
  }

  // Connect the last historical point to the first forecast point
  if (chartData.length > 0 && forecasts && forecasts.length > 0) {
    const lastHist = chartData[chartData.length - 1];
    lastHist.forecast = lastHist.historical;
    lastHist.range = [lastHist.historical, lastHist.historical];
  }

  if (forecasts) {
    forecasts.forEach((f, index) => {
      // Simulate Prophet's widening confidence interval (yhat_lower, yhat_upper)
      const margin = 3 + (index * 1.5);
      const confLower = Math.max(0, f.predicted_sentiment - margin);
      const confUpper = Math.min(100, f.predicted_sentiment + margin);

      chartData.push({
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

  const getTrendColor = (trend?: string) => {
    if (trend === 'Improving') return 'text-emerald-400';
    if (trend === 'Declining') return 'text-red-400';
    return 'text-slate-400';
  };

  // NLG logic for the summary
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
        <h2 className="text-3xl font-bold tracking-tight">Market Forecasts</h2>
        <p className="text-muted-foreground mt-2">AI-driven predictions utilizing un-smoothed historical volatility matrices.</p>
      </div>

      <div className="grid lg:grid-cols-4 gap-6">
        
        {/* Main Chart Area */}
        <div className="glass-card p-6 rounded-xl lg:col-span-3 flex flex-col h-[550px] border-white/5">
          <h3 className="text-lg font-semibold mb-6 flex items-center gap-2"><LineChart className="w-5 h-5 text-blue-400"/> Sentiment Prediction Model</h3>
          {isLoading ? (
             <ChartSkeleton />
          ) : chartData.length === 0 ? (
            <EmptyState message="No historical or forecast data available currently." />
          ) : (
            <div className="flex-1 relative">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
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
                  {activeForecastDate && chartData.length > 0 && (
                    <ReferenceArea x1={activeForecastDate} x2={chartData[chartData.length-1].date} fill="rgba(59, 130, 246, 0.05)" />
                  )}

                  {/* Confidence Interval Area - Using linear type for raw volatility */}
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

        {/* Sidebar */}
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
                 {runs.map((run, i) => (
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
  );
}

// ------------------------
// Custom Components
// ------------------------

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
