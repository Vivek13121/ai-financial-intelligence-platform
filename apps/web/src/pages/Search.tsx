import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { API } from "../lib/api";
import { Search as SearchIcon, Building2, TrendingUp, Cpu, Car } from "lucide-react";

export function Search() {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 300);
    return () => clearTimeout(timer);
  }, [query]);

  const { data: suggestions } = useQuery({
    queryKey: ["suggestions", debouncedQuery],
    queryFn: () => API.getSearchSuggestions(debouncedQuery),
    enabled: debouncedQuery.length >= 2,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/company/${encodeURIComponent(query.trim())}`);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    navigate(`/company/${encodeURIComponent(suggestion)}`);
  };

  const trendingSearches = [
    { name: "Nvidia", icon: Cpu, trend: "+12%" },
    { name: "Tesla", icon: Car, trend: "-4%" },
    { name: "Apple", icon: Building2, trend: "+2%" },
    { name: "Microsoft", icon: Building2, trend: "+8%" }
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-500 max-w-4xl mx-auto pt-10">
      <div className="text-center space-y-4">
        <div className="w-16 h-16 bg-primary/20 rounded-2xl flex items-center justify-center mx-auto mb-6 ring-1 ring-primary/30">
          <SearchIcon className="w-8 h-8 text-primary" />
        </div>
        <h2 className="text-4xl font-bold tracking-tight">Company Intelligence Engine</h2>
        <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
          Enter a company name to instantly generate a comprehensive AI-driven intelligence dashboard, sentiment forecast, and news analysis.
        </p>
      </div>

      <form onSubmit={handleSearch} className="relative group mt-8 z-50">
        <div className="absolute -inset-1 bg-gradient-to-r from-primary/50 to-blue-500/50 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-500"></div>
        <div className="relative flex items-center">
          <SearchIcon className="absolute left-6 w-6 h-6 text-muted-foreground" />
          <input 
            type="text" 
            placeholder="Search for a company (e.g. Nvidia, Tesla, OpenAI)..."
            className="w-full bg-background border-2 border-white/10 rounded-2xl py-6 pl-16 pr-36 outline-none focus:border-primary/50 transition-colors text-xl shadow-2xl relative z-10"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setTimeout(() => setIsFocused(false), 200)}
          />
          <button 
            type="submit"
            disabled={!query.trim()}
            className="absolute right-3 bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-3 rounded-xl font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg z-20"
          >
            Analyze
          </button>
        </div>
        
        {/* Autocomplete Dropdown */}
        {isFocused && suggestions && suggestions.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-slate-900/95 backdrop-blur-xl border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50">
            {suggestions.map((suggestion, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSuggestionClick(suggestion)}
                className="w-full text-left px-6 py-4 hover:bg-white/10 transition-colors flex items-center gap-3 border-b border-white/5 last:border-0"
              >
                <SearchIcon className="w-4 h-4 text-muted-foreground" />
                <span className="font-medium text-lg">{suggestion}</span>
              </button>
            ))}
          </div>
        )}
      </form>

      <div className="mt-16">
        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-6 text-center">Trending Companies</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {trendingSearches.map((company) => {
            const Icon = company.icon;
            const isPositive = company.trend.startsWith("+");
            return (
              <button 
                key={company.name}
                onClick={() => navigate(`/company/${company.name}`)}
                className="glass-card p-4 rounded-xl flex flex-col items-center gap-3 hover:bg-white/10 transition-colors group cursor-pointer"
              >
                <div className="p-3 bg-white/5 rounded-lg group-hover:bg-primary/20 transition-colors">
                  <Icon className="w-6 h-6 text-muted-foreground group-hover:text-primary transition-colors" />
                </div>
                <span className="font-semibold text-lg">{company.name}</span>
                <span className={`text-sm font-medium ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                  {isPositive ? <TrendingUp className="w-3 h-3 inline mr-1" /> : null}
                  {company.trend} sentiment
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
