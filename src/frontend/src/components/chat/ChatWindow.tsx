import { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { getThreadMessages, sendMessage } from "../../lib/api";
import type { ChatUiMessage } from "../../types";
import { InputBar } from "./InputBar";
import { MessageList } from "./MessageList";

type ChatWindowProps = {
  threadId: string;
  onThreadNamed?: (threadId: string, name: string) => void;
};

export function ChatWindow({ threadId, onThreadNamed }: ChatWindowProps) {
  const [messages, setMessages] = useState<ChatUiMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setMessages([]);
    setErrorMessage(null);
    setIsLoadingHistory(true);
    getThreadMessages(threadId)
      .then((history) => {
        if (!cancelled)
          setMessages(history.map((m) => ({ id: m.id, role: m.role, content: m.content })));
      })
      .catch(() => {})
      .finally(() => { if (!cancelled) setIsLoadingHistory(false); });
    return () => { cancelled = true; };
  }, [threadId]);

  const sendMutation = useMutation({
    mutationFn: async (text: string) => {
      const userMsgId = crypto.randomUUID();
      const assistantMsgId = crypto.randomUUID();
      setMessages((prev) => [
        ...prev,
        { id: userMsgId, role: "user", content: text },
        { id: assistantMsgId, role: "assistant", content: "" },
      ]);
      await sendMessage(
        text,
        threadId,
        (token) => setMessages((prev) =>
          prev.map((m) => m.id === assistantMsgId ? { ...m, content: m.content + token } : m)
        ),
        (name) => onThreadNamed?.(threadId, name),
      );
    },
    onError: (err: unknown) => {
      setErrorMessage(err instanceof Error ? err.message : "Unexpected error");
    },
  });

  const isSending = sendMutation.isPending;

  const submit = () => {
    const value = draft.trim();
    if (!value || isSending) return;
    setErrorMessage(null);
    setDraft("");
    sendMutation.mutate(value);
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
      <InputBar value={draft} isSending={isSending} onChange={setDraft} onSubmit={submit} />
    </div>
  );
}
