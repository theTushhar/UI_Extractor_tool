import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";
import type { ExtractedElement } from "../types";

interface Props {
  elements: ExtractedElement[];
}

const TYPE_COLORS = [
  "#6366f1", "#06b6d4", "#10b981", "#f59e0b", "#ef4444",
  "#8b5cf6", "#f97316", "#84cc16", "#ec4899", "#14b8a6",
];

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  const d = payload[0];
  return (
    <div className="px-3 py-2 rounded-xl border border-bg-border bg-bg-elevated shadow-xl text-sm">
      <p className="font-semibold text-slate-200">{d.name}</p>
      <p className="text-slate-400">
        <span style={{ color: d.payload.fill }} className="font-bold">{d.value}</span>
        {" "}elements
      </p>
    </div>
  );
};

const CustomLegend = ({ payload }: any) => (
  <div className="flex flex-wrap justify-center gap-x-4 gap-y-1.5 mt-2">
    {payload?.map((entry: any) => (
      <div key={entry.value} className="flex items-center gap-1.5 text-xs text-slate-400">
        <span
          className="w-2.5 h-2.5 rounded-full flex-shrink-0"
          style={{ background: entry.color }}
        />
        {entry.value}
      </div>
    ))}
  </div>
);

export function DistributionChart({ elements }: Props) {
  // Aggregate by element_type
  const countMap: Record<string, number> = {};
  for (const el of elements) {
    countMap[el.element_type] = (countMap[el.element_type] ?? 0) + 1;
  }
  const data = Object.entries(countMap)
    .sort((a, b) => b[1] - a[1])
    .map(([name, value], i) => ({ name, value, fill: TYPE_COLORS[i % TYPE_COLORS.length] }));

  if (data.length === 0) return null;

  return (
    <div className="rounded-xl border border-bg-border bg-bg-surface p-3" style={{ boxShadow: "0 2px 16px rgba(0,0,0,0.3)" }}>
      <h3 className="text-[10px] font-semibold uppercase tracking-widest text-slate-500 mb-1">
        Element Distribution
      </h3>
      <ResponsiveContainer width="100%" height={155}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={38}
            outerRadius={58}
            paddingAngle={3}
            dataKey="value"
            strokeWidth={0}
            animationBegin={0}
            animationDuration={700}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} opacity={0.9} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend content={<CustomLegend />} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
