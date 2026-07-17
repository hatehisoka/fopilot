// Усі запити йдуть на /api, який Vite прокидає на бекенд (див. vite.config.ts).
// Так браузер завжди звертається до свого origin — CORS не потрібен.

import type {
  ConcentrationReport,
  EpForecast,
  MonthlyUtilization,
  Payment,
  ReceiptsReport,
  UtilizationReport,
} from "./types";

const BASE = "/api";

async function get<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`);
  } catch {
    throw new Error("Немає зв'язку з сервером. Перевірте, що бекенд запущено.");
  }
  if (!response.ok) {
    throw new Error(`Помилка запиту (${response.status})`);
  }
  return response.json() as Promise<T>;
}

function lastDayOfMonth(year: number, month: number): string {
  const d = new Date(year, month, 0); // day 0 -> last day of 1-based month
  return `${year}-${String(month).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

export const api = {
  receipts: (year?: number) =>
    get<ReceiptsReport>(`/analytics/receipts?granularity=month${year ? `&year=${year}` : ""}`),

  concentration: (year?: number) =>
    get<ConcentrationReport>(`/analytics/concentration${year ? `?year=${year}` : ""}`),

  epForecast: () => get<EpForecast>("/analytics/ep-forecast"),

  payments: (limit = 10) => get<Payment[]>(`/payments?limit=${limit}`),

  // Utilization по місяцях: окремий запит на кожен місяць року до поточного.
  async utilizationByMonth(year: number, upToMonth: number): Promise<MonthlyUtilization[]> {
    const today = todayIso();
    const months = Array.from({ length: upToMonth }, (_, i) => i + 1);
    return Promise.all(
      months.map(async (m) => {
        const from = `${year}-${String(m).padStart(2, "0")}-01`;
        const monthEnd = lastDayOfMonth(year, m);
        const to = m === upToMonth && monthEnd > today ? today : monthEnd;
        const report = await get<UtilizationReport>(
          `/analytics/utilization?date_from=${from}&date_to=${to}`,
        );
        return {
          period: `${year}-${String(m).padStart(2, "0")}`,
          utilization: report.overall_utilization,
        };
      }),
    );
  },
};
