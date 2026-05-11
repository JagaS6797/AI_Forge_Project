import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { sendMessage } from "./api";

function sseStream(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  let i = 0;
  return new ReadableStream<Uint8Array>({
    pull(controller) {
      if (i >= chunks.length) {
        controller.close();
        return;
      }
      controller.enqueue(encoder.encode(chunks[i]));
      i += 1;
    },
  });
}

describe("api.sendMessage", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it("parses token and thread_name events and stops on done", async () => {
    const onToken = vi.fn();
    const onThreadName = vi.fn();

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: sseStream([
        'data: {"thread_name":"Project Plan"}\n\n',
        'data: {"token":"Hello"}\n\n',
        'data: {"token":" World"}\n\n',
        'data: {"done": true}\n\n',
      ]),
    } as unknown as Response);

    await sendMessage("Hi", "thread-1", [], false, onToken, onThreadName);

    expect(onThreadName).toHaveBeenCalledWith("Project Plan");
    expect(onToken).toHaveBeenNthCalledWith(1, "Hello");
    expect(onToken).toHaveBeenNthCalledWith(2, " World");
  });

  it("dispatches ragFallback browser event when backend emits rag_fallback", async () => {
    const handler = vi.fn();
    document.addEventListener("ragFallback", handler);

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: sseStream([
        'data: {"event":"rag_fallback"}\n\n',
        'data: {"done": true}\n\n',
      ]),
    } as unknown as Response);

    await sendMessage("Question", "thread-2");

    expect(handler).toHaveBeenCalled();
    document.removeEventListener("ragFallback", handler);
  });

  it("passes attachment events to handler", async () => {
    const onAttachment = vi.fn();

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: sseStream([
        'data: {"attachment":{"id":"a1","file_name":"img.png","file_type":"image/png","file_size":12,"created_at":"2026-01-01T00:00:00Z"}}\n\n',
        'data: {"done": true}\n\n',
      ]),
    } as unknown as Response);

    await sendMessage("/image cat", "thread-3", [], false, undefined, undefined, onAttachment);

    expect(onAttachment).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "a1",
        file_name: "img.png",
      }),
    );
  });

  it("throws when request fails", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      body: null,
    } as unknown as Response);

    await expect(sendMessage("Hi", "thread-4")).rejects.toThrow("Chat request failed with status 500");
  });
});
