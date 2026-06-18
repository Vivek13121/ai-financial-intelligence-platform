import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { API } from "../lib/api";
import {
  ArrowLeft, Activity, Newspaper,
  TrendingUp, TrendingDown, Minus, ExternalLink,
  BarChart2
} from "lucide-react";
import {
  AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  ResponsiveContainer, LineChart, Line
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
      <div className="space-y-6 animate-in fade-in duration-300 pb-10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full animate-pulse" style={{ backgroundColor: "rgba(255,255,255,0.06)" }} />
          <div className="space-y-2">
            <div className="h-7 w-48 rounded animate-pulse" style={{ backgroundColor: "rgba(255,255,255,0.06)" }} />
            <div className="h-3 w-32 rounded animate-pulse" style={{ backgroundColor: "rgba(255,255,255,0.04)" }} />
          </div>
        </div>
        <div className="grid md:grid-cols-3 gap-4">
          {[1,2,3].map(i => (
            <div key={i} className="card p-5 h-20 animate-pulse" style={{ backgroundColor: "rgba(255,255,255,0.04)" }} />
          ))}
        </div>
        <div className="card h-64 animate-pulse" style={{ backgroundColor: "rgba(255,255,255,0.04)" }} />
        <div className="grid lg:grid-cols-3 gap-5">
          <div className="card lg:col-span-2 h-[320px] animate-pulse" style={{ backgroundColor: "rgba(255,255,255,0.04)" }} />
          <div className="card h-[320px] animate-pulse" style={{ backgroundColor: "rgba(255,255,255,0.04)" }} />
        </div>
      </div>
    );
  }

  if (isError || !intel) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-4">
        <p className="text-sm" style={{ color: "var(--color-negative)" }}>Failed to load intelligence data.</p>
        <button
          onClick={() => navigate("/search")}
          className="btn-ghost flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Search
        </button>
      </div>
    );
  }

  const getScoreColor = (score: number) => {
    if (score > 60) return "var(--color-positive)";
    if (score < 40) return "var(--color-negative)";
    return "var(--color-neutral)";
  };

  const getTrendIcon = (direction: string) => {
    if (direction === "Bullish") return <TrendingUp className="w-5 h-5" style={{ color: "var(--color-positive)" }} />;
    if (direction === "Bearish") return <TrendingDown className="w-5 h-5" style={{ color: "var(--color-negative)" }} />;
    return <Minus className="w-5 h-5" style={{ color: "var(--color-neutral)" }} />;
  };

  const tsData = intel.sentiment_trend.map(d => ({
    ...d,
    formattedDate: format(parseISO(d.date), "MMM dd"),
  }));

  const forecastData = intel.forecast.map(d => ({
    ...d,
    formattedDate: format(parseISO(d.date), "MMM dd"),
  }));

  if (tsData.length > 0 && forecastData.length > 0) {
    forecastData.unshift({
      ...tsData[tsData.length - 1],
      predicted_sentiment: tsData[tsData.length - 1].sentiment_score,
    } as any);
  }

  const pieData = [
    { name: "Positive", value: intel.sentiment_distribution.positive, color: "var(--color-positive)" },
    { name: "Neutral",  value: intel.sentiment_distribution.neutral,  color: "var(--color-neutral)"  },
    { name: "Negative", value: intel.sentiment_distribution.negative, color: "var(--color-negative)" },
  ];

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div
          className="card-elevated p-3 rounded-lg shadow-xl"
          style={{ fontSize: "11px", border: "1px solid var(--color-border)" }}
        >
          <p className="text-muted-foreground mb-1">{label}</p>
          {payload.map((entry: any, i: number) => (
            <div key={i} className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color || entry.stroke }} />
              <span className="font-semibold num" style={{ color: entry.color || entry.stroke }}>
                {typeof entry.value === "number" ? entry.value.toFixed(1) : entry.value}
              </span>
              <span className="text-muted-foreground">{entry.name}</span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300 pb-10">

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate("/search")}
          className="p-1.5 rounded-lg transition-colors text-muted-foreground hover:text-foreground"
          style={{ border: "1px solid var(--color-border)" }}
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-foreground font-display">
            {intel.company_name}
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">Company Intelligence Report</p>
        </div>
      </div>

      {/* ── KPI Cards ────────────────────────────────────────────────────── */}
      <div className="grid md:grid-cols-3 gap-4">
        {/* Total Articles */}
        <div className="card p-5 flex items-center gap-4">
          <div
            className="p-2.5 rounded-lg flex-shrink-0"
            style={{ backgroundColor: "rgba(91,141,239,0.10)" }}
          >
            <Newspaper className="w-4 h-4" style={{ color: "var(--color-accent)" }} />
          </div>
          <div>
            <p className="label-section mb-1">Analyzed Articles</p>
            <p className="num text-3xl font-bold text-foreground">{intel.overview.total_articles}</p>
          </div>
        </div>

        {/* Current Sentiment */}
        <div className="card p-5 flex items-center gap-4">
          <div
            className="p-2.5 rounded-lg flex-shrink-0"
            style={{ backgroundColor: "rgba(63,191,135,0.08)" }}
          >
            <Activity className="w-4 h-4" style={{ color: "var(--color-positive)" }} />
          </div>
          <div>
            <p className="label-section mb-1">Current Sentiment</p>
            <p className="num text-3xl font-bold" style={{ color: getScoreColor(intel.overview.current_sentiment) }}>
              {intel.overview.current_sentiment.toFixed(1)}
            </p>
          </div>
        </div>

        {/* Forecast Direction */}
        <div className="card p-5 flex items-center gap-4">
          <div
            className="p-2.5 rounded-lg flex-shrink-0"
            style={{ backgroundColor: "rgba(255,255,255,0.04)" }}
          >
            {getTrendIcon(intel.overview.forecast_direction)}
          </div>
          <div>
            <p className="label-section mb-1">Forecast Direction</p>
            <p className="num text-3xl font-bold text-foreground">{intel.overview.forecast_direction}</p>
          </div>
        </div>
      </div>

      {/* ── AI Insight Panel ─────────────────────────────────────────────── */}
      <div
        className="card p-6 relative overflow-hidden"
        style={{ borderLeft: "3px solid var(--color-accent)" }}
      >
        <div className="flex gap-4 items-start">
          <div className="flex-shrink-0">
            <BarChart2 className="w-5 h-5 mt-0.5" style={{ color: "var(--color-accent)" }} />
          </div>
          <div>
            <h3 className="label-section mb-2">Intelligence Insight</h3>
            <p className="text-sm text-foreground leading-relaxed opacity-90">
              {intel.insights}
            </p>
          </div>
        </div>
      </div>

      {/* ── Charts Grid ──────────────────────────────────────────────────── */}
      <div className="grid lg:grid-cols-3 gap-5">

        {/* Sentiment Trend */}
        <div className="card p-5 lg:col-span-2 flex flex-col">
          <h3 className="label-section mb-4">Historical Trend · 30 Days</h3>
          <div className="flex-1 min-h-[260px]">
            {tsData.length === 0 ? (
              <div className="h-full flex items-center justify-center">
                <p className="text-xs text-muted-foreground">Insufficient historical data</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={tsData} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
                  <CartesianGrid
                    strokeDasharray="2 4"
                    stroke="rgba(255,255,255,0.04)"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="formattedDate"
                    stroke="transparent"
                    tick={{ fill: "var(--color-neutral)", fontSize: 10 }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    stroke="transparent"
                    tick={{ fill: "var(--color-neutral)", fontSize: 10 }}
                    tickLine={false}
                    axisLine={false}
                    domain={[0, 100]}
                  />
                  <RechartsTooltip content={<CustomTooltip />} cursor={{ stroke: "rgba(255,255,255,0.06)", strokeWidth: 1 }} />
                  <Line
                    type="monotone"
                    dataKey="sentiment_score"
                    name="Sentiment"
                    stroke="var(--color-accent)"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 3, fill: "var(--color-accent)" }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Distribution Pie */}
        <div className="card p-5 flex flex-col">
          <h3 className="label-section mb-4">Sentiment Distribution</h3>
          <div className="flex-1 min-h-[200px]">
            {pieData.every(d => d.value === 0) ? (
              <div className="h-full flex items-center justify-center">
                <p className="text-xs text-muted-foreground">No distribution data</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={75}
                    paddingAngle={3}
                    dataKey="value"
                    strokeWidth={0}
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} opacity={0.85} />
                    ))}
                  </Pie>
                  <RechartsTooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Legend */}
          <div className="space-y-2 mt-2">
            {pieData.map(({ name, value, color }) => {
              const total = pieData.reduce((s, d) => s + d.value, 0);
              const pct = total > 0 ? Math.round((value / total) * 100) : 0;
              return (
                <div key={name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
                    <span className="text-xs text-muted-foreground">{name}</span>
                  </div>
                  <span className="num text-xs font-semibold" style={{ color }}>{pct}%</span>
                </div>
              );
            })}
          </div>
        </div>

      </div>

      {/* ── Forecast Chart ───────────────────────────────────────────────── */}
      <div className="card p-5 flex flex-col">
        <h3 className="label-section mb-4">7-Day Sentiment Forecast</h3>
        <div className="min-h-[200px]">
          {forecastData.length <= 1 ? (
            <div className="h-full flex items-center justify-center">
              <p className="text-xs text-muted-foreground">Insufficient forecast data</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={forecastData} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
                <defs>
                  <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--color-accent)" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="var(--color-accent)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.04)" vertical={false} />
                <XAxis
                  dataKey="formattedDate"
                  stroke="transparent"
                  tick={{ fill: "var(--color-neutral)", fontSize: 10 }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  stroke="transparent"
                  tick={{ fill: "var(--color-neutral)", fontSize: 10 }}
                  tickLine={false}
                  axisLine={false}
                  domain={[0, 100]}
                />
                <RechartsTooltip content={<CustomTooltip />} cursor={{ stroke: "rgba(255,255,255,0.06)", strokeWidth: 1 }} />
                <Area
                  type="monotone"
                  dataKey="predicted_sentiment"
                  name="Forecast"
                  stroke="var(--color-accent)"
                  strokeWidth={2}
                  strokeDasharray="5 4"
                  fillOpacity={1}
                  fill="url(#forecastGrad)"
                  dot={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* ── News Feed ────────────────────────────────────────────────────── */}
      <div className="card p-5">
        <h3 className="label-section mb-4 flex items-center gap-1.5">
          <Newspaper className="w-3 h-3" style={{ color: "var(--color-accent)" }} />
          Recent Coverage · {intel.company_name}
        </h3>

        <div className="divide-y" style={{ borderColor: "var(--color-border)" }}>
          {intel.news_feed.length === 0 ? (
            <p className="text-xs text-muted-foreground py-4">No recent news found for this company.</p>
          ) : intel.news_feed.map((article) => {
            const compactTime = article.published_at
              ? format(new Date(article.published_at), "MMM d")
              : "—";
            return (
              <div key={article.id} className="py-3 flex items-start gap-4">
                <span className="num text-[10px] text-muted-foreground w-10 flex-shrink-0 pt-0.5">{compactTime}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground leading-snug line-clamp-2">
                    {article.title}
                  </p>
                </div>
                {article.article_url && (
                  <a
                    href={article.article_url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex-shrink-0 text-muted-foreground hover:text-foreground transition-colors mt-0.5"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                )}
              </div>
            );
          })}
        </div>
      </div>

    </div>
  );
}
