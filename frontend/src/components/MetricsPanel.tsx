import { motion } from "framer-motion";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { Activity, Zap, ShieldAlert, CheckCircle2, Wrench } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useMetrics, useLatencySeries } from "@/hooks/useMetrics";
import { formatLatency } from "@/lib/utils";

function Stat({ icon: Icon, label, value, accent }: any) {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="rounded-2xl border border-white/5 bg-card/40 p-5 backdrop-blur-xl">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-muted-foreground">{label}</span>
        <Icon className={`h-4 w-4 ${accent}`} />
      </div>
      <p className="text-2xl font-semibold">{value}</p>
    </motion.div>
  );
}

export function MetricsPanel() {
  const { data, isLoading } = useMetrics();
  const { data: series } = useLatencySeries(15);
  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Metrics</h1>
        <p className="text-sm text-muted-foreground">Real-time from Prometheus</p>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Stat icon={Activity} label="Requests" value={isLoading ? "—" : String(data?.total ?? 0)} accent="text-cyan-400" />
        <Stat icon={Zap} label="P95 Latency" value={isLoading ? "—" : formatLatency((data?.latency ?? 0) * 1000)} accent="text-amber-400" />
        <Stat icon={ShieldAlert} label="Guardrail Blocks" value={isLoading ? "—" : String(data?.blocks ?? 0)} accent="text-rose-400" />
        <Stat icon={CheckCircle2} label="Check Fails" value={isLoading ? "—" : String(data?.checks ?? 0)} accent="text-emerald-400" />
        <Stat icon={Wrench} label="Tool Calls" value={isLoading ? "—" : String(Math.round(data?.tools ?? 0))} accent="text-violet-400" />
      </div>
      <Card>
        <CardHeader><h2 className="font-semibold">Latency p50/p95/p99 (15m)</h2></CardHeader>
        <CardContent>
          {!series ? <Skeleton className="h-64 w-full" /> : series.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-sm text-muted-foreground">No data yet</div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={series}>
                <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="t" tickFormatter={(v) => new Date(v).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} stroke="rgba(255,255,255,0.3)" fontSize={11} />
                <YAxis stroke="rgba(255,255,255,0.3)" fontSize={11} tickFormatter={(v) => `${(v * 1000).toFixed(0)}ms`} />
                <Tooltip contentStyle={{ background: "rgba(15,15,25,0.95)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12, fontSize: 12 }} formatter={(v: number) => `${(v * 1000).toFixed(0)}ms`} />
                <Line type="monotone" dataKey="p50" stroke="#06b6d4" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="p95" stroke="#f59e0b" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="p99" stroke="#ef4444" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </div>
  );
}