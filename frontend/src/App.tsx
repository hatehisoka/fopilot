import { useEffect, useState } from "react";

import { api } from "./api";
import { ConcentrationChart } from "./components/ConcentrationChart";
import { EpForecastCard } from "./components/EpForecastCard";
import { ReceiptsChart } from "./components/ReceiptsChart";
import { TransactionsTable } from "./components/TransactionsTable";
import { UtilizationChart } from "./components/UtilizationChart";
import type {
  ConcentrationReport,
  EpForecast,
  MonthlyUtilization,
  Payment,
  ReceiptsReport,
} from "./types";

interface DashboardData {
  receipts: ReceiptsReport;
  utilization: MonthlyUtilization[];
  concentration: ConcentrationReport;
  ep: EpForecast;
  payments: Payment[];
}

export function App() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth() + 1;

    Promise.all([
      api.receipts(year),
      api.utilizationByMonth(year, month),
      api.concentration(year),
      api.epForecast(),
      api.payments(10),
    ])
      .then(([receipts, utilization, concentration, ep, payments]) =>
        setData({ receipts, utilization, concentration, ep, payments }),
      )
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="state">Завантаження…</div>;
  }
  if (error) {
    return (
      <div className="state error">
        <p>Не вдалося завантажити дані.</p>
        <p className="state-detail">{error}</p>
      </div>
    );
  }
  if (!data) {
    return null;
  }

  return (
    <main className="page">
      <header className="page-header">
        <h1>FOPilot</h1>
        <p>Облік і фінансова аналітика ФОП · КВЕД 62.01</p>
      </header>

      <div className="dashboard">
        <ReceiptsChart report={data.receipts} />
        <UtilizationChart data={data.utilization} />
        <ConcentrationChart report={data.concentration} />
        <EpForecastCard forecast={data.ep} />
      </div>

      <TransactionsTable payments={data.payments} />
    </main>
  );
}
