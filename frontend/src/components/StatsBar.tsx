import { Layers, Shield, MousePointerClick } from "lucide-react";

interface Props {
  total: number;
  stable: number;
  actionElements: number;
}

const statConfig = [
  {
    key: "total",
    label: "Total Elements",
    icon: Layers,
    color: "from-primary/20 to-primary/5",
    iconBg: "bg-primary/15",
    iconColor: "text-primary-light",
    borderColor: "border-primary/20",
    valueColor: "text-white",
  },
  {
    key: "stable",
    label: "Stable Locators",
    icon: Shield,
    color: "from-mode-input/20 to-mode-input/5",
    iconBg: "bg-mode-input/15",
    iconColor: "text-mode-input",
    borderColor: "border-mode-input/20",
    valueColor: "text-mode-input",
  },
  {
    key: "action",
    label: "Action Elements",
    icon: MousePointerClick,
    color: "from-accent/20 to-accent/5",
    iconBg: "bg-accent/15",
    iconColor: "text-accent",
    borderColor: "border-accent/20",
    valueColor: "text-accent",
  },
] as const;

export function StatsBar({ total, stable, actionElements }: Props) {
  const values = { total, stable, action: actionElements };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      {statConfig.map((s) => {
        const Icon = s.icon;
        const val = values[s.key as keyof typeof values];
        const pct = total > 0 ? Math.round((val / total) * 100) : 0;

        return (
          <div
            key={s.key}
            className={`relative overflow-hidden rounded-xl border ${s.borderColor} bg-bg-surface animate-fade-in`}
            style={{ boxShadow: "0 4px 24px rgba(0,0,0,0.3)" }}
          >
            {/* Gradient bg */}
            <div className={`absolute inset-0 bg-gradient-to-br ${s.color} pointer-events-none`} />

            <div className="relative p-3 flex items-center gap-3">
              <div className={`flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-lg ${s.iconBg}`}>
                <Icon size={18} className={s.iconColor} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-[10px] font-medium text-slate-400 uppercase tracking-widest mb-0.5">
                  {s.label}
                </p>
                <div className="flex items-baseline gap-2">
                  <span className={`text-2xl font-bold ${s.valueColor} tabular-nums`}>{val}</span>
                  {s.key !== "total" && (
                    <span className="text-xs text-slate-500 font-medium">{pct}%</span>
                  )}
                </div>
                {/* Mini progress bar */}
                {s.key !== "total" && (
                  <div className="mt-2 h-1 rounded-full bg-bg-border overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${
                        s.key === "stable" ? "bg-mode-input" : "bg-accent"
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
