import { formatDate, formatMoney } from "../format";
import type { MatchStatus, Payment } from "../types";

const STATUS_META: Record<MatchStatus, { label: string; variant: string }> = {
  unmatched: { label: "Не зіставлено", variant: "neutral" },
  auto: { label: "Авто", variant: "success" },
  needs_review: { label: "На підтвердження", variant: "warning" },
  confirmed: { label: "Підтверджено", variant: "success" },
  rejected: { label: "Відхилено", variant: "neutral" },
};

export function TransactionsTable({ payments }: { payments: Payment[] }) {
  return (
    <section className="card wide">
      <header className="card-header">
        <h2>Останні надходження</h2>
      </header>
      {payments.length === 0 ? (
        <p className="empty">Немає даних</p>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Дата</th>
                <th>Джерело</th>
                <th className="num">Сума</th>
                <th className="num">У грн</th>
                <th>Статус</th>
                <th>Дохід</th>
              </tr>
            </thead>
            <tbody>
              {payments.map((p) => {
                const status = STATUS_META[p.match_status];
                return (
                  <tr key={p.id}>
                    <td>{formatDate(p.paid_date)}</td>
                    <td>{p.source ?? "—"}</td>
                    <td className="num">{formatMoney(p.amount, p.currency)}</td>
                    <td className="num">
                      {p.amount_uah === null ? (
                        <span className="badge badge-warning">не сконвертовано</span>
                      ) : (
                        formatMoney(p.amount_uah)
                      )}
                    </td>
                    <td>
                      <span className={`badge badge-${status.variant}`}>{status.label}</span>
                    </td>
                    <td>
                      <span className={`badge badge-${p.is_revenue ? "success" : "neutral"}`}>
                        {p.is_revenue ? "Так" : "Ні"}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
