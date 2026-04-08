import { useState, useRef, useEffect } from "react";
import { Search, ChevronDown, X, Filter } from "lucide-react";
import type { ElementMode, Filters } from "../types";

interface Props {
  filters: Filters;
  onChange: (filters: Filters) => void;
  availableTypes: string[];
  totalCount: number;
  filteredCount: number;
  className?: string;
}

const MODES: Array<"All" | ElementMode> = ["All", "Input", "UserAction", "Output", "Unknown"];

function Dropdown({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-bg-border bg-bg-surface hover:border-primary/40 hover:bg-bg-elevated transition-all text-xs text-slate-300 min-w-[100px] justify-between group"
      >
        <span className="text-slate-500 mr-0.5">{label}:</span>
        <span className="font-medium truncate">{value}</span>
        <ChevronDown
          size={12}
          className={`text-slate-500 group-hover:text-slate-300 transition-transform flex-shrink-0 ${open ? "rotate-180" : ""}`}
        />
      </button>
      {open && (
        <div className="absolute top-full mt-1 left-0 z-30 min-w-full rounded-xl border border-bg-border bg-bg-elevated shadow-xl shadow-black/50 overflow-hidden animate-fade-in">
          {options.map((opt) => (
            <button
              key={opt}
              onClick={() => { onChange(opt); setOpen(false); }}
              className={`w-full text-left px-3 py-2 text-xs transition-colors hover:bg-bg-hover ${
                value === opt ? "text-primary-light font-medium bg-primary/10" : "text-slate-300"
              }`}
            >
              {opt}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export function FilterBar({ filters, onChange, availableTypes, totalCount, filteredCount, className }: Props) {
  const activeFilterCount = [
    filters.mode !== "All",
    filters.elementType !== "All",
    filters.stableOnly,
    filters.search.length > 0,
  ].filter(Boolean).length;

  function reset() {
    onChange({ search: "", mode: "All", elementType: "All", stableOnly: false });
  }

  return (
    <div className={`flex items-center gap-2 ${className ?? ""}`}>
      {/* Search */}
      <div className="relative">
        <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
        <input
          type="text"
          placeholder="Search…"
          value={filters.search}
          onChange={(e) => onChange({ ...filters, search: e.target.value })}
          className="w-36 pl-7 pr-2 py-1.5 rounded-lg border border-bg-border bg-bg-surface text-xs text-slate-200 placeholder-slate-500 focus:border-primary/50 focus:bg-bg-elevated transition-all outline-none"
        />
        {filters.search && (
          <button
            onClick={() => onChange({ ...filters, search: "" })}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
          >
            <X size={11} />
          </button>
        )}
      </div>

      {/* Mode filter */}
      <Dropdown
        label="Mode"
        value={filters.mode}
        options={MODES}
        onChange={(v) => onChange({ ...filters, mode: v })}
      />

      {/* Type filter */}
      <Dropdown
        label="Type"
        value={filters.elementType}
        options={["All", ...availableTypes]}
        onChange={(v) => onChange({ ...filters, elementType: v })}
      />

      {/* Stable only toggle */}
      <button
        onClick={() => onChange({ ...filters, stableOnly: !filters.stableOnly })}
        className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs font-medium transition-all ${
          filters.stableOnly
            ? "border-mode-input/60 bg-mode-input/15 text-mode-input"
            : "border-bg-border bg-bg-surface text-slate-400 hover:border-primary/40"
        }`}
      >
        <Shield size={12} />
        Stable
      </button>

      {/* Active filter count + reset */}
      {activeFilterCount > 0 && (
        <div className="flex items-center gap-1.5">
          <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-primary/15 border border-primary/30 text-xs font-medium text-primary-light">
            <Filter size={10} />
            {filteredCount}/{totalCount}
          </span>
          <button
            onClick={reset}
            className="text-xs text-slate-500 hover:text-slate-200 transition-colors px-1.5 py-0.5 rounded-md hover:bg-bg-elevated"
          >
            Clear
          </button>
        </div>
      )}
    </div>
  );
}

function Shield({ size, className }: { size: number; className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  );
}
