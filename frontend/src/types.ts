// Дзеркало Pydantic-схем бекенду. Грошові поля приходять рядками (Decimal -> str).

export interface PeriodAmount {
  period: string;
  amount_uah: string;
}

export interface ReceiptsReport {
  granularity: string;
  year: number;
  periods: PeriodAmount[];
  total_uah: string;
  unconverted_count: number;
}

export interface ProjectUtilization {
  project_id: number;
  project_name: string;
  billable_hours: string;
  utilization: number | null;
}

export interface UtilizationReport {
  date_from: string;
  date_to: string;
  working_days: number;
  work_hours_per_day: number;
  capacity_hours: string;
  total_billable_hours: string;
  overall_utilization: number | null;
  projects: ProjectUtilization[];
}

export interface ClientShare {
  client_id: number;
  client_name: string;
  amount_uah: string;
  share: number;
}

export interface ConcentrationReport {
  year: number;
  total_attributed_uah: string;
  top_client_share: number | null;
  clients: ClientShare[];
  unattributed_uah: string;
  unconverted_count: number;
}

export interface EpForecast {
  year: number;
  limit: string;
  received_uah: string;
  as_of: string;
  days_elapsed: number;
  days_in_year: number;
  share_of_limit: number;
  run_rate_per_day: string | null;
  projected_annual: string | null;
  projected_exceed_date: string | null;
  insufficient_data: boolean;
  unconverted_count: number;
}

export type MatchStatus =
  | "unmatched"
  | "auto"
  | "needs_review"
  | "confirmed"
  | "rejected";

export interface Payment {
  id: number;
  invoice_id: number | null;
  bank_transaction_id: number | null;
  paid_date: string;
  amount: string;
  currency: string;
  amount_uah: string | null;
  source: string | null;
  match_status: MatchStatus;
  is_revenue: boolean;
}

export interface MonthlyUtilization {
  period: string;
  utilization: number | null;
}
