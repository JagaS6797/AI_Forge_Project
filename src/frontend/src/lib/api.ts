const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

import type {
  AuthUser,
  ChatAttachment,
  FileUploadResponse,
  ChatHistoryMessage,
  PdfUploadResponse,
  ChatThread,
  LoginResponse,
  SqlQueryResult,
  DataFrameQueryResult,
  TicTacToeCell,
  TicTacToeGameState,
} from "../types";

const AUTH_TOKEN_KEY = "amzur_chat_access_token";

let authToken: string | null = null;

try {
  authToken = localStorage.getItem(AUTH_TOKEN_KEY);
} catch {
  authToken = null;
}

export function setAuthToken(token: string): void {
  authToken = token;
  localStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function clearAuthToken(): void {
  authToken = null;
  localStorage.removeItem(AUTH_TOKEN_KEY);
}

export function getAuthToken(): string | null {
  return authToken;
}

function withAuthHeaders(headers: Record<string, string>): Record<string, string> {
  if (!authToken) return headers;
  return { ...headers, Authorization: `Bearer ${authToken}` };
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    ...init,
    headers: withAuthHeaders({
      "Content-Type": "application/json",
      ...(init?.headers as Record<string, string> ?? {}),
    }),
  });

  if (!response.ok) {
    let detail = `API request failed with status ${response.status}`;
    try {
      const body = await response.json() as { detail?: { message?: string } | string };
      if (typeof body.detail === "object" && body.detail?.message) {
        detail = body.detail.message;
      } else if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch { /* ignore parse errors */ }
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export async function login(userId: string, password: string): Promise<LoginResponse> {
  return apiRequest<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ user_id: userId, password }),
  });
}

export async function register(userId: string, password: string): Promise<LoginResponse> {
  return apiRequest<LoginResponse>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ user_id: userId, password }),
  });
}

export async function googleLogin(credential: string): Promise<LoginResponse> {
  return apiRequest<LoginResponse>("/api/auth/google", {
    method: "POST",
    body: JSON.stringify({ credential }),
  });
}

export async function getCurrentUser(): Promise<AuthUser> {
  return apiRequest<AuthUser>("/api/auth/me");
}

// ── Threads ───────────────────────────────────────────────────────────────────

export async function getThreads(): Promise<ChatThread[]> {
  return apiRequest<ChatThread[]>("/api/threads");
}

export async function createThread(name = "New Chat"): Promise<ChatThread> {
  return apiRequest<ChatThread>("/api/threads", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export async function renameThread(threadId: string, name: string): Promise<ChatThread> {
  return apiRequest<ChatThread>(`/api/threads/${threadId}`, {
    method: "PATCH",
    body: JSON.stringify({ name }),
  });
}

export async function deleteThread(threadId: string): Promise<void> {
  await fetch(`${API_BASE_URL}/api/threads/${threadId}`, {
    method: "DELETE",
    credentials: "include",
    headers: withAuthHeaders({}),
  });
}

export async function getThreadMessages(threadId: string): Promise<ChatHistoryMessage[]> {
  return apiRequest<ChatHistoryMessage[]>(`/api/threads/${threadId}/messages`);
}

// ── Chat streaming ─────────────────────────────────────────────────────────

type TokenHandler = (token: string) => void;
type ThreadNameHandler = (name: string) => void;
type AttachmentHandler = (attachment: ChatAttachment) => void;

export async function sendMessage(
  message: string,
  threadId: string,
  attachmentIds: string[] = [],
  ragEnabled = false,
  onToken?: TokenHandler,
  onThreadName?: ThreadNameHandler,
  onAttachment?: AttachmentHandler,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    credentials: "include",
    headers: withAuthHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ 
      message, 
      thread_id: threadId,
      attachment_ids: attachmentIds,
      rag_enabled: ragEnabled,
    }),
  });

  if (!response.ok || !response.body) {
    throw new Error(`Chat request failed with status ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";

    for (const event of events) {
      const dataLine = event
        .split("\n")
        .map((l) => l.trim())
        .find((l) => l.startsWith("data:"));

      if (!dataLine) continue;

      const jsonPayload = dataLine.replace(/^data:\s*/, "");
      const parsed = JSON.parse(jsonPayload) as {
        token?: string;
        thread_name?: string;
        attachment?: ChatAttachment;
        done?: boolean;
        event?: string;
      };

      if (parsed.done) return;
      if (parsed.event === "rag_fallback") {
        document.dispatchEvent(new CustomEvent("ragFallback"));
      }
      if (parsed.thread_name && onThreadName) onThreadName(parsed.thread_name);
      if (parsed.token && onToken) onToken(parsed.token);
      if (parsed.attachment && onAttachment) onAttachment(parsed.attachment);
    }
  }
}

// ── Attachments ────────────────────────────────────────────────────────────

export async function uploadAttachments(formData: FormData): Promise<FileUploadResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat/upload`, {
    method: "POST",
    credentials: "include",
    headers: withAuthHeaders({}),
    body: formData,
  });

  if (!response.ok) {
    let detail = `Upload failed with status ${response.status}`;
    try {
      const body = await response.json() as { detail?: { message?: string } | string };
      if (typeof body.detail === "object" && body.detail?.message) {
        detail = body.detail.message;
      } else if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch { /* ignore parse errors */ }
    throw new Error(detail);
  }

  return (await response.json()) as FileUploadResponse;
}

export async function uploadPdf(threadId: string, file: File): Promise<PdfUploadResponse> {
  const formData = new FormData();
  formData.append("thread_id", threadId);
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/chat/upload-pdf`, {
    method: "POST",
    credentials: "include",
    headers: withAuthHeaders({}),
    body: formData,
  });

  if (!response.ok) {
    let detail = `PDF upload failed with status ${response.status}`;
    try {
      const body = await response.json() as { detail?: { message?: string } | string };
      if (typeof body.detail === "object" && body.detail?.message) {
        detail = body.detail.message;
      } else if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // ignore parse errors
    }
    throw new Error(detail);
  }

  return (await response.json()) as PdfUploadResponse;
}

export async function askPdfQuestion(
  question: string,
  threadId: string,
  onToken?: TokenHandler,
  onThreadName?: ThreadNameHandler,
  onAttachment?: AttachmentHandler,
): Promise<void> {
  await sendMessage(question, threadId, [], true, onToken, onThreadName, onAttachment);
}

export async function downloadAttachment(attachmentId: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/chat/attachments/${attachmentId}`, {
    method: "GET",
    credentials: "include",
    headers: withAuthHeaders({}),
  });

  if (!response.ok) {
    throw new Error(`Download failed with status ${response.status}`);
  }

  return response.blob();
}

