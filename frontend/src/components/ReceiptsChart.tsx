import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { AXIS_TICK, BAR_RADIUS, GRID_STROKE, SERIES_ACCENT } from "../chartTheme";
import { formatMoney, formatNumber, formatPeriodLabel } from "../format";
import type { ReceiptsReport } from "../types";
import { ChartTooltip } from "./ChartTooltip";
import { UnconvertedBadge } from "./UnconvertedBadge";

export function ReceiptsChart({ report }: { report: ReceiptsReport }) {
  const data = report.periods.map((p) => ({
    label: formatPeriodLabel(p.period),
    amount: Number(p.amount_uah),
  }));

  return (
    <section className="card">
      <header className="card-header">
        <h2>Надходження по місяцях</h2>
        <UnconvertedBadge count={report.unconverted_count} />
      </header>
      {data.length === 0 ? (
        <p className="empty">Немає даних</p>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
            <CartesianGrid stroke={GRID_STROKE} vertical={false} />
            <XAxis dataKey="label" tick={AXIS_TICK} axisLine={false} tickLine={false} />
            <YAxis
              tickFormatter={(v) => formatNumber(v)}
              tick={AXIS_TICK}
              axisLine={false}
              tickLine={false}
              width={72}
            />
            <Tooltip
              cursor={{ fill: "var(--color-bg)" }}
              content={<ChartTooltip valueFormatter={(v) => formatMoney(v)} />}
            />
            <Bar dataKey="amount" fill={SERIES_ACCENT} radius={[BAR_RADIUS, BAR_RADIUS, 0, 0]} name="Надходження" />
          </BarChart>
        </ResponsiveContainer>
      )}
    </section>
  );
}
