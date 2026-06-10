import { useQuery } from "@tanstack/react-query";
import { API } from "../lib/api";
import type { Article } from "../lib/api";
import { format } from "date-fns";
import { ExternalLink, Clock } from "lucide-react";

export function LiveFeed() {
  const { data: articles, isLoading } = useQuery({
    queryKey: ["articles"],
    queryFn: () => API.getArticles(0, 50),
    refetchInterval: 15000,
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Live News Feed</h2>
        <p className="text-muted-foreground mt-2">Latest financial news ingested by the system.</p>
      </div>

      <div className="space-y-4">
        {isLoading ? (
          Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="glass-card p-6 rounded-xl animate-pulse">
              <div className="h-6 w-2/3 bg-white/10 rounded mb-4" />
              <div className="h-4 w-full bg-white/10 rounded mb-2" />
              <div className="h-4 w-4/5 bg-white/10 rounded" />
            </div>
          ))
        ) : (
          articles?.map((article) => <ArticleCard key={article.id} article={article} />)
        )}
        
        {articles?.length === 0 && !isLoading && (
          <div className="glass-card p-12 text-center rounded-xl">
            <p className="text-muted-foreground">No articles found in the database.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function ArticleCard({ article }: { article: Article }) {
  return (
    <div className="glass-card p-6 rounded-xl hover:bg-white/5 transition-colors group">
      <div className="flex justify-between items-start gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            {article.source && (
              <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                {article.source}
              </span>
            )}
            {article.company && (
              <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
                {article.company}
              </span>
            )}
          </div>
          
          <h3 className="text-xl font-semibold mb-2 group-hover:text-primary transition-colors">
            {article.title}
          </h3>
          <p className="text-muted-foreground text-sm line-clamp-2 leading-relaxed mb-4">
            {article.content}
          </p>
          
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5" />
              {article.published_at ? format(new Date(article.published_at), "MMM d, yyyy h:mm a") : 'Unknown date'}
            </div>
            {article.article_url && (
              <a 
                href={article.article_url} 
                target="_blank" 
                rel="noreferrer"
                className="flex items-center gap-1.5 hover:text-primary transition-colors"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                Read Original
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
