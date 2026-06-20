/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { API } from "../lib/api";
import { 
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip, Legend,
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  BarChart, Bar,
  AreaChart, Area
} from "recharts";
import { format, parseISO } from "date-fns";
import { Activity, Database, TrendingUp, AlertCircle, BarChart3, ListOrdered } from "lucide-react";

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
        <div className="glass-card p-6 rounded-xl col-span-full md:col-span-2 lg:col-span-2 flex flex-col border-white/5 h-[350px]">
          <h3 className="text-lg font-semibold mb-6 flex items-center gap-2 shrink-0"><TargetIcon className="w-5 h-5 text-primary"/> Thematic Extraction (7 Days)</h3>
          {topicsLoading ? <ChartSkeleton /> : !topics || (topics.positive.length === 0 && topics.negative.length === 0) ? <EmptyState message="Not enough entities extracted yet" /> : (
            <div className="grid sm:grid-cols-2 gap-8 flex-1 min-h-0">
              <div className="flex flex-col min-h-0">
                <h4 className="text-emerald-400 font-medium mb-4 flex items-center gap-2 shrink-0">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" /> Bullish Topics
                </h4>
                <div className="space-y-3 overflow-y-auto pr-2 flex-1 min-h-0">
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
              <div className="flex flex-col min-h-0">
                <h4 className="text-red-400 font-medium mb-4 flex items-center gap-2 shrink-0">
                  <span className="w-2 h-2 rounded-full bg-red-400" /> Bearish Topics
                </h4>
                <div className="space-y-3 overflow-y-auto pr-2 flex-1 min-h-0">
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
