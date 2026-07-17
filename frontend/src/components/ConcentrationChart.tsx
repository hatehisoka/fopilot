import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { formatMoney, formatPercent } from "../format";
import type { ConcentrationReport } from "../types";
import { UnconvertedBadge } from "./UnconvertedBadge";

const COLORS = ["#2f6feb", "#12a150", "#e8a33d", "#c4443c", "#7b53c1", "#3aa6b9"];

export function ConcentrationChart({ report }: { report: ConcentrationReport }) {
  const data = report.clients.map((c) => ({
    name: c.client_name,
    value: Number(c.amount_uah),
    share: c.share,
  }));

  return (
    <section className="card">
      <header className="card-header">
        <h2>Концентрація доходу по клієнтах</h2>
        <UnconvertedBadge count={report.unconverted_count} />
      </header>
      {data.length === 0 ? (
        <p className="empty">Немає даних</p>
      ) : (
        <>
          {report.top_client_share !== null && report.top_client_share >= 0.5 && (
            <p className="risk-note">
              Топ-клієнт: {formatPercent(report.top_client_share)} доходу — висока концентрація
            </p>
          )}
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80}>
                {data.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(v) => (typeof v === "number" ? formatMoney(v) : String(v))} />
              <Legend formatter={(_, __, i) => `${data[i].name} (${formatPercent(data[i].share)})`} />
            </PieChart>
          </ResponsiveContainer>
        </>
      )}
    </section>
  );
}
