import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const [h, r] = await Promise.allSettled([api.health(), api.ready()]);
      return {
        online: h.status === "fulfilled" && h.value.status === "ok",
        ready: r.status === "fulfilled" && r.value.status === "ready",
      };
    },
    refetchInterval: 10_000,
    retry: false,
  });
}