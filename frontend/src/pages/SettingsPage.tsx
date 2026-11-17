import { useState } from "react";
import { useChatStore } from "@/store/chatStore";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Trash2, Check } from "lucide-react";

export function SettingsPage() {
  const [apiKey, setApiKey] = useState(localStorage.getItem("api-key") || "dev-key");
  const [saved, setSaved] = useState(false);
  const clear = useChatStore((s) => s.clear);

  const save = () => {
    localStorage.setItem("api-key", apiKey);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">Configure the console</p>
      </div>
      <Card>
        <CardHeader><h2 className="font-semibold">API Key</h2><p className="text-xs text-muted-foreground mt-1">For Kong gateway</p></CardHeader>
        <CardContent className="space-y-3">
          <Input value={apiKey} onChange={(e) => setApiKey(e.target.value)} />
          <Button onClick={save} className="gap-2">{saved ? <Check className="h-4 w-4" /> : null}{saved ? "Saved" : "Save"}</Button>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><h2 className="font-semibold">Conversation</h2></CardHeader>
        <CardContent>
          <Button variant="destructive" onClick={clear} className="gap-2"><Trash2 className="h-4 w-4" />Clear history</Button>
        </CardContent>
      </Card>
    </div>
  );
}