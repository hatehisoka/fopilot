import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { AXIS_TICK, GRID_STROKE, SERIES_LINE } from "../chartTheme";
import { formatPercent, formatPeriodLabel } from "../format";
import type { MonthlyUtilization } from "../types";
import { ChartTooltip } from "./ChartTooltip";

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
        <h2>Завантаженість по місяцях</h2>
      </header>
      {!hasAny ? (
        <p className="empty">Немає даних</p>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={points} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
            <CartesianGrid stroke={GRID_STROKE} vertical={false} />
            <XAxis dataKey="label" tick={AXIS_TICK} axisLine={false} tickLine={false} />
            <YAxis
              domain={[0, 100]}
              tickFormatter={(v) => `${v}%`}
              tick={AXIS_TICK}
              axisLine={false}
              tickLine={false}
              width={44}
            />
            <Tooltip
              cursor={{ stroke: "var(--color-border)" }}
              content={<ChartTooltip valueFormatter={(v) => formatPercent(v / 100)} />}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={SERIES_LINE}
              strokeWidth={2}
              dot={{ r: 3, fill: SERIES_LINE }}
              connectNulls={false}
              name="Завантаженість"
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </section>
  );
}
