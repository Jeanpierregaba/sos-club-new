import { Gem, Lock, Medal } from "lucide-react";

import type { BadgeParcours } from "@/lib/api/client";
import { fondBadge } from "@/lib/certification";
import { dateCourte } from "@/lib/dates";

// Les cinq badges du parcours (spec 029) : obtenus en couleur, à venir grisés avec leur palier.
export function BadgesParcours({ badges }: { badges: BadgeParcours[] }) {
  return (
    <ul className="grid grid-cols-2 gap-3 sm:grid-cols-5">
      {badges.map((b) => {
        const obtenu = b.obtenu_le !== null;
        const Icone = b.rang === 5 ? Gem : Medal;
        return (
          <li
            key={b.rang}
            className={`flex flex-col items-center gap-2 rounded-2xl p-4 text-center ring-1 ${obtenu ? "bg-white ring-primary/30" : "bg-mist/60 ring-border"}`}
          >
            <span
              className={`grid size-14 place-items-center rounded-full ${obtenu ? `bg-gradient-to-br ${fondBadge(b.rang)} text-white shadow-card` : "bg-white text-muted-foreground"}`}
            >
              {obtenu ? (
                <Icone aria-hidden className="size-7" />
              ) : (
                <Lock aria-hidden className="size-6" />
              )}
            </span>
            <span className="text-sm font-extrabold leading-tight text-ink">{b.nom}</span>
            <span className="text-xs text-muted-foreground">
              {obtenu && b.obtenu_le
                ? `Obtenu le ${dateCourte(b.obtenu_le)}`
                : `Après ${b.palier} quiz réussis`}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
