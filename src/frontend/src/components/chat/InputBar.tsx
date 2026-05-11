import { useEffect, useRef, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import { Plus, X, Image, Video, Code, File, Upload, MessageSquare, Sparkles } from "lucide-react";
import { PdfAttachmentPreview } from "../attachments/PdfAttachmentPreview";

interface UploadedAttachment {
  id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  created_at: string;
}

type InputBarProps = {
  value: string;
  isSending: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
  mode: "normal" | "upload" | "upload_pdf_rag" | "generate_image";
  onModeChange: (mode: "normal" | "upload" | "upload_pdf_rag" | "generate_image") => void;
  uploadedAttachments?: UploadedAttachment[];
  onRemoveAttachment?: (id: string) => void;
  isUploading?: boolean;
  hasRagDocument?: boolean;
  ragEnabled?: boolean;
  onRagToggle?: (enabled: boolean) => void;
};

const getFileIcon = (fileType: string) => {
  if (fileType.startsWith("image/")) return <Image className="h-3.5 w-3.5" />;
  if (fileType.startsWith("video/")) return <Video className="h-3.5 w-3.5" />;
  if (
    fileType.includes("javascript") ||
    fileType.includes("typescript") ||
    fileType.includes("python") ||
    fileType.includes("code")
  ) return <Code className="h-3.5 w-3.5" />;
  return <File className="h-3.5 w-3.5" />;
};

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
};

