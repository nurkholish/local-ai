const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const API_KEY = import.meta.env.VITE_API_KEY || "dev-key";
const PROM_URL = import.meta.env.VITE_PROMETHEUS_URL || "http://localhost:9090";

export interface ChatResponse {
  answer: string;
  route: string;
  trace_id: string;
  latency_ms: number;
  blocked_by: string | null;
  steps: Array<{ name: string; result: string; blocked: boolean }>;
  checks: Array<{ name: string; passed: boolean }>;
  cost?: Record<string, unknown>;
}

export interface ChatRequest {
  message: string;
  user_key?: string;
  history?: Array<{ role: string; content: string }>;
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  timeoutMs = 180_000
): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${API_URL}${path}`, {
      ...init,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        ...(init.headers || {}),
      },
    });

    if (!res.ok) {
      const err = await res.text();
      throw new Error(`HTTP ${res.status}: ${err.slice(0, 200)}`);
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

export const api = {
  chat: (body: ChatRequest) =>
    request<ChatResponse>("/v1/chat", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  health: () => request<{ status: string }>("/healthz", {}, 5000),
  ready: () => request<{ status: string }>("/readyz", {}, 5000),
};

// ── Streaming SSE ───────────────────────────────
export interface StreamCallbacks {
  onStart?: (traceId: string) => void;
  onToken: (token: string) => void;
  onDone: (traceId: string) => void;
  onError: (err: string) => void;
}

/**
 * Parse SSE stream — handles both \n\n and \r\n\r\n delimiters.
 * sse-starlette sends \r\n\r\n by default.
 */
export async function streamChat(
  body: ChatRequest,
  callbacks: StreamCallbacks,
  abortSignal?: AbortSignal
): Promise<void> {
  try {
    const res = await fetch(`${API_URL}/v1/chat/stream`, {
      method: "POST",
      signal: abortSignal,
      headers: {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
      },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const errText = await res.text();
      callbacks.onError(`HTTP ${res.status}: ${errText.slice(0, 200)}`);
      return;
    }

    const reader = res.body?.getReader();
    if (!reader) {
      callbacks.onError("no body reader");
      return;
    }

    const decoder = new TextDecoder();
    let buffer = "";
    let traceId = "";
    let receivedDone = false;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Normalize CRLF → LF (sse-starlette uses \r\n\r\n)
      buffer = buffer.replace(/\r\n/g, "\n");

      // SSE events separated by \n\n
      const events = buffer.split("\n\n");
      buffer = events.pop() || "";

      for (const rawEvent of events) {
        if (!rawEvent.trim()) continue;

        // Parse SSE lines
        let eventType = "message";
        let dataStr = "";

        for (const line of rawEvent.split("\n")) {
          if (line.startsWith("event:")) {
            eventType = line.slice(6).trim();
          } else if (line.startsWith("data:")) {
            dataStr = line.slice(5).trim();
          }
        }

        if (!dataStr) continue;

        try {
          const parsed = JSON.parse(dataStr);
          const type = parsed.type || eventType;

          if (type === "start") {
            traceId = parsed.trace_id || "";
            callbacks.onStart?.(traceId);
          } else if (type === "token") {
            if (parsed.content) {
              callbacks.onToken(parsed.content);
            }
          } else if (type === "done") {
            receivedDone = true;
            callbacks.onDone(parsed.trace_id || traceId);
          } else if (type === "error") {
            callbacks.onError(parsed.error || "stream error");
          }
        } catch (e) {
          console.warn("SSE parse fail:", dataStr, e);
        }
      }
    }

    // Stream ended without "done" event — force done
    if (!receivedDone) {
      callbacks.onDone(traceId);
    }
  } catch (e) {
    if ((e as Error).name === "AbortError") return;
    callbacks.onError(e instanceof Error ? e.message : "stream failed");
  }
}

// ── Prometheus ──────────────────────────────────
export async function queryMetrics(query: string): Promise<number> {
  const url = `${PROM_URL}/api/v1/query?query=${encodeURIComponent(query)}`;
  const res = await fetch(url);
  const data = await res.json();
  const value = data?.data?.result?.[0]?.value?.[1];
  return value ? parseFloat(value) : 0;
}

export async function queryMetricsRange(
  query: string,
  start: number,
  end: number,
  step: number
): Promise<Array<{ t: number; v: number }>> {
  const url = `${PROM_URL}/api/v1/query_range?query=${encodeURIComponent(
    query
  )}&start=${start}&end=${end}&step=${step}`;
  const res = await fetch(url);
  const data = await res.json();
  const values = data?.data?.result?.[0]?.values || [];
  return values.map(([t, v]: [number, string]) => ({ t: t * 1000, v: parseFloat(v) }));
}