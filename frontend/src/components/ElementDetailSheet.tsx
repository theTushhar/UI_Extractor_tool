import { useState } from "react";
import { X, Copy, CheckCircle, ChevronDown, ChevronRight, Tag, Layers } from "lucide-react";
import type { ExtractedElement, ElementMode } from "../types";
import { LocatorRow } from "./LocatorRow";

interface Props {
  element: ExtractedElement | null;
  onClose: () => void;
  onCopy: (value: string) => void;
}

const modeStyle: Record<ElementMode, { badge: string; dot: string }> = {
  Input: { badge: "bg-mode-input/15 text-mode-input border-mode-input/30", dot: "bg-mode-input" },
  UserAction: { badge: "bg-mode-action/15 text-mode-action border-mode-action/30", dot: "bg-mode-action" },
  Output: { badge: "bg-mode-output/15 text-mode-output border-mode-output/30", dot: "bg-mode-output" },
  Unknown: { badge: "bg-mode-unknown/15 text-mode-unknown border-mode-unknown/30", dot: "bg-mode-unknown" },
};

function scoreColor(score: number) {
  if (score >= 80) return "text-score-high";
  if (score >= 50) return "text-score-mid";
  return "text-score-low";
}

export function ElementDetailSheet({ element, onClose, onCopy }: Props) {
  const [attrOpen, setAttrOpen] = useState(false);
  const [recoCopied, setRecoCopied] = useState(false);

  function copyReco() {
    if (!element) return;
    navigator.clipboard.writeText(element.recommended_locator.value).then(() => {
      setRecoCopied(true);
      onCopy(element.recommended_locator.value);
      setTimeout(() => setRecoCopied(false), 2000);
    });
  }

  // Close on Escape key
  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Escape") onClose();
  }

  if (!element) return null;
  const ms = modeStyle[element.mode];
  const attrEntries = Object.entries(element.attributes);

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 sheet-overlay"
        onClick={onClose}
      />

      {/* Centered Popup Modal */}
      <div
        className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none"
      >
        <div
          className="pointer-events-auto w-full max-w-2xl max-h-[90vh] flex flex-col rounded-2xl border border-bg-border bg-bg-surface shadow-2xl shadow-black/60 animate-slide-up"
          onKeyDown={handleKeyDown}
          tabIndex={-1}
        >
          {/* ── Header ── */}
          <div className="flex items-start justify-between px-4 py-3 border-b border-bg-border flex-shrink-0">
            <div className="flex-1 min-w-0 pr-3">
              <div className="flex items-center gap-2 mb-1">
                <code className="text-xs font-mono text-slate-500">&lt;{element.tag}&gt;</code>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${ms.badge}`}>
                  {element.mode}
                </span>
                <span className="text-xs text-slate-500">{element.element_type}</span>
              </div>
              <h2 className="text-base font-semibold text-slate-100 truncate" title={element.element_name}>
                {element.element_name}
              </h2>
            </div>
            <button
              onClick={onClose}
              className="flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-lg border border-bg-border hover:bg-bg-elevated hover:text-slate-200 text-slate-500 transition-all"
            >
              <X size={14} />
            </button>
          </div>

          {/* ── Scrollable content ── */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">

            {/* Recommended Locator card */}
            <div className="rounded-xl border border-primary/25 bg-primary/5 p-3">
              <div className="flex items-center gap-2 mb-2">
                <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${ms.dot}`} />
                <span className="text-xs font-semibold uppercase tracking-widest text-slate-500">Recommended</span>
                <span className="px-1.5 py-0.5 text-xs rounded-md bg-bg-surface border border-bg-border font-mono text-slate-400 ml-auto">
                  {element.recommended_locator.strategy}
                </span>
                <div className="flex items-center gap-1.5">
                  <div className="h-1 w-14 rounded-full bg-bg-border overflow-hidden">
                    <div
                      className="h-full rounded-full bg-score-high"
                      style={{ width: `${element.recommended_locator.score}%` }}
                    />
                  </div>
                  <span className={`text-xs font-bold tabular-nums ${scoreColor(element.recommended_locator.score)}`}>
                    {element.recommended_locator.score}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <code className="flex-1 text-sm font-mono text-accent break-all leading-relaxed min-w-0">
                  {element.recommended_locator.value}
                </code>
                <button
                  onClick={copyReco}
                  title="Copy recommended locator"
                  className={`flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-lg border transition-all ${
                    recoCopied
                      ? "border-mode-input/50 bg-mode-input/15 text-mode-input"
                      : "border-primary/30 bg-primary/10 text-primary-light hover:bg-primary/20"
                  }`}
                >
                  {recoCopied ? <CheckCircle size={14} /> : <Copy size={14} />}
                </button>
              </div>
              {element.recommended_locator.reason && (
                <p className="mt-1.5 text-xs text-slate-500 leading-relaxed">
                  {element.recommended_locator.reason}
                </p>
              )}
            </div>

            {/* All locators */}
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-2 flex items-center gap-2">
                <Layers size={11} />
                All Locators
                <span className="px-1.5 py-0.5 rounded-md text-xs bg-bg-elevated border border-bg-border text-slate-400 font-mono">
                  {element.locators.length}
                </span>
              </h3>
              <div className="space-y-1.5">
                {element.locators.map((loc, i) => (
                  <LocatorRow
                    key={i}
                    locator={loc}
                    isRecommended={loc.value === element.recommended_locator.value}
                    onCopy={onCopy}
                  />
                ))}
              </div>
            </div>

            {/* Attributes */}
            {attrEntries.length > 0 && (
              <div>
                <button
                  onClick={() => setAttrOpen((o) => !o)}
                  className="w-full flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-slate-500 hover:text-slate-300 transition-colors mb-2 group"
                >
                  <Tag size={11} />
                  Attributes
                  <span className="px-1.5 py-0.5 rounded-md text-xs bg-bg-elevated border border-bg-border text-slate-400 font-mono">
                    {attrEntries.length}
                  </span>
                  <span className="ml-auto">
                    {attrOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                  </span>
                </button>
                {attrOpen && (
                  <div className="rounded-xl border border-bg-border overflow-hidden animate-fade-in">
                    {attrEntries.map(([key, val], i) => (
                      <div
                        key={key}
                        className={`flex gap-0 ${i > 0 ? "border-t border-bg-border" : ""}`}
                      >
                        <div className="px-3 py-1.5 w-[35%] flex-shrink-0 bg-bg-elevated border-r border-bg-border">
                          <code className="text-xs font-mono text-slate-400 block truncate">{key}</code>
                        </div>
                        <div className="px-3 py-1.5 flex-1 min-w-0">
                          <code className="text-xs font-mono text-slate-300 break-all">{val}</code>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
