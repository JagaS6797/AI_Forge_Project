import { useEffect, useRef } from "react";
import type { ChatUiMessage } from "../../types";

type MessageListProps = {
  messages: ChatUiMessage[];
  isStreaming?: boolean;
};

export function MessageList({ messages, isStreaming = false }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
      {messages.length === 0 ? (
        <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-100 text-2xl">💬</div>
          <p className="text-base font-medium text-slate-700">How can I help you today?</p>
          <p className="text-sm text-slate-400">Ask me anything — I'm your Amzur AI assistant.</p>
        </div>
      ) : (
        messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${
              message.role === "user" ? "flex-row-reverse" : "flex-row"
            }`}
          >
            {/* Avatar */}
            <div
              className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                message.role === "user"
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-200 text-slate-700"
              }`}
            >
              {message.role === "user" ? "You" : "AI"}
            </div>

            {/* Bubble */}
            <div
              className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                message.role === "user"
                  ? "rounded-tr-sm bg-indigo-600 text-white"
                  : "rounded-tl-sm bg-white text-slate-800 shadow-sm border border-slate-100"
              }`}
            >
              {message.content || (
                isStreaming && message.role === "assistant" ? (
                  <span className="inline-flex gap-1">
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:0ms]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:150ms]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:300ms]" />
                  </span>
                ) : null
              )}
            </div>
          </div>
        ))
      )}
      <div ref={bottomRef} />
    </div>
  );
}
