/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { API, type AISummaryResponse } from "../lib/api";
import { 
  AlertTriangle, Lightbulb, TrendingUp,
  RefreshCw, Clock, CheckCircle2, ChevronDown, ChevronUp, AlertCircle,
  FileText, FileSearch
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface AISummaryCardProps {
  companyName: string;
}

export function AISummaryCard({ companyName }: AISummaryCardProps) {
  const queryClient = useQueryClient();
  const [isExpanded, setIsExpanded] = useState(true);

  // Check if we have a cached summary
  const { data: statusData, isLoading: statusLoading } = useQuery({
    queryKey: ["ai-summary-status", companyName],
    queryFn: () => API.getAISummaryStatus(companyName),
    refetchInterval: 60000,
  });

  // Fetch the actual summary only if it's cached OR if user clicks Generate
  const { data: summary, isLoading: summaryLoading, isError: summaryError, error } = useQuery<AISummaryResponse>({
    queryKey: ["ai-summary", companyName],
    queryFn: () => API.getAISummary(companyName),
    enabled: !!statusData?.is_cached,
    staleTime: 1000 * 60 * 60 * 6, // 6 hours
  });

  // Mutation to trigger generation (essentially forces the query to run and update cache)
  const generateMutation = useMutation({
    mutationFn: () => API.getAISummary(companyName),
    onSuccess: (data) => {
      queryClient.setQueryData(["ai-summary", companyName], data);
      queryClient.invalidateQueries({ queryKey: ["ai-summary-status", companyName] });
      setIsExpanded(true);
    },
  });

  const handleGenerate = () => {
    generateMutation.mutate();
  };

  const isGenerating = generateMutation.isPending;

  return (
    <div className="card p-6 relative overflow-hidden" style={{ borderTop: "3px solid var(--color-accent)" }}>
      {/* Background glow */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-[var(--color-accent)] opacity-[0.03] blur-3xl rounded-full pointer-events-none -translate-y-1/2 translate-x-1/4" />

      {/* Header */}
      <div className="flex items-start justify-between mb-6 relative z-10">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-xl" style={{ backgroundColor: "rgba(91,141,239,0.12)", border: "1px solid rgba(91,141,239,0.2)" }}>
            <FileText className="w-6 h-6" style={{ color: "var(--color-accent)" }} />
          </div>
          <div>
            <h3 className="text-xl font-bold text-foreground flex items-center gap-2">
              Executive Summary
              {summary && (
                <span className="badge badge-positive flex items-center gap-1.5 ml-2">
                  <CheckCircle2 className="w-3 h-3" /> Ready
                </span>
              )}
            </h3>
            <p className="text-sm text-muted-foreground mt-1">
              AI-generated executive analysis covering risks, opportunities, and sentiment forecast.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {summary?.generated_at && (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground mr-2 font-mono">
              <Clock className="w-3.5 h-3.5" />
              {formatDistanceToNow(new Date(summary.generated_at), { addSuffix: true })}
            </div>
          )}
          
          {summary && (
            <button 
              onClick={() => setIsExpanded(!isExpanded)}
              className="btn-ghost !p-2"
              title={isExpanded ? "Collapse" : "Expand"}
            >
              {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          )}
        </div>
      </div>

      {/* Content Area */}
      <div className="relative z-10">
        {summaryError || generateMutation.isError ? (
          <div className="card-elevated p-6 flex flex-col items-center justify-center gap-3 border-[var(--color-negative)] border-opacity-30">
            <AlertCircle className="w-8 h-8 text-[var(--color-negative)]" />
            <p className="text-sm text-[var(--color-negative)] font-medium">
              {(error as any)?.response?.data?.detail || generateMutation.error?.message || "Failed to generate AI report. Please try again."}
            </p>
            <button onClick={handleGenerate} className="btn-primary mt-2">
              Retry Generation
            </button>
          </div>
        ) : isGenerating ? (
          <div className="card-elevated p-8 flex flex-col items-center justify-center gap-4">
            <div className="relative w-12 h-12 flex items-center justify-center">
              <div className="absolute inset-0 border-2 border-[var(--color-border)] rounded-full" />
              <div className="absolute inset-0 border-2 border-[var(--color-accent)] rounded-full border-t-transparent animate-spin" />
              <FileSearch className="w-5 h-5 text-[var(--color-accent)] animate-pulse" />
            </div>
            <div className="text-center">
              <p className="font-semibold text-foreground">Synthesizing Intelligence...</p>
              <p className="text-xs text-muted-foreground mt-1 font-mono">Running Gemini 3.5 Flash pipeline</p>
            </div>
          </div>
        ) : !summary ? (
          <div className="card-elevated p-8 flex flex-col items-center justify-center gap-5 text-center">
            <div className="p-4 rounded-full bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.05)]">
              <FileSearch className="w-8 h-8 text-muted-foreground" />
            </div>
            <div>
              <p className="text-foreground font-medium text-lg"></p>
              <p className="text-sm text-muted-foreground max-w-md mx-auto mt-2 leading-relaxed">
                Generate a comprehensive AI report for {companyName} to unlock executive summaries, risk analysis, and forecasting insights.
              </p>
            </div>
            <button 
              onClick={handleGenerate} 
              className="btn-primary shadow-[0_0_20px_rgba(91,141,239,0.3)] hover:shadow-[0_0_30px_rgba(91,141,239,0.5)] transition-all px-6 py-3"
            >
              <RefreshCw className="w-4 h-4" />
              Generate Intelligence Report
            </button>
          </div>
        ) : summary && isExpanded ? (
          <div className="space-y-6 animate-in slide-in-from-top-4 duration-300">
            {/* Executive Summary */}
            <div className="space-y-2">
              <h4 className="label-section flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                Executive Summary
              </h4>
              <p className="text-sm text-foreground leading-relaxed opacity-90 pl-5 border-l-2 border-[var(--color-border)]">
                {summary.executive_summary}
              </p>
            </div>

            <div className="grid md:grid-cols-2 gap-6 pt-2">
              {/* Risks */}
              <div className="space-y-3">
                <h4 className="label-section flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-[var(--color-negative)]" />
                  Key Risks
                </h4>
                <ul className="space-y-2 pl-5 border-l-2 border-[var(--color-border)]">
                  {summary.risks.map((risk, idx) => (
                    <li key={idx} className="text-sm text-foreground opacity-90 leading-relaxed flex items-start gap-2">
                      <span className="text-[var(--color-negative)] mt-0.5">•</span>
                      <span>{risk}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Opportunities */}
              <div className="space-y-3">
                <h4 className="label-section flex items-center gap-1.5">
                  <Lightbulb className="w-3.5 h-3.5 text-[var(--color-positive)]" />
                  Key Opportunities
                </h4>
                <ul className="space-y-2 pl-5 border-l-2 border-[var(--color-border)]">
                  {summary.opportunities.map((opp, idx) => (
                    <li key={idx} className="text-sm text-foreground opacity-90 leading-relaxed flex items-start gap-2">
                      <span className="text-[var(--color-positive)] mt-0.5">•</span>
                      <span>{opp}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Forecast Outlook */}
            <div className="space-y-2 pt-2 border-t border-[var(--color-border)]">
              <h4 className="label-section flex items-center gap-1.5 pt-4">
                <TrendingUp className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                Forecast Outlook
              </h4>
              <p className="text-sm text-foreground leading-relaxed opacity-90 pl-5 border-l-2 border-[var(--color-border)]">
                {summary.forecast_outlook}
              </p>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
