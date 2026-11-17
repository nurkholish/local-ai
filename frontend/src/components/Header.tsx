import { Link, useLocation } from "react-router-dom";
import { MessageSquare, Activity, Settings } from "lucide-react";
import { HealthBadge } from "./HealthBadge";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/", label: "Chat", icon: MessageSquare },
  { to: "/metrics", label: "Metrics", icon: Activity },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function Header() {
  const { pathname } = useLocation();
  return (
    <header className="sticky top-0 z-40 border-b border-white/5 bg-background/60 backdrop-blur-xl">
      <div className="flex h-14 items-center gap-6 px-6">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500 to-cyan-500">
            <span className="text-sm font-bold text-white">AI</span>
          </div>
          <span className="font-semibold text-sm tracking-tight">Local-AI</span>
        </Link>
        <nav className="flex items-center gap-1">
          {NAV.map(({ to, label, icon: Icon }) => (
            <Link key={to} to={to} className={cn("flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors", pathname === to ? "bg-white/10 text-foreground" : "text-muted-foreground hover:text-foreground hover:bg-white/5")}>
              <Icon className="h-3.5 w-3.5" />
              {label}
            </Link>
          ))}
        </nav>
        <div className="ml-auto"><HealthBadge /></div>
      </div>
    </header>
  );
}