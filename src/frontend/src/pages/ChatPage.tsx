import { useEffect, useRef, useState } from "react";
import { GoogleLogin } from "@react-oauth/google";
import { ChatWindow } from "../components/chat/ChatWindow";
import { ThreadSidebar } from "../components/chat/ThreadSidebar";
import {
  clearAuthToken,
  createThread,
  deleteThread,
  getAuthToken,
  getCurrentUser,
  getThreads,
  googleLogin,
  login,
  register,
  renameThread,
  setAuthToken,
} from "../lib/api";
import type { AuthUser, ChatThread } from "../types";

type Screen = "login" | "register" | "chat";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined;

export default function ChatPage() {
  const [screen, setScreen] = useState<Screen>("login");
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [user, setUser] = useState<AuthUser | null>(null);
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const userIdRef = useRef<HTMLInputElement>(null);

  const loadThreads = async () => {
    const data = await getThreads();
    setThreads(data);
    return data;
  };

  const afterLogin = async (response: Awaited<ReturnType<typeof login>>) => {
    setAuthToken(response.access_token);
    setUser(response.user);
    const data = await loadThreads();
    if (data.length > 0) setActiveThreadId(data[0].id);
    setScreen("chat");
  };

  useEffect(() => {
    const bootstrap = async () => {
      const token = getAuthToken();
      if (!token) { setIsLoading(false); return; }
      try {
        const currentUser = await getCurrentUser();
        setUser(currentUser);
        const data = await loadThreads();
        if (data.length > 0) setActiveThreadId(data[0].id);
        setScreen("chat");
      } catch {
        clearAuthToken();
      } finally {
        setIsLoading(false);
      }
    };
    void bootstrap();
  }, []);

  const handleRegister = async () => {
    const uid = userId.trim().toLowerCase();
    if (!uid || !password) { setError("All fields are required"); return; }
    if (password !== confirmPassword) { setError("Passwords do not match"); return; }
    if (password.length < 8) { setError("Password must be at least 8 characters"); return; }
    setError(null);
    setIsSubmitting(true);
    try {
      await register(uid, password);
      setUserId(uid);
      setPassword("");
      setConfirmPassword("");
      setSuccessMsg("Account created! Please login.");
      setScreen("login");
      setTimeout(() => userIdRef.current?.focus(), 100);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogin = async () => {
    const uid = userId.trim().toLowerCase();
    if (!uid || !password) { setError("User ID and password are required"); return; }
    setError(null);
    setSuccessMsg(null);
    setIsSubmitting(true);
    try {
      const result = await login(uid, password);
      setUserId("");
      setPassword("");
      await afterLogin(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGoogleSuccess = async (credentialResponse: { credential?: string }) => {
    if (!credentialResponse.credential) return;
    setError(null);
    setIsSubmitting(true);
    try {
      const result = await googleLogin(credentialResponse.credential);
      await afterLogin(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Google login failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogout = () => {
    clearAuthToken();
    setUser(null);
    setThreads([]);
    setActiveThreadId(null);
    setError(null);
    setPassword("");
    setScreen("login");
  };

  const handleNewThread = async () => {
    try {
      const thread = await createThread("New Chat");
      setThreads((prev) => [thread, ...prev]);
      setActiveThreadId(thread.id);
    } catch { /* ignore */ }
  };

  const handleRenameThread = async (threadId: string, name: string) => {
    try {
      const updated = await renameThread(threadId, name);
      setThreads((prev) => prev.map((t) => (t.id === threadId ? updated : t)));
    } catch { /* ignore */ }
  };

  const handleDeleteThread = async (threadId: string) => {
    try {
      await deleteThread(threadId);
      setThreads((prev) => prev.filter((t) => t.id !== threadId));
      if (activeThreadId === threadId) {
        const remaining = threads.filter((t) => t.id !== threadId);
        setActiveThreadId(remaining.length > 0 ? remaining[0].id : null);
      }
    } catch { /* ignore */ }
  };

  const handleThreadNamed = (threadId: string, name: string) => {
    setThreads((prev) => prev.map((t) => (t.id === threadId ? { ...t, name } : t)));
  };

  // ── Loading screen ──────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent" />
          <p className="text-sm text-slate-500">Loading…</p>
        </div>
      </div>
    );
  }

  // ── Register screen ─────────────────────────────────────────────────────────
  if (screen === "register") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
        <div className="w-full max-w-md">
          <div className="mb-6 text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-600 text-white text-xl font-bold">A</div>
            <h1 className="text-2xl font-bold text-slate-900">Create Account</h1>
            <p className="mt-1 text-sm text-slate-500">Amzur employees only · @amzur.com email required</p>
          </div>
          <div className="rounded-2xl bg-white p-8 shadow-lg">
            <div className="space-y-4">
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-700">User ID (Email)</label>
                <input ref={userIdRef} className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" placeholder="name@amzur.com" type="email" value={userId} onChange={(e) => setUserId(e.target.value)} disabled={isSubmitting} />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-700">Password</label>
                <input className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" placeholder="Min 8 characters" type="password" value={password} onChange={(e) => setPassword(e.target.value)} disabled={isSubmitting} />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-700">Confirm Password</label>
                <input className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" placeholder="Repeat password" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} disabled={isSubmitting} onKeyDown={(e) => e.key === "Enter" && handleRegister()} />
              </div>
              {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">{error}</p>}
              <button className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60" type="button" onClick={handleRegister} disabled={isSubmitting || !userId.trim() || password.length < 8}>
                {isSubmitting ? "Creating account…" : "Create Account"}
              </button>
            </div>
            <p className="mt-5 text-center text-sm text-slate-500">
              Already have an account?{" "}
              <button className="font-medium text-indigo-600 hover:underline" type="button" onClick={() => { setScreen("login"); setError(null); }}>Login</button>
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ── Login screen ────────────────────────────────────────────────────────────
  if (screen === "login") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
        <div className="w-full max-w-md">
          <div className="mb-6 text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-600 text-white text-xl font-bold">A</div>
            <h1 className="text-2xl font-bold text-slate-900">Welcome back</h1>
            <p className="mt-1 text-sm text-slate-500">Login to your Amzur AI Chat account</p>
          </div>
          <div className="rounded-2xl bg-white p-8 shadow-lg">
            {GOOGLE_CLIENT_ID && (
              <div className="mb-4 flex flex-col items-center gap-3">
                <GoogleLogin
                  onSuccess={handleGoogleSuccess}
                  onError={() => setError("Google login failed")}
                  width="100%"
                  text="signin_with"
                  shape="rectangular"
                />
                <div className="flex w-full items-center gap-2">
                  <hr className="flex-1 border-slate-200" />
                  <span className="text-xs text-slate-400">or login with email</span>
                  <hr className="flex-1 border-slate-200" />
                </div>
              </div>
            )}
            <div className="space-y-4">
              {successMsg && <p className="rounded-lg bg-green-50 px-3 py-2 text-xs font-medium text-green-700">{successMsg}</p>}
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-700">User ID (Email)</label>
                <input ref={userIdRef} className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" placeholder="name@amzur.com" type="email" value={userId} onChange={(e) => setUserId(e.target.value)} disabled={isSubmitting} />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-700">Password</label>
                <input className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" placeholder="Your password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} disabled={isSubmitting} onKeyDown={(e) => e.key === "Enter" && handleLogin()} />
              </div>
              {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">{error}</p>}
              <button className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60" type="button" onClick={handleLogin} disabled={isSubmitting || !userId.trim() || !password}>
                {isSubmitting ? "Logging in…" : "Login"}
              </button>
            </div>
            <p className="mt-5 text-center text-sm text-slate-500">
              No account yet?{" "}
              <button className="font-medium text-indigo-600 hover:underline" type="button" onClick={() => { setScreen("register"); setError(null); setSuccessMsg(null); }}>Register</button>
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ── Chat screen ─────────────────────────────────────────────────────────────
  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <ThreadSidebar
        threads={threads}
        activeThreadId={activeThreadId}
        onSelect={(t) => setActiveThreadId(t.id)}
        onCreate={handleNewThread}
        onRename={handleRenameThread}
        onDelete={handleDeleteThread}
        userEmail={user?.email ?? ""}
        onLogout={handleLogout}
      />

      <main className="flex flex-1 flex-col overflow-hidden">
        {activeThreadId ? (
          <>
            {/* Thread header */}
            <header className="flex items-center border-b border-slate-200 bg-white px-5 py-3 shadow-sm">
              <h2 className="text-sm font-semibold text-slate-800 truncate">
                {threads.find((t) => t.id === activeThreadId)?.name ?? "Chat"}
              </h2>
            </header>
            <ChatWindow threadId={activeThreadId} onThreadNamed={handleThreadNamed} />
          </>
        ) : (
          <div className="flex flex-1 flex-col items-center justify-center gap-4 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-100 text-2xl">💬</div>
            <p className="text-base font-medium text-slate-700">Start a new conversation</p>
            <p className="text-sm text-slate-400">Click <strong>New Chat</strong> in the sidebar to begin.</p>
          </div>
        )}
      </main>
    </div>
  );
}
