import { useCallback, useState } from "react";
import { useChatStore } from "@/store/chatStore";
import { streamChat } from "@/lib/api";
import { nanoid } from "@/lib/nanoid";

export function useChat() {
  const { addMessage, updateMessage, appendToMessage } = useChatStore();
  const [isPending, setIsPending] = useState(false);
  const [abortController, setAbortController] = useState<AbortController | null>(null);

  const cancel = useCallback(() => {
    abortController?.abort();
    setAbortController(null);
    setIsPending(false);
  }, [abortController]);

  const mutate = useCallback(
    async (text: string) => {
      if (isPending) return;
      setIsPending(true);

      const userId = nanoid();
      const assistantId = nanoid();
      const controller = new AbortController();
      setAbortController(controller);

      addMessage({ id: userId, role: "user", content: text, timestamp: Date.now() });
      addMessage({
        id: assistantId,
        role: "assistant",
        content: "",
        timestamp: Date.now(),
        loading: true,
        streaming: false,
      });

      const history = useChatStore
        .getState()
        .messages.filter(
          (m) => !m.loading && !m.streaming && m.id !== userId && m.id !== assistantId
        )
        .slice(-6)
        .map((m) => ({ role: m.role, content: m.content }));

      try {
        await streamChat(
          { message: text, history },
          {
            onStart: (traceId) => {
              updateMessage(assistantId, { loading: false, streaming: true, traceId });
            },
            onToken: (token) => {
              appendToMessage(assistantId, token);
            },
            onDone: (traceId) => {
              const finalContent =
                useChatStore.getState().messages.find((m) => m.id === assistantId)?.content || "";
              updateMessage(assistantId, {
                content: finalContent,
                streaming: false,
                loading: false,
                traceId,
              });
            },
            onError: (err) => {
              updateMessage(assistantId, {
                content: `**Error:** ${err}`,
                error: err,
                streaming: false,
                loading: false,
              });
            },
          },
          controller.signal
        );
      } catch (e) {
        const err = e instanceof Error ? e.message : "Unknown error";
        updateMessage(assistantId, {
          content: `**Error:** ${err}`,
          error: err,
          streaming: false,
          loading: false,
        });
      } finally {
        setIsPending(false);
        setAbortController(null);
      }
    },
    [isPending, addMessage, updateMessage, appendToMessage]
  );

  return { mutate, isPending, cancel };
}