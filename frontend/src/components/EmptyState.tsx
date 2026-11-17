import { motion } from "framer-motion";
import { Sparkles, ArrowRight } from "lucide-react";
import { SUGGESTIONS } from "@/lib/constants";
import { useChat } from "@/hooks/useChat";

export function EmptyState() {
  const chat = useChat();
  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col items-center justify-center min-h-[60vh] px-6 text-center">
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-3xl bg-gradient-to-br from-violet-500/30 to-cyan-500/30 border border-white/10 glow">
        <Sparkles className="h-8 w-8 text-cyan-300" />
      </div>
      <h1 className="text-3xl font-semibold tracking-tight mb-2 bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">Local AI Agent</h1>
      <p className="text-muted-foreground mb-8 max-w-md text-sm">Powered by Ollama, Kong, and full observability. Ask anything.</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-w-2xl w-full">
        {SUGGESTIONS.map((s) => (
          <button key={s} onClick={() => chat.mutate(s)} className="group flex items-center justify-between gap-3 rounded-xl border border-white/5 bg-white/[0.02] px-4 py-3 text-left text-sm hover:border-primary/30 hover:bg-primary/5 transition-all">
            <span className="text-muted-foreground group-hover:text-foreground">{s}</span>
            <ArrowRight className="h-3.5 w-3.5 text-muted-foreground/40 group-hover:text-primary" />
          </button>
        ))}
      </div>
    </motion.div>
  );
}