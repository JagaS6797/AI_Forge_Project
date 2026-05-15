export type SqlQueryResult = {
  question: string;
  generated_sql: string;
  rows: Record<string, unknown>[];
  row_count: number;
  columns: string[];
  generated_at: string;
};
