import { useQuery } from "@tanstack/react-query";
import { API } from "../lib/api";
import type { Article } from "../lib/api";
import { formatDistanceToNow } from "date-fns";
import { ExternalLink } from "lucide-react";

export function LiveFeed() {
  const { data: articles, isLoading } = useQuery({
    queryKey: ["articles"],
    queryFn: () => API.getArticles(0, 50),
    refetchInterval: 15000,
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-500 pb-12">
      
      {/* ── Page Header ──────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 pb-6 mb-2 border-b" style={{ borderColor: "var(--color-border)" }}>
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-foreground font-display">
            Live News Feed
          </h2>
          <p className="text-sm text-muted-foreground mt-1.5">Financial news ingested and processed in real-time.</p>
        </div>
        <div className="flex items-center gap-2 text-[10px] font-bold tracking-[0.1em] uppercase text-muted-foreground font-mono">
          <span className="flex h-1.5 w-1.5 relative mr-1">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-60" style={{ backgroundColor: "var(--color-positive)" }} />
            <span className="relative inline-flex rounded-full h-1.5 w-1.5" style={{ backgroundColor: "var(--color-positive)" }} />
          </span>
          {articles?.length || 0} articles • LIVE
        </div>
      </div>

      {/* ── Feed Container ───────────────────────────────────────────────── */}
      <div className="border rounded-lg overflow-hidden" style={{ borderColor: "var(--color-border)", backgroundColor: "rgba(0,0,0,0.15)" }}>
        {isLoading ? (
          Array.from({ length: 15 }).map((_, i) => (
            <div key={i} className="flex items-start gap-4 p-4 border-b last:border-b-0 animate-pulse" style={{ borderColor: "var(--color-border)" }}>
              <div className="w-[120px] flex flex-col gap-2">
                <div className="h-3 w-20 bg-white/5 rounded" />
                <div className="h-2 w-16 bg-white/5 rounded" />
              </div>
              <div className="flex-1 flex flex-col gap-2">
                <div className="h-4 w-3/4 bg-white/5 rounded" />
                <div className="h-3 w-1/2 bg-white/5 rounded" />
              </div>
            </div>
          ))
        ) : (
          articles?.map((article, idx) => <ArticleRow key={article.id} article={article} index={idx} />)
        )}
        
        {articles?.length === 0 && !isLoading && (
          <div className="p-12 text-center">
            <p className="text-muted-foreground text-sm">No articles found in the database.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function ArticleRow({ article, index }: { article: Article, index: number }) {
  // Simulate active state on the second row purely for visual match with reference
  const isActive = index === 1; 

  return (
    <div 
      className={`group flex items-start gap-4 p-4 border-b last:border-b-0 transition-colors relative ${isActive ? 'bg-[rgba(91,141,239,0.06)]' : 'hover:bg-[rgba(255,255,255,0.02)]'}`}
      style={{ borderColor: "var(--color-border)" }}
    >
      {isActive && (
        <div className="absolute left-0 top-0 bottom-0 w-[2px]" style={{ backgroundColor: "var(--color-accent)", boxShadow: "0 0 8px var(--color-accent)" }} />
      )}
      
      {/* ── Left Column: Source and Time ── */}
      <div className="w-[120px] flex-shrink-0 flex flex-col gap-1.5 pt-0.5">
        <span className="text-[10px] font-mono tracking-widest uppercase text-muted-foreground opacity-80 truncate">
          {article.source || "UNKNOWN"}
        </span>
        <span className="text-[9px] font-mono text-muted-foreground opacity-50">
          {article.published_at ? formatDistanceToNow(new Date(article.published_at), { addSuffix: true }) : 'N/A'}
        </span>
      </div>

      {/* ── Center Column: Headlines ── */}
      <div className="flex-1 min-w-0 pr-4">
        <h3 className="text-[13px] font-medium text-foreground tracking-wide truncate mb-1 transition-colors">
          {article.title}
        </h3>
        <p className="text-[11px] text-muted-foreground truncate opacity-70">
          {article.content || article.title}
        </p>
      </div>

      {/* ── Right Column: External Link ── */}
      <div className="w-8 flex-shrink-0 flex items-center justify-end opacity-0 group-hover:opacity-100 transition-opacity pt-0.5">
        {article.article_url ? (
          <a href={article.article_url} target="_blank" rel="noreferrer" className="text-muted-foreground hover:text-[var(--color-accent)] transition-colors">
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        ) : (
          <div className="w-3.5 h-3.5" /> // Spacer
        )}
      </div>
    </div>
  );
}
