import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { API } from "../lib/api";
import {
  Activity, Server, TrendingUp, Zap,
  RefreshCw, BarChart2, Target,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";

export function Dashboard() {
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const {
    data: stats,
    isLoading: statsLoading,
    dataUpdatedAt: statsUpdatedAt,
  } = useQuery({
    queryKey: ["analytics-stats"],
    queryFn: API.getAnalyticsStats,
    refetchInterval: 20000,
  });

  const {
    data: system,
    isLoading: systemLoading,
    dataUpdatedAt: systemUpdatedAt,
  } = useQuery({
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

  const dist = stats?.sentiment_distribution;
  const totalSentiments = dist ? dist.positive + dist.negative + dist.neutral : 0;
  // Use largest-remainder method so values always sum to 100%
  const posPct = totalSentiments > 0 ? Math.round((dist!.positive / totalSentiments) * 100) : 0;
  const negPct = totalSentiments > 0 ? Math.round((dist!.negative / totalSentiments) * 100) : 0;
  const neuPct = totalSentiments > 0 ? 100 - posPct - negPct : 0;

  const getMovementText = () => {
    if (!stats) return "Gathering data...";
    if (stats.sentiment_change > 0) return "Bullish Momentum Up";
    if (stats.sentiment_change < 0) return "Bearish Momentum Down";
    return "Stable Momentum";
  };

  const getMovementSubtext = () => {
    if (!stats) return "";
    if (stats.sentiment_change > 0) return "Market optimism increasing";
    if (stats.sentiment_change < 0) return "Negative sentiment accelerating";
    return "Minor movement detected";
  };

  const getMovementPointsText = () => {
    if (!stats) return "";
    if (stats.sentiment_change > 0) return `(+${stats.sentiment_change.toFixed(1)} pts)`;
    if (stats.sentiment_change < 0) return `(${stats.sentiment_change.toFixed(1)} pts)`;
    return "(0.0 pts)";
  };

  const getMovementPointsValue = () => {
    if (!stats) return "0.0 pts";
    if (stats.sentiment_change > 0) return `+${stats.sentiment_change.toFixed(1)} pts`;
    if (stats.sentiment_change < 0) return `${stats.sentiment_change.toFixed(1)} pts`;
    return "0.0 pts";
  };

  const getForecastFreshness = () => {
    if (!latestRun) return "Pending";
    return formatDistanceToNow(new Date(latestRun.generated_at), { addSuffix: true });
  };

  const isHeartbeatOnline =
    system?.scheduler_heartbeat &&
    new Date().getTime() - new Date(system.scheduler_heartbeat).getTime() < 5 * 60 * 1000;

  const movementColor =
    stats?.sentiment_change && stats.sentiment_change > 0
      ? "var(--color-positive)"
      : stats?.sentiment_change && stats.sentiment_change < 0
      ? "var(--color-negative)"
      : "var(--color-neutral)";

  const movementBg =
    stats?.sentiment_change && stats.sentiment_change > 0
      ? "rgba(63,191,135,0.10)"
      : stats?.sentiment_change && stats.sentiment_change < 0
      ? "rgba(229,89,79,0.10)"
      : "rgba(148,163,184,0.08)";

  return (
    <div className="space-y-8 animate-in fade-in duration-500 pb-12">

      {/* ── Page Header ──────────────────────────────────────────────────── */}
      <div
        className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 pb-6 border-b"
        style={{ borderColor: "var(--color-border)" }}
      >
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-foreground flex items-center gap-3 font-display">
            Financial Intelligence
            {/* Live pulse */}
            <span className="flex h-2 w-2 relative mt-1">
              <span
                className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-60"
                style={{ backgroundColor: "var(--color-positive)" }}
              />
              <span
                className="relative inline-flex rounded-full h-2 w-2"
                style={{ backgroundColor: "var(--color-positive)" }}
              />
            </span>
          </h2>
        </div>

        {/* Sync badge */}
        <div
          className="num flex items-center gap-1.5 flex-shrink-0"
          style={{ color: "var(--color-neutral)", fontSize: "11px" }}
        >
          <RefreshCw
            className={`w-3 h-3 ${statsLoading || systemLoading ? "animate-spin" : ""}`}
          />
          Synced {formatDistanceToNow(lastUpdated, { addSuffix: true })}
        </div>
      </div>

      {/* ── Main Grid ────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">

        {/* ── A) Market Mood Breakdown ───────────────────────────────────── */}
        <div
          className="card p-5 relative overflow-hidden hover:border-[rgba(91,141,239,0.22)] transition-colors"
        >
          <h3 className="label-section mb-4 flex items-center gap-1.5">
            <Target className="w-3 h-3" style={{ color: "var(--color-accent)" }} />
            Market Mood · {stats?.window_used || "7d"}
          </h3>

          {/* Sentiment bars */}
          <div className="space-y-4">
            {[
              { label: "Positive", pct: posPct, color: "var(--color-positive)" },
              { label: "Neutral",  pct: neuPct, color: "var(--color-neutral)"  },
              { label: "Negative", pct: negPct, color: "var(--color-negative)" },
            ].map(({ label, pct, color }) => (
              <div key={label}>
                <div className="flex justify-between items-baseline mb-1.5">
                  <span className="text-xs text-muted-foreground">{label}</span>
                  <span
                    className="num text-xl font-bold leading-none"
                    style={{ color }}
                  >
                    {pct}%
                  </span>
                </div>
                <div
                  className="h-1 w-full rounded-full overflow-hidden"
                  style={{ backgroundColor: "rgba(255,255,255,0.05)" }}
                >
                  <div
                    className="h-full rounded-full transition-all duration-1000"
                    style={{ width: `${pct}%`, backgroundColor: color }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ── B) Trending Companies ─────────────────────────────────────── */}
        <div className="card p-5">
          <h3 className="label-section mb-4 flex items-center gap-1.5">
            <BarChart2 className="w-3 h-3" style={{ color: "var(--color-accent)" }} />
            Top Companies · {stats?.window_used || "7d"}
          </h3>

          <div className="space-y-2">
            {statsLoading ? (
              <div className="space-y-2">
                {[1,2,3,4,5].map(i => (
                  <div key={i} className="h-10 rounded animate-pulse" style={{ backgroundColor: "rgba(255,255,255,0.04)" }} />
                ))}
              </div>
            ) : stats?.trending_companies?.length === 0 ? (
              <p className="text-xs text-muted-foreground py-4">No companies tracked in this window.</p>
            ) : (
              stats?.trending_companies.slice(0, 5).map((company, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between py-2 border-b last:border-0"
                  style={{ borderColor: "var(--color-border)" }}
                >
                  <div className="flex items-center gap-2.5">
                    <span
                      className="num text-[10px] font-bold w-4 text-right flex-shrink-0"
                      style={{ color: "var(--color-neutral)" }}
                    >
                      {idx + 1}
                    </span>
                    <span className="text-sm font-medium text-foreground">{company.company}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="num text-xs text-muted-foreground">{company.mentions}m</span>
                    <span
                      className="text-xs font-bold"
                      style={{
                        color: company.direction === "up"
                          ? "var(--color-positive)"
                          : company.direction === "down"
                          ? "var(--color-negative)"
                          : "var(--color-neutral)"
                      }}
                    >
                      {company.direction === "up" ? "↑" : company.direction === "down" ? "↓" : "—"}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* ── C) Momentum Shift ────────────────────────────────────────── */}
        <div className="card p-5 flex flex-col">
          <h3 className="label-section mb-4 flex items-center gap-1.5">
            <Activity className="w-3 h-3" style={{ color: "var(--color-accent)" }} />
            Momentum Shift
          </h3>
          <div className="flex-1 flex flex-col justify-center items-center text-center gap-3">
            {statsLoading ? (
              <div
                className="w-10 h-10 rounded-full animate-pulse"
                style={{ backgroundColor: "rgba(255,255,255,0.06)" }}
              />
            ) : (
              <div
                className="p-3 rounded-full"
                style={{ backgroundColor: movementBg }}
              >
                {stats?.sentiment_change && stats.sentiment_change > 0
                  ? <TrendingUp className="w-6 h-6" style={{ color: movementColor }} />
                  : stats?.sentiment_change && stats.sentiment_change < 0
                  ? <TrendingUp className="w-6 h-6 rotate-180" style={{ color: movementColor }} />
                  : <Activity className="w-6 h-6" style={{ color: movementColor }} />
                }
              </div>
            )}
            <div>
              <p className="text-lg font-bold" style={{ color: movementColor }}>{getMovementText()}</p>
              <div className="text-xs text-muted-foreground mt-1.5 space-y-1">
                <p>{getMovementSubtext()}</p>
                <p>{getMovementPointsText()}</p>
              </div>
            </div>
            {!statsLoading && stats && (
              <div className="mt-2">
                <span className="badge" style={{ color: movementColor, backgroundColor: movementBg }}>
                  {getMovementPointsValue()}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* ── D) Processing Metrics ────────────────────────────────────── */}
        <div className="card p-5 lg:col-span-2">
          <h3 className="label-section mb-4 flex items-center gap-1.5">
            <Server className="w-3 h-3" style={{ color: "var(--color-accent)" }} />
            System Processing
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              {
                label: "Last Ingestion",
                value: system?.last_activity
                  ? formatDistanceToNow(new Date(system.last_activity), { addSuffix: true })
                  : "N/A",
                color: "var(--color-positive)"
              },
              {
                label: "Last Sentiment Run",
                value: system?.last_sentiment_time
                  ? formatDistanceToNow(new Date(system.last_sentiment_time), { addSuffix: true })
                  : "N/A",
                color: "var(--color-accent)"
              },
              {
                label: "Articles/hr",
                value: String(system?.articles_per_hour || 0),
                color: "var(--color-positive)"
              },
              {
                label: "Total Analyzed",
                value: String(stats?.total_articles || 0),
                color: "var(--color-accent)"
              },
            ].map(({ label, value, color }) => (
              <div
                key={label}
                className="card-elevated p-3 rounded-lg"
              >
                <p className="label-section mb-1.5">{label}</p>
                <p className="num text-sm font-bold" style={{ color }}>{value}</p>
              </div>
            ))}
          </div>

          {/* Scheduler heartbeat row */}
          <div
            className="mt-4 pt-4 flex items-center justify-between"
            style={{ borderTop: "1px solid var(--color-border)" }}
          >
            <span className="text-xs text-muted-foreground">Scheduler Heartbeat</span>
            {isHeartbeatOnline ? (
              <span className="badge badge-positive">Online</span>
            ) : (
              <span className="badge badge-negative">Offline</span>
            )}
          </div>
        </div>

        {/* ── E) Forecast Intelligence Summary ─────────────────────────── */}
        <div className="card p-5">
          <h3 className="label-section mb-4 flex items-center gap-1.5">
            <Zap className="w-3 h-3" style={{ color: "var(--color-accent)" }} />
            AI Forecast
          </h3>
          {runsLoading ? (
            <div className="space-y-3">
              {[1,2,3].map(i => (
                <div key={i} className="h-12 rounded animate-pulse" style={{ backgroundColor: "rgba(255,255,255,0.04)" }} />
              ))}
            </div>
          ) : !latestRun ? (
            <p className="text-xs text-muted-foreground py-4">No active forecast models running.</p>
          ) : (
            <div className="space-y-3">
              <div
                className="card-elevated p-3 rounded-lg flex items-center justify-between"
              >
                <span className="text-xs text-muted-foreground">Direction</span>
                <span
                  className="num text-sm font-bold"
                  style={{
                    color: latestRun.trend === "Improving"
                      ? "var(--color-positive)"
                      : latestRun.trend === "Declining"
                      ? "var(--color-negative)"
                      : "var(--color-neutral)"
                  }}
                >
                  {latestRun.trend === "Improving" ? "Bullish" : latestRun.trend === "Declining" ? "Bearish" : "Neutral"}
                </span>
              </div>
              <div className="card-elevated p-3 rounded-lg flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Freshness</span>
                <span className="num text-xs font-medium text-muted-foreground">{getForecastFreshness()}</span>
              </div>
              <div className="card-elevated p-3 rounded-lg flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Total Forecasts</span>
                <span className="num text-sm font-bold" style={{ color: "var(--color-accent)" }}>
                  {stats?.total_forecasts || 0}
                </span>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
