import type { AttachmentMetadata } from "./attachment";

export type PdfUploadResponse = {
  attachment: AttachmentMetadata;
  chunks_indexed: number;
  status: "ready";
};

export type PdfProcessingStatus = "idle" | "uploading" | "processing" | "ready" | "error";
