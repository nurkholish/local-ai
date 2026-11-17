import { useQuery } from "@tanstack/react-query";
import { queryMetrics, queryMetricsRange } from "@/lib/api";

interface MetricPoint {
  t: number;
  v: number;
}

export function useMetrics() {
  return useQuery({
    queryKey: ["metrics"],
    queryFn: async () => {
      const [total, latency, blocks, checks, tools] = await Promise.all([
        queryMetrics("sum(agent_requests_total)"),
        queryMetrics("histogram_quantile(0.95, rate(agent_latency_seconds_bucket[5m]))"),
        queryMetrics("sum(rate(agent_guardrail_blocks_total[5m]))"),
        queryMetrics("sum(rate(agent_check_fails_total[5m]))"),
        queryMetrics("sum(rate(agent_tool_calls_total[5m]))"),
      ]);
      return { total, latency, blocks, checks, tools };
    },
    refetchInterval: 15_000,
    retry: false,
  });
}

interface LatencyRow {
  t: number;
  p50: number;
  p95: number;
  p99: number;
}

export function useLatencySeries(minutes = 15) {
  return useQuery<LatencyRow[]>({
    queryKey: ["latency-series", minutes],
    queryFn: async (): Promise<LatencyRow[]> => {
      const end = Math.floor(Date.now() / 1000);
      const start = end - minutes * 60;
      const step = Math.max(Math.floor((end - start) / 60), 15);

      const [p50, p95, p99] = await Promise.all([
        queryMetricsRange("histogram_quantile(0.5, rate(agent_latency_seconds_bucket[2m]))", start, end, step),
        queryMetricsRange("histogram_quantile(0.95, rate(agent_latency_seconds_bucket[2m]))", start, end, step),
        queryMetricsRange("histogram_quantile(0.99, rate(agent_latency_seconds_bucket[2m]))", start, end, step),
      ]);

      const tMap = new Map<number, LatencyRow>();
      p50.forEach((d: MetricPoint) => { tMap.set(d.t, { t: d.t, p50: d.v, p95: 0, p99: 0 }); });
      p95.forEach((d: MetricPoint) => { const e = tMap.get(d.t); if (e) e.p95 = d.v; });
      p99.forEach((d: MetricPoint) => { const e = tMap.get(d.t); if (e) e.p99 = d.v; });

      return Array.from(tMap.values()).sort((a, b) => a.t - b.t);
    },
    refetchInterval: 15_000,
    retry: false,
  });
}