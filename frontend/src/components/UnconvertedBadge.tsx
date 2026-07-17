// Помітний попереджувальний бейдж про несконвертовані платежі (ADR-017):
// дірка в даних має бути видимою, а не захованою в JSON.

export function UnconvertedBadge({ count }: { count: number }) {
  if (count <= 0) {
    return null;
  }
  return (
    <span
      className="badge-warning"
      title="Ці платежі не враховані в сумі, бо курс НБУ ще не сконвертовано"
    >
      ⚠ {count} не сконвертовано
    </span>
  );
}