export function InputBar({ 
  value, 
  isSending, 
  onChange, 
  onSubmit,
  mode,
  onModeChange,
  uploadedAttachments = [],
  onRemoveAttachment,
  isUploading = false,
  hasRagDocument = false,
  ragEnabled = false,
  onRagToggle,
}: InputBarProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onSubmit();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  const handlePlusClick = () => {
    setIsMenuOpen((prev) => !prev);
  };

  useEffect(() => {
    const onOutsideClick = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    };

    document.addEventListener("mousedown", onOutsideClick);
    return () => document.removeEventListener("mousedown", onOutsideClick);
  }, []);

  const selectMode = (nextMode: "normal" | "upload" | "upload_pdf_rag" | "generate_image") => {
    onModeChange(nextMode);
    setIsMenuOpen(false);

    if (nextMode === "upload" || nextMode === "upload_pdf_rag") {
      fileInputRef.current?.click();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.currentTarget.files;
    if (files) {
      // Trigger the upload through a custom event
      const event = new CustomEvent('filesSelected', {
        detail: {
          files: Array.from(files),
          mode,
        },
      });
      document.dispatchEvent(event);
    }
    // Reset input so same file can be selected again
    e.currentTarget.value = '';
  };

  return (
    <div className="border-t border-slate-200 bg-white px-4 py-3 space-y-3">
      {/* PDF Attachment with RAG toggle */}
      {uploadedAttachments.length > 0 && (
        <div className="space-y-2">
          {uploadedAttachments
            .filter(att => att.file_type === "application/pdf" || att.file_name.endsWith(".pdf"))
            .map((att) => (
              <div key={att.id} className="flex items-center gap-2">
                <PdfAttachmentPreview
                  fileName={att.file_name}
                  chunksIndexed={undefined}
                  status="ready"
                />
                <button
                  onClick={() => onRemoveAttachment?.(att.id)}
                  className="p-1.5 text-slate-500 hover:text-slate-700 transition"
                  title="Remove attachment"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          {/* Other attachments */}
          {uploadedAttachments
            .filter(att => !(att.file_type === "application/pdf" || att.file_name.endsWith(".pdf")))
            .length > 0 && (
            <div className="flex flex-wrap gap-2">
              {uploadedAttachments
                .filter(att => !(att.file_type === "application/pdf" || att.file_name.endsWith(".pdf")))
                .map((att) => (
                  <div
                    key={att.id}
                    className="flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1.5 text-xs border border-slate-200 hover:border-slate-300 transition"
                  >
                    <div className="text-slate-600">
                      {getFileIcon(att.file_type)}
                    </div>
                    <span className="truncate max-w-[100px] text-slate-700 font-medium">
                      {att.file_name}
                    </span>
                    <span className="text-slate-500 text-xs">
                      {formatFileSize(att.file_size)}
                    </span>
                    <button
                      onClick={() => onRemoveAttachment?.(att.id)}
                      className="ml-1 text-slate-500 hover:text-slate-700 transition"
                      title="Remove attachment"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
            </div>
          )}
        </div>
      )}

      <form className="flex items-end gap-2" onSubmit={handleSubmit}>
        <div className="relative" ref={menuRef}>
          <button
            type="button"
            onClick={handlePlusClick}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition disabled:cursor-not-allowed disabled:opacity-50"
            disabled={isSending || isUploading}
            title="Select chat mode"
          >
            <Plus className="h-5 w-5" />
          </button>

          {isMenuOpen && (
            <div className="absolute bottom-12 left-0 z-20 w-52 rounded-xl border border-slate-200 bg-white p-2 shadow-lg">
              <button
                type="button"
                onClick={() => selectMode("normal")}
                className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-slate-100"
              >
                <span className="flex items-center gap-2"><MessageSquare className="h-4 w-4" />Normal Chat</span>
                {mode === "normal" ? <span>✓</span> : null}
              </button>
              <button
                type="button"
                onClick={() => selectMode("upload")}
                className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-slate-100"
              >
                <span className="flex items-center gap-2"><Upload className="h-4 w-4" />Upload Files</span>
                {mode === "upload" ? <span>✓</span> : null}
              </button>
              <button
                type="button"
                onClick={() => selectMode("upload_pdf_rag")}
                className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-slate-100"
              >
                <span className="flex items-center gap-2"><File className="h-4 w-4" />Upload PDF (RAG)</span>
                <span className="flex items-center gap-2">
                  {mode === "upload_pdf_rag" ? <span>✓</span> : null}
                  <button
                    type="button"
                    onClick={(event) => {
                      event.stopPropagation();
                      if (!hasRagDocument) {
                        return;
                      }
                      onRagToggle?.(!ragEnabled);
                    }}
                    className={`relative inline-flex h-5 w-9 items-center rounded-full transition ${
                      ragEnabled && hasRagDocument ? "bg-emerald-500" : "bg-slate-300"
                    } ${hasRagDocument ? "cursor-pointer" : "cursor-not-allowed opacity-50"}`}
                    aria-pressed={ragEnabled}
                    aria-label="Toggle RAG"
                    title={hasRagDocument ? (ragEnabled ? "RAG enabled" : "RAG disabled") : "Upload a PDF to enable RAG"}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                        ragEnabled && hasRagDocument ? "translate-x-4" : "translate-x-0.5"
                      }`}
                    />
                  </button>
                </span>
              </button>
              <button
                type="button"
                onClick={() => selectMode("generate_image")}
                className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-slate-100"
              >
                <span className="flex items-center gap-2"><Sparkles className="h-4 w-4" />Generate Image</span>
                {mode === "generate_image" ? <span>✓</span> : null}
              </button>
            </div>
          )}
        </div>

        <input
          ref={fileInputRef}
          type="file"
          multiple={mode !== "upload_pdf_rag"}
          accept={
            mode === "upload_pdf_rag"
              ? ".pdf,application/pdf"
              : "image/*,video/mp4,video/webm,video/quicktime,text/*,.pdf,.csv,.xlsx,.ts,.tsx,.js,.jsx,.py,.java,.cpp,.c,.go,.rb,.php,.html,.css,.md"
          }
          className="hidden"
          onChange={handleFileChange}
          disabled={isSending || isUploading}
        />

        <textarea
          rows={1}
          className="flex-1 resize-none rounded-lg border border-slate-300 px-4 py-2.5 text-sm outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 max-h-32"
          placeholder={
            mode === "generate_image"
              ? "Describe the image to generate..."
              : mode === "upload_pdf_rag"
                ? "Ask questions about the uploaded PDF..."
                : "Type a message or use /image <prompt> to generate an image"
          }
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isSending || isUploading}
        />

        <button
          type="submit"
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-indigo-600 text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={isSending || isUploading || (value.trim().length === 0 && uploadedAttachments.length === 0)}
          title="Send message"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
            <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
          </svg>
        </button>
      </form>

      {isSending && (
        <p className="text-xs text-slate-400">AI is analyzing your message…</p>
      )}
      {isUploading && (
        <p className="text-xs text-slate-400">Uploading files…</p>
      )}
    </div>
  );
}
