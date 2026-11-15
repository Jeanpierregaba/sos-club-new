import type { RapportResume } from "@/lib/api/client";
import { ETATS_RAPPORT } from "@/lib/rapports";

export function EtatRapport({ etat }: { etat: RapportResume["etat"] }) {
  const { libelle, classe } = ETATS_RAPPORT[etat];
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${classe}`}>{libelle}</span>
  );
}
