import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { formatMoney, formatNumber, formatPeriodLabel } from "../format";
import type { ReceiptsReport } from "../types";
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
          <BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="label" fontSize={12} />
            <YAxis tickFormatter={(v) => formatNumber(v)} width={72} fontSize={12} />
            <Tooltip formatter={(v) => (typeof v === "number" ? formatMoney(v) : String(v))} />
            <Bar dataKey="amount" fill="#2f6feb" radius={[4, 4, 0, 0]} name="Надходження" />
          </BarChart>
        </ResponsiveContainer>
      )}
    </section>
  );
}
