import { useState, useRef, useEffect, type KeyboardEvent } from "react";
import { ArrowUp, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useChat } from "@/hooks/useChat";

export function ChatInput() {
  const [text, setText] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);
  const chat = useChat();

  useEffect(() => {
    if (ref.current) {
      ref.current.style.height = "auto";
      ref.current.style.height = `${Math.min(ref.current.scrollHeight, 200)}px`;
    }
  }, [text]);

  const submit = () => {
    const trimmed = text.trim();
    if (!trimmed || chat.isPending) return;
    chat.mutate(trimmed);
    setText("");
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="relative">
      <div className="flex items-end gap-2 rounded-2xl border border-white/10 bg-white/[0.03] p-2 backdrop-blur-xl transition-all focus-within:border-primary/40 focus-within:ring-2 focus-within:ring-primary/20">
        <textarea
          ref={ref}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Ask the agent anything… (Shift+Enter for newline)"
          rows={1}
          disabled={chat.isPending}
          className="flex-1 resize-none bg-transparent px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none scrollbar-thin"
        />
        {chat.isPending ? (
          <Button
            size="icon"
            variant="destructive"
            onClick={chat.cancel}
            className="shrink-0 rounded-xl"
            title="Stop generating"
          >
            <Square className="h-4 w-4" />
          </Button>
        ) : (
          <Button
            size="icon"
            onClick={submit}
            disabled={!text.trim()}
            className="shrink-0 rounded-xl"
          >
            <ArrowUp className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
}