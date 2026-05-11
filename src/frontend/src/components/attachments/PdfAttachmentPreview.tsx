import { FileText } from "lucide-react";

type PdfAttachmentPreviewProps = {
  fileName: string;
  chunksIndexed?: number;
  status: "uploading" | "processing" | "ready";
};

export function PdfAttachmentPreview({ fileName, chunksIndexed, status }: PdfAttachmentPreviewProps) {
  const statusText =
    status === "uploading"
      ? "Uploading..."
      : status === "processing"
        ? "Processing PDF..."
        : "Ready for questions";

  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-700">
      <div className="flex items-center gap-2 font-medium">
        <FileText className="h-4 w-4 text-slate-600" />
        <span className="truncate">{fileName}</span>
      </div>
      <p className="mt-1 text-slate-500">{statusText}{status === "ready" && typeof chunksIndexed === "number" ? ` (${chunksIndexed} chunks indexed)` : ""}</p>
    </div>
  );
}
