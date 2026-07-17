// Локалізація через Intl (uk-UA): нерозривний пробіл у тисячах, кома в десяткових,
// dd.MM.yyyy для дат, ₴ для гривні. Жодних власних форматерів на регулярках.

const dateFmt = new Intl.DateTimeFormat("uk-UA", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

const numberFmt = new Intl.NumberFormat("uk-UA", { maximumFractionDigits: 2 });

const percentFmt = new Intl.NumberFormat("uk-UA", {
  style: "percent",
  maximumFractionDigits: 1,
});

function toNumber(value: string | number): number {
  return typeof value === "string" ? Number(value) : value;
}

export function formatDate(iso: string): string {
  return dateFmt.format(new Date(iso));
}

export function formatNumber(value: string | number): string {
  return numberFmt.format(toNumber(value));
}

export function formatMoney(value: string | number, currency = "UAH"): string {
  return new Intl.NumberFormat("uk-UA", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(toNumber(value));
}

export function formatPercent(ratio: number): string {
  return percentFmt.format(ratio);
}

// "2026-03" -> "Бер", "2026-Q1" -> "I кв." для підписів осей.
const MONTHS = ["Січ", "Лют", "Бер", "Кві", "Тра", "Чер", "Лип", "Сер", "Вер", "Жов", "Лис", "Гру"];

export function formatPeriodLabel(period: string): string {
  const [, tail] = period.split("-");
  if (tail?.startsWith("Q")) {
    return `${tail.replace("Q", "")} кв.`;
  }
  const month = Number(tail);
  return MONTHS[month - 1] ?? period;
}
