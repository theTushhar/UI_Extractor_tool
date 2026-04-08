import { useState } from "react";
import { ChevronUp, ChevronDown, Copy } from "lucide-react";
import type { ExtractedElement, ElementMode, SortField, SortDir, Filters } from "../types";

interface Props {
  elements: ExtractedElement[];
  filters: Filters;
  onSelectElement: (el: ExtractedElement) => void;
  onCopy: (value: string) => void;
}

const modeStyles: Record<ElementMode, string> = {
  Input: "bg-mode-input/15 text-mode-input border-mode-input/30",
  UserAction: "bg-mode-action/15 text-mode-action border-mode-action/30",
  Output: "bg-mode-output/15 text-mode-output border-mode-output/30",
  Unknown: "bg-mode-unknown/15 text-mode-unknown border-mode-unknown/30",
};

const modeDot: Record<ElementMode, string> = {
  Input: "bg-mode-input",
  UserAction: "bg-mode-action",
  Output: "bg-mode-output",
  Unknown: "bg-mode-unknown",
};

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

function SortIcon({ active, dir }: { active: boolean; dir: SortDir }) {
  if (!active) return <span className="opacity-20"><ChevronUp size={12} /></span>;
  return dir === "asc" ? <ChevronUp size={12} className="text-primary-light" /> : <ChevronDown size={12} className="text-primary-light" />;
}

function applyFilters(elements: ExtractedElement[], filters: Filters): ExtractedElement[] {
  return elements.filter((el) => {
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
  });
}

function sortElements(elements: ExtractedElement[], field: SortField, dir: SortDir) {
  return [...elements].sort((a, b) => {
    let av: number | string;
    let bv: number | string;
    switch (field) {
      case "element_name": av = a.element_name; bv = b.element_name; break;
      case "element_type": av = a.element_type; bv = b.element_type; break;
      case "mode": av = a.mode; bv = b.mode; break;
      case "score": av = a.recommended_locator.score; bv = b.recommended_locator.score; break;
      case "locators": av = a.locators.length; bv = b.locators.length; break;
      default: return 0;
    }
    if (typeof av === "number" && typeof bv === "number") {
      return dir === "asc" ? av - bv : bv - av;
    }
    return dir === "asc"
      ? String(av).localeCompare(String(bv))
      : String(bv).localeCompare(String(av));
  });
}

const columns: { key: SortField; label: string; width?: string }[] = [
  { key: "element_name", label: "Element", width: "w-[28%]" },
  { key: "mode", label: "Mode", width: "w-[11%]" },
  { key: "element_type", label: "Type", width: "w-[13%]" },
  { key: "score", label: "Score", width: "w-[18%]" },
  { key: "locators", label: "Locators", width: "w-[10%]" },
];

export function ElementsTable({ elements, filters, onSelectElement, onCopy }: Props) {
  const [sortField, setSortField] = useState<SortField>("score");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  function toggleSort(field: SortField) {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  }

  const filtered = applyFilters(elements, filters);
  const sorted = sortElements(filtered, sortField, sortDir);

  return (
    <div className="rounded-2xl border border-bg-border bg-bg-surface overflow-hidden" style={{ boxShadow: "0 4px 24px rgba(0,0,0,0.3)" }}>
      {/* Table header */}
      <div className="flex items-center border-b border-bg-border bg-bg-elevated px-4 py-3">
        {columns.map((col) => (
          <button
            key={col.key}
            className={`flex items-center gap-1.5 text-xs font-semibold uppercase tracking-widest text-slate-500 hover:text-slate-300 transition-colors ${col.width ?? "flex-1"}`}
            onClick={() => toggleSort(col.key)}
          >
            {col.label}
            <SortIcon active={sortField === col.key} dir={sortDir} />
          </button>
        ))}
        {/* Actions column header */}
        <div className="text-xs font-semibold uppercase tracking-widest text-slate-500 w-[20%] text-right pr-1">
          Locator
        </div>
      </div>

      {/* Rows */}
      {sorted.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-slate-500">
          <div className="text-5xl mb-4 opacity-30">🔍</div>
          <p className="text-sm font-medium">No elements match your filters.</p>
          <p className="text-xs mt-1 text-slate-600">Try loosening the search or clearing filters.</p>
        </div>
      ) : (
        <div>
          {sorted.map((el, idx) => (
            <div
              key={idx}
              className="flex items-center px-4 py-3.5 border-b border-bg-border table-row-hover cursor-pointer group"
              onClick={() => onSelectElement(el)}
            >
              {/* Element name + tag */}
              <div className="w-[28%] pr-3 min-w-0">
                <p className="text-sm font-semibold text-slate-200 truncate group-hover:text-white transition-colors">
                  {el.element_name}
                </p>
                <p className="text-xs text-slate-500 font-mono mt-0.5">&lt;{el.tag}&gt;</p>
              </div>

              {/* Mode badge */}
              <div className="w-[11%]">
                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${modeStyles[el.mode]}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${modeDot[el.mode]}`} />
                  {el.mode}
                </span>
              </div>

              {/* Element type */}
              <div className="w-[13%]">
                <span className="text-xs text-slate-400 font-medium">{el.element_type}</span>
              </div>

              {/* Score + bar */}
              <div className="w-[18%] flex items-center gap-2.5 pr-4">
                <div className="flex-1 h-1.5 rounded-full bg-bg-border overflow-hidden">
                  <div
                    className={`h-full rounded-full ${scoreBg(el.recommended_locator.score)}`}
                    style={{ width: `${el.recommended_locator.score}%` }}
                  />
                </div>
                <span className={`text-sm font-bold tabular-nums w-8 text-right ${scoreColor(el.recommended_locator.score)}`}>
                  {el.recommended_locator.score}
                </span>
              </div>

              {/* Locator count */}
              <div className="w-[10%]">
                <span className="px-2 py-0.5 rounded-md text-xs bg-bg-elevated border border-bg-border text-slate-400 font-mono">
                  {el.locators.length}
                </span>
              </div>

              {/* Recommended locator value + copy */}
              <div className="w-[20%] flex items-center gap-2 justify-end min-w-0 pl-2">
                <code
                  className="text-xs font-mono text-slate-400 truncate max-w-[120px] group-hover:text-accent transition-colors"
                  title={el.recommended_locator.value}
                >
                  {el.recommended_locator.value}
                </code>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    navigator.clipboard.writeText(el.recommended_locator.value);
                    onCopy(el.recommended_locator.value);
                  }}
                  title="Copy locator"
                  className="opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-lg border border-bg-border hover:border-primary/50 hover:text-primary-light text-slate-500"
                >
                  <Copy size={12} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Footer */}
      {sorted.length > 0 && (
        <div className="px-4 py-2.5 border-t border-bg-border bg-bg-elevated flex items-center justify-between">
          <span className="text-xs text-slate-600">
            Showing <span className="text-slate-400 font-medium">{sorted.length}</span> of{" "}
            <span className="text-slate-400 font-medium">{elements.length}</span> elements
          </span>
          <span className="text-xs text-slate-600">
            Click row to inspect • Hover to copy
          </span>
        </div>
      )}
    </div>
  );
}
