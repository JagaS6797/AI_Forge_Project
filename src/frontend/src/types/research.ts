export interface ResearchPaper {
  title: string;
  authors: string[];
  published: string;
  summary: string;
  url: string;
}

export interface ResearchDigestDonePayload {
  topic: string;
  papers_found: number;
  digest: string;
  key_papers: ResearchPaper[];
  generated_at: string;
}

export type ResearchEventType =
  | "status"
  | "papers_found"
  | "selected_papers"
  | "papers_selected"
  | "digest_chunk"
  | "done"
  | "error";

export interface ResearchSseEvent {
  type: ResearchEventType;
  data: Record<string, unknown>;
}
