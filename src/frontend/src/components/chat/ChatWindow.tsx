import { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { getThreadMessages, sendMessage } from "../../lib/api";
import type { ChatUiMessage } from "../../types";
import { useAttachments } from "../../hooks/useAttachments";
import { InputBar } from "./InputBar";
import { MessageList } from "./MessageList";

type ChatWindowProps = {
  threadId: string;
  onThreadNamed?: (threadId: string, name: string) => void;
};

export function ChatWindow({ threadId, onThreadNamed }: ChatWindowProps) {
  const [messages, setMessages] = useState<ChatUiMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [mode, setMode] = useState<"normal" | "upload" | "upload_pdf_rag" | "generate_image">("normal");
  const [hasRagDocument, setHasRagDocument] = useState(false);
  const [ragEnabled, setRagEnabled] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  
  const {
    uploadedAttachments,
    isUploading,
    uploadError,
    pdfStatus,
    removeAttachment,
    uploadFiles,
    getAttachmentIds,
    clearAttachments,
  } = useAttachments();

  // Listen for file selection from InputBar
  useEffect(() => {
    const handleFilesSelected = (event: Event) => {
      const customEvent = event as CustomEvent<{ files: File[]; mode: "normal" | "upload" | "upload_pdf_rag" | "generate_image" }>;
      const files = customEvent.detail?.files ?? [];
      const selectedMode = customEvent.detail?.mode ?? mode;
      uploadFiles(files, { mode: selectedMode, threadId });
      if (selectedMode === "upload_pdf_rag") {
        setHasRagDocument(true);
        setRagEnabled(true);
      }
    };

    document.addEventListener('filesSelected', handleFilesSelected);
    return () => document.removeEventListener('filesSelected', handleFilesSelected);
  }, [mode, threadId, uploadFiles]);

  // Listen for RAG fallback signal from backend
  useEffect(() => {
    const handleRagFallback = () => {
      setRagEnabled(false);
    };

    document.addEventListener('ragFallback', handleRagFallback);
    return () => document.removeEventListener('ragFallback', handleRagFallback);
  }, []);

  useEffect(() => {
    let cancelled = false;
    setMessages([]);
    setErrorMessage(null);
    setIsLoadingHistory(true);
    setHasRagDocument(false);
    setRagEnabled(false);
    getThreadMessages(threadId)
      .then((history) => {
        if (!cancelled) {
          setMessages(history.map((m: any) => ({ 
            id: m.id, 
            role: m.role, 
            content: m.content,
            attachment_ids: m.attachment_ids || [],
            attachments: m.attachments || [],
          })));
          const threadHasPdf = history.some((m: any) =>
            Array.isArray(m.attachments) &&
            m.attachments.some((attachment: any) => attachment.attachment_type === "pdf"),
          );
          setHasRagDocument(threadHasPdf);
          setRagEnabled(threadHasPdf);
        }
      })
      .catch(() => {})
      .finally(() => { if (!cancelled) setIsLoadingHistory(false); });
    return () => { cancelled = true; };
  }, [threadId]);

  useEffect(() => {
    if (pdfStatus === "ready") {
      setHasRagDocument(true);
      setRagEnabled(true);
    }
  }, [pdfStatus]);

  const sendMutation = useMutation({
    mutationFn: async (text: string) => {
      const userMsgId = crypto.randomUUID();
      const assistantMsgId = crypto.randomUUID();
      const attachmentIds = getAttachmentIds();
      
      setMessages((prev) => [
        ...prev,
        { id: userMsgId, role: "user", content: text, attachment_ids: attachmentIds, attachments: uploadedAttachments },
        { id: assistantMsgId, role: "assistant", content: "", attachment_ids: [], attachments: [] },
      ]);
      
      const outgoingText =
        mode === "generate_image" && text.trim() && !text.trim().startsWith("/image")
          ? `/image ${text.trim()}`
          : text;

      await sendMessage(
        outgoingText,
        threadId,
        attachmentIds,
        ragEnabled && hasRagDocument,
        (token) => setMessages((prev) =>
          prev.map((m) => m.id === assistantMsgId ? { ...m, content: m.content + token } : m)
        ),
        (name) => onThreadNamed?.(threadId, name),
        (attachment) =>
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId
                ? {
                    ...m,
                    attachment_ids: [...(m.attachment_ids ?? []), attachment.id],
                    attachments: [...(m.attachments ?? []), attachment],
                  }
                : m,
            ),
          ),
      );
    },
    onError: (err: unknown) => {
      setErrorMessage(err instanceof Error ? err.message : "Unexpected error");
    },
    onSuccess: () => {
      clearAttachments();
      if (mode === "upload" || mode === "upload_pdf_rag") {
        setMode("normal");
      }
    },
  });

  const isSending = sendMutation.isPending;

  const submit = () => {
    const value = draft.trim();
    if ((!value && uploadedAttachments.length === 0) || isSending) return;
    setErrorMessage(null);
    setDraft("");
    sendMutation.mutate(value || "");
  };

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {isLoadingHistory ? (
        <div className="flex flex-1 items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
        </div>
      ) : (
        <MessageList messages={messages} isStreaming={isSending} />
      )}
      {errorMessage && (
        <p className="border-t border-red-100 bg-red-50 px-4 py-2 text-xs text-red-500">{errorMessage}</p>
      )}
      {uploadError && (
        <p className="border-t border-red-100 bg-red-50 px-4 py-2 text-xs text-red-500">{uploadError}</p>
      )}
      {pdfStatus === "uploading" && (
        <p className="border-t border-amber-100 bg-amber-50 px-4 py-2 text-xs text-amber-700">Uploading...</p>
      )}
      {pdfStatus === "processing" && (
        <p className="border-t border-amber-100 bg-amber-50 px-4 py-2 text-xs text-amber-700">Processing PDF...</p>
      )}
      {pdfStatus === "ready" && (
        <p className="border-t border-emerald-100 bg-emerald-50 px-4 py-2 text-xs text-emerald-700">Ready for questions</p>
      )}
      <InputBar 
        value={draft} 
        isSending={isSending} 
        onChange={setDraft} 
        onSubmit={submit}
        mode={mode}
        onModeChange={setMode}
        uploadedAttachments={uploadedAttachments}
        onRemoveAttachment={removeAttachment}
        isUploading={isUploading}
        hasRagDocument={hasRagDocument}
        ragEnabled={ragEnabled}
        onRagToggle={setRagEnabled}
      />
    </div>
  );
}
