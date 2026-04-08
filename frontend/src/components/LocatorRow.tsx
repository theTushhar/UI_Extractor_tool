import { useState } from "react";
import { ChevronDown, ChevronRight, Copy, CheckCircle } from "lucide-react";
import type { LocatorCandidate } from "../types";

interface Props {
  locator: LocatorCandidate;
  isRecommended?: boolean;
  onCopy: (value: string) => void;
}

function scoreColor(score: number) {
  if (score >= 80) return "text-score-high";
  if (score >= 50) return "text-score-mid";
  return "text-score-low";
}

function scoreBg(score: number) {
  if (score >= 80) return "bg-score-high";
  if (score >= 50) return "bg-score-mid";
  return "bg-score-low";
}

export function LocatorRow({ locator, isRecommended, onCopy }: Props) {
  const [expanded, setExpanded] = useState(isRecommended ?? false);
  const [copied, setCopied] = useState(false);

  function handleCopy(e: React.MouseEvent) {
    e.stopPropagation();
    navigator.clipboard.writeText(locator.value).then(() => {
      setCopied(true);
      onCopy(locator.value);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div
      className={`rounded-xl border transition-all ${
        isRecommended
          ? "border-primary/30 bg-primary/5"
          : "border-bg-border bg-bg-elevated/50"
      }`}
    >
      {/* Header row */}
      <button
        className="w-full flex items-center gap-3 px-4 py-3 text-left group"
        onClick={() => setExpanded((e) => !e)}
      >
        {/* Rank */}
        <span className="w-6 text-center text-xs font-bold text-slate-500">
          #{locator.rank}
        </span>

        {/* Strategy chip */}
        <span className="px-2 py-0.5 rounded-md text-xs font-mono font-medium bg-bg-surface text-slate-300 border border-bg-border flex-shrink-0">
          {locator.strategy}
        </span>

        {/* Value preview */}
        <code className="flex-1 text-xs font-mono text-slate-300 truncate">
          {locator.value}
        </code>

        {/* Score */}
        <span className={`text-sm font-bold tabular-nums mr-2 ${scoreColor(locator.score)}`}>
          {locator.score}
        </span>

        {/* Unique badge */}
        {locator.unique && (
          <span className="text-xs px-1.5 py-0.5 rounded-md bg-mode-input/15 text-mode-input border border-mode-input/20 flex-shrink-0">
            unique
          </span>
        )}

        {/* Expand icon */}
        <span className="text-slate-600 group-hover:text-slate-400 transition-colors ml-1">
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </span>
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div className="px-4 pb-4 pt-0 border-t border-bg-border/50 animate-fade-in">
          {/* Full value with copy */}
          <div className="mt-3 flex items-start gap-2">
            <div className="flex-1 font-mono text-xs p-3 rounded-lg bg-bg-base border border-bg-border text-slate-300 break-all leading-relaxed">
              {locator.value}
            </div>
            <button
              onClick={handleCopy}
              title="Copy locator"
              className={`flex-shrink-0 w-9 h-9 flex items-center justify-center rounded-lg border transition-all ${
                copied
                  ? "border-mode-input/50 bg-mode-input/15 text-mode-input"
                  : "border-bg-border bg-bg-surface text-slate-400 hover:border-primary/50 hover:text-primary-light"
              }`}
            >
              {copied ? <CheckCircle size={15} /> : <Copy size={15} />}
            </button>
          </div>

          {/* Score bar */}
          <div className="mt-3 flex items-center gap-3">
            <span className="text-xs text-slate-500 w-10">Score</span>
            <div className="flex-1 h-1.5 rounded-full bg-bg-border overflow-hidden">
              <div
                className={`h-full rounded-full ${scoreBg(locator.score)}`}
                style={{ width: `${locator.score}%` }}
              />
            </div>
            <span className={`text-xs font-bold tabular-nums ${scoreColor(locator.score)}`}>
              {locator.score}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
