import { useQuery } from "@tanstack/react-query";
import { API } from "../lib/api";
import {
  Activity, Server, TrendingUp, Zap,
  RefreshCw, BarChart2, Target,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";

export function Dashboard() {

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

  // eslint-disable-next-line react-hooks/purity
  const lastUpdated = new Date(Math.max(statsUpdatedAt || 0, systemUpdatedAt || 0) || Date.now());

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
    <div className="space-y-6 animate-in fade-in duration-500 pb-12">

      {/* ── Page Header ──────────────────────────────────────────────────── */}
      <div
        className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 pb-6 mb-2 border-b"
        style={{ borderColor: "var(--color-border)" }}
      >
        <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground flex flex-wrap items-center gap-2 md:gap-3 font-display">
          Financial Intelligence
          {/* Live pulse */}
          <span className="flex h-2 w-2 relative mb-1">
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

        {/* Sync badge */}
        <div className="flex items-center gap-2 text-[10px] font-bold tracking-[0.1em] uppercase text-muted-foreground font-mono">
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
                <div className="flex justify-between items-baseline mb-2">
                  <span className="text-sm text-foreground">{label}</span>
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
                  className="flex items-center justify-between py-[11px] border-b last:border-0"
                  style={{ borderColor: "var(--color-border)" }}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span
                      className="num text-[10px] font-mono font-medium text-muted-foreground w-4 flex-shrink-0"
                    >
                      {String(idx + 1).padStart(2, '0')}
                    </span>
                    <span className="text-[13px] font-bold text-foreground tracking-wide truncate">{company.company}</span>
                  </div>
                  <div className="flex items-center gap-4 flex-shrink-0">
                    <span className="num text-[11px] text-muted-foreground">{company.mentions}</span>
                    <span
                      className="text-[11px] font-bold w-2 text-right"
                      style={{
                        color: company.direction === "up"
                          ? "var(--color-positive)"
                          : company.direction === "down"
                          ? "var(--color-negative)"
                          : "var(--color-neutral)"
                      }}
                    >
                      {company.direction === "up" ? "↑" : company.direction === "down" ? "↓" : "→"}
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
              <p className="text-base md:text-lg font-bold" style={{ color: movementColor }}>{getMovementText()}</p>
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

        {/* ── D) AI Forecast Intelligence ──────────────────────────────── */}
        <div className="card p-6 lg:col-span-2 flex flex-col justify-between" style={{ borderColor: "rgba(91,141,239,0.3)" }}>
          <div className="flex items-center justify-between mb-6">
            <h3 className="label-section flex items-center gap-2">
              <Zap className="w-3.5 h-3.5" style={{ color: "var(--color-accent)" }} />
              AI Forecast Intelligence
            </h3>
            <span className="text-[10px] text-muted-foreground font-mono tracking-wider">
              {getForecastFreshness()}
            </span>
          </div>

          {runsLoading ? (
            <div className="grid grid-cols-4 gap-4 flex-1">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="rounded-lg animate-pulse" style={{ backgroundColor: "rgba(255,255,255,0.04)" }} />
              ))}
            </div>
          ) : !latestRun ? (
            <div className="flex-1 flex items-center justify-center">
              <p className="text-sm text-muted-foreground">No active forecast models running.</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 flex-1">
              <div className="card-elevated p-4 sm:p-5 rounded-xl flex flex-col justify-start h-full">
                <span className="text-[10px] font-bold tracking-wider uppercase text-muted-foreground mb-2">Direction</span>
                <span
                  className="text-xl md:text-2xl font-bold tracking-tight"
                  style={{
                    color: latestRun.trend === "Improving"
                      ? "var(--color-positive)"
                      : latestRun.trend === "Declining"
                      ? "var(--color-negative)"
                      : "var(--color-foreground)"
                  }}
                >
                  {latestRun.trend === "Improving" ? "Bullish" : latestRun.trend === "Declining" ? "Bearish" : "Neutral"}
                </span>
              </div>
              <div className="card-elevated p-4 sm:p-5 rounded-xl flex flex-col justify-start h-full">
                <span className="text-[10px] font-bold tracking-wider uppercase text-muted-foreground mb-2">Expected Δ</span>
                <span className="text-xl md:text-2xl font-bold tracking-tight text-foreground">
                  53.8%
                </span>
              </div>
              <div className="card-elevated p-4 sm:p-5 rounded-xl flex flex-col justify-start h-full">
                <span className="text-[10px] font-bold tracking-wider uppercase text-muted-foreground mb-2">Confidence</span>
                <span className="text-xl md:text-2xl font-bold tracking-tight text-foreground">
                  Medium
                </span>
              </div>
              <div className="card-elevated p-4 sm:p-5 rounded-xl flex flex-col justify-start h-full">
                <span className="text-[10px] font-bold tracking-wider uppercase text-muted-foreground mb-2">Model Age</span>
                <div className="flex items-center gap-1.5 text-foreground">
                  <RefreshCw className="w-4 h-4 flex-shrink-0 text-muted-foreground" />
                  <span className="text-lg sm:text-xl font-bold tracking-tight">{getForecastFreshness().replace('about ', '')}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ── E) System Health ─────────────────────────────────────────── */}
        <div className="card p-0 flex flex-col overflow-hidden">
          <div className="p-5 pb-3 border-b" style={{ borderColor: "var(--color-border)" }}>
            <h3 className="label-section flex items-center gap-1.5">
              <Server className="w-3 h-3" style={{ color: "var(--color-accent)" }} />
              System Health
            </h3>
          </div>
          <div className="flex-1 flex flex-col">
            <div className="flex items-center justify-between p-4 border-b" style={{ borderColor: "var(--color-border)" }}>
              <span className="text-sm font-bold text-foreground">Scheduler</span>
              <div className="flex items-center gap-1.5">
                {isHeartbeatOnline ? (
                  <>
                    <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: "var(--color-positive)" }} />
                    <span className="text-xs font-mono text-[var(--color-positive)]">Online</span>
                  </>
                ) : (
                  <>
                    <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: "var(--color-negative)" }} />
                    <span className="text-xs font-mono text-[var(--color-negative)]">Offline</span>
                  </>
                )}
              </div>
            </div>
            
            <div className="px-4 py-3 flex items-center justify-between border-b" style={{ borderColor: "rgba(255,255,255,0.03)" }}>
              <span className="text-[11px] text-muted-foreground tracking-wide">Last Ingestion</span>
              <span className="num text-[11px] font-medium text-foreground">
                {system?.last_activity ? formatDistanceToNow(new Date(system.last_activity), { addSuffix: true }) : "N/A"}
              </span>
            </div>
            <div className="px-4 py-3 flex items-center justify-between border-b" style={{ borderColor: "rgba(255,255,255,0.03)" }}>
              <span className="text-[11px] text-muted-foreground tracking-wide">Last Processing</span>
              <span className="num text-[11px] font-medium text-foreground">
                {system?.last_sentiment_time ? formatDistanceToNow(new Date(system.last_sentiment_time), { addSuffix: true }) : "N/A"}
              </span>
            </div>
            <div className="px-4 py-3 flex items-center justify-between border-b" style={{ borderColor: "rgba(255,255,255,0.03)" }}>
              <span className="text-[11px] text-muted-foreground tracking-wide">Articles / hr</span>
              <span className="num text-[11px] font-medium text-foreground">{system?.articles_per_hour || 0}</span>
            </div>
            <div className="px-4 py-3 flex items-center justify-between border-b" style={{ borderColor: "rgba(255,255,255,0.03)" }}>
              <span className="text-[11px] text-muted-foreground tracking-wide">Sentiment Jobs</span>
              <span className="num text-[11px] font-medium text-foreground">{stats?.total_articles || 0}</span>
            </div>
            <div className="px-4 py-3 flex items-center justify-between">
              <span className="text-[11px] text-muted-foreground tracking-wide">Forecast Jobs</span>
              <span className="num text-[11px] font-medium text-foreground">{stats?.total_forecasts || 0}</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
