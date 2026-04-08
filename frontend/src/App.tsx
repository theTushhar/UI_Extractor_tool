import { useState, useMemo, useCallback } from "react";
import { Scan, Loader2, AlertCircle, Sparkles, Code2, RotateCcw, ChevronDown, ChevronUp } from "lucide-react";
import { api } from "./api";
import type { ExtractResponse, ExtractedElement, Filters } from "./types";
import { InteractiveStatsCards } from "./components/InteractiveStatsCards";
import { FilterBar } from "./components/FilterBar";
import { ElementsTable } from "./components/ElementsTable";
import { ElementDetailSheet } from "./components/ElementDetailSheet";
import { ExportMenu } from "./components/ExportMenu";
import { ToastNotification } from "./components/ToastNotification";

const SAMPLE_HTML = `<!DOCTYPE html>
<html>
<head><title>Login</title></head>
<body>
  <form id="login-form">
    <h1>Welcome back</h1>
    <label for="email">Email</label>
    <input id="email" type="email" name="email" placeholder="you@example.com" required />
    <label for="password">Password</label>
    <input id="password" type="password" name="password" placeholder="Your password" required />
    <a href="/forgot" class="forgot-link">Forgot password?</a>
    <button id="login-btn" type="submit" class="btn-primary">Sign In</button>
    <p class="signup-text">Don't have an account? <a href="/signup">Sign up</a></p>
  </form>
</body>
</html>`;

