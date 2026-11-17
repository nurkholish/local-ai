import { useEffect, useRef } from "react";
import { useChatStore } from "@/store/chatStore";
import { ChatMessage } from "@/components/ChatMessage";
import { ChatInput } from "@/components/ChatInput";
import { EmptyState } from "@/components/EmptyState";

export function ChatPage() {
  const messages = useChatStore((s) => s.messages);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)]">
      <div ref={scrollRef} className="flex-1 overflow-y-auto scrollbar-thin">
        {messages.length === 0 ? <EmptyState /> : (
          <div className="max-w-3xl mx-auto py-6">
            {messages.map((m) => <ChatMessage key={m.id} message={m} />)}
          </div>
        )}
      </div>
      <div className="border-t border-white/5 bg-background/60 backdrop-blur-xl">
        <div className="max-w-3xl mx-auto p-4">
          <ChatInput />
          <p className="mt-2 text-center text-[10px] text-muted-foreground/60">Agent may use tools</p>
        </div>
      </div>
    </div>
  );
}