import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { API } from "../lib/api";
import { AlertTriangle, Lightbulb, TrendingUp, Sparkles, Clock } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface Props {
  companyName: string;
}

export function AISummaryCard({ companyName }: Props) {
  const [showSummary, setShowSummary] = useState(false);

  // Check if cache exists without generating
  const { data: status, isLoading: isStatusLoading } = useQuery({
    queryKey: ["company-summary-status", companyName],
    queryFn: () => API.checkCompanySummaryStatus(companyName),
    staleTime: 1000 * 60 * 5, // check every 5 minutes
  });

  // Only fetch the full summary when the user clicks the button
  const { data: summary, isLoading, isError, isFetching } = useQuery({
    queryKey: ["company-summary", companyName],
    queryFn: () => API.getCompanySummary(companyName),
    enabled: showSummary,
    staleTime: 1000 * 60 * 60, // 1 hour frontend stale time
    retry: false,
  });

  if (!showSummary) {
    return (
      <div className="glass-card p-8 rounded-2xl border-primary/30 relative overflow-hidden flex flex-col items-center justify-center text-center">
        <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-primary to-purple-500" />
        <Sparkles className="w-10 h-10 text-primary mb-4" />
        <h3 className="text-xl font-bold mb-2">AI Intelligence Summary</h3>
        <p className="text-muted-foreground mb-6 max-w-lg">
          Generate an on-demand executive summary, risk analysis, and forecast outlook.
        </p>
        <button
          onClick={() => setShowSummary(true)}
          disabled={isStatusLoading}
          className="px-6 py-3 bg-primary text-primary-foreground font-semibold rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          {isStatusLoading 
            ? "Checking status..." 
            : status?.is_cached 
              ? "View AI Summary" 
              : "Generate AI Intelligence Summary"}
        </button>
      </div>
    );
  }

  if (isLoading || isFetching) {
    return (
      <div className="glass-card p-8 rounded-2xl border-primary/30 relative overflow-hidden animate-pulse">
        <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-primary to-purple-500" />
        <div className="flex items-center gap-3 mb-6">
          <Sparkles className="w-6 h-6 text-primary" />
          <div className="h-6 w-48 bg-white/10 rounded" />
        </div>
        <div className="space-y-4">
          <div className="h-4 w-full bg-white/5 rounded" />
          <div className="h-4 w-5/6 bg-white/5 rounded" />
          <div className="h-4 w-4/6 bg-white/5 rounded" />
        </div>
      </div>
    );
  }

  if (isError || !summary) {
    return (
      <div className="glass-card p-6 rounded-2xl border-red-500/30 flex flex-col items-center justify-center text-center">
        <p className="text-red-400 mb-4">Unable to generate summary at this time.</p>
        <button
          onClick={() => setShowSummary(false)}
          className="px-4 py-2 border border-red-500/50 text-red-400 rounded-lg hover:bg-red-500/10 transition-colors"
        >
          Close
        </button>
      </div>
    );
  }

  return (
    <div className="glass-card p-8 rounded-2xl border-primary/30 relative overflow-hidden">
      <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-primary to-purple-500" />
      
      <div className="flex justify-between items-start mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-primary/20 rounded-xl">
            <Sparkles className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h3 className="text-xl font-bold">Executive Summary</h3>
            <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
              {summary.generated_at && (
                <span className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" />
                  Generated {formatDistanceToNow(new Date(summary.generated_at), { addSuffix: true })}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      <p className="text-slate-200 leading-relaxed mb-8 text-lg">
        {summary.executive_summary}
      </p>

      <div className="grid md:grid-cols-3 gap-6">
        <div className="bg-white/5 p-5 rounded-xl border border-white/5 hover:bg-white/10 transition-colors">
          <h4 className="flex items-center gap-2 text-red-400 font-semibold mb-4">
            <AlertTriangle className="w-5 h-5" /> Key Risks
          </h4>
          <ul className="space-y-3">
            {summary.risks.map((risk, i) => (
              <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-red-400/50 mt-1.5 flex-shrink-0" />
                {risk}
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-white/5 p-5 rounded-xl border border-white/5 hover:bg-white/10 transition-colors">
          <h4 className="flex items-center gap-2 text-emerald-400 font-semibold mb-4">
            <Lightbulb className="w-5 h-5" /> Key Opportunities
          </h4>
          <ul className="space-y-3">
            {summary.opportunities.map((opp, i) => (
              <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400/50 mt-1.5 flex-shrink-0" />
                {opp}
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-white/5 p-5 rounded-xl border border-white/5 hover:bg-white/10 transition-colors">
          <h4 className="flex items-center gap-2 text-blue-400 font-semibold mb-4">
            <TrendingUp className="w-5 h-5" /> Forecast Outlook
          </h4>
          <p className="text-sm text-slate-300 leading-relaxed">
            {summary.forecast_outlook}
          </p>
        </div>
      </div>
    </div>
  );
}
