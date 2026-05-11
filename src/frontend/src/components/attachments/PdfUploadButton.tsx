import { FileText, Upload } from "lucide-react";

type PdfUploadButtonProps = {
  disabled?: boolean;
  onClick: () => void;
};

export function PdfUploadButton({ disabled = false, onClick }: PdfUploadButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
    >
      <FileText className="h-4 w-4" />
      <span>Upload PDF</span>
      <Upload className="h-3.5 w-3.5" />
    </button>
  );
}
