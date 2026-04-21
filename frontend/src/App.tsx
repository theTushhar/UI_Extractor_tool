import { useState } from "react";
import { Scan, Loader2, AlertCircle, Sparkles, Code2, RotateCcw, ChevronDown, ChevronUp, ShieldCheck, Globe, Maximize2, ExternalLink } from "lucide-react";
import type { ExtractedElement } from "./types";
import { InteractiveStatsCards } from "./components/extractor/InteractiveStatsCards";
import { FilterBar } from "./components/extractor/FilterBar";
import { ElementsTable } from "./components/extractor/ElementsTable";
import { ElementDetailSheet } from "./components/extractor/ElementDetailSheet";
import { ExportMenu } from "./components/extractor/ExportMenu";
import { ToastNotification } from "./components/common/ToastNotification";
import { useExtractor } from "./hooks/useExtractor";
import { useFilters } from "./hooks/useFilters";
import { useToast } from "./hooks/useToast";
import { SAMPLE_HTML } from "./constants";

export default function App() {
  const {
    htmlInput,
    setHtmlInput,
    urlInput,
    setUrlInput,
    results,
    loading,
    error,
    verifications,
    verifying,
    inputExpanded,
    setInputExpanded,
    handleExtract,
    handleExtractURL,
    handleVerify,
    handleReset,
  } = useExtractor();

  const [activeTab, setActiveTab] = useState<"html" | "url">("html");
  const [showScreenshot, setShowScreenshot] = useState(true);

  const {
    filters,
    setFilters,
    availableTypes,
    filteredCount,
  } = useFilters(results);

  const {
    toast,
    setToast,
    dismissToast,
    handleCopy,
  } = useToast();

  const [selectedElement, setSelectedElement] = useState<ExtractedElement | null>(null);

  const onExtract = () => handleExtract(setFilters);
  const onExtractURL = () => handleExtractURL(setFilters);
  const onVerify = () => handleVerify(setToast);
  const onReset = () => {
    handleReset(setFilters);
    setActiveTab("html");
  };

  // Whether we show the full textarea or the collapsed summary bar
  const showCollapsed = !!results && !inputExpanded;

  return (
    <div className="min-h-screen bg-bg-base text-slate-200 font-sans selection:bg-primary/30">
      {/* ── Ambient gradient blobs ── */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10">
        <div className="absolute -top-40 -left-40 w-[500px] h-[500px] rounded-full bg-primary/5 blur-[120px]" />
        <div className="absolute top-1/2 -right-40 w-[400px] h-[400px] rounded-full bg-accent/5 blur-[100px]" />
      </div>

      {/* ── Header ── */}
      <header className="sticky top-0 z-20 border-b border-bg-border glass backdrop-blur-md bg-bg-base/60">
        <div className="max-w-7xl mx-auto px-4 h-12 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-glow border border-white/10">
              <Scan size={16} className="text-white" />
            </div>
            <div>
              <span className="font-bold text-slate-100 text-sm tracking-tight">UI Extractor</span>
              <div className="flex items-center gap-1.5 leading-none mt-0.5">
                <span className="px-1.5 py-0.5 text-[9px] rounded-md border border-primary/30 bg-primary/10 text-primary-light font-bold uppercase tracking-wider">
                  Pro
                </span>
                <span className="text-[10px] text-slate-500 font-medium tracking-wide italic">Powered by Playwright</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {results && (
              <button
                onClick={onReset}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-bg-border text-xs text-slate-400 hover:text-slate-200 hover:border-slate-500 hover:bg-bg-elevated transition-all shadow-sm active:scale-95"
              >
                <RotateCcw size={12} />
                New Extraction
              </button>
            )}
            <div className="h-4 w-px bg-bg-border" />
            <div className="flex items-center gap-2 text-xs text-slate-500 bg-bg-surface/50 px-2 py-1 rounded-full border border-bg-border">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
              Live Engine Ready
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">

        {/* ── Input Section ── */}
        <div
          className="rounded-2xl border border-bg-border bg-bg-surface overflow-hidden transition-all duration-300 shadow-2xl"
          style={{ boxShadow: "0 10px 40px -10px rgba(0,0,0,0.5)" }}
        >
          {/* Always-visible top bar with Tabs */}
          <div className="flex items-center gap-4 px-5 py-2 border-b border-bg-border bg-bg-elevated/50">
             <div className="flex items-center gap-1 bg-bg-base/80 p-1 rounded-xl border border-bg-border/50">
                <button 
                  onClick={() => setActiveTab("html")}
                  className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-[11px] font-semibold transition-all duration-200 ${activeTab === "html" ? "bg-bg-elevated text-primary-light shadow-lg border border-white/5" : "text-slate-500 hover:text-slate-300"}`}
                >
                  <Code2 size={13} />
                  HTML Source
                </button>
                <button 
                  onClick={() => setActiveTab("url")}
                  className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-[11px] font-semibold transition-all duration-200 ${activeTab === "url" ? "bg-bg-elevated text-accent shadow-lg border border-white/5" : "text-slate-500 hover:text-slate-300"}`}
                >
                  <Globe size={13} />
                  Live URL
                </button>
             </div>

            {showCollapsed ? (
              /* Collapsed state: show summary pill */
              <div className="flex-1 flex items-center justify-between">
                <div className="flex items-center gap-3 px-3 py-1 bg-bg-base rounded-full border border-bg-border text-[11px] text-slate-400 font-mono max-w-lg overflow-hidden">
                  {results.url ? (
                    <>
                      <Globe size={10} className="text-accent" />
                      <span className="truncate">{results.url}</span>
                    </>
                  ) : (
                    <>
                      <Code2 size={10} className="text-primary-light" />
                      <span>{htmlInput.length.toLocaleString()} characters extracted</span>
                    </>
                  )}
                </div>
                <button
                  onClick={() => setInputExpanded(true)}
                  className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-100 transition-colors px-3 py-1 rounded-lg hover:bg-bg-hover border border-transparent hover:border-bg-border"
                >
                  <ChevronDown size={14} />
                  Modify Source
                </button>
              </div>
            ) : (
              /* Expanded state: Load sample + char count */
              <div className="flex-1 flex items-center justify-end gap-4">
                {activeTab === "html" && (
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setHtmlInput(SAMPLE_HTML)}
                      className="text-[11px] font-bold text-slate-500 hover:text-accent uppercase tracking-wider transition-colors px-2 py-1"
                    >
                      Load Sample
                    </button>
                    <div className="h-3 w-px bg-bg-border" />
                    <span className="text-[11px] text-slate-500 font-mono">
                      {htmlInput.length.toLocaleString()} chars
                    </span>
                  </div>
                )}
                {results && (
                  <button
                    onClick={() => setInputExpanded(false)}
                    className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-100 transition-colors px-3 py-1 rounded-lg hover:bg-bg-hover border border-transparent hover:border-bg-border"
                  >
                    <ChevronUp size={14} />
                    Collapse
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Textarea or URL input — hidden when collapsed */}
          {!showCollapsed && (activeTab === "html" ? (
             <div className="p-4">
                <textarea
                  id="html-input"
                  className="w-full h-48 resize-none bg-bg-base/40 text-slate-300 text-xs p-4 rounded-xl border border-bg-border placeholder-slate-600 leading-relaxed focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary/50 transition-all font-mono"
                  value={htmlInput}
                  onChange={(e) => setHtmlInput(e.target.value)}
                  placeholder={`<html>\n  <body>\n    <div class="card">\n       <button id="login">Login</button>\n    </div>\n  </body>\n</html>`}
                  spellCheck={false}
                />
                <div className="flex items-center justify-between mt-4">
                  <div className="flex items-center gap-2 text-slate-500">
                    <Sparkles size={13} className="text-primary-light" />
                    <span className="text-[11px]">Paste your HTML source or component snippet for static analysis.</span>
                  </div>
                  <button
                    id="extract-btn"
                    onClick={onExtract}
                    disabled={!htmlInput.trim() || loading}
                    className="group relative flex items-center gap-2.5 px-6 py-2.5 rounded-xl font-bold text-xs transition-all disabled:opacity-40 disabled:cursor-not-allowed bg-gradient-to-r from-primary to-accent text-white hover:shadow-glow hover:scale-[1.02] active:scale-[0.98] border border-white/10 overflow-hidden"
                  >
                    <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                    {loading ? (
                      <>
                        <Loader2 size={14} className="animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Scan size={14} />
                        Extract Locators
                      </>
                    )}
                  </button>
                </div>
             </div>
          ) : (
             <div className="p-4 flex flex-col items-center justify-center min-h-[16rem] bg-gradient-to-b from-bg-surface to-bg-base/20">
                <div className="w-full max-w-2xl text-center space-y-6">
                   <div className="space-y-2">
                      <h3 className="text-lg font-bold text-slate-100">Browse Live Website</h3>
                      <p className="text-xs text-slate-500 leading-relaxed">
                        Extract locators from any live URL. We'll render the page with Playwright, handle dynamic JavaScript content, and capture a full visual state.
                      </p>
                   </div>
                   
                   <div className="relative group max-w-xl mx-auto w-full">
                      <div className="absolute -inset-1 bg-gradient-to-r from-accent/20 to-primary/20 rounded-2xl blur-lg opacity-0 group-focus-within:opacity-100 transition-opacity" />
                      <div className="relative flex items-center gap-3 p-1.5 bg-bg-base border border-bg-border rounded-2xl group-focus-within:border-accent/50 transition-all shadow-xl">
                        <div className="w-10 h-10 flex items-center justify-center rounded-xl bg-bg-elevated text-accent">
                           <Globe size={18} />
                        </div>
                        <input 
                          type="text" 
                          className="flex-1 bg-transparent border-none text-sm text-slate-200 py-2 focus:outline-none placeholder-slate-600 font-medium"
                          placeholder="https://app.example.com/login"
                          value={urlInput}
                          onChange={(e) => setUrlInput(e.target.value)}
                          onKeyDown={(e) => e.key === "Enter" && onExtractURL()}
                        />
                        <button
                          onClick={onExtractURL}
                          disabled={!urlInput.trim() || loading}
                          className="flex items-center gap-2 px-6 py-2.5 rounded-xl font-bold text-xs transition-all disabled:opacity-40 disabled:cursor-not-allowed bg-accent text-white hover:brightness-110 active:scale-95 shadow-lg shadow-accent/20"
                        >
                          {loading ? (
                            <Loader2 size={14} className="animate-spin" />
                          ) : (
                            <ExternalLink size={14} />
                          )}
                          Go
                        </button>
                      </div>
                   </div>

                   {loading && (
                      <div className="flex flex-col items-center gap-3 animate-in fade-in slide-in-from-bottom-2">
                         <div className="flex gap-1">
                            <div className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce [animation-delay:-0.3s]" />
                            <div className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce [animation-delay:-0.15s]" />
                            <div className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce" />
                         </div>
                         <span className="text-[11px] font-bold text-accent uppercase tracking-widest">Waking up browser...</span>
                      </div>
                   )}
                </div>
             </div>
          ))}

          {/* When collapsed, show hint */}
          {showCollapsed && (
            <div className="px-5 py-2.5 flex items-center justify-between border-t border-bg-border/30 bg-bg-base/30">
              <div className="flex items-center gap-2 text-[10px] text-slate-500 font-medium uppercase tracking-wider">
                <ShieldCheck size={10} className="text-emerald-500" />
                Processing complete
              </div>
              <p className="text-[11px] text-slate-600 italic">
                Extraction results are shown below. Expand to re-run with different source.
              </p>
            </div>
          )}
        </div>

        {/* ── Error State ── */}
        {error && (
          <div className="flex items-start gap-4 p-4 rounded-2xl border border-red-500/20 bg-red-500/5 animate-in fade-in slide-in-from-top-2">
            <div className="w-8 h-8 rounded-lg bg-red-500/10 flex items-center justify-center flex-shrink-0">
              <AlertCircle size={18} className="text-red-400" />
            </div>
            <div className="flex-1 pt-1">
              <p className="text-sm font-bold text-red-200">Execution Error</p>
              <p className="text-xs text-red-400/80 mt-1 leading-relaxed">{error}</p>
            </div>
          </div>
        )}

        {/* ── Results ── */}
        {results && !loading && (
          <div className="space-y-6 animate-in fade-in duration-500">
            
            <div className="flex gap-6 items-start">
              {/* Left Column: Metrics and Tools */}
              <div className="flex-1 space-y-6 min-w-0">
                <InteractiveStatsCards
                  elements={results.elements}
                  filters={filters}
                  onFilterChange={setFilters}
                />

                <div className="flex items-center gap-4 bg-bg-surface/50 p-2 rounded-2xl border border-bg-border">
                  <div className="flex-1 flex items-center gap-4 px-2">
                    <div className="flex-shrink-0">
                      <h2 className="text-sm font-bold text-slate-100 tracking-tight">{results.page_name}</h2>
                      <p className="text-[10px] text-slate-500 font-medium uppercase tracking-wider mt-0.5">
                        {results.total_elements} Detected • {results.stable_elements} Stable
                      </p>
                    </div>
                    <div className="h-6 w-px bg-bg-border" />
                    <button
                      onClick={onVerify}
                      disabled={verifying}
                      className={`flex items-center gap-2 px-4 py-2 rounded-xl border text-[11px] font-bold transition-all shadow-sm active:scale-95 ${
                        verifications 
                          ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400" 
                          : "border-primary/30 bg-primary/10 text-primary-light hover:bg-primary/20"
                      }`}
                    >
                      {verifying ? (
                        <Loader2 size={12} className="animate-spin" />
                      ) : (
                        <ShieldCheck size={12} />
                      )}
                      {verifications ? "RE-VERIFY ALL" : "VERIFY LOCATORS"}
                    </button>
                  </div>

                  <ExportMenu data={results} filters={filters} />
                </div>
              </div>

              {/* Right Column: Live Screenshot Preview (Sticky) */}
              {results.screenshot && (
                <div className={`transition-all duration-500 ease-in-out ${showScreenshot ? 'w-80 opacity-100' : 'w-10 opacity-50'}`}>
                   <div className="sticky top-20 rounded-2xl border border-bg-border bg-bg-surface shadow-2xl overflow-hidden group">
                      <div className="flex items-center justify-between px-3 py-2 border-b border-bg-border bg-bg-elevated/80">
                         <div className="flex items-center gap-2 overflow-hidden">
                            <Globe size={11} className="text-accent flex-shrink-0" />
                            {showScreenshot && <span className="text-[10px] text-slate-300 font-bold uppercase tracking-wider truncate">Visual State</span>}
                         </div>
                         <button 
                            onClick={() => setShowScreenshot(!showScreenshot)}
                            className="p-1 hover:bg-bg-hover rounded-md text-slate-500 hover:text-slate-200 transition-colors"
                          >
                            <Maximize2 size={12} />
                         </button>
                      </div>
                      
                      {showScreenshot && (
                        <div className="relative aspect-[3/4] overflow-auto scrollbar-hide bg-black/40 group-hover:bg-transparent transition-colors">
                           <img 
                             src={`data:image/png;base64,${results.screenshot}`} 
                             alt="Page Screenshot" 
                             className="w-full h-auto grayscale-[20%] group-hover:grayscale-0 transition-all duration-500"
                           />
                           <div className="absolute inset-0 shadow-[inset_0_0_40px_rgba(0,0,0,0.5)] pointer-events-none" />
                        </div>
                      )}
                   </div>
                </div>
              )}
            </div>

            {/* Filter and Table */}
            <div className="space-y-4">
               <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <FilterBar
                      filters={filters}
                      onChange={setFilters}
                      availableTypes={availableTypes}
                      totalCount={results.total_elements}
                      filteredCount={filteredCount}
                    />
                  </div>
               </div>

               <ElementsTable
                 elements={results.elements}
                 filters={filters}
                 onSelectElement={setSelectedElement}
                 onCopy={handleCopy}
                 verifications={verifications ?? undefined}
               />
            </div>
          </div>
        )}
      </main>

      {/* ── Detail Popup ── */}
      <ElementDetailSheet
        element={selectedElement}
        onClose={() => setSelectedElement(null)}
        onCopy={handleCopy}
        verification={verifications?.find(v => v.absolute_xpath === selectedElement?.absolute_xpath)?.verification}
      />

      {/* ── Toast ── */}
      {toast && (
        <ToastNotification message={toast} onDismiss={dismissToast} />
      )}
    </div>
  );
}
