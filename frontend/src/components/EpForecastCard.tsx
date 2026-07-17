import { PolarAngleAxis, RadialBar, RadialBarChart, ResponsiveContainer } from "recharts";

import { EP_GAUGE_THRESHOLDS } from "../config";
import { formatDate, formatMoney, formatPercent } from "../format";
import type { EpForecast } from "../types";
import { UnconvertedBadge } from "./UnconvertedBadge";

export function EpForecastCard({ forecast }: { forecast: EpForecast }) {
  const share = forecast.share_of_limit;
  const exceeded = share >= 1;
  const gaugeValue = Math.min(share, 1) * 100;

  const color =
    share > EP_GAUGE_THRESHOLDS.red
      ? "var(--color-danger)"
      : share >= EP_GAUGE_THRESHOLDS.amber
        ? "var(--color-warning)"
        : "var(--color-accent)";

  return (
    <section className="card ep-card">
      <header className="card-header">
        <h2>Прогрес до ліміту ЄП ({forecast.year})</h2>
        <UnconvertedBadge count={forecast.unconverted_count} />
      </header>

      <div className="ep-gauge">
        <ResponsiveContainer width="100%" height={180}>
          <RadialBarChart
            innerRadius="72%"
            outerRadius="100%"
            data={[{ value: gaugeValue, fill: color }]}
            startAngle={90}
            endAngle={-270}
          >
            <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
            <RadialBar
              dataKey="value"
              background={{ fill: "var(--color-surface-2)" }}
              cornerRadius={8}
            />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="gauge-center">{formatPercent(share)}</div>
      </div>

      <Headline forecast={forecast} exceeded={exceeded} />

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
    </section>
  );
}

function Headline({ forecast, exceeded }: { forecast: EpForecast; exceeded: boolean }) {
  if (forecast.insufficient_data) {
    return (
      <p className="ep-headline">
        <span className="ep-headline-value muted">Недостатньо даних для прогнозу</span>
      </p>
    );
  }
  if (exceeded) {
    return (
      <p className="ep-headline">
        <span className="ep-headline-value danger">Ліміт перевищено</span>
      </p>
    );
  }
  if (forecast.projected_exceed_date) {
    return (
      <p className="ep-headline">
        <span className="ep-headline-caption">Орієнтовна дата перевищення</span>
        <span className="ep-headline-value warning">
          {formatDate(forecast.projected_exceed_date)}
        </span>
      </p>
    );
  }
  return (
    <p className="ep-headline">
      <span className="ep-headline-value muted">Перевищення не прогнозується цьогоріч</span>
    </p>
  );
}
