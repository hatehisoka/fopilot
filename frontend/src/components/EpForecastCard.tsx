import { PolarAngleAxis, RadialBar, RadialBarChart, ResponsiveContainer } from "recharts";

import { formatDate, formatMoney, formatPercent } from "../format";
import type { EpForecast } from "../types";
import { UnconvertedBadge } from "./UnconvertedBadge";

export function EpForecastCard({ forecast }: { forecast: EpForecast }) {
  const share = forecast.share_of_limit;
  const exceeded = share >= 1;
  const gaugeValue = Math.min(share, 1) * 100;
  const color = exceeded ? "#c4443c" : share >= 0.8 ? "#e8a33d" : "#12a150";

  return (
    <section className="card">
      <header className="card-header">
        <h2>Прогрес до ліміту ЄП ({forecast.year})</h2>
        <UnconvertedBadge count={forecast.unconverted_count} />
      </header>

      <div className="gauge-wrap">
        <ResponsiveContainer width="100%" height={200}>
          <RadialBarChart
            innerRadius="70%"
            outerRadius="100%"
            data={[{ value: gaugeValue, fill: color }]}
            startAngle={90}
            endAngle={-270}
          >
            <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
            <RadialBar dataKey="value" background cornerRadius={8} />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="gauge-center">{formatPercent(share)}</div>
      </div>

      <dl className="ep-facts">
        <div>
          <dt>Отримано</dt>
          <dd>{formatMoney(forecast.received_uah)}</dd>
        </div>
        <div>
          <dt>Ліміт</dt>
          <dd>{formatMoney(forecast.limit)}</dd>
        </div>
      </dl>

      <p className={`ep-status ${exceeded ? "danger" : ""}`}>{statusText(forecast, exceeded)}</p>
    </section>
  );
}

function statusText(forecast: EpForecast, exceeded: boolean): string {
  if (forecast.insufficient_data) {
    return "Недостатньо даних для прогнозу";
  }
  if (exceeded) {
    return "Ліміт перевищено";
  }
  if (forecast.projected_exceed_date) {
    return `Орієнтовна дата перевищення: ${formatDate(forecast.projected_exceed_date)}`;
  }
  return "У межах ліміту — перевищення не прогнозується цьогоріч";
}