export default function App() {
  const [htmlInput, setHtmlInput] = useState("");
  const [results, setResults] = useState<ExtractResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedElement, setSelectedElement] = useState<ExtractedElement | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [inputExpanded, setInputExpanded] = useState(false); // collapsed after extraction
  const [filters, setFilters] = useState<Filters>({
    search: "",
    mode: "All",
    elementType: "All",
    stableOnly: false,
  });

  const handleExtract = async () => {
    if (!htmlInput.trim()) return;
    setLoading(true);
    setError(null);
    setResults(null);
    setSelectedElement(null);
    setFilters({ search: "", mode: "All", elementType: "All", stableOnly: false });
    try {
      const data = await api.extractLocators(htmlInput);
      setResults(data);
      setInputExpanded(false); // collapse after successful extraction
    } catch (err: any) {
      setError(err.message ?? "Extraction failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setHtmlInput("");
    setResults(null);
    setError(null);
    setSelectedElement(null);
    setToast(null);
    setInputExpanded(false);
    setFilters({ search: "", mode: "All", elementType: "All", stableOnly: false });
  };

  const handleCopy = useCallback((value: string) => {
    setToast(`Copied: ${value.length > 40 ? value.slice(0, 40) + "…" : value}`);
  }, []);

  const availableTypes = useMemo(
    () => [...new Set(results?.elements.map((e) => e.element_type) ?? [])].sort(),
    [results]
  );


  const filteredCount = useMemo(() => {
    if (!results) return 0;
    return results.elements.filter((el) => {
      if (filters.search) {
        const q = filters.search.toLowerCase();
        const match =
          el.element_name.toLowerCase().includes(q) ||
          el.element_type.toLowerCase().includes(q) ||
          el.recommended_locator.value.toLowerCase().includes(q);
        if (!match) return false;
      }
      if (filters.mode !== "All" && el.mode !== filters.mode) return false;
      if (filters.elementType !== "All" && el.element_type !== filters.elementType) return false;
      if (filters.stableOnly && el.recommended_locator.score < 80) return false;
      return true;
    }).length;
  }, [results, filters]);

  // Whether we show the full textarea or the collapsed summary bar
  const showCollapsed = !!results && !inputExpanded;

  return (
    <div className="min-h-screen bg-bg-base text-slate-200">
      {/* ── Ambient gradient blobs ── */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10">
        <div className="absolute -top-40 -left-40 w-[500px] h-[500px] rounded-full bg-primary/5 blur-[120px]" />
        <div className="absolute top-1/2 -right-40 w-[400px] h-[400px] rounded-full bg-accent/5 blur-[100px]" />
      </div>

      {/* ── Header ── */}
      <header className="sticky top-0 z-20 border-b border-bg-border glass">
        <div className="max-w-7xl mx-auto px-4 h-11 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-glow">
              <Scan size={14} className="text-white" />
            </div>
            <span className="font-semibold text-slate-100 text-sm">UI Extractor</span>
            <span className="px-1.5 py-0.5 text-[10px] rounded-full border border-primary/30 bg-primary/10 text-primary-light font-mono">
              v0.1
            </span>
          </div>
          <div className="flex items-center gap-3">
            {results && (
              <button
                onClick={handleReset}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-bg-border text-xs text-slate-400 hover:text-slate-200 hover:border-slate-500 hover:bg-bg-elevated transition-all"
              >
                <RotateCcw size={12} />
                Reset
              </button>
            )}
            <div className="flex items-center gap-1.5 text-xs text-slate-500">
              <div className="w-1.5 h-1.5 rounded-full bg-mode-input animate-pulse" />
              Deterministic Parser
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-4 space-y-4">

        {/* ── Input Section ── */}
        <div
          className="rounded-xl border border-bg-border bg-bg-surface overflow-hidden"
          style={{ boxShadow: "0 2px 16px rgba(0,0,0,0.35)" }}
        >
          {/* Always-visible top bar */}
          <div className="flex items-center gap-2 px-4 py-2.5 border-b border-bg-border bg-bg-elevated">
            <Code2 size={13} className="text-primary-light flex-shrink-0" />
            <span className="text-xs font-medium text-slate-400 flex-shrink-0">HTML Source</span>

            {showCollapsed ? (
              /* Collapsed state: show summary pill */
              <>
                <span className="flex-1 font-mono text-xs text-slate-500 truncate ml-1">
                  {htmlInput.length.toLocaleString()} chars
                </span>
                <button
                  onClick={() => setInputExpanded(true)}
                  className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-200 transition-colors px-2 py-0.5 rounded-lg hover:bg-bg-hover"
                >
                  <ChevronDown size={12} />
                  Edit
                </button>
              </>
            ) : (
              /* Expanded state: Load sample + char count */
              <>
                <div className="flex-1" />
                <button
                  onClick={() => setHtmlInput(SAMPLE_HTML)}
                  className="text-xs text-slate-500 hover:text-accent transition-colors px-2 py-0.5 rounded-lg hover:bg-accent/10"
                >
                  Load sample
                </button>
                <span className="text-xs text-slate-600 font-mono">
                  {htmlInput.length.toLocaleString()} chars
                </span>
                {results && (
                  <button
                    onClick={() => setInputExpanded(false)}
                    className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-200 transition-colors px-2 py-0.5 rounded-lg hover:bg-bg-hover"
                  >
                    <ChevronUp size={12} />
                    Collapse
                  </button>
                )}
              </>
            )}
          </div>

          {/* Textarea — hidden when collapsed */}
          {!showCollapsed && (
            <div className="p-3">
              <textarea
                id="html-input"
                className="w-full h-32 resize-none bg-bg-base text-slate-300 text-xs p-3 rounded-lg border border-bg-border placeholder-slate-600 leading-relaxed"
                value={htmlInput}
                onChange={(e) => setHtmlInput(e.target.value)}
                placeholder={`<html>\n  <body>\n    <button id="login">Login</button>\n  </body>\n</html>`}
                spellCheck={false}
              />
              <div className="flex items-center justify-between mt-2">
                <div className="flex items-center gap-1.5">
                  <Sparkles size={11} className="text-accent" />
                  <span className="text-xs text-slate-600">Paste any HTML — forms, full pages, component snippets</span>
                </div>
                <button
                  id="extract-btn"
                  onClick={handleExtract}
                  disabled={!htmlInput.trim() || loading}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg font-semibold text-xs transition-all disabled:opacity-40 disabled:cursor-not-allowed bg-gradient-to-r from-primary to-accent text-white hover:shadow-glow hover:scale-[1.02] active:scale-[0.98]"
                  style={{ boxShadow: loading ? "none" : "0 3px 14px rgba(99,102,241,0.35)" }}
                >
                  {loading ? (
                    <>
                      <Loader2 size={13} className="animate-spin" />
                      Analyzing…
                    </>
                  ) : (
                    <>
                      <Scan size={13} />
                      Extract Locators
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* When collapsed, show inline extract button if user edits */}
          {showCollapsed && (
            <div className="px-4 py-2 flex items-center justify-end border-t border-bg-border/50">
              <button
                onClick={() => setInputExpanded(true)}
                className="text-xs text-slate-600 hover:text-slate-300 transition-colors"
              >
                Click "Edit" above to modify HTML and re-extract
              </button>
            </div>
          )}
        </div>

        {/* ── Error State ── */}
        {error && (
          <div className="flex items-start gap-2.5 p-3 rounded-xl border border-red-500/30 bg-red-500/10 animate-fade-in">
            <AlertCircle size={15} className="text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-xs font-semibold text-red-300">Extraction Failed</p>
              <p className="text-xs text-red-400/80 mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {/* ── Loading skeleton ── */}
        {loading && (
          <div className="space-y-3 animate-pulse">
            <div className="grid grid-cols-3 gap-3">
              {[0, 1, 2].map((i) => (
                <div key={i} className="h-20 rounded-xl bg-bg-surface border border-bg-border" />
              ))}
            </div>
            <div className="h-48 rounded-xl bg-bg-surface border border-bg-border" />
          </div>
        )}

        {/* ── Results ── */}
        {results && !loading && (
          <div className="space-y-4 animate-fade-in">

            {/* Interactive filter cards */}
            <InteractiveStatsCards
              elements={results.elements}
              filters={filters}
              onFilterChange={setFilters}
            />

            {/* Toolbar: page name | filters | export */}
            <div className="flex items-center gap-3">
              {/* Page name */}
              <div className="flex-shrink-0">
                <h2 className="text-sm font-semibold text-slate-100 leading-none">{results.page_name}</h2>
                <p className="text-[10px] text-slate-500 mt-0.5">
                  {results.total_elements} elements • {results.stable_elements} stable
                </p>
              </div>

              {/* Divider */}
              <div className="w-px h-7 bg-bg-border flex-shrink-0" />

              {/* Filters — fills remaining space */}
              <FilterBar
                filters={filters}
                onChange={setFilters}
                availableTypes={availableTypes}
                totalCount={results.total_elements}
                filteredCount={filteredCount}
                className="flex-1"
              />

              {/* Export */}
              <ExportMenu data={results} />
            </div>

            {/* Table */}
            <ElementsTable
              elements={results.elements}
              filters={filters}
              onSelectElement={setSelectedElement}
              onCopy={handleCopy}
            />
          </div>
        )}
      </main>

      {/* ── Detail Popup ── */}
      <ElementDetailSheet
        element={selectedElement}
        onClose={() => setSelectedElement(null)}
        onCopy={handleCopy}
      />

      {/* ── Toast ── */}
      {toast && (
        <ToastNotification message={toast} onDismiss={() => setToast(null)} />
      )}
    </div>
  );
}
