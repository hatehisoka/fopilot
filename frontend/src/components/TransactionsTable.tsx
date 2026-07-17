import { formatDate, formatMoney } from "../format";
import type { MatchStatus, Payment } from "../types";

const STATUS_LABELS: Record<MatchStatus, string> = {
  unmatched: "Не зіставлено",
  auto: "Авто",
  needs_review: "На підтвердження",
  confirmed: "Підтверджено",
  rejected: "Відхилено",
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
              {payments.map((p) => (
                <tr key={p.id}>
                  <td>{formatDate(p.paid_date)}</td>
                  <td>{p.source ?? "—"}</td>
                  <td className="num">{formatMoney(p.amount, p.currency)}</td>
                  <td className="num">
                    {p.amount_uah === null ? (
                      <span className="badge-warning">не сконвертовано</span>
                    ) : (
                      formatMoney(p.amount_uah)
                    )}
                  </td>
                  <td>{STATUS_LABELS[p.match_status]}</td>
                  <td>{p.is_revenue ? "Так" : "Ні"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
