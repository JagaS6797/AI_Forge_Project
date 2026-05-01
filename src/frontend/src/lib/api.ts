const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

import type {
  AuthUser,
  ChatHistoryMessage,
  ChatThread,
  LoginResponse,
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

export async function sendMessage(
  message: string,
  threadId: string,
  onToken?: TokenHandler,
  onThreadName?: ThreadNameHandler,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    credentials: "include",
    headers: withAuthHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ message, thread_id: threadId }),
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
        done?: boolean;
      };

      if (parsed.done) return;
      if (parsed.thread_name && onThreadName) onThreadName(parsed.thread_name);
      if (parsed.token && onToken) onToken(parsed.token);
    }
  }
}
