import type { EtatContenu as Etat } from "@/lib/api/client";
import { ETATS } from "@/lib/articles";

export function EtatContenu({ etat, enLigne = false }: { etat: Etat; enLigne?: boolean }) {
  const { libelle, classe } = ETATS[etat];
  return (
    <span className="inline-flex flex-wrap items-center gap-1.5">
      <span className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${classe}`}>{libelle}</span>
      {enLigne && etat !== "publie" && (
        <span className="rounded-full bg-leaf/20 px-2.5 py-0.5 text-xs font-bold text-ink">
          Version en ligne
        </span>
      )}
    </span>
  );
}
