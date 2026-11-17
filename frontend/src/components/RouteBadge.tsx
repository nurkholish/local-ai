import { Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ROUTE_COLORS } from "@/lib/constants";
import { cn } from "@/lib/utils";

export function RouteBadge({ route }: { route: string }) {
  return (
    <Badge variant="outline" className={cn("capitalize", ROUTE_COLORS[route])}>
      <Sparkles className="h-3 w-3" />
      {route || "auto"}
    </Badge>
  );
}