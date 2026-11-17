import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Bot, User, AlertCircle, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ToolCallCard } from "./ToolCallCard";
import { RouteBadge } from "./RouteBadge";
import { TypingIndicator } from "./TypingIndicator";
import { cn, formatLatency } from "@/lib/utils";
import type { Message } from "@/store/chatStore";

export function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const isError = !!message.error;
  const isStreaming = message.streaming && message.content.length > 0;

  const tokens = message.response?.cost
    ? Number(message.response.cost.total_tokens ?? 0)
    : 0;
  const costUsd = message.response?.cost
    ? Number(message.response.cost.cost_usd ?? 0)
    : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={cn("flex gap-4 px-4 py-3", isUser ? "flex-row-reverse" : "flex-row")}
    >
      <div
        className={cn(
          "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border",
          isUser
            ? "bg-primary/20 border-primary/30"
            : isError
              ? "bg-rose-500/20 border-rose-500/30"
              : "bg-gradient-to-br from-violet-500/20 to-cyan-500/20 border-white/10"
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-primary" />
        ) : isError ? (
          <AlertCircle className="h-4 w-4 text-rose-400" />
        ) : (
          <Bot className="h-4 w-4 text-cyan-300" />
        )}
      </div>

      <div className={cn("flex-1 min-w-0", isUser && "flex flex-col items-end")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-3 max-w-[85%]",
            isUser
              ? "bg-primary text-primary-foreground rounded-tr-sm"
              : isError
                ? "bg-rose-500/10 border border-rose-500/20"
                : "bg-white/5 border border-white/5"
          )}
        >
          {message.loading ? (
            <TypingIndicator />
          ) : isUser ? (
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose-chat">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
              {isStreaming && (
                <span className="inline-flex items-center gap-1.5 ml-2 text-xs text-cyan-400/70">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  <span>streaming…</span>
                </span>
              )}
            </div>
          )}
        </div>

        {message.response && !message.streaming && (
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {message.response.route && <RouteBadge route={message.response.route} />}
            <Badge variant="outline">
              <span className="font-mono text-[10px]">
                {formatLatency(message.response.latency_ms)}
              </span>
            </Badge>
            {message.response.checks.map((c) => (
              <Badge
                key={c.name}
                variant={c.passed ? "success" : "destructive"}
                className="text-[10px]"
              >
                {c.name.replace(/_/g, " ")}
              </Badge>
            ))}
            {message.response.blocked_by && (
              <Badge variant="destructive">Blocked: {message.response.blocked_by}</Badge>
            )}
            {tokens > 0 && (
              <Badge variant="outline" className="font-mono text-[10px]">
                {tokens} tok
                {costUsd > 0 && <> · ${costUsd.toFixed(6)}</>}
              </Badge>
            )}
          </div>
        )}

        {message.response && message.response.steps.length > 0 && !message.streaming && (
          <div className="mt-2 space-y-1.5 w-full max-w-[85%]">
            {message.response.steps.map((s, i) => (
              <ToolCallCard key={i} step={s} />
            ))}
          </div>
        )}

        {(message.response?.trace_id || message.traceId) && !message.streaming && (
          <p className="mt-2 font-mono text-[10px] text-muted-foreground/60">
            trace: {(message.response?.trace_id || message.traceId || "").slice(0, 12)}…
          </p>
        )}
      </div>
    </motion.div>
  );
}