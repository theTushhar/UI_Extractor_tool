import { Layers, Shield, MousePointerClick, Eye, HelpCircle, CheckCircle2 } from "lucide-react";
import type { ExtractedElement, ElementMode, Filters } from "../types";

interface Props {
  elements: ExtractedElement[];
  filters: Filters;
  onFilterChange: (filters: Filters) => void;
}

type CardKey = "all" | "input" | "action" | "output" | "stable" | "unknown";

interface CardDef {
  key: CardKey;
  label: string;
  icon: React.ElementType;
  color: string;         // text
  bg: string;            // active bg
  border: string;        // active border
  activeBg: string;      // active icon bg
  barColor: string;
  idleBorder: string;
}

const CARDS: CardDef[] = [
  {
    key: "all",
    label: "All",
    icon: Layers,
    color: "text-slate-200",
    bg: "bg-primary/10",
    border: "border-primary/50",
    activeBg: "bg-primary/20",
    barColor: "bg-primary",
    idleBorder: "border-bg-border",
  },
  {
    key: "input",
    label: "Input",
    icon: CheckCircle2,
    color: "text-mode-input",
    bg: "bg-mode-input/10",
    border: "border-mode-input/50",
    activeBg: "bg-mode-input/20",
    barColor: "bg-mode-input",
    idleBorder: "border-bg-border",
  },
  {
    key: "action",
    label: "User Action",
    icon: MousePointerClick,
    color: "text-mode-action",
    bg: "bg-mode-action/10",
    border: "border-mode-action/50",
    activeBg: "bg-mode-action/20",
    barColor: "bg-mode-action",
    idleBorder: "border-bg-border",
  },
  {
    key: "output",
    label: "Output",
    icon: Eye,
    color: "text-mode-output",
    bg: "bg-mode-output/10",
    border: "border-mode-output/50",
    activeBg: "bg-mode-output/20",
    barColor: "bg-mode-output",
    idleBorder: "border-bg-border",
  },
  {
    key: "stable",
    label: "Stable",
    icon: Shield,
    color: "text-accent",
    bg: "bg-accent/10",
    border: "border-accent/50",
    activeBg: "bg-accent/20",
    barColor: "bg-accent",
    idleBorder: "border-bg-border",
  },
  {
    key: "unknown",
    label: "Unknown",
    icon: HelpCircle,
    color: "text-mode-unknown",
    bg: "bg-mode-unknown/10",
    border: "border-mode-unknown/50",
    activeBg: "bg-mode-unknown/20",
    barColor: "bg-mode-unknown",
    idleBorder: "border-bg-border",
  },
];

function getCount(elements: ExtractedElement[], key: CardKey): number {
  switch (key) {
    case "all":     return elements.length;
    case "input":   return elements.filter((e) => e.mode === "Input").length;
    case "action":  return elements.filter((e) => e.mode === "UserAction").length;
    case "output":  return elements.filter((e) => e.mode === "Output").length;
    case "stable":  return elements.filter((e) => e.recommended_locator.score >= 80).length;
    case "unknown": return elements.filter((e) => e.mode === "Unknown").length;
  }
}

function isActive(key: CardKey, filters: Filters): boolean {
  switch (key) {
    case "all":     return filters.mode === "All" && !filters.stableOnly;
    case "input":   return filters.mode === "Input" && !filters.stableOnly;
    case "action":  return filters.mode === "UserAction" && !filters.stableOnly;
    case "output":  return filters.mode === "Output" && !filters.stableOnly;
    case "stable":  return filters.stableOnly;
    case "unknown": return filters.mode === "Unknown" && !filters.stableOnly;
  }
}

function applyFilter(key: CardKey, filters: Filters, onFilterChange: Props["onFilterChange"]) {
  if (isActive(key, filters)) {
    // Toggle off → reset to All
    onFilterChange({ ...filters, mode: "All", stableOnly: false });
    return;
  }
  switch (key) {
    case "all":     onFilterChange({ ...filters, mode: "All", stableOnly: false }); break;
    case "input":   onFilterChange({ ...filters, mode: "Input", stableOnly: false }); break;
    case "action":  onFilterChange({ ...filters, mode: "UserAction", stableOnly: false }); break;
    case "output":  onFilterChange({ ...filters, mode: "Output", stableOnly: false }); break;
    case "stable":  onFilterChange({ ...filters, mode: "All", stableOnly: true }); break;
    case "unknown": onFilterChange({ ...filters, mode: "Unknown", stableOnly: false }); break;
  }
}

export function InteractiveStatsCards({ elements, filters, onFilterChange }: Props) {
  const total = elements.length;

  return (
    <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
      {CARDS.map((card) => {
        const Icon = card.icon;
        const count = getCount(elements, card.key);
        const active = isActive(card.key, filters);
        const pct = total > 0 && card.key !== "all" ? Math.round((count / total) * 100) : 100;

        return (
          <button
            key={card.key}
            onClick={() => applyFilter(card.key, filters, onFilterChange)}
            className={`group relative flex flex-col items-center gap-1.5 p-3 rounded-xl border transition-all duration-200 text-left w-full
              ${active
                ? `${card.border} ${card.bg} shadow-sm`
                : `${card.idleBorder} bg-bg-surface hover:${card.bg} hover:${card.border}`
              }`}
            title={`Filter by ${card.label}`}
          >
            {/* Active indicator dot */}
            {active && (
              <span className={`absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full ${card.barColor}`} />
            )}

            {/* Icon */}
            <div className={`flex items-center justify-center w-8 h-8 rounded-lg transition-colors
              ${active ? card.activeBg : "bg-bg-elevated group-hover:" + card.activeBg}
            `}>
              <Icon size={15} className={active ? card.color : `text-slate-500 group-hover:${card.color} transition-colors`} />
            </div>

            {/* Count */}
            <span className={`text-xl font-bold tabular-nums leading-none ${active ? card.color : "text-slate-300"}`}>
              {count}
            </span>

            {/* Label */}
            <span className={`text-[10px] font-medium leading-none ${active ? card.color : "text-slate-500"}`}>
              {card.label}
            </span>

            {/* Mini progress bar */}
            <div className="w-full h-0.5 rounded-full bg-bg-border overflow-hidden mt-0.5">
              <div
                className={`h-full rounded-full transition-all duration-500 ${card.barColor} ${active ? "opacity-100" : "opacity-40"}`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </button>
        );
      })}
    </div>
  );
}
