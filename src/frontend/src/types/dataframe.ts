export type DataFrameQueryResult = {
  question: string;
  answer: string;
  data_summary: string;
  source: "google_sheets" | "csv";
  row_count: number;
  column_names: string[];
  generated_at: string;
};
