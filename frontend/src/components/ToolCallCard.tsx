import { Wrench, CheckCircle2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";

export function ToolCallCard({ step }: { step: { name: string; result: string; blocked: boolean } }) {
  return (
    <div className={cn("rounded-xl border px-3 py-2 text-xs", step.blocked ? "border-rose-500/20 bg-rose-500/5" : "border-white/5 bg-white/[0.02]")}>
      <div className="flex items-center gap-2 mb-1">
        <Wrench className="h-3 w-3 text-muted-foreground" />
        <span className="font-mono font-medium">{step.name}</span>
        {step.blocked ? <XCircle className="h-3 w-3 text-rose-400 ml-auto" /> : <CheckCircle2 className="h-3 w-3 text-emerald-400 ml-auto" />}
      </div>
      <p className="text-muted-foreground line-clamp-2 font-mono text-[10px]">{step.result}</p>
    </div>
  );
}