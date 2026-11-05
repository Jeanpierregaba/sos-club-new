import { Crown, UserMinus } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { EncadreurDuClub, Fonction, MembreClub, MembresDuClub } from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";
import { libelleFonction } from "@/lib/fonctions";

// La liste du club (spec 020) : les membres par pseudonyme, jamais par leur nom (docs/RULES.md), puis les
// encadreurs rattachés. Le président seul reçoit les boutons « Retirer ».
export function ListeMembres({
  liste,
  onRetirerMembre,
  onRetirerEncadreur,
}: {
  liste: MembresDuClub;
  onRetirerMembre?: (membre: MembreClub) => void;
  onRetirerEncadreur?: (encadreur: EncadreurDuClub) => void;
}) {
  return (
    <div className="space-y-5">
      <div>
        <p className="text-sm font-extrabold uppercase tracking-wider text-muted-foreground">
          {liste.membres.length} membre{liste.membres.length > 1 ? "s" : ""}
        </p>
        <ul className="mt-2 divide-y rounded-2xl border">
          {liste.membres.map((m) => (
            <li key={m.id} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3">
              <span>
                <span className="flex items-center gap-2 font-bold text-ink">
                  {m.pseudonyme}
                  {m.president && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-sun/30 px-2 py-0.5 text-xs font-extrabold text-ink">
                      <Crown aria-hidden className="size-3.5" /> Président
                    </span>
                  )}
                </span>
                <span className="text-sm font-medium text-muted-foreground">
                  Membre depuis le {dateCourte(m.depuis)}
                </span>
              </span>
              {onRetirerMembre && !m.president && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onRetirerMembre(m)}
                  className="rounded-full font-bold"
                >
                  <UserMinus className="size-4" /> Retirer
                </Button>
              )}
            </li>
          ))}
        </ul>
      </div>

      <div>
        <p className="text-sm font-extrabold uppercase tracking-wider text-muted-foreground">
          Encadreurs
        </p>
        {liste.encadreurs.length === 0 ? (
          <p className="mt-2 rounded-2xl bg-mist-soft px-4 py-3 text-sm font-medium text-muted-foreground">
            Aucun encadreur rattaché pour l'instant.
          </p>
        ) : (
          <ul className="mt-2 divide-y rounded-2xl border">
            {liste.encadreurs.map((e) => (
              <li
                key={e.id}
                className="flex flex-wrap items-center justify-between gap-2 px-4 py-3"
              >
                <span>
                  <span className="block font-bold text-ink">
                    {e.prenom} {e.nom}
                  </span>
                  <span className="text-sm font-medium text-muted-foreground">
                    {libelleFonction(e.fonction as Fonction)}
                  </span>
                </span>
                {onRetirerEncadreur && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onRetirerEncadreur(e)}
                    className="rounded-full font-bold"
                  >
                    <UserMinus className="size-4" /> Retirer
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