// -- Project 8: NL to SQL ----------------------------------------------------

export async function askDatabaseQuestion(
  question: string,
  maxRows = 50,
): Promise<SqlQueryResult> {
  return apiRequest<SqlQueryResult>("/api/sql/query", {
    method: "POST",
    body: JSON.stringify({ question, max_rows: maxRows }),
  });
}

// -- Project 9: CSV/Google Sheets ---------------------------------------------------

export async function queryDataFrameWithNL(
  question: string,
  useGoogleSheets = true,
  csvFileId: string | null = null,
): Promise<DataFrameQueryResult> {
  return apiRequest<DataFrameQueryResult>("/api/dataframe/query", {
    method: "POST",
    body: JSON.stringify({
      question,
      use_google_sheets: useGoogleSheets,
      csv_file_id: csvFileId,
    }),
  });
}

// -- Project 10: Research Digest Agent ---------------------------------------------------

export function streamResearchDigest(
  topic: string,
  maxPapers = 5,
  onEvent: (eventName: string, data: Record<string, unknown>) => void,
  signal?: AbortSignal,
): Promise<void> {
  return new Promise((resolve, reject) => {
    fetch(`${API_BASE_URL}/api/research/digest`, {
      method: "POST",
      credentials: "include",
      headers: withAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ topic, max_papers: maxPapers }),
      signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          let msg = `Request failed: ${response.status}`;
          try {
            const body = await response.json() as { detail?: string };
            if (typeof body.detail === "string") msg = body.detail;
          } catch { /* ignore */ }
          reject(new Error(msg));
          return;
        }

        const reader = response.body?.getReader();
        if (!reader) { reject(new Error("No response body")); return; }

        const decoder = new TextDecoder();
        let buffer = "";

        const pump = async (): Promise<void> => {
          const { done, value } = await reader.read();
          if (done) { resolve(); return; }
          buffer += decoder.decode(value, { stream: true });

          // Split on double newlines (SSE message boundaries)
          const parts = buffer.split("\n\n");
          buffer = parts.pop() ?? "";

          for (const part of parts) {
            const lines = part.split("\n");
            let eventName = "message";
            let dataLine = "";
            for (const line of lines) {
              if (line.startsWith("event: ")) eventName = line.slice(7).trim();
              else if (line.startsWith("data: ")) dataLine = line.slice(6).trim();
            }
            if (dataLine) {
              try {
                const parsed = JSON.parse(dataLine) as Record<string, unknown>;
                onEvent(eventName, parsed);
                if (eventName === "done" || eventName === "error") { resolve(); return; }
              } catch { /* skip malformed */ }
            }
          }
          return pump();
        };

        return pump();
      })
      .catch(reject);
  });
}

export async function uploadCsvFile(file: File): Promise<{ file_id: string; file_name: string; size: number }> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/dataframe/upload-csv`, {
    method: "POST",
    credentials: "include",
    headers: withAuthHeaders({}),
    body: formData,
  });

  if (!response.ok) {
    let detail = `CSV upload failed with status ${response.status}`;
    try {
      const body = await response.json() as { detail?: { message?: string } | string };
      if (typeof body.detail === "object" && body.detail?.message) {
        detail = body.detail.message;
      } else if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch { /* ignore parse errors */ }
    throw new Error(detail);
  }

  return (await response.json()) as { file_id: string; file_name: string; size: number };
}

// -- Project 11: Tic Tac Toe Agent ---------------------------------------------------

export async function startTicTacToeGame(
  userSymbol: "X" | "O" = "X",
  agentStarts = false,
): Promise<TicTacToeGameState> {
  return apiRequest<TicTacToeGameState>("/api/tic-tac-toe/new", {
    method: "POST",
    body: JSON.stringify({ user_symbol: userSymbol, agent_starts: agentStarts }),
  });
}

export async function playTicTacToeMove(
  board: TicTacToeCell[],
  userSymbol: "X" | "O",
  userMove: number,
): Promise<TicTacToeGameState> {
  return apiRequest<TicTacToeGameState>("/api/tic-tac-toe/move", {
    method: "POST",
    body: JSON.stringify({ board, user_symbol: userSymbol, user_move: userMove }),
  });
}
