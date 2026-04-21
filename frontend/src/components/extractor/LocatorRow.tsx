import { useState } from "react";
import { ChevronDown, ChevronRight, Copy, CheckCircle, Terminal, ShieldCheck, ShieldAlert, ShieldX } from "lucide-react";
import type { LocatorCandidate, VerificationResult } from "../../types";

interface Props {
  locator: LocatorCandidate;
  isRecommended?: boolean;
  onCopy: (value: string) => void;
  verification?: VerificationResult;
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

export function LocatorRow({ locator, isRecommended, onCopy, verification }: Props) {
  const [expanded, setExpanded] = useState(isRecommended ?? false);
  const [copied, setCopied] = useState(false);
  const [copiedPW, setCopiedPW] = useState(false);

  function handleCopy(e: React.MouseEvent) {
    e.stopPropagation();
    navigator.clipboard.writeText(locator.value).then(() => {
      setCopied(true);
      onCopy(locator.value);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  function handleCopyPW(e: React.MouseEvent) {
    e.stopPropagation();
    const pwValue = `page.locator('${locator.value.replace(/'/g, "\\'")}')`;
    navigator.clipboard.writeText(pwValue).then(() => {
      setCopiedPW(true);
      onCopy(pwValue);
      setTimeout(() => setCopiedPW(false), 2000);
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

        {/* Verification Status */}
        {(verification || locator.status) && (
          <div className="flex items-center gap-1.5 ml-2">
             {(verification?.status === 'correct' || locator.status === 'correct') && (
               <span className="flex items-center gap-1 text-[10px] font-bold uppercase py-0.5 px-1.5 rounded-md bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                 <ShieldCheck size={10} /> Correct
               </span>
             )}
             {(verification?.status === 'duplicate' || (locator.status === 'shifted' && locator.actual_matches && locator.actual_matches > 1)) && (
               <span className="flex items-center gap-1 text-[10px] font-bold uppercase py-0.5 px-1.5 rounded-md bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">
                 <ShieldAlert size={10} /> Duplicate ({verification?.match_count || locator.actual_matches})
               </span>
             )}
             {(verification?.status === 'broken' || locator.status === 'broken') && (
               <span className="flex items-center gap-1 text-[10px] font-bold uppercase py-0.5 px-1.5 rounded-md bg-rose-500/20 text-rose-400 border border-rose-500/30">
                 <ShieldX size={10} /> Broken
               </span>
             )}
             {(verification?.status === 'misidentified' || (locator.status === 'shifted' && locator.actual_matches === 1)) && (
               <span className="flex items-center gap-1 text-[10px] font-bold uppercase py-0.5 px-1.5 rounded-md bg-orange-500/20 text-orange-400 border border-orange-500/30">
                 <ShieldAlert size={10} /> Wrong Element
               </span>
             )}
          </div>
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
              onClick={handleCopyPW}
              title="Copy as Playwright locator"
              className={`flex-shrink-0 px-2 h-9 flex items-center justify-center gap-2 rounded-lg border text-xs font-semibold transition-all ${
                copiedPW
                  ? "border-primary/50 bg-primary/15 text-primary-light"
                  : "border-bg-border bg-bg-surface text-slate-400 hover:border-primary/50 hover:text-primary-light"
              }`}
            >
              {copiedPW ? <CheckCircle size={14} /> : <Terminal size={14} />}
              <span>Playwright</span>
            </button>
            <button
              onClick={handleCopy}
              title="Copy raw locator"
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
