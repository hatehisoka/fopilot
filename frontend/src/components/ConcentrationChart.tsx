import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { CATEGORICAL } from "../chartTheme";
import { formatMoney, formatPercent } from "../format";
import type { ConcentrationReport } from "../types";
import { ChartTooltip } from "./ChartTooltip";
import { UnconvertedBadge } from "./UnconvertedBadge";

export function ConcentrationChart({ report }: { report: ConcentrationReport }) {
  const data = report.clients.map((c, i) => ({
    name: c.client_name,
    value: Number(c.amount_uah),
    share: c.share,
    color: CATEGORICAL[i % CATEGORICAL.length],
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
          <div className="concentration-body">
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={data}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={54}
                  outerRadius={90}
                  paddingAngle={1}
                  stroke="none"
                >
                  {data.map((d) => (
                    <Cell key={d.name} fill={d.color} />
                  ))}
                </Pie>
                <Tooltip content={<ChartTooltip valueFormatter={(v) => formatMoney(v)} />} />
              </PieChart>
            </ResponsiveContainer>
            <ul className="pie-legend">
              {data.map((d) => (
                <li key={d.name}>
                  <span className="swatch" style={{ background: d.color }} />
                  <span className="pie-legend-name">{d.name}</span>
                  <span className="pie-legend-pct num">{formatPercent(d.share)}</span>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </section>
  );
}
