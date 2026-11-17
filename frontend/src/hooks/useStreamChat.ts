import { useCallback, useState } from "react";
import { streamChat } from "@/lib/api";

interface UseStreamChatResult {
  stream: (message: string, onToken: (token: string) => void) => Promise<string>;
  isStreaming: boolean;
  cancel: () => void;
}

export function useStreamChat(): UseStreamChatResult {
  const [isStreaming, setIsStreaming] = useState(false);
  const [controller, setController] = useState<AbortController | null>(null);

  const stream = useCallback(
    async (message: string, onToken: (token: string) => void): Promise<string> => {
      if (isStreaming) return "";

      setIsStreaming(true);
      const ctrl = new AbortController();
      setController(ctrl);

      let accumulated = "";
      let traceId = "";

      await streamChat(
        { message },
        {
          onStart: (tid) => {
            traceId = tid;
          },
          onToken: (token) => {
            accumulated += token;
            onToken(token);
          },
          onDone: () => {},
          onError: (err) => {
            console.error("stream error:", err);
          },
        },
        ctrl.signal
      );

      setIsStreaming(false);
      setController(null);
      return accumulated || traceId;
    },
    [isStreaming]
  );

  const cancel = useCallback(() => {
    controller?.abort();
    setController(null);
    setIsStreaming(false);
  }, [controller]);

  return { stream, isStreaming, cancel };
}