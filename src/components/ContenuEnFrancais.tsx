// Mention des contenus saisis en français (articles, agenda, quiz…) sur une page lue en anglais ou en allemand
// (spec 052). Rien en français.
import { Languages } from "lucide-react";

import { LANGUE_DE_BASE, langueCourante } from "@/lib/langues";
import { cn } from "@/lib/utils";
import { m } from "@/paraglide/messages.js";

export function ContenuEnFrancais({ className }: { className?: string }) {
  if (langueCourante() === LANGUE_DE_BASE) return null;
  return (
    <p
      className={cn(
        "flex items-center gap-1.5 text-xs font-semibold text-muted-foreground",
        className,
      )}
    >
      <Languages aria-hidden className="h-3.5 w-3.5 shrink-0" />
      {m.contenu_en_francais()}
    </p>
  );
}
