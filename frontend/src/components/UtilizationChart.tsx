import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { formatPercent, formatPeriodLabel } from "../format";
import type { MonthlyUtilization } from "../types";

export function UtilizationChart({ data }: { data: MonthlyUtilization[] }) {
  // Нульова ємність (напр. місяць без робочих днів) -> utilization === null -> "—".
  const points = data.map((d) => ({
    label: formatPeriodLabel(d.period),
    value: d.utilization === null ? null : Math.round(d.utilization * 1000) / 10,
  }));
  const hasAny = points.some((p) => p.value !== null && p.value > 0);

  return (
    <section className="card">
      <header className="card-header">
        <h2>Utilization по місяцях</h2>
      </header>
      {!hasAny ? (
        <p className="empty">Немає даних</p>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={points} margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="label" fontSize={12} />
            <YAxis
              domain={[0, 100]}
              tickFormatter={(v) => `${v}%`}
              width={48}
              fontSize={12}
            />
            <Tooltip
              formatter={(v) => (typeof v === "number" ? formatPercent(v / 100) : "—")}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#12a150"
              strokeWidth={2}
              connectNulls={false}
              name="Utilization"
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </section>
  );
}
