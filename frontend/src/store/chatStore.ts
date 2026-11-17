import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ChatResponse } from "@/lib/api";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  response?: ChatResponse;
  error?: string;
  loading?: boolean;
  streaming?: boolean;      // ← NEW: true while tokens arriving
  traceId?: string;          // ← NEW: from stream start event
}

interface ChatState {
  messages: Message[];
  addMessage: (m: Message) => void;
  updateMessage: (id: string, patch: Partial<Message>) => void;
  appendToMessage: (id: string, token: string) => void;  // ← NEW: streaming append
  clear: () => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      messages: [],

      addMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),

      updateMessage: (id, patch) =>
        set((s) => ({
          messages: s.messages.map((m) => (m.id === id ? { ...m, ...patch } : m)),
        })),

      appendToMessage: (id, token) =>
        set((s) => ({
          messages: s.messages.map((m) =>
            m.id === id ? { ...m, content: m.content + token, streaming: true } : m
          ),
        })),

      clear: () => set({ messages: [] }),
    }),
    {
      name: "local-ai-chat",
      partialize: (s) => ({
        messages: s.messages
          .filter((m) => !m.streaming)
          .slice(-20),
      }),
    }
  )
);