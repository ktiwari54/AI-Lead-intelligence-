"use client";

import { useState, useEffect, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { post } from "@/lib/api";

interface SearchResult {
  id: string;
  entity_type: "company" | "contact";
  name: string;
  title?: string;
  industry?: string;
  seniority?: string;
  score?: number;
  highlights?: string[];
}

interface SearchResponse {
  results: SearchResult[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

const SENIORITY_OPTIONS = ["C_LEVEL", "VP", "DIRECTOR", "MANAGER", "INDIVIDUAL"];
const ENTITY_OPTIONS = ["both", "companies", "contacts"] as const;
type EntityType = typeof ENTITY_OPTIONS[number];

function ResultCard({ result }: { result: SearchResult }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 hover:border-indigo-300 transition-colors">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span
              className={`inline-block px-2 py-0.5 rounded text-xs font-semibold uppercase ${
                result.entity_type === "company"
                  ? "bg-indigo-100 text-indigo-700"
                  : "bg-emerald-100 text-emerald-700"
              }`}
            >
              {result.entity_type}
            </span>
            {result.seniority && (
              <span className="text-xs text-gray-400">{result.seniority}</span>
            )}
          </div>
          <p className="font-semibold text-gray-900 truncate">{result.name}</p>
          {result.title && (
            <p className="text-sm text-gray-500 truncate">{result.title}</p>
          )}
          {result.industry && (
            <p className="text-xs text-gray-400 mt-0.5">{result.industry}</p>
          )}
          {result.highlights && result.highlights.length > 0 && (
            <ul className="mt-2 space-y-0.5">
              {result.highlights.slice(0, 2).map((h, i) => (
                <li key={i} className="text-xs text-gray-500 italic truncate">
                  ...{h}...
                </li>
              ))}
            </ul>
          )}
        </div>
        {result.score !== undefined && (
          <div className="flex-shrink-0 text-center">
            <span
              className={`text-xl font-bold ${
                result.score >= 70
                  ? "text-green-600"
                  : result.score >= 40
                  ? "text-yellow-600"
                  : "text-red-500"
              }`}
            >
              {Math.round(result.score)}
            </span>
            <p className="text-xs text-gray-400">score</p>
          </div>
        )}
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-gray-400">
      <svg
        className="w-12 h-12 mb-3"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z"
        />
      </svg>
      <p className="text-sm font-medium">No results found</p>
      <p className="text-xs mt-1">Try adjusting your filters or search query</p>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="bg-white rounded-xl border border-gray-200 p-4 animate-pulse">
          <div className="h-3 bg-gray-200 rounded w-1/4 mb-2" />
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-1" />
          <div className="h-3 bg-gray-200 rounded w-1/2" />
        </div>
      ))}
    </div>
  );
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [entityType, setEntityType] = useState<EntityType>("both");
  const [industries, setIndustries] = useState("");
  const [seniorities, setSeniorities] = useState<string[]>([]);
  const [minEmployees, setMinEmployees] = useState("");
  const [maxEmployees, setMaxEmployees] = useState("");
  const [minScore, setMinScore] = useState(0);
  const [page, setPage] = useState(1);
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [saveModalOpen, setSaveModalOpen] = useState(false);
  const [saveName, setSaveName] = useState("");

  // Debounce query
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQuery(query), 300);
    return () => clearTimeout(t);
  }, [query]);

  const searchMutation = useMutation({
    mutationFn: (payload: object) =>
      post<{ data: SearchResponse }>("/search/", payload),
    onSuccess: (res: any) => {
      setResults(res?.data ?? res);
    },
  });

  const saveMutation = useMutation({
    mutationFn: (name: string) =>
      post("/search/saved", {
        name,
        query: buildPayload(page),
      }),
    onSuccess: () => setSaveModalOpen(false),
  });

  const buildPayload = (p: number) => ({
    query: debouncedQuery,
    entity_type: entityType === "both" ? undefined : entityType,
    industries: industries ? industries.split(",").map((s) => s.trim()).filter(Boolean) : undefined,
    seniorities: seniorities.length ? seniorities : undefined,
    min_employees: minEmployees ? Number(minEmployees) : undefined,
    max_employees: maxEmployees ? Number(maxEmployees) : undefined,
    min_score: minScore > 0 ? minScore : undefined,
    page: p,
    page_size: 10,
  });

  const handleSearch = (p = 1) => {
    setPage(p);
    searchMutation.mutate(buildPayload(p));
  };

  const handleClear = () => {
    setQuery("");
    setDebouncedQuery("");
    setEntityType("both");
    setIndustries("");
    setSeniorities([]);
    setMinEmployees("");
    setMaxEmployees("");
    setMinScore(0);
    setResults(null);
    setPage(1);
  };

  const toggleSeniority = (s: string) => {
    setSeniorities((prev) =>
      prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]
    );
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Search</h1>
        {results && (
          <button
            onClick={() => setSaveModalOpen(true)}
            className="px-4 py-2 text-sm font-medium rounded-lg border border-indigo-300 text-indigo-600 hover:bg-indigo-50 transition-colors"
          >
            Save Search
          </button>
        )}
      </div>

      <div className="flex gap-6">
        {/* Sidebar filters */}
        <aside className="w-64 flex-shrink-0 space-y-5">
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
              Search Query
            </label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Name, title, company..."
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
              Entity Type
            </label>
            <div className="space-y-1">
              {ENTITY_OPTIONS.map((opt) => (
                <label key={opt} className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                  <input
                    type="radio"
                    name="entityType"
                    value={opt}
                    checked={entityType === opt}
                    onChange={() => setEntityType(opt)}
                    className="accent-indigo-600"
                  />
                  <span className="capitalize">{opt}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
              Industries (comma-separated)
            </label>
            <input
              type="text"
              value={industries}
              onChange={(e) => setIndustries(e.target.value)}
              placeholder="SaaS, Fintech..."
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
              Seniority
            </label>
            <div className="space-y-1">
              {SENIORITY_OPTIONS.map((s) => (
                <label key={s} className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={seniorities.includes(s)}
                    onChange={() => toggleSeniority(s)}
                    className="accent-indigo-600"
                  />
                  {s.replace("_", " ")}
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
              Employee Range
            </label>
            <div className="flex gap-2">
              <input
                type="number"
                value={minEmployees}
                onChange={(e) => setMinEmployees(e.target.value)}
                placeholder="Min"
                className="w-full rounded-lg border border-gray-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <input
                type="number"
                value={maxEmployees}
                onChange={(e) => setMaxEmployees(e.target.value)}
                placeholder="Max"
                className="w-full rounded-lg border border-gray-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
              Min Score: <span className="text-indigo-600 font-bold">{minScore}</span>
            </label>
            <input
              type="range"
              min={0}
              max={100}
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              className="w-full accent-indigo-600"
            />
          </div>

          <div className="flex gap-2 pt-1">
            <button
              onClick={() => handleSearch(1)}
              disabled={searchMutation.isPending}
              className="flex-1 px-3 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {searchMutation.isPending ? "Searching..." : "Search"}
            </button>
            <button
              onClick={handleClear}
              className="px-3 py-2 border border-gray-300 text-gray-600 rounded-lg text-sm font-medium hover:border-gray-400 transition-colors"
            >
              Clear
            </button>
          </div>
        </aside>

        {/* Results */}
        <main className="flex-1 min-w-0">
          {searchMutation.isPending ? (
            <LoadingSkeleton />
          ) : results ? (
            <>
              <p className="text-sm text-gray-500 mb-3">
                {results.total} result{results.total !== 1 ? "s" : ""} found
              </p>
              {results.results.length === 0 ? (
                <EmptyState />
              ) : (
                <div className="space-y-3">
                  {results.results.map((r) => (
                    <ResultCard key={r.id} result={r} />
                  ))}
                </div>
              )}

              {/* Pagination */}
              {results.total_pages > 1 && (
                <div className="flex items-center justify-center gap-2 mt-6">
                  <button
                    onClick={() => handleSearch(page - 1)}
                    disabled={page <= 1}
                    className="px-3 py-1.5 rounded-lg border border-gray-300 text-sm text-gray-600 hover:border-gray-400 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <span className="text-sm text-gray-500">
                    Page {results.page} of {results.total_pages}
                  </span>
                  <button
                    onClick={() => handleSearch(page + 1)}
                    disabled={page >= results.total_pages}
                    className="px-3 py-1.5 rounded-lg border border-gray-300 text-sm text-gray-600 hover:border-gray-400 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          ) : (
            <div className="flex flex-col items-center justify-center py-20 text-gray-400">
              <svg
                className="w-14 h-14 mb-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z"
                />
              </svg>
              <p className="text-sm font-medium">Configure filters and click Search</p>
            </div>
          )}
        </main>
      </div>

      {/* Save Search Modal */}
      {saveModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-xl p-6 w-80 space-y-4">
            <h2 className="text-base font-semibold text-gray-900">Save Search</h2>
            <input
              type="text"
              value={saveName}
              onChange={(e) => setSaveName(e.target.value)}
              placeholder="Search name..."
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <div className="flex gap-2">
              <button
                onClick={() => saveMutation.mutate(saveName)}
                disabled={saveMutation.isPending || !saveName.trim()}
                className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
              >
                {saveMutation.isPending ? "Saving..." : "Save"}
              </button>
              <button
                onClick={() => setSaveModalOpen(false)}
                className="px-4 py-2 border border-gray-300 text-gray-600 rounded-lg text-sm font-medium hover:border-gray-400 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
