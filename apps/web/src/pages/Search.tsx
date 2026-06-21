import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { API } from "../lib/api";
import { Search as SearchIcon, Building2, Cpu, Car } from "lucide-react";

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
    { ticker: "NVDA", name: "Nvidia",    icon: Cpu,       trend: "+12%" },
    { ticker: "TSLA", name: "Tesla",     icon: Car,       trend: "-4%"  },
    { ticker: "AAPL", name: "Apple",     icon: Building2, trend: "+2%"  },
    { ticker: "MSFT", name: "Microsoft", icon: Building2, trend: "+8%"  },
  ];

  return (
    <div className="animate-in fade-in duration-300 max-w-2xl mx-auto pt-6 md:pt-12 px-2 sm:px-0">

      {/* Header */}
      <div className="mb-10">
        <div
          className="inline-flex items-center justify-center w-12 h-12 rounded-xl mb-6"
          style={{ backgroundColor: "rgba(91,141,239,0.10)", border: "1px solid rgba(91,141,239,0.20)" }}
        >
          <SearchIcon className="w-5 h-5" style={{ color: "var(--color-accent)" }} />
        </div>
        <h2 className="text-xl md:text-2xl font-bold tracking-tight text-foreground font-display mb-2">
          Company Intelligence Search
        </h2>
        <p className="text-sm text-muted-foreground leading-relaxed">
          Search by company name, ticker symbol, or alias. Resolves to a canonical entity and returns full intelligence coverage.
        </p>
      </div>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="relative mb-10">
        <div
          className="flex items-center rounded-lg overflow-visible"
          style={{
            backgroundColor: "var(--color-surface)",
            border: `1px solid ${isFocused ? "rgba(91,141,239,0.4)" : "var(--color-border)"}`,
            transition: "border-color 0.2s",
          }}
        >
          <SearchIcon className="w-4 h-4 ml-4 flex-shrink-0" style={{ color: "var(--color-neutral)" }} />
          <input
            type="text"
            placeholder="Search for a company, ticker, or alias…"
            className="flex-1 bg-transparent px-3 py-3.5 text-sm outline-none text-foreground placeholder:text-muted-foreground"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setTimeout(() => setIsFocused(false), 200)}
          />
          <button
            type="submit"
            disabled={!query.trim()}
            className="btn-primary mr-2 my-2 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Analyze
          </button>
        </div>

        {/* Autocomplete */}
        {isFocused && suggestions && suggestions.length > 0 && (
          <div
            className="absolute top-full left-0 right-0 mt-1 rounded-lg overflow-hidden shadow-2xl z-50"
            style={{
              backgroundColor: "var(--color-elevated)",
              border: "1px solid var(--color-border)",
            }}
          >
            {suggestions.map((suggestion, idx) => (
              <button
                key={idx}
                type="button"
                onMouseDown={(e) => {
                  e.preventDefault(); // Prevents input onBlur from firing before this handles
                  setQuery(suggestion);
                  setIsFocused(false);
                  handleSuggestionClick(suggestion);
                }}
                className="w-full text-left px-4 py-3 flex items-center gap-3 transition-colors text-sm"
                style={{ borderBottom: idx < suggestions.length - 1 ? `1px solid var(--color-border)` : "none" }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "rgba(255,255,255,0.03)")}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "")}
              >
                <SearchIcon className="w-3.5 h-3.5 flex-shrink-0 text-muted-foreground" />
                <span className="font-medium text-foreground">{suggestion}</span>
              </button>
            ))}
          </div>
        )}
      </form>

      {/* Trending Companies */}
      <div>
        <p className="label-section mb-4">Trending Companies</p>
        <div className="flex flex-col divide-y" style={{ borderColor: "var(--color-border)" }}>
          {trendingSearches.map((company) => {
            const isPositive = company.trend.startsWith("+");
            return (
              <button
                key={company.ticker}
                onClick={() => navigate(`/company/${company.name}`)}
                className="flex items-center justify-between py-3 text-left transition-colors group"
                onMouseEnter={(e) => (e.currentTarget.style.color = "var(--color-accent)")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "")}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span
                    className="num text-[10px] font-bold px-1.5 py-0.5 rounded flex-shrink-0"
                    style={{
                      backgroundColor: "rgba(91,141,239,0.08)",
                      color: "var(--color-accent)",
                      border: "1px solid rgba(91,141,239,0.16)"
                    }}
                  >
                    {company.ticker}
                  </span>
                  <span className="text-sm font-medium text-foreground truncate">{company.name}</span>
                </div>
                <span
                  className="num text-xs font-semibold flex-shrink-0"
                  style={{ color: isPositive ? "var(--color-positive)" : "var(--color-negative)" }}
                >
                  {company.trend}
                </span>
              </button>
            );
          })}
        </div>
      </div>

    </div>
  );
}
