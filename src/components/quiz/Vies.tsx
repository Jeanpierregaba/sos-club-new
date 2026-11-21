import { Heart } from "lucide-react";

import type { Vies as ViesDuJour } from "@/lib/api/client";
import { messagePlusDeVies } from "@/lib/vies";

// Les vies du jour (spec 048) : 7 cœurs, communs aux quiz des jeux et à la certification. Un cœur plein par vie
// restante ; une vie perdue (partie ratée) ou réservée (partie en cours) est un cœur vide. L'API arbitre : ce
// composant ne fait qu'afficher.
export function Vies({
  vies,
  clair = false,
}: {
  vies: ViesDuJour | null | undefined;
  clair?: boolean;
}) {
  if (!vies) return null;
  const texte = clair ? "text-white" : "text-ink";
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-3">
        <p
          className="flex items-center gap-1"
          // Le texte voisin dit déjà le nombre de vies : les cœurs ne sont pas relus.
          aria-hidden
        >
          {Array.from({ length: vies.total }, (_, i) => (
            <Heart
              key={i}
              aria-hidden
              className={`size-6 ${
                i < vies.restantes
                  ? "fill-logo-red text-logo-red"
                  : clair
                    ? "text-white/40"
                    : "text-logo-red/30"
              }`}
            />
          ))}
        </p>
        <p className={`text-sm font-bold ${texte}`}>
          {vies.restantes} vie{vies.restantes > 1 ? "s" : ""} sur {vies.total} aujourd'hui
        </p>
      </div>
      {vies.restantes === 0 ? (
        <p role="status" className="rounded-2xl bg-logo-red/10 p-3 text-sm font-semibold text-ink">
          {messagePlusDeVies(vies.total)}
        </p>
      ) : (
        <p className={`text-xs font-medium ${clair ? "text-white/75" : "text-muted-foreground"}`}>
          Une partie ratée coûte une vie, une partie réussie ne coûte rien. Jeux et certification
          partagent les mêmes vies.
        </p>
      )}
    </div>
  );
}
