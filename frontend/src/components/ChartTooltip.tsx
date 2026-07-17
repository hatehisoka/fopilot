// Кастомний тултіп у стилі карток; форматування значень — через format.ts.
// active/payload/label інжектить Recharts, valueFormatter передаємо ми.

interface TooltipEntry {
  value: number | string;
  name?: string;
}

interface ChartTooltipProps {
  active?: boolean;
  payload?: TooltipEntry[];
  label?: string;
  valueFormatter: (value: number) => string;
}

export function ChartTooltip({ active, payload, label, valueFormatter }: ChartTooltipProps) {
  if (!active || !payload || payload.length === 0) {
    return null;
  }
  return (
    <div className="chart-tooltip">
      {label && <div className="chart-tooltip-label">{label}</div>}
      {payload.map((entry, i) => (
        <div className="chart-tooltip-row" key={i}>
          {entry.name && <span className="chart-tooltip-name">{entry.name}</span>}
          <span className="chart-tooltip-value">
            {typeof entry.value === "number" ? valueFormatter(entry.value) : String(entry.value)}
          </span>
        </div>
      ))}
    </div>
  );
}
