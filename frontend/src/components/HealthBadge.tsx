import { useHealth } from "@/hooks/useHealth";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export function HealthBadge() {
  const { data, isLoading } = useHealth();
  const online = data?.online ?? false;
  return (
    <Badge variant="outline" className={cn("font-mono text-[10px]", online ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300" : isLoading ? "bg-white/5" : "bg-rose-500/10 border-rose-500/30 text-rose-300")}>
      <span className={cn("h-1.5 w-1.5 rounded-full", online ? "bg-emerald-400 animate-pulse" : "bg-rose-400")} />
      {isLoading ? "checking" : online ? "online" : "offline"}
    </Badge>
  );
}