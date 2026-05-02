import { useEffect, useState } from "react";

export default function App() {
  const [email, setEmail] = useState("employee@amzur.com");
  const [password, setPassword] = useState("");
  const [user, setUser] = useState(null);
  const [threads, setThreads] = useState([]);
  const [activeThreadId, setActiveThreadId] = useState(null);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [authLoading, setAuthLoading] = useState(false);
  const [threadLoading, setThreadLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchMessages = async (threadId) => {
    if (!threadId) {
      setMessages([]);
      return;
    }

    const response = await fetch(`/api/chat/messages?thread_id=${threadId}`, {
      credentials: "include",
    });
    if (!response.ok) {
      throw new Error("Failed to load messages");
    }

    const payload = await response.json();
    setMessages(
      payload.messages.map((item) => ({
        role: item.role,
        text: item.content,
      }))
    );
  };

  const fetchThreads = async () => {
    const response = await fetch("/api/threads", {
      credentials: "include",
    });
    if (!response.ok) {
      throw new Error("Failed to load threads");
    }
    const payload = await response.json();
    setThreads(payload.threads);
    return payload.threads;
  };

  useEffect(() => {
    const boot = async () => {
      try {
        const meRes = await fetch("/api/auth/me", { credentials: "include" });
        if (!meRes.ok) {
          return;
        }

        const meData = await meRes.json();
        setUser(meData);

        const loadedThreads = await fetchThreads();
        if (loadedThreads.length > 0) {
          setActiveThreadId(loadedThreads[0].id);
          await fetchMessages(loadedThreads[0].id);
        }
      } catch (_e) {
        setError("Unable to connect to backend");
      }
    };

    boot();
  }, []);

  const onRegister = async (event) => {
    event.preventDefault();
    setError("");
    setAuthLoading(true);

    try {
      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const payload = await response.json();
        throw new Error(payload?.detail?.message || "Register failed");
      }

      setError("Registration successful. Please login.");
    } catch (e) {
      setError(e.message || "Register failed");
    } finally {
      setAuthLoading(false);
    }
  };

  const onLogin = async (event) => {
    event.preventDefault();
    setError("");
    setAuthLoading(true);

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password }),
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload?.detail?.message || "Login failed");
      }

      setUser(payload.user);
      setThreads(payload.threads || []);

      if ((payload.threads || []).length > 0) {
        const firstThreadId = payload.threads[0].id;
        setActiveThreadId(firstThreadId);
        await fetchMessages(firstThreadId);
      } else {
        setActiveThreadId(null);
        setMessages([]);
      }
    } catch (e) {
      setError(e.message || "Login failed");
    } finally {
      setAuthLoading(false);
    }
  };

  const onGoogleLogin = () => {
    window.location.href = "/api/auth/google/login";
  };

  const onCreateThread = async () => {
    if (!user || threadLoading) {
      return;
    }

    setThreadLoading(true);
    setError("");
    try {
      const response = await fetch("/api/threads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({}),
      });
      if (!response.ok) {
        throw new Error("Unable to create thread");
      }

      const created = await response.json();
      setThreads((prev) => [created, ...prev]);
      setActiveThreadId(created.id);
      setMessages([]);
    } catch (e) {
      setError(e.message || "Unable to create thread");
    } finally {
      setThreadLoading(false);
    }
  };

  const onSelectThread = async (threadId) => {
    setActiveThreadId(threadId);
    setError("");
    try {
      await fetchMessages(threadId);
    } catch (_e) {
      setError("Unable to load thread messages");
    }
  };

  const onRenameThread = async (thread) => {
    const nextTitle = window.prompt("Rename thread", thread.title);
    if (!nextTitle || !nextTitle.trim()) {
      return;
    }

    try {
      const response = await fetch(`/api/threads/${thread.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ title: nextTitle.trim() }),
      });
      if (!response.ok) {
        throw new Error("Unable to rename thread");
      }

      const updated = await response.json();
      setThreads((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
    } catch (e) {
      setError(e.message || "Unable to rename thread");
    }
  };

  const onDeleteThread = async (threadId) => {
    if (!window.confirm("Delete this thread?")) {
      return;
    }

    try {
      const response = await fetch(`/api/threads/${threadId}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!response.ok) {
        throw new Error("Unable to delete thread");
      }

      const nextThreads = threads.filter((item) => item.id !== threadId);
      setThreads(nextThreads);

      if (activeThreadId === threadId) {
        if (nextThreads.length > 0) {
          setActiveThreadId(nextThreads[0].id);
          await fetchMessages(nextThreads[0].id);
        } else {
          setActiveThreadId(null);
          setMessages([]);
        }
      }
    } catch (e) {
      setError(e.message || "Unable to delete thread");
    }
  };

  const onLogout = async () => {
    await fetch("/api/auth/logout", {
      method: "POST",
      credentials: "include",
    });
    setUser(null);
    setThreads([]);
    setActiveThreadId(null);
    setMessages([]);
    setPassword("");
  };

  const sendMessage = async (event) => {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed || loading || !user) {
      return;
    }

    setMessages((prev) => [...prev, { role: "user", text: trimmed }]);
    setMessage("");
    setLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ message: trimmed, thread_id: activeThreadId }),
      });

      if (!response.ok) {
        throw new Error("Request failed");
      }

      const data = await response.json();
      setMessages((prev) => [...prev, { role: "assistant", text: data.reply }]);

      if (!activeThreadId && data.thread_id) {
        setActiveThreadId(data.thread_id);
      }

      const nextThreads = await fetchThreads();
      if (!activeThreadId && nextThreads.length > 0) {
        setActiveThreadId(nextThreads[0].id);
      }
    } catch (_error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "I could not reach the backend. Please check that the API server is running.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page">
      <div className="background-orb orb-left" aria-hidden="true" />
      <div className="background-orb orb-right" aria-hidden="true" />

      <section className="chat-shell">
        <header className="chat-header">
          <div>
            <p className="eyebrow">Amzur AI Platform</p>
            <h1>AI Chat Workspace</h1>
            <p className="subtitle">Fast answers with secure employee sign-in and persistent thread history.</p>
          </div>
          <span className="status-pill">Live</span>
        </header>

        {!user ? (
          <form className="auth-form" onSubmit={onLogin}>
            <p className="section-title">Employee Sign In</p>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Employee email"
              required
            />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              required
              minLength={8}
            />
            <div className="auth-actions">
              <button type="submit" className="btn-primary" disabled={authLoading}>
                {authLoading ? "Please wait..." : "Login"}
              </button>
              <button type="button" className="btn-secondary" onClick={onRegister} disabled={authLoading}>
                Register
              </button>
              <button type="button" className="btn-google" onClick={onGoogleLogin} disabled={authLoading}>
                Continue with Google
              </button>
            </div>
            {error ? <p className="error">{error}</p> : null}
          </form>
        ) : (
          <>
            <div className="session-bar">
              <div>
                <p className="session-title">Signed in</p>
                <span>{user.email}</span>
              </div>
              <div className="session-meta">
                <span>{messages.length} messages</span>
                <button type="button" className="btn-secondary" onClick={onLogout}>
                  Logout
                </button>
              </div>
            </div>

            <div className="content-grid">
              <aside className="threads-panel">
                <div className="threads-header">
                  <h3>Threads</h3>
                  <button type="button" className="btn-secondary" onClick={onCreateThread} disabled={threadLoading}>
                    New
                  </button>
                </div>

                <div className="threads-list">
                  {threads.length === 0 ? (
                    <p className="empty-threads">No threads yet.</p>
                  ) : (
                    threads.map((thread) => (
                      <article
                        key={thread.id}
                        className={`thread-item ${activeThreadId === thread.id ? "active" : ""}`}
                      >
                        <button type="button" className="thread-title" onClick={() => onSelectThread(thread.id)}>
                          {thread.title}
                        </button>
                        <div className="thread-actions">
                          <button type="button" onClick={() => onRenameThread(thread)}>
                            Rename
                          </button>
                          <button type="button" onClick={() => onDeleteThread(thread.id)}>
                            Delete
                          </button>
                        </div>
                      </article>
                    ))
                  )}
                </div>
              </aside>

              <div className="chat-panel">
                <div className="messages" aria-live="polite">
                  {messages.length === 0 ? (
                    <div className="empty-state">Select or create a thread to start chatting.</div>
                  ) : (
                    messages.map((item, index) => (
                      <article key={index} className={`bubble ${item.role}`}>
                        <strong>{item.role === "user" ? "You" : "Assistant"}</strong>
                        <p>{item.text}</p>
                      </article>
                    ))
                  )}
                </div>
              </div>
            </div>

            <form className="composer" onSubmit={sendMessage}>
              <input
                type="text"
                value={message}
                placeholder="Type your question..."
                onChange={(e) => setMessage(e.target.value)}
                disabled={loading || !user}
              />
              <button type="submit" className="btn-primary" disabled={loading || !message.trim()}>
                {loading ? "Sending..." : "Send"}
              </button>
            </form>
            {error ? <p className="error page-error">{error}</p> : null}
          </>
        )}
      </section>
    </main>
  );
}
